#!/usr/bin/env python3
"""Public Google Trends TW trending-search RSS, NOT Shopee sales or Shopee keyword volumes.
No scraping of marketplace sites; stores only the public syndicated RSS data.
"""
import datetime as dt
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'signals.json'
RSS = 'https://trends.google.com/trending/rss?geo=TW'
# Specific products only; broad categories intentionally omitted. These are FILTER TERMS,
# not claims of sales, trends, popularity, or endorsements.
PRODUCTS = [
    ('美甲拋光條','美甲'),('穿戴甲收納冊','美甲'),('美甲雙面黏膠','美甲'),
    ('美甲凝膠燈','美甲'),('甲片展示卡紙','美甲'),('洗甲棉','美甲'),
    ('抽屜分隔收納盒','收納'),('滑輪收納箱','收納'),('衣物壓縮袋','收納'),
    ('保冷便當袋','居家'),('折疊瀝水架','廚房'),('茶葉過濾器','廚房'),
    ('尼龍托特包','包包'),('手機斜背包','包包'),('寵物除毛刷','寵物'),
    ('寵物飲水器','寵物'),('保暖中筒襪','季節'),('機車防寒手套','季節'),
    ('防曬袖套','季節'),('防曬口罩','季節'),('桌面收納盒','收納'),
    ('美甲筆刷','美甲'),('美甲色卡','美甲'),('穿戴甲','美甲'),
]

def collect(fetcher=None):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    result = {
        'updated_at': now,
        'source': {'name':'Google Trends 台灣每日熱門搜尋 RSS','url':RSS,'scope':'TW','metric':'RSS 搜尋趨勢與粗略流量標籤，不是蝦皮搜尋次數或銷量'},
        'shopee': {'monthly_sales':None,'keyword_search_volume':None,'status':'尚無經確認可合法免費自動讀取的蝦皮全站數據來源'},
        'records': [], 'matched_products':[], 'errors':[],
        'product_filter_count':len(PRODUCTS),
    }
    try:
        if fetcher:
            raw=fetcher(RSS)
        else:
            req=urllib.request.Request(RSS,headers={'User-Agent':'QilegoMarketResearch/2.0 (public RSS) Accept application/rss+xml'})
            with urllib.request.urlopen(req,timeout=22) as response: raw=response.read(2000000)
        root=ET.fromstring(raw)
        items=root.findall('./channel/item')
        ns={'ht':'https://trends.google.com/trending/rss'}
        for item in items[:100]:
            title=(item.findtext('title') or '').strip()
            if not title: continue
            traffic=(item.findtext('ht:approx_traffic',default='',namespaces=ns) or '').strip()
            link=(item.findtext('link') or '').strip()
            date=(item.findtext('pubDate') or '').strip()
            news=[]
            for story in item.findall('ht:news_item',ns)[:3]:
                news.append({'title':story.findtext('ht:news_item_title','',ns), 'url':story.findtext('ht:news_item_url','',ns), 'source':story.findtext('ht:news_item_source','',ns)})
            result['records'].append({'term':title,'traffic_label':traffic or None,'published':date,'link':link,'related_news':news,'source':'google_trends_rss'})
        for name,category in PRODUCTS:
            hits=[r for r in result['records'] if name.lower() in r['term'].lower()]
            if hits: result['matched_products'].append({'product':name,'category':category,'hits':hits,'evidence_count':len(hits)})
    except Exception as exc:
        result['errors'].append({'source':'google_trends_rss','error_type':type(exc).__name__,'message':'RSS 來源目前無法讀取，不能推論搜尋量為 0'})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('trends:',len(result['records']),'exact_product_hits:',len(result['matched_products']),'errors:',len(result['errors']))
    return result

if __name__ == '__main__': collect()
