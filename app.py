import re

def parse_netkeiba_complete(raw_text):
    """
    エラーで絶対に画面を真っ白にさせない、安全ガード付きパーススクリプト
    """
    # 初期構造を作っておく（パース失敗しても空のデータで返すことで画面崩壊を防ぐ）
    race_info = {
        "race_num": 0, "race_name": "データ解析エラー", "distance": 1200,
        "track_type": "ダ", "direction": "左", "weather": "不明", "condition": "良"
    }
    horses_list = []

    if not raw_text or not raw_text.strip():
        return {"race_info": race_info, "horses": horses_list}

    # 1. レース基本情報の抽出（安全対策版）
    try:
        info_match = re.search(r'(\d+)R\s+([^\n]+)\s+.*?発走\s+/\s+([ダ芝])(\d+)m\s*\((.*?)\)\s+/\s+天候:(.*?)\s+/\s+馬場:(.*)', raw_text)
        if info_match:
            race_info["race_num"] = int(info_match.group(1))
            race_info["race_name"] = info_match.group(2).strip()
            race_info["track_type"] = info_match.group(3)
            race_info["distance"] = int(info_match.group(4))
            race_info["direction"] = info_match.group(5).strip()
            race_info["weather"] = info_match.group(6).strip()
            race_info["condition"] = info_match.group(7).split()[0].strip()
    except Exception as e:
        print(f"[Warning] レース情報の取得に失敗: {e}") # ログには出すが落とさない

    # 2. 馬ごとのブロックに分割（行頭の枠番・馬番・ハイフンを厳密にマッチング）
    block_pattern = r'(?:\n|^)(\d+)\s+(\d+)\s*\n?--'
    chunks = re.split(block_pattern, raw_text)
    blocks = chunks[1:]
    
    # 分割データが3の倍数になっていない場合の安全ガード
    for i in range(0, len(blocks) - 2, 3):
        try:
            waku = int(blocks[i].strip())
            uma_ban = int(blocks[i+1].strip())
            body = blocks[i+2].strip()
            
            lines = [l.strip() for l in body.split('\n') if l.strip()]
            if not lines:
                continue
                
            horse_name = lines[0]
            
            # 体重・オッズなどの安全抽出
            weight, weight_diff, odds, popularity = None, None, 1.0, 1
            weight_match = re.search(r'(\d+)kg\((.*?)\)\s+([\d.]+)\s+\((\d+)人気\)', body)
            if weight_match:
                weight = int(weight_match.group(1))
                weight_diff = weight_match.group(2)
                odds = float(weight_match.group(3))
                popularity = int(weight_match.group(4))
                
            # 斤量
            kinryo = None
            kinryo_match = re.search(r'\b(\d{2}\.\d)\b', body)
            if kinryo_match:
                kinryo = float(kinryo_match.group(1))
                
            # 脚質
            leg_type = "不明"
            for lt in ["逃", "先", "差", "追"]:
                if lt in lines:
                    leg_type = lt
                    break
            if leg_type == "不明":
                lt_match = re.search(r'\b(逃|先|差|追)\b', body)
                if lt_match:
                    leg_type = lt_match.group(1)

            # --- 過去走の抽出（ここが最もエラーが起きやすいので個別try） ---
            past_races = []
            race_starts = [m.start() for m in re.finditer(r'\b\d{4}\.\d{2}\.\d{2}\s+[^\s]+\s+\d+\b', body)]
            
            for idx, start_pos in enumerate(race_starts):
                try:
                    end_pos = race_starts[idx+1] if idx+1 < len(race_starts) else len(body)
                    race_chunk = body[start_pos:end_pos].strip()
                    race_lines = [rl.strip() for rl in race_chunk.split('\n') if rl.strip()]
                    
                    if len(race_lines) < 2:
                        continue
                        
                    # 日付、競馬場などの分解（要素数不足でのIndexErrorを徹底防御）
                    head_meta = race_lines[0].split()
                    if len(head_meta) < 3:
                        continue
                    date = head_meta[0]
                    track_name = head_meta[1]
                    past_race_num = head_meta[2]
                    
                    past_race_name = race_lines[1] if len(race_lines) > 1 else "不明"
                    
                    # タイムと馬場の抽出
                    track_info_match = re.search(r'([芝ダ])(\d+)\s+([\d:]+\.\d+)\s+([良|稍|重|不])', race_chunk)
                    
                    if track_info_match:
                        p_type = track_info_match.group(1)
                        p_dist = int(track_info_match.group(2))
                        p_time = track_info_match.group(3)
                        p_cond = track_info_match.group(4)
                        
                        pass_order, agari = None, None
                        pass_match = re.search(r'([\d-]+)\s+\(([\d.]+)\)', race_chunk)
                        if pass_match:
                            pass_order = pass_match.group(1)
                            agari = float(pass_match.group(2))
                        
                        past_races.append({
                            "date": date, "track": track_name, "race_num": past_race_num,
                            "race_name": past_race_name, "track_type": p_type, "distance": p_dist,
                            "time": p_time, "condition": p_cond, "pass_order": pass_order, "agari_3f": agari
                        })
                except Exception as past_e:
                    # 過去走の1つがパース失敗しても、他の過去走や他の馬の処理を続行する
                    continue

            horses_list.append({
                "waku": waku, "uma_ban": uma_ban, "horse_name": horse_name,
                "kinryo": kinryo, "leg_type": leg_type, "weight": weight,
                "weight_diff": weight_diff, "odds": odds, "popularity": popularity,
                "past_races": past_races
            })
            
        except Exception as horse_e:
            # 特定の馬のデータ処理に致命的な問題があっても、次の馬へスキップして全体を落とさない
            print(f"[Warning] 馬のパースに失敗: {horse_e}")
            continue
        
    return {
        "race_info": race_info,
        "horses": horses_list
    }
