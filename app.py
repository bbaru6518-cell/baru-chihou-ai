import streamlit as st
import google.generativeai as genai # 内部で最新版として動作させます
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
st.title("🏇 Baru 競馬AI - 【最新エンジン搭載版】")

with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス", value=cfg.get("b", "地方の深い砂に対応できるパワー馬、先行馬を最優先。"), height=150)
    if st.button("💾 保存"):
        save_cfg(api_key, bias)
        st.success("最新キーを保存しました。")

col1, col2 = st.columns([2, 1])
with col1:
    data = st.text_area("📋 レースデータ", height=500, key="data_input")
with col2:
    if st.button("🚀 最新エンジンで解析"):
        if not api_key or not data:
            st.error("入力不足です")
        else:
            try:
                # --- 最新の指定方法に変更 ---
                genai.configure(api_key=api_key)
                
                # 総監督が見つけたドキュメントに合わせ、最も新しいモデル名を直接指定
                # 404が出ないよう、複数の候補を自動で試します
                model_found = False
                for model_name in ["gemini-1.5-flash", "gemini-1.5-pro"]:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content(f"{bias}\n\nデータ:\n{data}")
                        st.success(f"✨ 通信成功！ (Model: {model_name})")
                        st.markdown("---")
                        st.markdown(response.text)
                        model_found = True
                        break
                    except:
                        continue
                
                if not model_found:
                    st.error("最新モデルへのアクセスが拒否されました。APIキーが『新しいプロジェクト』で作られたものか再確認してください。")

            except Exception as e:
                st.error(f"エラー詳細: {e}")

st.caption("v6.0 - Latest Gemini Engine Integration")
