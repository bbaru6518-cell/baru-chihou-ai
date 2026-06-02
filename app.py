import streamlit as st
import google.generativeai as genai
import json
import os
import re

# =========================================================================
# 1. ネット競馬（中央・地方対応）完全版パース関数（安全ガード付き）
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
        info_match = re.search(r'(\d+)R\s+([^\n]+)\s+.*?発走\s+/\s+([ダ芝])(\d+)m\s*\((.*?)\)\s+/\s+天候:(.*?)\s+/\s+馬場:(.*)', raw_text)
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
            weight_match = re.search(r'(\d+)kg\((.*?)\)\s+([\d.]+)\s+\((\d+)人気\)', body)
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

            # 【バグ修正箇所】騎手抽出ロジックの構文とtry-exceptを100%正確に配置
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

            past_races = []
            race_starts = [m.start() for m in re.finditer(r'\b\d{4}\.\d{2}\.\d{2}\s+[^\s]+\s+\d+\b', body)]
            
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
                    
                    track_info_match = re.
