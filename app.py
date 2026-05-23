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

cfg = load_cfg()
st.set_page_config(page_title="Baru AI Pro v24.1", layout="wide")
st.title("🏇 Baru 競馬AI Pro - 【Ver 24.1 構文修正・展開脚質完全版】")

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

# --- データを取得するためのヘルパー関数 ---
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
                             next((x for x in models if "pro" in x), 
                             models[0]))
                
                model = genai.GenerativeModel(m_name)
                
                # --- トリプルクォーテーションのエラーを解消した鉄壁プロンプト ---
                prompt = f"""あなたは中央競馬（JRA）および地方競馬を統括する競馬AIであり、総監督Baruの絶対的右腕だ。
入力されたテキストデータから人気・枠・馬番・馬名・オッズ・過去の通過順を完全に解剖し、逃げ・先行馬の有利不利を見抜いた勝負指示書を作成せよ。

【データ解剖における絶対掟】
1. 過去9走の通過順データ（例: 1-1-1 や 11-10-8 等）や、データ分析テキスト内の「有利な脚質：逃げ」などの文脈から、今回の出走馬の脚質を「逃げ」「先行」「差し」「追込」に超精密に分類せよ。
2. 特に、ハナを叩きそうな「逃げ」馬、好位をキープする「先行」馬にはマーク（印）をつけ、展開面での有利不利を可視化せよ。

【出力フォーマット】
以下の3つのセクション構成のみを出力せよ。余計な前置きや挨拶は一切禁止する。

### 📊 全頭精密診断・血統適性リスト
必ず以下の列を持つMarkdownテーブル形式で今回の出走馬を全頭出力せよ。
| 馬番 | 馬名 | 父 | 母 | 血統適性 | 脚質 | 人気 | 評価 | 理由 |
※【脚質】列には
