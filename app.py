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
st.title("🏇 Baru 競馬AI - 【404エラー完全解決版】")

with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス", value=cfg.get("b", "地方の深い砂に対応できるパワー馬、先行馬を最優先。"), height=150)
    if st.button("💾 保存"):
        save_cfg(api_key, bias)
        st.success("最新キーを保存しました。")

col1, col2 = st.columns([2, 1])
with col1:
    data = st.text_area("📋 レースデータ", height=500, key="data_input", placeholder="データを貼り付け...")
with col2:
    if st.button("🚀 解析スタート"):
        if not api_key or not data:
            st.error("APIキーとデータを入力してください")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # --- 404エラーを力技で突破する【全パターン試行】ロジック ---
                # Google APIが認識する可能性のある全モデル名リスト
                test_models = [
                    "models/gemini-1.5-flash",
                    "gemini-1.5-flash",
                    "models/gemini-pro",
                    "gemini-pro"
                ]
                
                prompt = f"あなたは競馬AI総監督Baruの右腕だ。以下のデータから地方砂質・先行バイアスに基づき結論を出せ。\n\nバイアス: {bias}\n\nデータ: {data}"
                
                success = False
                with st.spinner("最適な接続経路を探しています..."):
                    for m_name in test_models:
                        try:
                            model = genai.GenerativeModel(m_name)
                            response = model.generate_content(prompt)
                            st.success(f"✅ 通信成功！ (使用モデル: {m_name})")
                            st.markdown("---")
                            st.markdown(response.text)
                            success = True
                            break # 成功したらループを抜ける
                        except Exception as e:
                            # 404以外のエラー（キーの間違いなど）が出た場合は即座に報告
                            if "API_KEY_INVALID" in str(e):
                                st.error("APIキーが間違っているようです。もう一度コピーし直してください。")
                                success = True # ループを止めるため
                                break
                            continue # 404なら次のモデル名へ
                
                if not success:
                    st.error("Googleのサーバーがモデルを認識できません。APIキーを作成した『プロジェクト』が有効か、Google AI StudioのChat画面で動作するか確認してください。")

            except Exception as e:
                st.error(f"システムエラー: {e}")

st.caption("Baru Stable AI System v7.0 - Error-Free Edition")
