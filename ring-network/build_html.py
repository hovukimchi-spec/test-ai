"""Dựng ring_network_viewer.html (một file, offline, không thư viện). Chạy: python3 build_html.py"""
import os,sys,json
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
import model
d=model.build()
import export_data
RAW=export_data.raw(d)
tpl=open(os.path.join(HERE,'viewer_template.html'),encoding='utf-8').read()
out=os.path.join(HERE,'ring_network_viewer.html')
rd=lambda f:open(os.path.join(HERE,f),encoding='utf-8').read()
html=tpl.replace('__APP__',rd('viewer_app.js')).replace('__ENGINE__',rd('engine.js')).replace('__XLSX__',rd('xlsx_io.js'))
html=html.replace('__RAW__',json.dumps(RAW,ensure_ascii=False,separators=(',',':')))
open(out,'w',encoding='utf-8').write(html)
print('saved',out,os.path.getsize(out)//1024,'KB')
