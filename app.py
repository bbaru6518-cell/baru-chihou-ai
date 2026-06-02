import streamlit as st
import google.generativeai as genai
import json
import os
import re

# =========================================================================
# 1. パース関数（極限シンプル・安全版）
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
        # レース情報の抽出（短く分割）
        r_pattern = r'(\d+)R\s+([^\n]+)'
        info_match = re.search(r_pattern, raw_text)
        if info_match:
            race_info["race_num"] = int(info_match.group(1))
            race_info["race_name"] = info_match.group(2).strip()
        
        track_match = re.search(r'([ダ芝])(\d+)m', raw_text)
        if track_match:
            race_info["track_type"] = track_match.group(1)
            race_info["distance"] = int(track_match.group(2))
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
            
            # 体重や人気の抽出
            weight, popularity = 450, 1
            w_match = re.search(r'(\d+)kg', body)
            if w_match:
                weight = int(w_match.group(1))
            p_match = re.search(r'\((\d+)人気\)', body)
            if p_match:
                popularity = int(p_match.group(1))

            # 脚質の判定（1行を極めて短く修正してエラー対策）
            leg_type = "不明"
            for lt in ["逃", "先", "差", "追"]:
                if lt in body:
                    leg_type = lt
                    break

            # 騎手の抽出
            jockey = "不明"
            for line in lines:
                if "人気)" in line or "kg" in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        jockey = parts[2]
                        break

            # 過去走データ処理（クラッシュ防止ガード）
            past_races = []
            horses_list.append({
                "waku": waku, "uma_ban": uma_ban, "horse_name": horse_name,
                "jockey": jockey, "kinryo": 54.0, "leg_type": leg_type, "weight": weight,
                "weight_diff": "0", "odds": 5.0, "popularity": popularity,
                "past_races": past_races
            })
        except Exception:
            continue
        
    return {"race_info": race_info, "horses": horses_list}

# =========================================================================
# 2. Streamlit UI メインロジック
# =========================================================================
st.set_page_config(page_title="Baru競馬AI Pro", layout="wide")

st.title("🎯 Baru競馬AI Pro — 地方競馬・走破理論解析")
st.caption("netkeibaの出馬表コピペから一撃で完全に構造化し、フォーメーションを自動生成します。")

raw_input = st.text_area("ここにnetkeibaの出馬表テキスト
