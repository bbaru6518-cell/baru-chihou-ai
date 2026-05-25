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
LOG_DIR = "racing_logs_triple"  # トリプル馬単地方競馬専用の独立フォルダ
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
        # 【トリプル馬単地方競馬特化】馬単を3連続で射抜くための、地方の展開・ハナ争い・完全前残り・または紛れる重馬場バイアスに特化した初期指示
        "b": "トリプル馬単対象地方レース（主に後半3R）のトラックバイアス, 砂質, 1角ポジション争い, 絶対に崩れない軸馬の選定, および逆転候補の展開利・ハナ争いを統合解析せよ。"
    }

def clean_filename(name):
    if not name:
        return ""
    clean = re.sub(r'[\\/*?:"<>| \t]', '_', name.strip())
    return clean[:50]

cfg = load_cfg()

# 👑 【完全修正】ブラウザタブおよび大看板タイトルから古い表記を徹底排除し、完全リニューアル！
st.set_page_config(page_title="Baru AI Triple Local Pro v24.8.5", layout="wide", initial_sidebar_state="expanded")
st.title("🏇 Baru トリプル馬単地方競馬AI Pro - 【Ver 24.8.5 高速・トリプル特化版】")

with st.sidebar:
    st.header("⚙️ 総監督ルーム（トリプル馬単地方競馬・司令部）")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（トリプル馬単地方競馬専用・補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("1レース予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("トリプル馬単地方競馬専用の設定を保存しました。")

    # 📂 過去ログ呼び出し ＆ 復習ルーム
    st.markdown("---")
    st.header("📂 トリプル馬単地方競馬・過去ログ復習")
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
        
        if st.button("🚨 馬単の着順
