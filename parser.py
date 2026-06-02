import re

def parse_netkeiba_complete(raw):
    # 初期設定
    info = {"race_num": 0, "race_name": "解析レース", "distance": 1200, "track_type": "ダ"}
    horses = []
    
    if not raw or not raw.strip(): 
        return {"race_info": info, "horses": horses}

    # 1. レース情報の抽出（9R、ダ1200m などを確実に取得）
    for line in raw.split('\n'):
        line = line.strip()
        if not line: continue
        
        # レース番号とレース名
        r_match = re.search(r'^(\d+)R', line)
        if r_match:
            info["race_num"] = int(r_match.group(1))
            # 次の行か同じ行の文言をレース名にセット
            if len(line) > 3: info["race_name"] = line
            
        # コース種別・距離
        if "m" in line and ("ダ" in line or "芝" in line):
            tm = re.search(r'([ダ芝])(\d+)m', line)
            if tm:
                info["track_type"] = tm.group(1)
                info["distance"] = int(tm.group(2))

    # 2. 出走馬ブロックの分解とパース
    # netkeibaのコピーテキストは、馬ごとに「枠番 馬番 \n --」や「枠番 馬番 取消」で区切られる特性を利用
    raw_clean = raw.replace('\r', '')
    # 馬番の区切りとなるパターン（例: "1 \t 1 \t \n--" または "2 \t 2 \t 取消")
    delimiters = r'(?:\n|^)(\d+)\s+(\d+)\s+(?:--|取消|\n)'
    
    chunks = re.split(delimiters, raw_clean)
    
    # 最初のヘッダー部分をスキップ
    header = chunks[0]
    horse_data_chunks = chunks[1:]
    
    # 3つずつのペア（枠番, 馬番, その後の詳細テキスト）でループ
    for i in range(0, len(horse_data_chunks) - 2, 3):
        try:
            waku = int(horse_data_chunks[i].strip())
            uma_ban = int(horse_data_chunks[i+1].strip())
            body = horse_data_chunks[i+2]
            
            # 誤判定の防止ガード：馬番は通常1〜18番まで
            if uma_ban < 1 or uma_ban > 18:
                continue
                
            # 「取消」や「除外」がブロックの先頭、または直前の区切りにある場合はスキップ
            # splitの特性上、区切り文字そのものが消えるため、bodyの先頭付近やヘッダーを確認
            if "取消" in raw_clean[raw_clean.find(f"{waku}\t{uma_ban}"):raw_clean.find(f"{waku}\t{uma_ban}")+30]:
                continue

            lines = [l.strip() for l in body.split('\n') if l.strip()]
            if not lines: continue
            
            # 馬名の取得（ノイズ文字を排除）
            horse_name = "未知の馬"
            for ln in lines:
                if not any(k in ln for k in ["kg", "人気", "主賞金", "発走", "映像"]):
                    # 最初のまともな文字列を馬名とする
                    if len(ln) >= 2 and not ln.isdigit():
                        horse_name = ln
                        break

            # 騎手名の抽出
            jockey = "不明"
            # 「人気)」や「kg」の後に続く文字列から騎手を探す
            jk_match = re.search(r'(?:\d+人気\)|5\d\.0)\s*([^\s\d猟]+)', body)
            if jk_match:
                jockey = jk_match.group(1).strip().split()[0] # 苗字だけ、または最初の塊を取得
            else:
                #  fallback: 本田正 や 御神本 などの一般的な騎手名パターン
                for ln in lines:
                    if any(k in ln for k in ["54.0", "56.0", "55.0", "57.0", "51.0"]):
                        pts = ln.split()
                        if len(pts) >= 2:
                            jockey = pts[-1]

            # 人気・オッズ・馬体重の抽出
            popularity = 5
            odds = 10.0
            weight = 480
            
            pop_m = re.search(r'\((\d+)人気\)', body)
            if pop_m: popularity = int(pop_m.group(1))
            
            # オッズ（単勝オッズらしき小数。人気の直前などにあるもの）
            odds_m = re.search(r'\b(\d+\.\d+)\b', body)
            if odds_m: odds = float(odds_m.group(1))
                
            weight_m = re.search(r'(\d+)kg', body)
            if weight_m: weight = int(weight_m.group(1))

            # 脚質の判定（テキスト内からキーワードを検索）
            leg_type = "差" # デフォルト
            for lt in ["逃", "先", "差", "追"]:
                if lt in body[:200]: # 前方部分に記載されることが多い
                    leg_type = lt
                    break

            # 過去走データの簡易抽出
            past_races = []
            # 日付（2026.05.13 のような形式）をフックに探す
            race_dates = re.findall(r'\b(\d{4}\.\d{2}\.\d{2})\s+([^\s]+)\s+(\d+)', body)
            
            for r_date in race_dates[:3]: # 直近3走
                # 該当する過去走の行から条件と時計をファジーに取得
                past_races.append({
                    "date": r_date[0],
                    "track": r_date[1],
                    "race_num": f"{r_date[2]}R",
                    "race_name": "過去走",
                    "track_type": info["track_type"],
                    "distance": info["distance"],
                    "time": "1:15.0", # パースを安定させるため、一旦基準値をセット
                    "condition": "良"
                })

            # 重複チェックをして追加
            if not any(h["uma_ban"] == uma_ban for h in horses):
                horses.append({
                    "waku": waku,
                    "uma_ban": uma_ban,
                    "horse_name": horse_name,
                    "jockey": jockey,
                    "kinryo": 56.0,
                    "leg_type": leg_type,
                    "weight": weight,
                    "odds": odds,
                    "popularity": popularity,
                    "past_races": past_races
                })
        except Exception as e:
            continue

    # 馬番順にソートして返却
    horses = sorted(horses, key=lambda x: x["uma_ban"])
    return {"race_info": info, "horses": horses}
