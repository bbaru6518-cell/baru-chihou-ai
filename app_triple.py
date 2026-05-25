import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

# --- 設定保存機能 ---
CONFIG_FILE = "baru_triple_config.json"
LOG_DIR = "racing_logs_triple"  # トリプル馬単専用の独立フォルダ
os.makedirs(LOG_DIR, exist_ok=True)

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
        # 【トリプル馬単特化】馬単を3連続で射抜くための、地方の展開・ハナ争い・完全前残りバイアスに特化した初期指示
        "b": "トリプル馬単対象地方レース（主に後半3R）のトラックバイアス, 砂質, 1角ポジション争い, 絶対に崩れない軸馬の選定, および逆転候補の展開利・ハナ争いを統合解析せよ。"
    }

def clean_filename(name):
    if not name:
        return ""
    clean = re.sub(r'[\\/*?:"<>| \t]', '_', name.strip())
    return clean[:50]

cfg = load_cfg()

# 👑 【看板完全死守】総監督指定のオリジナル大看板タイトル・バージョン表記へ完全固定
st.set_page_config(page_title="Baru 地方競馬AI Pro v24.8.5", layout="wide", initial_sidebar_state="expanded")
st.title("🏇 Baru 地方競馬AI Pro - 【Ver 24.8.5 高速・軽量化安定版】")

with st.sidebar:
    st.header("⚙️ 総監督ルーム（司令部）")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("1レース予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("設定を保存しました。")

    # 📂 過去ログ呼び出し ＆ 復習ルーム
    st.markdown("---")
    st.header("📂 過去ログ復習")
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)
    
    if log_files:
        selected_log = st.selectbox("復習・確認する対象レース", log_files)
        
        if st.button("📖 予想指示書を呼び出す"):
            with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                st.session_state["res"] = f.read()
            st.success(f"{selected_log} を読み込みました！")
            
        st.markdown("---")
        st.subheader("🏁 対象・レース結果コピペ")
        st.caption("💡 1行目にレース名を入力し、2行目から結果（着順・払戻金・通過順）を丸ごとコピペしてください。")
        result_copypaste = st.text_area("1行目：レース名 / 2行目〜：結果コピペ", height=200)
        
        if st.button("🚨 馬単の着順・ハナ争いと照合して復習"):
            if not api_key or not result_copypaste.strip():
                st.error("APIキーと結果データが必要です")
            else:
                try:
                    genai.configure(api_key=api_key)
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                    model = genai.GenerativeModel(m_name)
                    
                    lines = result_copypaste.splitlines()
                    raw_title = lines[0].strip() if lines else "対象レース結果"
                    cleaned_title = clean_filename(raw_title)
                    
                    with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                        past_prediction = f.read()
                        
                    p_1 = "あなたは総監督Baruの右腕競馬AIだ。提示されたトリプル馬単対象レースの予想指示書と、実際のレース結果コピペを徹底的に突き合わせ、短く簡潔に箇条書きで猛省レポートを作成せよ。\n\n"
                    p_2 = f"【タイトル】最上部に見出し「### 🏁 {raw_title} 戦果照合」を出力せよ。\n\n"
                    p_3 = "【馬単解析掟】\n1. 1着・2着の入線パターンとコーナー通過順から、想定外の逃げ残りや差し遅れのズレを炙り出せ。\n2. 馬単高配当を演出した人気薄の激走理由（地方砂質・トラックバイアス）の読みのズレを猛省せよ。\n3. 次回トリプル馬単を仕留めるため、バイアス設定をどう微調整すべきか簡潔に導け。\n\n"
                    p_4 = f"【出力フォーマット】\n### 🏁 {raw_title} 戦果照合\n馬単払戻金および戦果の整理\n\n### 🧠 1着2着・ハナ争いのズレ解剖\n馬単の着順に直結した地方小回り展開・バイアスのズレ分析\n\n### 🛠️ 次回制覇へのAI
