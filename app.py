import re
import json

def parse_netkeiba_complete(raw_text):
    """
    netkeibaの出馬表コピペテキスト（中央・地方両対応）を完全にパースするスクリプト
    """
    # 1. レース基本情報の抽出
    race_info = {
        "race_num": None,
        "race_name": None,
        "distance": None,
        "track_type": "ダ", # デフォルト
        "direction": None,
        "weather": None,
        "condition": None
    }
    
    # 2R 3歳三 15:15発走 / ダ1200m (左) / 天候:晴 / 馬場:良 みたいな行を探す
    info_match = re.search(r'(\d+)R\s+([^\n]+)\s+.*?発走\s+/\s+([ダ芝])(\d+)m\s*\((.*?)\)\s+/\s+天候:(.*?)\s+/\s+馬場:(.*)', raw_text)
    if info_match:
        race_info["race_num"] = int(info_match.group(1))
        race_info["race_name"] = info_match.group(2).strip()
        race_info["track_type"] = info_match.group(3)
        race_info["distance"] = int(info_match.group(4))
        race_info["direction"] = info_match.group(5).strip()
        race_info["weather"] = info_match.group(6).strip()
        race_info["condition"] = info_match.group(7).split()[0].strip() # 余計なテキスト排除

    # 2. 馬ごとのブロックに分割
    # 地方競馬の行頭パターン「枠番 \t 馬番 \t \n--」または「枠番 \t 馬番 \t --」で割る
    block_pattern = r'(?:\n|^)(\d+)\s+(\d+)\s*\n?--'
    chunks = re.split(block_pattern, raw_text)
    
    # 最初のヘッダー（レース情報など）をスキップ
    blocks = chunks[1:]
    
    horses_list = []
    
    # 分割データは [枠番, 馬番, その馬のテキストブロック, 枠番, 馬番, ...] の順になる
    for i in range(0, len(blocks), 3):
        if i + 2 >= len(blocks):
            break
            
        waku = int(blocks[i].strip())
        uma_ban = int(blocks[i+1].strip())
        body = blocks[i+2].strip()
        
        # 空白行を除去して配列化
        lines = [l.strip() for l in body.split('\n') if l.strip()]
        if not lines:
            continue
            
        # --- 現在の出走馬情報の抽出 ---
        # 1行目は馬名
        horse_name = lines[0]
        
        # 体重・オッズ・人気の抽出 (例: 483kg(-5) 48.1 (8人気))
        weight, weight_diff, odds, popularity = None, None, None, None
        weight_match = re.search(r'(\d+)kg\((.*?)\)\s+([\d.]+)\s+\((\d+)人気\)', body)
        if weight_match:
            weight = int(weight_match.group(1))
            weight_diff = weight_match.group(2)
            odds = float(weight_match.group(3))
            popularity = int(weight_match.group(4))
            
        # 斤量の抽出 (例: 54.0)
        kinryo = None
        kinryo_match = re.search(r'\b(\d{2}\.\d)\b', body)
        if kinryo_match:
            kinryo = float(kinryo_match.group(1))
            
        # 脚質セクション (例: 差、逃、先、追)
        leg_type = "不明"
        for lt in ["逃", "先", "差", "追"]:
            if lt in lines: # 独立した行として存在することが多い
                leg_type = lt
                break
        if leg_type == "不明":
            # 行の中に含まれる場合をフォールバック
            lt_match = re.search(r'\b(逃|先|差|追)\b', body)
            if lt_match:
                leg_type = lt_match.group(1)

        # --- 過去5走（近走履歴）の抽出 ---
        # 過去走は 「日付 競馬場 レース番号」から始まるブロック (例: 2026.05.11 川崎 4)
        past_races = []
        # 各過去走の戦闘インデックスを見つける
        race_starts = [m.start() for m in re.finditer(r'\b\d{4}\.\d{2}\.\d{2}\s+[^\s]+\s+\d+\b', body)]
        
        for idx, start_pos in enumerate(race_starts):
            # 次の過去走の開始位置までを切り出す
            end_pos = race_starts[idx+1] if idx+1 < len(race_starts) else len(body)
            race_chunk = body[start_pos:end_pos].strip()
            race_lines = [rl.strip() for rl in race_chunk.split('\n') if rl.strip()]
            
            if len(race_lines) < 3:
                continue
                
            # 1行目: 日付 競馬場 レース番号
            head_meta = race_lines[0].split()
            date = head_meta[0]
            track_name = head_meta[1]
            past_race_num = head_meta[2]
            
            # 2行目: レース名やクラス (例: リュフト(3歳) or 3歳三)
            past_race_name = race_lines[1]
            
            # 3行目: コース・タイム・馬場 (例: ダ900 0:56.3 良)
            track_info_match = re.search(r'([芝ダ])(\d+)\s+([\d:]+\.\d+)\s+([良|稍|重|不])', race_chunk)
            
            if track_info_match:
                p_type = track_info_match.group(1)
                p_dist = int(track_info_match.group(2))
                p_time = track_info_match.group(3)
                p_cond = track_info_match.group(4)
                
                # 4行目以降から「通過順(上り3F)」と「頭数・馬番・人気」を安全に引っこ抜く
                # 例: 11頭 5番 8人 池谷匠翔 54.0
                # 例: 3-4 (38.6) 488(-5)
                pass_order, agari = None, None
                pass_match = re.search(r'([\d-]+)\s+\(([\d.]+)\)', race_chunk)
                if pass_match:
                    pass_order = pass_match.group(1)
                    agari = float(pass_match.group(2))
                
                past_races.append({
                    "date": date,
                    "track": track_name,
                    "race_num": past_race_num,
                    "race_name": past_race_name,
                    "track_type": p_type,
                    "distance": p_dist,
                    "time": p_time,
                    "condition": p_cond,
                    "pass_order": pass_order,
                    "agari_3f": agari
                })

        horses_list.append({
            "waku": waku,
            "uma_ban": uma_ban,
            "horse_name": horse_name,
            "kinryo": kinryo,
            "leg_type": leg_type,
            "weight": weight,
            "weight_diff": weight_diff,
            "odds": odds,
            "popularity": popularity,
            "past_races": past_races
        })
        
    return {
        "race_info": race_info,
        "horses": horses_list
    }

# --- テスト実行用のラッパー ---
if __name__ == "__main__":
    # ここにプロンプトのコピペテキストを流し込む想定
    # data = parse_netkeiba_complete(YOUR_COPY_PASTE_TEXT)
    pass
