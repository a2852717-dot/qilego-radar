#!/usr/bin/env python3
"""Collect publicly syndicated news RSS, not private marketplace metrics."""
import json, pathlib, urllib.parse, urllib.request, xml.etree.ElementTree as ET, datetime, re, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'data.json'
KEYWORDS=['蝦皮 熱銷 商品','抖音 爆款 商品','小紅書 爆款 好物','淘寶 熱賣 商品','1688 新品 趨勢','冬季 保暖 商品','美甲 收納 新品','台灣 電商 熱銷']
PLATFORMS=['蝦皮','抖音','小紅書','淘寶','1688']

def collect():
    records=[]; errors=[]
    for kw in KEYWORDS:
        url='https://news.google.com/rss/search?q='+urllib.parse.quote(kw+' when:30d')+'&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'QilegoRadar/1.0 (public RSS; no platform scraping)'})
            with urllib.request.urlopen(req,timeout=18) as response: raw=response.read(1500000)
            root=ET.fromstring(raw)
            for item in root.findall('./channel/item')[:25]:
                title=(item.findtext('title') or '').strip()
                link=(item.findtext('link') or '').strip()
                date=(item.findtext('pubDate') or '').strip()
                source=item.find('source')
                publisher=(source.text or '').strip() if source is not None else ''
                if not title or not link: continue
                uid=hashlib.sha256(link.encode()).hexdigest()[:16]
                records.append({'id':uid,'title':title[:240],'link':link,'published':date,'publisher':publisher,'search_keyword':kw,'platform_mentions':[p for p in PLATFORMS if p in (title+' '+kw)],'source_type':'public_news_rss','verified_sales':False})
        except Exception as exc:
            errors.append({'keyword':kw,'error':type(exc).__name__})
    unique={r['id']:r for r in records}
    result={'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'data_type':'public_news_mentions_not_marketplace_sales','coverage':'Google News public RSS; mentions are NOT platform internal data','articles':list(unique.values()),'errors':errors,'queries':KEYWORDS}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('articles:',len(unique),'errors:',len(errors))
if __name__=='__main__':collect()
