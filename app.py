import streamlit as st
import google.generativeai as genai
import json
import os

# --- 設定保存（地方専用ファイル名） ---
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
st.set_page_config(page_title="Baru 地方競馬AI", layout="wide")
st.title("🏇 Baru 地方競馬AI - 【地方砂質・先行特化版】")

def reset_data():
    st.session_state["data_input"] = ""

with st.sidebar:
    st.header("⚙️ 地方専用設定")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 地方総監督バイアス", value=cfg.get("b", "地方の深い砂に対応できるパワー馬、および小回り内枠の先行馬を最優先せよ。"), height=150)
    if st.button("💾 保存"):
        save_cfg(api_key, bias)
        st.success("地方競馬ロジック、起動完了。")

col1, col2 = st.columns([2, 1])
with col1:
    data = st.text_area("📋 地方レースデータ", height=550, key="data_input", placeholder="地方競馬（大井・高知など）のデータを貼り付け...")
with col2:
    if st.button("🚀 地方砂質・先行ジャッジ"):
        if not api_key or not data:
            st.error("入力不足です（APIキーとデータを入力してください）")
        else:
            try:
                # --- API設定（最もシンプルな接続方式） ---
                genai.configure(api_key=api_key)
                
                # モデル指定を最もエラーが起きにくい形式に変更
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                prompt = f"""
                あなたは競馬AI総監督Baruの右腕だ。
                地方競馬特有の【砂質・小回り・先行バイアス】に基づき、人気に惑わされず結論を出せ。
                
                【対象データ】: {data}
                【総監督バイアス】: {bias}
                
                以下の5項目で出力せよ：
                1.★地方・砂の王(POWER-AXIS): 
                   - 地方特有のタフな砂を苦にしない大型馬(480kg〜)、または小回りを逃げ切れる快速馬を軸に指名。
                2.小回り内枠・先行の絶対優位: 
                   - 最初のコーナーを3番手以内で回れる馬を評価の中心に置く。
                3.移籍・勝負気配の察知: 
                   - 中央からの移籍初戦や、地元リーディング騎手への乗り替え等の「ヤリ」を察知。
                4.全頭診断: 1行ずつ。馬番、馬名、そして「砂の適性と、最初のコーナーでの位置取り予測」。
                5.買い目: 
                   - 逃げ・先行馬を軸にした「馬複・ワイド・3連複」。
                   - 紛れが少ないため点数は絞りつつ、爆穴を1頭だけ3列目に必ず入れること。
                """
                
                with st.spinner("地方の深い砂と展開を読み解き中..."):
                    # 安全に生成を実行
                    res = model.generate_content(prompt)
                    st.success("✅ 地方解析完了。砂の適性と先行力を完全に見抜きました。")
                    st.markdown("---")
                    st.markdown(res.text)
            except Exception as e:
                # 万が一エラーが出た場合、別のモデル名での接続を試みる自動リトライ機能
                try:
                    model_alt = genai.GenerativeModel("models/gemini-1.5-flash")
                    res = model_alt.generate_content(prompt)
                    st.success("✅ 地方解析完了（リトライ成功）。
