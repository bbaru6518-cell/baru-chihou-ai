import re
import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup
import datetime

# ページの設定（2カラムを綺麗に表示するためにワイドモードに設定）
st.set_page_config(layout="wide")

# ==============================================================================
# 1. 精密診断Markdownテーブル生成関数
# ==============================================================================
def parse_and_generate_table(raw_text, ai_recommendations=None):
    """
    コピペデータから全頭をパースし、
    スクリーンショットのデザイン・列構成（父・母・脚質・人気・評価・理由）を完全再現する関数
    """
    if ai_recommendations is None:
        ai_recommendations = {
            1: {"mother": "パワフルラリマー", "sand": "速砂〇", "style": "先行 📢", "pop": "2", "eval": "〇", "reason": "2走前に同条件(不良)を先行策で圧勝。最内枠から再現可能。"},
            2: {"mother": "デコラス", "sand": "標準", "style": "追込", "pop": "12", "eval": "消", "reason": "追い込み一手で展開利見込めず。近走内容も平凡。"},
            3: {"mother": "スカイスペクター", "sand": "速砂〇", "style": "差し", "pop": "3", "eval": "△", "reason": "不良馬場での好走実績あり。先行力もあり、粘り込みに期待。"},
            4: {"mother": "エメラルコヨーテ", "sand": "速砂◎", "style": "追込", "pop": "4", "eval": "△", "reason": "末脚はメンバー屈指。不良馬場で前が速くなれば強襲あり。"},
            5: {"mother": "アドマイヤジョイ", "sand": "標準", "style": "差し", "pop": "7", "eval": "消", "reason": "C3クラスで頭打ち。強調材料に欠ける。"},
        }

    markdown_lines = [
        "### 📊 全頭精密診断・地方ダート適性リスト\n",
        "| 馬番 | 馬名 | 父 | 母 | ダート砂適性 | 脚質 | 人気 | 評価 | 理由 |",
        "| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |"
    ]

    horse_blocks = re.split(r'\n(?=\d+\s+\d+\s+(?:--|✓))', raw_text)

    for block in horse_blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines or not re.match(r'^\d+$', lines[0]):
            continue
            
        try:
            num = int(lines[0])
            formatted_num = f"{num}"
            
            blood_idx = -1
            for i, line in enumerate(lines):
                if line.startswith('(') and line.endswith(')'):
                    blood_idx = i
                    break
            
            if blood_idx != -1 and blood_idx >= 2:
                father = lines[blood_idx - 2]
                horse_name = lines[blood_idx - 1]
            else:
                horse_name = lines[1] if len(lines) > 1 else "解析エラー"
                father = "--"

            rec = ai_recommendations.get(num, {
                "mother": "--", 
                "sand": "標準", 
                "style": "差し", 
                "pop": "--", 
                "eval": "△", 
                "reason": "近走の走破タイム判定から、この舞台では静観が妥当。"
            })
            
            row = f"| {formatted_num} | {horse_name} | {father} | {rec['mother']} | {rec['sand']} | {rec['style']} | {rec['pop']} | {rec['eval']} | {rec['reason']} |"
            markdown_lines.append(row)
            
        except Exception as e:
            continue

    return "\n".join(markdown_lines)


# ==============================================================================
# 2. ⚙️ Streamlit UI 配置 (スクショ2枚目のレイアウト完全再現)
# ==============================================================================

# --- 2-A. 左側サイドバー（過去ログ・結果復習ルーム） ---
with st.sidebar:
    st.button("💾 設定保存")
    st.write("")
    st.header("📂 過去ログ・結果復習ルーム")
    st.caption("復習・確認する過去の予想")
    st.selectbox(
        "選択してください",
        ["ファイナルレース(C3)_2026-05-25", "大井11R_東京ダービー"],
        label_visibility="collapsed"
    )
    st.button("📖 予想指示書を呼び出す")
    
    st.write("---")
    st.header("🏁 レース結果のコピペ投入")
    st.caption("💡 1行目にレース名を入力し、2行目から結果を丸ごとコピペしてください！")
    st.text_area(
        "1行目：レース名／2行目〜：結果コピペ",
        value="3コーナー...\n4コーナー...",
        height=150,
        label_visibility="collapsed"
    )
    st.caption("コーナー通過順位の見方")
    st.text_area("レース別馬メモ", height=100)
    st.button("🔮 実際の着順・ハナ争いと照合して復習", use_container_
