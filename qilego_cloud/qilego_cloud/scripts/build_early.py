#!/usr/bin/env python3
"""Build evidence-only product trend observations from syndicated Google Trends RSS.

This is NOT Shopee sales, a product-wide search volume feed, or a prediction model.
Only signal events provided by collect_signals.py are used. Historical snapshots
are committed to GitHub, keyed by UTC+8 calendar day to avoid counting reruns.
"""
import datetime as dt
import json
import re
from collections import defaultdict
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / 'docs'
SOURCE = DOCS / 'signals.json'
HISTORY = DOCS / 'early_history.json'
OUTPUT = DOCS / 'early.json'
TZ = dt.timezone(dt.timedelta(hours=8))
# PRODUCT ENDINGS are syntactic filters, not an endorsed preselected product list.
# Broad terms (美甲 / 寵物 / 收納) never count as concrete products.
ENDINGS = ('收納盒','收納袋','收納箱','保冷袋','保鮮盒','行動電源','充電線','充電器','藍牙耳機','滑鼠','鍵盤',
           '防曬袖套','防曬口罩','防曬帽','遮陽帽','防水袋','除毛刷','除毛滾輪','洗甲棉','拋光條','甲片','美甲燈',
           '凝膠燈','手提包','斜背包','托特包','側背包','後背包','雨傘','水壺','保溫杯','電風扇','小風扇',
           '吸塵器','瀝水架','瀝水籃','垃圾桶','掛勾','衣架','襪子','手套','筆袋','美工刀','護腕','按摩器',
           '寵物碗','貓砂盆','貓抓板','飲水器','鞋架','鞋袋','推車','收納架','清潔刷','保冷杯')
STOP = ('優惠','特價','直播','折扣','新聞','評價','開箱','推薦','排行','攻略','抽獎','免費','促銷','蝦皮','爆款','熱銷')


def product_name(term):
    """Conservative extractor; a false negative is safer than a fabricated SKU."""
    s = re.sub(r'\s+', '', str(term or ''))
    if len(s) < 3 or len(s) > 42 or any(x in s for x in STOP):
        return None
    # Only standalone specific-product search phrase, not arbitrary news headlines.
    if re.search(r'[，,。！!？?：:｜|／/【】()（）]', s):
        return None
    if re.search(r'\d{4}年|政治|颱風|股價|選舉|地震', s):
        return None
    if not any(s.endswith(x) for x in ENDINGS):
        return None
    if re.fullmatch(r'[\u4e00-\u9fffA-Za-z0-9\-]+', s) is None:
        return None
    return s


def build(now=None):
    now = now or dt.datetime.now(TZ)
    day = now.astimezone(TZ).date()
    raw = json.loads(SOURCE.read_text(encoding='utf-8')) if SOURCE.exists() else {}
    records = raw.get('records', []) if isinstance(raw, dict) else []
    if not isinstance(records, list):
        records = []
    errs = raw.get('errors', []) if isinstance(raw, dict) else []
    valid = not errs and isinstance(records,list) and len(records) > 0
    past = {'days': {}}
    if HISTORY.exists():
        try:
            past = json.loads(HISTORY.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            past = {'days': {}}
    days = past.get('days', {}) if isinstance(past.get('days'),dict) else {}
    if valid:
        products = {}
        for entry in records:
            name = product_name(entry.get('term')) if isinstance(entry,dict) else None
            if name:
                products[name] = {'product':name,'source':'Google Trends TW trending RSS',
                    'source_url':'https://trends.google.com/trending?geo=TW',
                    'traffic_label':entry.get('traffic_label'),
                    'published':entry.get('published')}
        # A second run on the same day replaces, rather than doubles, observations.
        days[str(day)] = {'source':'Google Trends TW trending RSS','observations':list(products.values()),
                          'raw_trending_terms':len(records)}
    earliest = str(day - dt.timedelta(days=90))
    days = {d:entry for d,entry in days.items() if earliest <= d <= str(day)}
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps({'schema_version':1,'days':dict(sorted(days.items()))},ensure_ascii=False,indent=2),encoding='utf-8')
    history = defaultdict(list)
    for date, entry in days.items():
        for obj in entry.get('observations',[]):
            name=obj.get('product')
            if name: history[name].append((date,obj))
    confirmed, observations = [], []
    for name, events in sorted(history.items()):
        events.sort()
        count7 = sum(str(day-dt.timedelta(days=6)) <= d <= str(day) for d,_ in events)
        before7 = sum(str(day-dt.timedelta(days=13)) <= d < str(day-dt.timedelta(days=6)) for d,_ in events)
        count30 = sum(str(day-dt.timedelta(days=29)) <= d <= str(day) for d,_ in events)
        item = {'product':name,'source':'Google Trends TW trending RSS','first_seen':events[0][0],
                'last_seen':events[-1][0],'observed_days_7d':count7,'observed_days_previous_7d':before7,
                'observed_days_30d':count30,'latest_traffic_label':events[-1][1].get('traffic_label'),
                'source_url':events[-1][1].get('source_url'), 'shopee_units_sold_30d':None,
                'shopee_search_volume_30d':None,'sales_probability':None,
                'note':'熱門搜尋榜出現的天數；不是搜尋次數或銷量'}
        # Only after >= 14 actually observed calendar days (not simply a 14-day date gap).
        available_14 = sum(str(day-dt.timedelta(days=i)) in days for i in range(14))
        item['observation_days_available_14d'] = available_14
        if available_14 >= 10 and count7 >= 2 and count7 > before7:
            item['status']='持續升溫線索（非銷量預測）'
            confirmed.append(item)
        else:
            item['status']='觀測不足／未達成長門檻'
            observations.append(item)
    result={'schema_version':1,'generated_at':now.isoformat(),'source':'Google Trends TW trending RSS',
            'source_note':'只觀測免費熱門搜尋 RSS，不含蝦皮全站商品銷量、完整商品搜索量、未驗證預測機率。',
            'history_days':len(days),'today_raw_terms':len(records) if valid else None,
            'today_extracted_products':len(days.get(str(day),{}).get('observations',[])),
            'data_status':'ok' if valid else 'source_unavailable',
            'warnings':['資料來源當日沒有有效結果，保留歷史但不以 0 代替缺失資料'] if not valid else [],
            'early_signals':sorted(confirmed,key=lambda x:(-x['observed_days_7d'],x['product'])),
            'watchlist':sorted(observations,key=lambda x:(-x['observed_days_30d'],x['product'])),
            'metrics_description':{'observed_days_7d':'近7天中此具體商品出現在公開熱門搜尋 RSS 的天數',
                'observed_days_previous_7d':'前7天出現天數',
                'shopee_units_sold_30d':'未接入合法授權銷量資料時為 null',
                'sales_probability':'未經驗證，永遠不虛構機率'}}
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('observed days:',len(days),'today products:',result['today_extracted_products'],
          'early signals:',len(confirmed),'unverified:',len(observations),'source status:',result['data_status'])
    return result

if __name__ == '__main__':
    build()
