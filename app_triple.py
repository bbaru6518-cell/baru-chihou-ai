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
        # ⭕ 【トリプル馬単特化】馬単を3連続で射抜くための、展開・ハナ争い・完全前残り・または紛れる重馬場バイアスに特化した初期指示
        "b": "トリプル馬単対象指定レース（主に後半3R）のトラックバイアス、砂質、1角ポジション争い、絶対に崩れない軸馬の選定、および逆転候補の展開利・ハナ争いを統合解析せよ。"
    }

def clean_filename(name):
    if not name:
        return ""
    clean = re.sub(r'[\\/*?:"<>| \t]', '_', name.strip())
    return clean[:50]

cfg = load_cfg()
# ⭕ 【トリプル馬単仕様】タイトル看板をトリプル馬単専用に変更
st.set_page_config(page_title="Baru AI Triple Pro v24.8.5", layout="wide", initial_sidebar_state="expanded")
st.title("🏇 Baru トリプル馬単AI Pro - 【Ver 24.8.5 地方特化・3連単並列解析型】")

with st.sidebar:
    st.header("⚙️ 総監督ルーム（トリプル馬単・司令部）")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（トリプル馬単専用・補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("1レース予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("トリプル馬単専用の設定を保存しました。")

    # 📂 過去ログ呼び出し ＆ 復習ルーム
    st.markdown("---")
    st.header("📂 トリプル馬単・過去ログ復習")
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)
    
    if log_files:
        selected_log = st.selectbox("復習・確認するトリプル対象レース", log_files)
        
        if st.button("📖 予想指示書を呼び出す"):
            with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                st.session_state["res"] = f.read()
            st.success(f"{selected_log} を読み込みました！")
            
        st.markdown("---")
        st.subheader("🏁 トリプル対象・レース結果コピペ")
        st.caption("💡 1行目にレース名を入力し、2行目から結果（着順・払戻金・通過順）を丸ごとコピペしてください。")
        result_copypaste = st.text_area("1行目：レース名 / 2行目〜：結果コピペ", height=200)
        
        if st.button("🚨 馬単の着順・ハナ争いと照合して復習"):
