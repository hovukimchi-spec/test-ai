import json
import model as M
D = M.build()
tot = 7.3 + 13.8 + 6 * 0.5 + 4 * 0.1 + 0.21 * 0.35 + 1.0
bud = 1.5 + 28
data = dict(
    floors=M.FLOORS, perFloor=M.HOMES_PER_FLOOR, nPon=M.N_PON, splPM=M.SPL_PM, splCab=M.SPL_CAB,
    fiberColors=M.FIBER_COLORS, tubeColors=M.TUBE_COLORS, pmUsed=M.PM_USED, odfs=[dict(name=n, trunks=[a, b_]) for n, a, b_ in M.ODFS], fiberHex=M.FIBER_HEX,
    budget=dict(loss=tot, total=bud, margin=bud - tot),
    cabinets=D['cabinets'], trunks=D['trunks'],
    spls=[{k: s[k] for k in ('id', 'cab', 'idx', 'fiber', 'trunk', 'n', 'pmspl', 'pmloc', 'pmout', 'pon')} for s in D['spls']],
    homes=[{k: h[k] for k in ('code', 'tower', 'floor', 'apt', 'cab', 'spl', 'port', 'trunk', 'fiber', 'pmspl', 'pmloc', 'pmout', 'pon')} for h in D['homes']])
html = open('viewer_template.html', encoding='utf-8').read().replace('/*DATA*/null', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
open('ftth_viewer.html', 'w', encoding='utf-8').write(html)
print(len(html) // 1024, 'KB')
