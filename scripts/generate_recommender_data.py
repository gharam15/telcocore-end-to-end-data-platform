#!/usr/bin/env python3
"""Reproducible synthetic telecom dataset. All identities, plans and outcomes are fictional."""
import argparse,csv,random,datetime,calendar,collections,pathlib,math
from decimal import Decimal
PLANS=[
('P01','Starter',90,5,120,50,'PREPAID'),('P02','Social',140,12,100,100,'PREPAID'),
('P03','Everyday',210,20,350,150,'PREPAID'),('P04','Data Plus',300,45,200,150,'PREPAID'),
('P05','Talk Plus',300,15,1000,300,'PREPAID'),('P06','Max',450,75,850,400,'PREPAID'),
('P07','Flex Postpaid',550,100,1000,500,'POSTPAID'),('P08','Premium Postpaid',850,200,2000,1000,'POSTPAID')]
# overage cost assumption for simulations, EGP/GB, EGP/min, EGP/SMS
RATES=(12.0,.42,.20)
GOV=['Cairo','Giza','Alexandria','Sharqia','Dakahlia','Gharbia','Qalyubia','Assiut','Sohag','Minya','Fayoum','Aswan']
FIELDS_CDR=['cdr_id','subscriber_id','event_timestamp','event_type','duration_sec','data_mb','cell_id','charge_amount','ingestion_timestamp']
def write(path,fields,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def money(n):return f'{n:.2f}'
def score(plan,gb,mins,sms):
 pid,_,fee,ag,am,asms,seg=plan
 extra=max(0,gb-ag)*RATES[0]+max(0,mins-am)*RATES[1]+max(0,sms-asms)*RATES[2]
 # Total monthly simulated out-of-bundle spend; excess allowances are allowed, but costly
 return round(fee+extra,2)
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='data');p.add_argument('--subscribers',type=int,default=1000);p.add_argument('--seed',type=int,default=20261017);p.add_argument('--cdr-per-subscriber-month',type=int,default=18);a=p.parse_args()
 if a.subscribers<1 or a.cdr_per_subscriber_month<3:p.error('Need positive scale and >=3 CDR per subscriber-month')
 r=random.Random(a.seed);base=pathlib.Path(a.output)
 write(base/'reference/plans.csv',['plan_id','plan_name','monthly_fee_egp','data_allowance_gb','voice_allowance_min','sms_allowance','customer_segment','overage_egp_per_gb','overage_egp_per_min','overage_egp_per_sms'],[dict(zip(['plan_id','plan_name','monthly_fee_egp','data_allowance_gb','voice_allowance_min','sms_allowance','customer_segment'],x),overage_egp_per_gb=12,overage_egp_per_min=.42,overage_egp_per_sms=.20) for x in PLANS])
 cellrows=[{'cell_id':f'CELL{i:04d}','governorate':GOV[(i-1)%len(GOV)],'network_generation':r.choice(['4G','4G','5G'])} for i in range(1,121)]
 write(base/'reference/cell_towers.csv',list(cellrows[0]),cellrows)
 cells=collections.defaultdict(list)
 for c in cellrows:cells[c['governorate']].append(c['cell_id'])
 subs=[];profiles=[];sub_hist=[];months=['2026-07','2026-08','2026-09'];usage=[];cdr=[];recharges=[];targets=[];actions=[];seq=0
 for i in range(1,a.subscribers+1):
  sid=f'SUB{i:08d}';seg=r.choices(['PREPAID','POSTPAID'],weights=[.82,.18])[0];gov=r.choice(GOV)
  archetype=r.choices(['LIGHT','DATA_HEAVY','VOICE_HEAVY','BALANCED','HEAVY_ALL'],weights=[.2,.25,.18,.27,.1])[0]
  dmean,mmean={'LIGHT':(4,55),'DATA_HEAVY':(58,130),'VOICE_HEAVY':(11,850),'BALANCED':(26,350),'HEAVY_ALL':(105,1100)}[archetype]
  prefer=r.choice(['LOW_COST','HIGH_DATA','HIGH_VOICE','BALANCED']);baseline=r.choice([x for x in PLANS if x[6]==seg]);cur_plan=baseline
  act=datetime.date(2021,1,1)+datetime.timedelta(days=r.randint(0,1700))
  subs.append({'subscriber_id':sid,'phone_number':f'EG-SIM-{i:08d}','activation_date':act.isoformat(),'plan_id':baseline[0],'governorate':gov,'status':'ACTIVE','customer_segment':seg,'created_at':act.isoformat()+'T10:00:00'})
  profiles.append({'subscriber_id':sid,'preferred_channel':r.choice(['APP','USSD','STORE']),'budget_preference_egp':r.choice([150,250,350,500,850]),'preference_type':prefer,'tenure_months_at_2026_09':(2026-act.year)*12+9-act.month,'consent_for_personalization':r.choice(['YES','YES','YES','NO'])})
  for monthindex,mo in enumerate(months):
   y,m=map(int,mo.split('-'));days=calendar.monthrange(y,m)[1]
   dgb=max(.1,r.gauss(dmean,dmean*.22)) * (1+.04*monthindex);mins=max(0,r.gauss(mmean,max(20,mmean*.2)));sms=max(0,round(r.gauss(80,32)))
   # Simulated voluntary changes: some users switch plans after a month; not a recommender label.
   if monthindex>0 and r.random()<.07:
    choices=[x for x in PLANS if x[6]==seg and x[0]!=cur_plan[0]]
    new=r.choice(choices);actions.append({'subscriber_id':sid,'change_date':f'{mo}-01','previous_plan_id':cur_plan[0],'new_plan_id':new[0],'change_source':'SIMULATED_CUSTOMER_CHOICE'});cur_plan=new
   sub_hist.append({'subscriber_id':sid,'month':mo,'plan_id':cur_plan[0],'customer_segment':seg})
   monthcounts=collections.Counter();data_sum=0.;voice_sum=0.;sms_sum=0
   for j in range(a.cdr_per_subscriber_month):
    kind=r.choices(['DATA','VOICE','SMS'],weights=[.5,.32,.18])[0];day=r.randint(1,days);hour=r.randint(0,23);minute=r.randint(0,59);second=r.randint(0,59)
    timestamp=datetime.datetime(y,m,day,hour,minute,second)
    late=r.random()<.04;ingest=timestamp+datetime.timedelta(hours=r.randint(2,72) if late else r.randint(0,1))
    dur=None;mb=None
    if kind=='DATA':mb=round(dgb*1024/a.cdr_per_subscriber_month/.5*r.uniform(.25,1.65),3);data_sum+=mb
    elif kind=='VOICE':dur=max(1,int(mins*60/a.cdr_per_subscriber_month/.32*r.uniform(.3,1.5)));voice_sum+=dur
    else:sms_sum+=1
    seq+=1
    cdr.append({'cdr_id':f'CDR{seq:012d}','subscriber_id':sid,'event_timestamp':timestamp.isoformat(),'event_type':kind,'duration_sec':dur if dur is not None else '', 'data_mb':mb if mb is not None else '', 'cell_id':r.choice(cells[gov]),'charge_amount':'0.00','ingestion_timestamp':ingest.isoformat()})
    monthcounts[kind]+=1
   # Monthly totals reflect generated events, rather than independently random synthetic numbers.
   gb=round(data_sum/1024,3);vm=round(voice_sum/60,2);sm=sms_sum
   paid=score(cur_plan,gb,vm,sm)
   usage.append({'subscriber_id':sid,'month':mo,'data_used_gb':gb,'voice_used_min':vm,'sms_sent':sm,'current_plan_id':cur_plan[0],'estimated_monthly_cost_egp':money(paid),'cdr_event_count':a.cdr_per_subscriber_month})
   if seg=='PREPAID':
    recharges.append({'recharge_id':f'RCH{len(recharges)+1:010d}','subscriber_id':sid,'recharge_timestamp':f'{mo}-{r.randint(1,days):02d}T12:00:00','amount_egp':r.choice([50,100,150,200,300,500]),'channel':r.choice(['APP','CARD','RETAIL'])})
   # Scenario label: hypothetical cheapest plan (same segment) for that MONTH'S observed usage.
   # ONLY suitable for cost-simulation ground truth, NOT behavior prediction, and never train on same-month label inputs to predict that month.
   candidates=[x for x in PLANS if x[6]==seg]
   ranked=sorted(candidates,key=lambda x:(score(x,gb,vm,sm),x[2],x[0]));best=ranked[0]
   targets.append({'subscriber_id':sid,'usage_month':mo,'current_plan_id':cur_plan[0],'cost_optimal_plan_id':best[0],'simulated_current_cost_egp':money(paid),'simulated_best_cost_egp':money(score(best,gb,vm,sm)),'potential_savings_egp':money(max(0,paid-score(best,gb,vm,sm))),'label_origin':'RULE_BASED_COST_SIMULATION'})
 write(base/'batch/subscribers.csv',list(subs[0]),subs)
 write(base/'batch/customer_profiles.csv',list(profiles[0]),profiles)
 write(base/'batch/subscriber_plan_history.csv',list(sub_hist[0]),sub_hist)
 write(base/'batch/cdr_events.csv',FIELDS_CDR,cdr)
 write(base/'batch/monthly_usage.csv',list(usage[0]),usage)
 write(base/'batch/recharges.csv',list(recharges[0]),recharges)
 write(base/'batch/plan_changes.csv',['subscriber_id','change_date','previous_plan_id','new_plan_id','change_source'],actions)
 write(base/'batch/cost_optimal_plan_labels.csv',list(targets[0]),targets)
 print(f'Generated {len(subs)} subscribers, {len(cdr)} CDRs, {len(usage)} monthly-usage rows and {len(targets)} cost-simulation labels.')
if __name__=='__main__': main()
