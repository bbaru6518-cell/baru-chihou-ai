import datetime
import json
import os
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

# 【サーバー環境連動】安定稼働する旧ライブラリ形式
import google.generativeai as genai

# ページレイアウトの設定（ワイドモードで広く使う）
st.set_page_config(page_title="Baru地方競馬AI Pro", layout="wide")

# APIキーの取得と設定
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
if not api_key:
    st.error("API KEY ERROR: StreamlitのSecretsを設定してください。")
    st.stop()

# Geminiの初期化
genai.configure(api_key=api_key)


# ==============================================================================
# データ処理・解析関数
# ==============================================================================
def parse_horse_line(line):
    """出走馬テキスト行を安全にパースする関数"""
    uma_ban = 0
    uma_name = "未知の馬"
    jockey = "不明"

    if not line.strip():
        return None

    try:
        parts = line.split()
        if len(parts) >= 2:
            uma_ban = int(parts[0])
            uma_name = parts[1]
            if len(parts) >= 3:
                jockey = parts[2]
            else:
                jockey = parts[1]
        else:
            return None
    except Exception as e:
        return None

    return {"uma_ban": uma_ban, "uma_name": uma_name, "jockey": jockey}


def generate_barus_formation(race_df, netkeiba_top3, wave_score):
    """バル式・最適化フォーメーション生成ロジック"""
    df_sorted = race_df.sort_values(by="ai_score", ascending=False).copy()

    # 1. 走破タイムAIによる初期選定
    jiku_candidates = df_sorted.iloc[0:2]["uma_ban"].tolist()
    aite_candidates = df_sorted.iloc[2:5]["uma_ban"].tolist()
    himo_candidates = df_sorted.iloc[4:9]["uma_ban"].tolist()

    # 秋元フィルター
    akimoto_filter_horses = [3]

    # 2. 🔥 データ分析上位馬の強制救済ロジック
    all_selected = set(jiku_candidates + aite_candidates + himo_candidates)
    saved_horses = []

    for uma in netkeiba_top3:
        if uma not in all_selected and uma not in akimoto_filter_horses:
            himo_candidates.append(uma)
            saved_horses.append(uma)

    # 3. フィルターの適用
    jiku_candidates = [
        m for m in jiku_candidates if m not in akimoto_filter_horses
    ]
    aite_candidates = [
        m for m in aite_candidates if m not in akimoto_filter_horses
    ]
    himo_candidates = [
        m for m in himo_candidates if m not in akimoto_filter_horses
    ]

    return {
        "jiku": jiku_candidates,
        "aite": aite_candidates,
        "himo": list(set(himo_candidates)),
        "saved": saved_horses,
        "filtered": akimoto_filter_horses,
    }


# ==============================================================================
# 👈 左側：サイドバー設定エリア
# ==============================================================================
st.sidebar.markdown("## 📋 1. 出走馬データ入力")
race_title = st.sidebar.text_input("レース名", "船橋 3R")
wave_input = st.sidebar.slider("波乱度スコア", 0, 100, 65)

default_text = "11 アイディアル 御神本\n05 ジョーエスポワール 笹川\n10 コスモミツボシ 矢野\n02 シャマル 川田\n09 ウインアザレア 森\n06 濱田達也 濱田\n01 藤江渉 藤江\n08 加藤雄真 加藤\n07 山林堂信 山林堂\n03 秋元耕成 秋元"
raw_horse_data = st.sidebar.text_area("馬データ", default_text)

st.sidebar.markdown("## 📊 2. netkeibaデータ入力")
top3_input = st.sidebar.text_input(
    "1枚目:データ分析上位3頭(カンマ区切り)", "1, 10, 12"
)
himo_input = st.sidebar.text_input(
    "2枚目:コース距離得意馬(カンマ区切り)", "6, 1, 8, 7"
)

# カンマ区切りの文字列をリストに変換
try:
    netkeiba_top3 = [int(x.strip()) for x in top3_input.split(",") if x.strip()]
    netkeiba_himo = [int(x.strip()) for x in himo_input.split(",") if x.strip()]
except ValueError:
    st.sidebar.error("入力は半角数字とカンマのみにしてください")
    st.stop()


# ==============================================================================
# 👉 右側：メイン表示エリア（解析結果）
# ==============================================================================
st.title("🎯 Baru地方競馬AI Pro")
st.subheader("〜 走破タイム理論 × netkeibaデータ分析救済 〜")
st.markdown("---")

# パース処理を実行してDataFrameを作成
lines = raw_horse_data.split("\n")
horse_list = []
dummy_scores = [85.2, 82.1, 79.5, 75.0, 71.4, 62.0, 58.3, 55.1, 52.0, 45.0]

score_idx = 0
for line in lines:
    parsed = parse_horse_line(line)
    if parsed:
        parsed["ai_score"] = (
            dummy_scores[score_idx]
            if score_idx < len(dummy_scores)
            else 40.0
        )
        horse_list.append(parsed)
        score_idx += 1

# ボタンが押されたら解析エンジンを起動（サイドバーの下ではなくメイン側に大きく配置）
if st.button("🚀 レース解析エンジンを起動", use_container_width=True):
    if not horse_list:
        st.warning("馬データが読み込めませんでした")
    else:
        race_df = pd.DataFrame(horse_list)

        # フォーメーション計算
        result = generate_barus_formation(race_df, netkeiba_top3, wave_input)

        # 2枚目の紐馬を3列目にマージ
        final_himo = list(set(result["himo"] + netkeiba_himo))

        # ログ風出力
        analysis_log = f"=========================================\n"
        analysis_log += f" 🎯 {race_title} 解析結果\n"
        analysis_log += f"=========================================\n\n"

        for _, row in race_df.iterrows():
            if row["uma_ban"] in result["saved"]:
                analysis_log += f" ⚠️ 馬番:{row['uma_ban']:02d} ({row['jockey']}) -> ネット連動救済\n"

        for _, row in race_df.iterrows():
            if row["uma_ban"] in result["filtered"]:
                analysis_log += (
                    f" ❌ 馬番:{row['uma_ban']:02d} -> 秋元フィルター排除\n"
                )

        st.code(
            f"""{analysis_log}
=========================================
 🎯 【最終出力】Baru式・最適化フォーメーション
=========================================
 1列目（軸） : {result['jiku']}
 2列目（相手）: {result['aite']}
 3列目（穴紐）: {final_himo}
 ---------------------------------------
解析完了。グッドラック！
=========================================""",
            language="text",
        )

        # 買い目の展開
        st.markdown("### 🎫 展開された買い目一覧")
        tickets = []
        for n1 in result["jiku"]:
            for n2 in result["aite"]:
                for n3 in final_himo:
                    if n1 != n2 and n2 != n3 and n1 != n3:
                        comb = sorted([n1, n2, n3])
                        if comb not in tickets:
                            tickets.append(comb)

        # 2列で見やすく表示
        t_col1, t_col2 = st.columns(2)
        for i, t in enumerate(tickets, 1):
            if i % 2 != 0:
                t_col1.write(f"**[{i:02d}]** `{t[0]}-{t[1]}-{t[2]}`")
            else:
                t_col2.write(f"**[{i:02d}]** `{t[0]}-{t[1]}-{t[2]}`")

        st.markdown("---")
        st.success(f"🔥 合計購入点数: {len(tickets)} 点")
