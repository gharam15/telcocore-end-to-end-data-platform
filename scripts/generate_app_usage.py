#!/usr/bin/env python3
"""Generate app-usage estimates & mock upload metadata linked to TelcoCore monthly usage.
All records are synthetic; NO screenshots or OCR output are fabricated.
"""
import argparse, csv, random, uuid
from collections import defaultdict
from pathlib import Path

APP_WEIGHTS = {
    'VIDEO': [('YouTube', .65), ('Netflix', .20), ('TikTok', .15)],
    'SOCIAL': [('Instagram', .42), ('TikTok', .30), ('Facebook', .28)],
    'MESSAGING': [('WhatsApp', .75), ('Telegram', .25)],
    'OTHER': [('Maps', .45), ('Browser', .55)]
}
APPS = [ (app, category, weight) for category, members in APP_WEIGHTS.items() for app, weight in members ]

def emit(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader();w.writerows(rows)

def generate(base, seed, mock_uploads):
    rnd = random.Random(seed)
    input_path = base/'batch'/'monthly_usage.csv'
    if not input_path.exists():
        raise SystemExit(f'Missing {input_path}; first generate recommender data pack.')
    with input_path.open(newline='', encoding='utf-8') as f:
        usages=list(csv.DictReader(f))
    rows=[];uploads=[];coverage={}
    for item in usages:
        sid=item['subscriber_id'];month=item['month']
        start=f'{month}-01'
        y,m=map(int,month.split('-'))
        end=f'{y+1}-01-01' if m==12 else f'{y}-{m+1:02d}-01'
        total_mb=max(0,round(float(item['data_used_gb'])*1024))
        # Add slight subscriber-specific preference shifts, preserve exact monthly total.
        weights=[weight * rnd.uniform(.5,1.5) for _, _, weight in APPS]
        s=sum(weights); parts=[round(total_mb*w/s) for w in weights]
        if parts: parts[-1]+=total_mb-sum(parts)
        for (app,category,_),used_mb in zip(APPS,parts):
            rows.append({'subscriber_id':sid, 'usage_month':month,'period_start':start,
                'period_end_exclusive':end,'app_name':app,'app_category':category,
                'mobile_data_mb':used_mb,'source':'SYNTHETIC_GENERATOR',
                'verification_status':'NOT_USER_VERIFIED'})
        if mock_uploads and rnd.random() < .12:
            uploads.append({'upload_id':'MOCK-'+uuid.UUID(int=rnd.getrandbits(128)).hex[:16],
                'subscriber_id':sid,'usage_month':month,'upload_status':'MOCK_ONLY',
                'source_type':'SIMULATED_SCREENSHOT_WORKFLOW', 'file_path':'',
                'network_scope':'MOBILE_DATA','period_confirmed':False,
                'user_confirmed':False,'raw_image_retained':False})
        coverage[(sid,month)]=total_mb
    emit(base/'batch'/'app_usage.csv', ['subscriber_id','usage_month','period_start',
        'period_end_exclusive','app_name','app_category','mobile_data_mb','source',
        'verification_status'],rows)
    emit(base/'batch'/'usage_uploads_mock.csv',['upload_id','subscriber_id','usage_month',
        'upload_status','source_type','file_path','network_scope','period_confirmed',
        'user_confirmed','raw_image_retained'],uploads)
    sums=defaultdict(int)
    for r in rows:sums[(r['subscriber_id'],r['usage_month'])]+=int(r['mobile_data_mb'])
    assert sums==coverage,'App usage totals must match monthly CDR-derived data usage'
    print(f'OK: {len(usages)} subscriber-months, {len(rows)} app usage rows, {len(uploads)} mock upload records')
    print('OK: app totals reconcile with every monthly_usage.data_used_gb (rounded to MB)')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--data-dir', default='data')
    p.add_argument('--seed',type=int,default=20261017)
    p.add_argument('--mock-uploads',action='store_true')
    a=p.parse_args();generate(Path(a.data_dir),a.seed,a.mock_uploads)
