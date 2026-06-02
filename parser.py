import re

def parse_netkeiba_complete(raw):
    info = {"race_num": 0, "race_name": "解析エラー", "distance": 1200, "track_type": "ダ"}
    horses = []
    if not raw or not raw.strip(): 
        return {"race_info": info, "horses": horses}
    try:
        m = re.search(r'(\d+)R\s+([^\n]+)', raw)
        if m: 
            info["race_num"] = int(m.group(1))
            info["race_name"] = m.group(2).strip()
        tm = re.search(r'([ダ芝])(\d+)m', raw)
        if tm: 
            info["track_type"] = tm.group(1)
            info["distance"] = int(tm.group(2))
    except: 
        pass

    blocks = re.split(r'(?:\n|^)(\d+)\s+(\d+)\s*\n?--', raw)[1:]
    for i in range(0, len(blocks) - 2, 3):
        try:
            wk = int(blocks[i])
            ub = int(blocks[i+1])
            body = blocks[i+2].strip()
            lines = [l.strip() for l in body.split('\n') if l.strip()]
            if not lines: continue
            
            wt, pop, odds = 450, 1, 5.0
            wm = re.search(r'(\d+)kg', body)
            if wm: wt = int(wm.group(1))
            pm = re.search(r'\((\d+)人気\)', body)
            if pm: pop = int(pm.group(1))
            om = re.search(r'\b(\d+\.\d+)\b', body)
            if om: odds = float(om.group(1))

            leg = "不明"
            for lt in ["逃", "先", "差", "追"]:
                if lt in body: leg = lt; break

            jk = "不明"
            jm = re.search(r'人気\)\s+([^\s\d]+)', body)
            if jm: jk = jm.group(1)
            else:
                for ln in lines:
                    if "人気)" in ln or "kg" in ln:
                        pts = ln.split()
                        if len(pts) >= 3: jk = pts[2]; break

            past = []
            p_regex = r'\b\d{4}\.\d{2}\.\d{2}\s+[^\s]+\s+\d+\b'
            starts = [m.start() for m in re.finditer(p_regex, body)]
            for idx, s_pos in enumerate(starts):
                try:
                    e_pos = starts[idx+1] if idx+1 < len(starts) else len(body)
                    chk = body[s_pos:e_pos].strip()
                    r_lns = [rl.strip() for rl in chk.split('\n') if rl.strip()]
                    if len(r_lns) < 2: continue
                    meta = r_lns[0].split()
                    ti = re.search(r'([芝ダ])(\d+)\s+([\d:]+\.\d+)\s+([良稍重不])', chk)
                    if ti:
                        past.append({
                            "date": meta[0], "track": meta[1], "race_num": meta[2], "race_name": r_lns[1],
                            "track_type": ti.group(1), "distance": int(ti.group(2)), "time": ti.group(3), "condition": ti.group(4)
                        })
                except: continue

            horses.append({
                "waku": wk, "uma_ban": ub, "horse_name": lines[0], "jockey": jk,
                "kinryo": 54.0, "leg_type": leg, "weight": wt, "odds": odds, "popularity": pop, "past_races": past
            })
        except: continue
    return {"race_info": info, "horses": horses}
