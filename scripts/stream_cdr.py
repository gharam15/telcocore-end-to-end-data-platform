#!/usr/bin/env python3
"""Simulated real-time telecom CDR source; JSON Lines to stdout or Kafka."""
import argparse,csv,datetime,json,pathlib,random,sys,time
from decimal import Decimal,ROUND_HALF_UP

def records(p):
 with open(p,newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def main():
 p=argparse.ArgumentParser(description='Emit synthetic CDRs continuously or for --count records')
 p.add_argument('--data-dir',default='data');p.add_argument('--rate',type=float,default=2.0,help='events/sec');p.add_argument('--count',type=int,default=0,help='0=continuous')
 p.add_argument('--seed',type=int,default=123);p.add_argument('--sink',choices=['stdout','kafka'],default='stdout');p.add_argument('--bootstrap-servers',default='localhost:9092');p.add_argument('--topic',default='telcocore.cdr.raw')
 p.add_argument('--late-pct',type=float,default=0.05);p.add_argument('--duplicate-pct',type=float,default=0.02)
 a=p.parse_args()
 if a.rate<=0 or a.count<0 or not(0<=a.late_pct<=1) or not(0<=a.duplicate_pct<=1):p.error('Invalid rate/count/probability')
 rng=random.Random(a.seed);base=pathlib.Path(a.data_dir)
 subs=records(base/'batch/subscribers.csv');cells=records(base/'reference/cell_towers.csv')
 eligible=[s for s in subs if s['status']=='ACTIVE']
 if not eligible or not cells: p.error('Need active subscribers and cell towers')
 producer=None
 if a.sink=='kafka':
  try:from kafka import KafkaProducer
  except ImportError: p.error('Install optional dependency: pip install kafka-python')
  producer=KafkaProducer(bootstrap_servers=a.bootstrap_servers,value_serializer=lambda v:json.dumps(v,separators=(',',':')).encode('utf-8'),key_serializer=lambda x:x.encode('utf-8'),acks='all',retries=3)
 last=None;i=0
 try:
  while not a.count or i<a.count:
   start=time.monotonic()
   if last is not None and rng.random()<a.duplicate_pct:
    record=dict(last);record['ingestion_timestamp']=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds');record['is_simulated_duplicate']=True
   else:
    sub=rng.choice(eligible);kind=rng.choices(['VOICE','SMS','DATA'],weights=[35,20,45])[0]
    dur=rng.randint(10,1800) if kind=='VOICE' else None
    mb=round(rng.uniform(0.5,1200),3) if kind=='DATA' else None
    amount=(dur*0.003 if dur is not None else 0.25 if kind=='SMS' else mb*0.007)
    now=datetime.datetime.now(datetime.timezone.utc)
    late=rng.random()<a.late_pct
    etime=now-datetime.timedelta(hours=rng.randint(1,48)) if late else now
    record={'cdr_id':f'LIVE-{a.seed}-{i+1:012d}','subscriber_id':sub['subscriber_id'],'event_timestamp':etime.isoformat(timespec='seconds'),'event_type':kind,'duration_sec':dur,'data_mb':mb,'cell_id':rng.choice(cells)['cell_id'],'charge_amount':str(Decimal(str(amount)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)),'ingestion_timestamp':now.isoformat(timespec='seconds'),'is_simulated_duplicate':False,'is_late_event':late}
    last=dict(record)
   if producer: producer.send(a.topic,key=record['subscriber_id'],value=record).get(timeout=20)
   else:print(json.dumps(record,ensure_ascii=False,separators=(',',':')),flush=True)
   i+=1;time.sleep(max(0,1/a.rate-(time.monotonic()-start)))
 except KeyboardInterrupt:pass
 finally:
  if producer:producer.flush(timeout=20);producer.close()
  print(f'Emitted {i} records to {a.sink}',file=sys.stderr)
if __name__=='__main__':main()
