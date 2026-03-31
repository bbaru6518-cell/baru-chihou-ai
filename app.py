import streamlit as st
import google.generativeai as genai
import json
import os

# --- 設定保存 ---
CONFIG_FILE = "baru_chihou_config.json"
def save_cfg(k, b):
    with open(CONFIG_FILE, "w") as f: json.dump({"k": k, "b": b}, f)
def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"k": "", "b": ""}

cfg = load_cfg()
st.set_page_config(page_title="Baru 競馬AI", layout="wide")
st.title("🏇 Baru 競馬AI - 【地方砂質・先行特化版】")

def reset_data():
    st.session_state["data_input"] = ""

with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス", value=cfg.get("b", "地方の深い砂に対応できるパワー馬、および小回り内枠の先行馬を最優先せよ。"), height=150)
    if st.button("💾 保存"):
        save_cfg(api_key, bias)
        st.success("設定を保存しました。")

col1, col2 = st.columns([2, 1])
with col1:
    data = st.text_area("📋 レースデータ", height=550, key="data_input", placeholder="データを貼り付け...")
with col2:
    if st.button("🚀 地方砂質・先行ジャッジ"):
        if not api_key or not data:
            st.error("入力不足です")
        else:
            try:
                genai.configure(api_key=api_key)
                prompt = f"競馬AI総監督Baruの右腕として、以下のデータから【地方砂質・先行バイアス】に基づき結論を出せ。\n\nデータ: {data}\nバイアス: {bias}"
                
                # --- 【最重要】404エラーを力技で突破するリトライループ ---
                success = False
                # 試行するモデル名の全パターン
                model_variants = ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-pro", "models/gemini-pro"]
                
                with st.spinner("あらゆる接続経路を試行中..."):
                    for m_name in model_variants:
                        try:
                            model = genai.GenerativeModel(m_name)
                            response = model.generate_content(prompt)
                            st.success(f"✅ 解析完了 (接続成功: {m_name})")
                            st.markdown("---")
                            st.markdown(response.text)
                            success = True
                            break # 成功したらループ終了
                        except Exception:
                            continue # 失敗したら次のパターンへ
                
                if not success:
                    st.error("全接続パターンが拒否されました。APIキーが『新しいプロジェクト』で作られたものか、再度ご確認ください。")

            except Exception as e:
                st.error(f"致命的なエラーが発生しました: {e}")

    st.button("🧹 データをクリア", on_click=reset_data)
