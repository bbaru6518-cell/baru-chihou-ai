import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup

# --- 設定保存機能 ---
CONFIG_FILE = "baru_pro_config.json"
def save_cfg(k, b):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"k": k, "b": b}, f, ensure_ascii=False, indent=4)

def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "k": "", 
        "b": "JRA（中央競馬）および地方競馬の高速馬場・トラックバイアス、芝・ダートのキレ、走破タイム理論（基準タイム・馬場補正）、上がり3F、展開・ハナ争いを統合解析せよ。"
    }

# --- データ取得ヘルパー関数 ---
def get_netkeiba_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        main_data = soup.find_all("table")
        combined_text = ""
        for table in main_data:
            combined_text += table.get_text(separator="\n", strip=True) + "\n"
        return combined_text[:50000]
    except Exception as e:
        return f"Error: {e}"

cfg = load_cfg()
st.set_page_config(page_title="Baru AI Pro v24.3", layout="wide")
st.title("🏇 Baru 競馬AI Pro - 【Ver 24.3 エラー完全絶滅・展開脚質版】")

with st.sidebar:
    st.header("⚙️ 総監督ルーム（JRA・地方ハイブリッド）")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（馬場・補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("総監督ルームの設定を保存しました。")

if "res" not in st.session_state:
    st.session_state["res"] = ""

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 9走馬柱・オッズ混在テキスト入力")
    url_input = st.text_input("🔗 レースURL（出馬表・オッズページ等）")
    manual_data = st.text_area("✍️ netkeibaコピペデータ（オッズ表やデータ分析テキストをそのまま一括投入）", height=500)
    
    if st.button("🚀 構造解剖・多角データ解析開始"):
        target_data = ""
        if url_input:
            with st.spinner("レースデータをバックグラウンドスクレイピング中..."):
                target_data = get_netkeiba_data(url_input)
        else:
            target_data = manual_data

        if not api_key or not target_data:
            st.error("APIキーと解析対象のデータが必要です")
        else:
            try:
                genai.configure(api_key=api_key)
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                m_name = next((x for x in models if "1.5-pro" in x), 
                             next((x for x
