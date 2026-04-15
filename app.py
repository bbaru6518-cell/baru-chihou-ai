import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup

# --- 設定保存機能 ---
CONFIG_FILE = "baru_pro_config.json"
def save_cfg(k, b):
    with open(CONFIG_FILE, "w") as f: json.dump({"k": k, "b": b}, f)
def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"k": "", "b": "芝の決め手、血統適性、上がり3F、トラックバイアスを統合解析せよ。近走不振でも急坂コースの上がり最速馬は特注。"}

cfg = load_cfg()
st.set_page_config(page_title="Baru 競馬AI Pro 18", layout="wide")
st.title("🏇 Baru 競馬AI Pro - 【勝率予測＆1軸4頭流し完全版】")

# --- スクレイピング関数 ---
def get_netkeiba_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        for ad in soup.find_all(class_=["rev_list", "ads_area", "p_ad", "taboola", "footer", "common_ad"]):
            ad.decompose()
        main_data = soup.find("table", class_=["RaceTable01", "db_table"]) or soup.find("div", id="netkeiba_db") or soup
        text = main_data.get_text(separator="\n", strip=True)
        return text[:20000]
    except Exception as e:
        return f"取得エラー: {e}"

if "res" not in st.session_state:
    st.session_state["res"] = ""

def clear_all():
    st.session_state["url_field"] = ""
    st.session_state["manual_field"] = ""
    st.session_state["res"] = ""

with st.sidebar:
    st.header("⚙️ 総監督ルーム")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias_val = cfg.get("b")
    bias = st.text_area("🧠 総監督バイアス", value=bias_val, height=200)
    budget = st.number_input("1レースの予算(円)", value=1000, step=100)
    
    if st.button("💾 設定を保存"):
        save_cfg(api_key, bias)
        st.success("設定を保存しました。")
    
    st.divider()
    st.button("🧹 全データをクリア", on_click=clear_all)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 データ入力")
    url_input = st.text_input("🔗 netkeiba PC版URL", key="url_field")
    st.write("--- または ---")
    manual_data = st.text_area("✍️ 馬柱データを貼り付け", height=500, key="manual_field")
    
    if st.button("🚀 勝率予測・フルスキャン開始"):
        target_data = ""
        if url_input:
            with st.spinner("PC版サイトから全頭データを抽出中..."):
                target_data = get_netkeiba_data(url_input)
        else:
            target_data = manual_data

        if not api_key or not target_data:
            st.error("APIキーとデータが必要です")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                # 勝率予測を義務付けるプロンプト
                prompt = f"""
                あなたは競馬AI総監督Baruの右腕だ。18頭フルゲートまで全頭を精密に解析せよ。
                
                【最重要：勝率予測ルール】
                全頭短評の冒頭に、独自アルゴリズムで算出した「単勝勝率％」と「複勝圏内率％」を必ず記載せよ。
                例：「1. 馬名 [単勝15%/複勝45%] - 短評...」
                ※全頭の単勝勝率の合計が100%になるよう、期待値を加味して調整すること。
                
                【構成】
                1. 芝の覇者/砂の王 (血統・適性)
                2. 先行優位ジャッジ (展開予測)
                3. 下剋上・勝負気配 (上がり最速ポテンシャル馬)
                4. 全頭解析＆勝率予測 [単%/複%] (1〜18番まで一頭も飛ばさず点呼)
                5. 最終結論 (◎○▲△×)
                6. 🚀 総監督・勝負馬券 (予算{budget}円)
                   - 【メイン】3連複 1軸4頭流し (◎軸、相手○▲△×) 100円×6点
                   - 【抑え】残予算で◎の単複や、期待値が高い馬連・ワイドを指示せよ。
                
                データ: {target_data}
                バイアス: {bias}
                """
                with st.spinner("18頭の勝率と期待値を計算中..."):
                    response = model.generate_content(prompt)
                    st.session_state["res"] = response.text
            except Exception as e:
                st.error(f"解析エラー: {e}")

with col2:
    st.subheader("📊 勝率予測・投資指示書")
    if st.session_state["res"]:
        st.markdown(st.session_state["res"])
    else:
        st.info("解析を開始すると、ここに勝率(%)付きの診断が表示されます。")

st.caption("Baru Stable AI Pro v12.3 - Win-Probability Model")
