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
                # --- 修正ポイント：API設定 ---
                genai.configure(api_key=api_key)
                
                # 404エラーを回避するため、models/ を付けない標準形式に固定
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                prompt = f"競馬AI総監督Baruの右腕として、以下のデータから【地方砂質・先行バイアス】に基づき結論を出せ。\n\nデータ: {data}\nバイアス: {bias}"
                
                with st.spinner("解析中..."):
                    # 安全な呼び出し
                    response = model.generate_content(prompt)
                    st.success("✅ 解析完了")
                    st.markdown("---")
                    st.markdown(response.text)
            except Exception as e:
                # もし gemini-1.5-flash がダメな場合の最終バックアップ
                try:
                    model_alt = genai.GenerativeModel("gemini-pro")
                    response = model_alt.generate_content(prompt)
                    st.success("✅ 解析完了 (Backup Model)")
                    st.markdown(response.text)
                except Exception as e2:
                    st.error(f"エラーが発生しました。APIキーを確認してください。\n詳細: {e2}")

    st.button("🧹 データをクリア", on_click=reset_data)
