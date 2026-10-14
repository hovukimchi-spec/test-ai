import json
import model as M
D = M.build()
tot = 7.3 + 13.8 + 6 * 0.5 + 4 * 0.1 + 0.21 * 0.35 + 1.0
bud = 1.5 + 28
data = dict(
    floors=M.FLOORS, perFloor=M.HOMES_PER_FLOOR, nPon=M.N_PON, inLocal=M.IN_LOCAL, ponPerTower=M.PON_PER_TOWER, splPM=M.SPL_PM, splCab=M.SPL_CAB,
    fiberColors=M.FIBER_COLORS, tubeColors=M.TUBE_COLORS, pmUsed=M.PM_USED, odfs=[dict(name=n, trunks=[a, b_]) for n, a, b_ in M.ODFS], fiberHex=M.FIBER_HEX,
    budget=dict(loss=tot, total=bud, margin=bud - tot),
    cabinets=[dict(c, drawing=next(({'odf': d[0], 'floor': d[1]} for d in M.DRAWING_ODF[c['tower']] if d[2] == c['zone']), None)) for c in D['cabinets']], trunks=D['trunks'],
    spls=[{k: s[k] for k in ('id', 'cab', 'idx', 'fiber', 'trunk', 'n', 'pmspl', 'pmloc', 'pmhalf', 'pmk', 'pmout', 'pmin', 'pon', 'odf', 'tray', 'floors')} for s in D['spls']],
    homes=[{k: h[k] for k in ('code', 'tower', 'floor', 'apt', 'cab', 'spl', 'port', 'trunk', 'fiber', 'pmspl', 'pmloc', 'pmhalf', 'pmk', 'pmout', 'pmin', 'pon')} for h in D['homes']])
html = open('viewer_template.html', encoding='utf-8').read().replace('/*DATA*/null', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
open('ftth_viewer.html', 'w', encoding='utf-8').write(html)
print(len(html) // 1024, 'KB')

# Bản dán lên Artifact: bỏ doctype/html/head/body, thêm meta cho viền an toàn
import re
art = html
art = re.sub(r'<!doctype html>\s*', '', art)
art = re.sub(r'<html[^>]*>\s*<head>\s*', '', art)
art = re.sub(r'<meta charset="utf-8">\s*', '', art)
art = re.sub(r'<meta name="viewport"[^>]*>\s*', '', art)
art = art.replace('</head>', '').replace('<body>', '').replace('</body>', '').replace('</html>', '')
art = art.replace('<title>FTTH Phố Đông – Sơ đồ phối quang</title>', '<title>FTTH Phố Đông</title>\n<meta name="claude:viewport-fit-sides" content="cover">')
open('ftth_viewer_artifact.html', 'w', encoding='utf-8').write(art.strip() + '\n')
print('artifact', len(art) // 1024, 'KB')
