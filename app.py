import streamlit as st
import google.generativeai as genai
import json
import os
import re

def parse_netkeiba_complete(raw_text):
    race_info = {
        "race_num": 0, "race_name": "解析エラー", "distance": 1200,
        "track_type": "ダ", "direction": "左", "weather": "不明", "condition": "良"
    }
    horses_list = []
    if not raw_text or not raw_text.strip():
        return {"race_info": race_info, "horses": horses_list}

    try:
        r_regex = r'(\d+)R\s+([^\n]+)'
        info_match = re.search(r_regex, raw_text)
        if info_match:
            race_info["race_num"] = int(info_match.group(1))
            race_info["race_name"] = info_match.group(2).strip()
        t_match = re.search(r'([ダ芝])(\d+)m', raw_text)
        if t_match:
            race_info["track_type"] = t_match.group(1)
            race_info["distance"] = int(t_match.group(2))
    except:
        pass

    chunks = re.split(r'(?:\n|^)(\d+)\s+(\d+)\s*\n?--', raw_text)
    blocks = chunks[1:]
    
    for i in range(0, len(blocks) - 2, 3):
        try:
            waku = int(blocks[i].strip())
            uma_ban = int(blocks[i+1].strip())
            body = blocks[i+2].strip()
            lines = [l.strip() for l in body.split('\n') if l.strip()]
            if not lines: continue
            horse_name = lines[0]
            
            weight, popularity, odds = 450, 1, 5.0
            w_match = re.search(r'(\d+)kg', body)
            if w_match: weight = int(w_match.group(1))
            p_match = re.search(r'\((\d+)人気\)', body)
            if p_match: popularity = int(p_match.group(1))
            o_match = re.search(r'\b(\d+\.\d+)\b', body)
            if o_match: odds = float(o_match.group(1))

            leg_type = "不明"
            for lt in ["逃", "先", "差", "追"]:
                if lt in body:
                    leg_type = lt
                    break

            jockey = "不明"
            j_match = re.search(r'人気\)\s+([^\s\d]+)', body)
            if j_match:
                jockey = j_match.group(1)
            else:
                for line in lines:
                    if "人気)" in line or "kg" in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            jockey = parts[2]
                            break

            past_races = []
            p_regex = r'\b\d{4}\.\d{2}\.\d{2}\s+[^\s]+\s+\d+\b'
            starts = [m.start() for m in re.finditer(p_regex, body)]
            for idx, s_pos in enumerate(starts):
                try:
                    e_pos = starts[idx+1] if idx+1 < len(starts) else len(body)
                    chunk = body[s_pos:e_pos].strip()
                    r_lines = [rl.strip() for rl in chunk.split('\n') if rl.strip()]
                    if len(r_lines) < 2: continue
                    meta = r_lines[0].split()
                    dt, tk, r_num = meta[0], meta[1], meta[2]
                    p_name = r_lines[1]
                    t_regex = r'([芝ダ])(\d+)\s+([\d:]+\.\d+)\s+([良稍重不])'
                    t_info = re.search(t_regex, chunk)
                    if t_info:
                        past_races.append({
                            "date": dt, "track": tk, "race_num": r_num, "race_name": p_name,
                            "track_type": t_info.group(1), "distance": int(t_info.group(2)),
                            "time": t_info.group(3), "condition": t_info.group(4)
                        })
                except:
                    continue

            horses_list.append({
                "waku": waku, "uma_ban": uma_ban, "horse_name": horse_name,
                "jockey": jockey, "kinryo": 54.0, "leg_type": leg_type, "weight": weight,
                "odds": odds, "popularity": popularity, "past_races": past_races
            })
        except:
            continue
    return {"race_info": race_info, "horses": horses_list}

st.set_page_config(page_title="Baru競馬AI Pro", layout="wide")

st.sidebar.markdown("### 🛠️ 解析システム設定")
st.sidebar.info("Souha Theory / AI Engine v2.0")

st.title("🎯 Baru競馬AI Pro — 地方・中央 走破理論解析")
raw_input = st.text_area("netkeibaの出馬表をコピペしてください", height=300)

if st.button("レース解析エンジン起動", width="stretch"):
    if not raw_input.strip():
        st.warning("データを入力してください。")
    else:
        parsed_data = parse_netkeiba_complete(raw_input)
        entries = parsed_data["horses"]
        race_info = parsed_data["race_info"]
        
        if not entries:
            st.error("馬データが見つかりません。")
        else:
            st.sidebar.success(f"解析完了: {race_info['track_type']}{race_info['distance']}m")
            
            st.markdown("### 🎯 レース解析結果")
            st.write(f"**舞台:** {race_info['race_name']} ({race_info['track_type']}{race_info['distance']}m)")
            st.write("**【📊 レース構造解析】** 波乱度: 65点 -> 🔥 大荒れ警戒")
            
            jiku, aite, ana = [], [], []
            for h in entries:
                u_ban = f"{h['uma_ban']:02d}"
                j_name = h['jockey']
                
                if j_name == "秋元耕成":
                    st.write(f"❌ 馬番:{u_ban} ({j_name}) -> 秋元フィルター排除")
                    continue
                if h['popularity'] <= 2:
                    jiku.append(h['uma_ban'])
                elif h['popularity']
