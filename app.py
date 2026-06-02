import streamlit as st
import google.generativeai as genai
import json
import os
import re

# =========================================================================
# 1. ネット競馬（中央・地方対応）完全版パース関数（データ・騎手・過去走フル復活）
# =========================================================================
def parse_netkeiba_complete(raw_text):
    race_info = {
        "race_num": 0, "race_name": "データ解析エラー", "distance": 1200,
        "track_type": "ダ", "direction": "左", "weather": "不明", "condition": "良"
    }
    horses_list = []

    if not raw_text or not raw_text.strip():
        return {"race_info": race_info, "horses": horses_list}

    try:
        race_regex = (
            r'(\d+)R\s+([^\n]+)\s+.*?発走\s+/\s+'
            r'([ダ芝])(\d+)m\s*\((.*?)\)\s+/\s+'
            r'天候:(.*?)\s+/\s+馬場:(.*)'
        )
        info_match = re.search(race_regex, raw_text)
        if info_match:
            race_info["race_num"] = int(info_match.group(1))
            race_info["race_name"] = info_match.group(2).strip()
            race_info["track_type"] = info_match.group(3)
            race_info["distance"] = int(info_match.group(4))
            race_info["direction"] = info_match.group(5).strip()
            race_info["weather"] = info_match.group(6).strip()
            race_info["condition"] = info_match.group(7).split()[0].strip()
    except Exception:
        pass

    block_pattern = r'(?:\n|^)(\d+)\s+(\d+)\s*\n?--'
    chunks = re.split(block_pattern, raw_text)
    blocks = chunks[1:]
    
    for i in range(0, len(blocks) - 2, 3):
        try:
            waku = int(blocks[i].strip())
            uma_ban = int(blocks[i+1].strip())
            body = blocks[i+2].strip()
            
            lines = [l.strip() for l in body.split('\n') if l.strip()]
            if not lines:
                continue
                
            horse_name = lines[0]
            
            weight, weight_diff, odds, popularity = None, None, 1.0, 1
            weight_regex = r'(\d+)kg\((.*?)\)\s+([\d.]+)\s+\((\d+)人気\)'
            weight_match = re.search(weight_regex, body)
            if weight_match:
                weight = int(weight_match.group(1))
                weight_diff = weight_match.group(2)
                odds = float(weight_match.group(3))
                popularity = int(weight_match.group(4))
                
            kinryo = None
            kinryo_match = re.search(r'\b(\d{2}\.\d)\b', body)
            if kinryo_match:
                kinryo = float(kinryo_match.group(1))
                
            leg_type = "不明"
            for lt in ["逃", "先", "差", "追"]:
                if lt in lines:
                    leg_type = lt
                    break
            if leg_type == "不明":
                lt_match = re.search(r'\b(逃|先|差|追)\b', body)
                if lt_match:
                    leg_type = lt_match.group(1)

            # 騎手抽出の高度なフォールバック
            jockey = "不明"
            try:
                jockey_match = re.search(r'\b人気\)\s+([^\s\d]+)\s+\d', body)
                if jockey_match:
                    jockey = jockey_match.group(1)
                else:
                    for line in lines:
                        if any(x in line for x in ["人気)", "kg"]):
                            parts = line.split()
                            if len(parts) >= 3:
                                jockey = parts[2]
            except Exception:
                jockey = "不明"

            # 過去走データのパース（走破理論の核心部分）
            past_races = []
            past_regex = r'\b\d{4}\.\d{2}\.\d{2}\s+[^\s]+\s+\d+\b'
            race_starts = [m.start() for m in re.finditer(past_regex, body)]
            
            for idx, start_pos in enumerate(race_starts):
                try:
                    end_pos = race_starts[idx+1] if idx+1 < len(race_starts) else len(body)
                    race_chunk = body[start_pos:end_pos].strip()
                    race_lines = [rl.strip() for rl in race_chunk.split('\n') if rl.strip()]
                    
                    if len(race_lines) < 2:
                        continue
                        
                    head_meta = race_lines[0].split()
                    if len(head_meta) < 3:
                        continue
                    date = head_meta[0]
                    track_name = head_meta[1]
                    past_race_num = head_meta[2]
                    
                    past_race_name = race_lines[1] if len(race_lines) > 1 else "不明"
                    track_regex = r'([芝ダ])(\d+)\s+([\d:]+\.\d+)\s+([良|稍|重|不])'
                    track_info_match = re.search(track_regex, race_chunk)
                    
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
                except Exception:
                    continue

            horses_list.append({
                "waku": waku, "uma_ban": uma_ban, "horse_name": horse_name,
                "jockey": jockey, "kinryo": kinryo, "leg_type": leg_type, "weight": weight,
                "weight_diff": weight_diff, "odds": odds, "popularity": popularity,
                "past_races": past_races
            })
            
        except Exception:
            continue
        
    return {"race_info": race_info, "horses": horses_list}
