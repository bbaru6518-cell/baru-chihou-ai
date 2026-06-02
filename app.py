import datetime
import json
import os
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

# ==============================================================================
# 【最新仕様対応】google-genai への移行（警告対策）
# 従来の import google.generativeai as genai から最新の google.genai へスイッチ
# ==============================================================================
from google import genai
from google.genai import types

# ページレイアウトの設定（Streamlit最新仕様に対応）
st.set_page_config(page_title="Baru地方競馬AI Pro", layout="wide")

# APIキーの取得（StreamlitのSecrets、または環境変数から）
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
if not api_key:
    st.error("エラー: GEMINI_API_KEY が設定されていません。")
    st.stop()

# 最新のGenAIクライアント初期化
client = genai.Client(api_key=api_key)


# ==============================================================================
# データ処理・解析関数
# ==============================================================================
def parse_horse_line(line):
    """出走馬テキスト行を安全にパースする関数（83行目のエラー修正箇所）"""
    # 初期値の設定
    uma_ban = 0
    uma_name = "未知の馬"
    jockey = "不明"

    if not line.strip():
        return None

    try:
        parts = line.split()
        if len(parts) >= 2:
            # 「06 濱田達也」のような形式を想定
            uma_ban = int(parts[0])
            uma_name = parts[1]
            if len(parts) >= 3:
                jockey = parts[2]
            else:
                jockey = parts[1]  # 騎手名が馬名と同一視される場合のケア
        else:
            # 要素が足りない場合はスキップまたは暫定処理
            return None
    except Exception as e:
        # エラーが起きてもシステムを止めず、安全にスキップ
        return None

    return {"uma_ban": uma_ban, "uma_name": uma_name, "jockey": jockey}


def generate_barus_formation(race_df, netkeiba_top3, wave_score):
    """バル式・最適化フォーメーション生成ロジック"""
    # AIスコア（走破タイム理論ベース）でソート
    df_sorted = race_df.sort_values(by="ai_score", ascending=False).copy()

    # 1. 走破タイムAIによる初期選定
    jiku_candidates = df_sorted.iloc[0:2]["uma_ban"].tolist()
    aite_candidates = df_sorted.iloc[2:5]["uma_ban"].tolist()
    himo_candidates = df_sorted.iloc[4:9]["uma_ban"].tolist()

    # 秋元フィルター（例：特定の条件で特定の馬番を弾くロジック）
    # ※ 必要に応じてここに条件を追記できます
    akimoto_filter_horses = [3]  # テスト用として3番をフィルター対象に

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
# Streamlit UI 画面構築
# ==============================================================================
st.title("🎯 Baru地方競馬AI Pro")
st.subheader("〜 走破タイム理論 × netkeibaデータ分析救済システム 〜")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 1. 出走馬・前日データ入力")
    race_title = st.text_input("レース名（例: 船橋 3R (C3)）", "船橋 3R (C3)")
    wave_input = st.slider("波乱度スコア（想定）", 0, 100, 65)

    # ユーザーがコピペで馬の情報を入れられるテキストエリア
    raw_horse_data = st.text_area(
        "出走馬データ（馬番 馬名 騎手名...の順で1行ずつ）",
        "11 アイディアル 御神本\n05 ジョーエスポワール 笹川\n10 コスモミツボシ 矢野\n0
