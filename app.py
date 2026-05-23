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
        "b": "JRA（中央競馬）および地方競馬の高速馬場・トラックバイアス、芝・ダートのキレ、走破タイム理論（基準タイム・馬場補正）、上がり3Fを統合解析せよ。"
    }

cfg = load_cfg()
st.set_page_config(page_title="Baru AI Pro v23.5", layout="wide")
st.title("🏇 Baru 競馬AI Pro - 【Ver 23.5 オッズ構造解析＆データ分析枠完全版】")

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

with col1:
    st.subheader("📋 9走馬柱・オッズ混在テキスト入力")
    url_input = st.text_input("🔗 レースURL（出馬表・オッズページ等）")
    manual_data = st.text_area("✍️ netkeibaコピペデータ（オッズ表やデータ分析テキストをそのまま一括投入）", height=500)
    
    if st.button("🚀 構造解剖・多角データ解析開始"):
        target_data = ""
        if url_input:
            with st.spinner("レースデータをバックグラウンドスクレイピング中..."):
                try:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    res = requests.get(url_input, headers=headers)
                    res.encoding = res.apparent_encoding
                    soup = BeautifulSoup(res.text, "html.parser")
                    main_data = soup.find_all("table")
                    for table in main_data:
                        target_data += table.get_text(separator="\n", strip=True) + "\n"
                    target_data = target_data[:50000]
                except Exception as e:
                    st.error(f"スクレイピングエラー: {e}")
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
                
                # --- 1行凝縮オッズとデータ分析を完全にマッピングする超絶プロンプト ---
                prompt = f"""
                あなたは中央競馬（JRA）および地方一発逆転ファイナルを統括する競馬AIであり、総監督Baruの絶対的右腕だ。
                今回入力されるデータは、人気・枠・馬番・馬名・オッズが「1710オーミパルーザ2.8」のように完全に1行に凝縮された特殊なオッズ表や、過去9走の馬柱データ、データ分析テキストの混在である。
                文字の塊を完全に解剖（パース）し、狂いのない投資指示書を作成せよ。

                【データ解剖における絶対掟】
                1. 「1710オーミパルーザ2.8」という行の場合、先頭の「1」＝人気、「7」＝枠番、「10」＝馬番、「オーミパルーザ」＝馬名、「2.8」＝単勝オッズ、と完全に見極めよ。人気順の並び（1, 2, 3...）をインデックスとして活用し、馬番（1桁〜2桁）を絶対に誤認するな。
                2. 別データにある「2メイジ」「8ジョウ」などの省略表記がある場合、このオッズ表にある馬番「5番メイジョウエナジー」「8番ジョウショーレーヴ」の正式名称と脳内で100%正しく紐付け（マッピング）して補完せよ。
                3. 過去9走前のデータにある着順やオッズが混ざっていても、今回の最新の馬番・オッズを最優先にせよ。

                【出力フォーマット】
                以下の3つのセクション構成のみを出力せよ。余計な前置きや挨拶は一切禁止する。

                ### 📊 全頭精密診断・血統適性リスト
                必ず以下の列を持つMarkdownテーブル形式で今回の出走馬を全頭出力せよ。
                | 馬番 | 馬名 | 父 | 母 | 血統適性 | 人気 | 評価 | 理由 |
                ※評価は（◎、○、▲、△、注、消）で厳選せよ。
                ※オッズ表から取得した正確な「馬番」と「人気」を記載すること。

                ### 📈 走破タイム・トラックバイアス深層データ分析
                総監督が展開を組み立てるためのデータ分析専用枠。以下の4項目について、簡潔に箇条書きで分析せよ。
                1. **【走破理論・スピード指数分析】**: 距離・コース・今回の馬場状態（不・重など）から、走破タイムの基準値・補正値が最も優秀な上位3頭。
                2. **【トラックバイアス・位置取り予測】**: 想定されるペース（ハイ/ミドル/スロー）と、馬場状態（良/重/不良）から有利に働く脚質・枠順の傾向。
                3. **【激走のシグナル（上積みチェック）】**: 過去9走の馬体重の変動、レース間隔の実績、調教評価から、今回「完全叩き一変」の激走気配がある下剋上穴馬。
                4. **【血統×コースマトリクス】**: 開催競馬場・コース（例: 高知ダ1300m、東京芝1600mなど）のリーディングサイアー実績に最も合致する特注配合馬。

                ### 💰 三連複フォーメーション：厳選15点指示書
                投資効率を最大化する【合計15点】のフォーメーションを強制生成せよ。
                - 1頭目（軸馬）：◎（1頭）
                - 2頭目（対抗）：○や▲から「厳選した2頭」のみを指定
                - 3頭目（紐・穴）：◎、○、▲、△、注を含めた「合計7頭」を指定
                ※計算式：1頭×2頭×(7頭 - 2頭) ＝ 【15点】に完全固定。

                フォーマット例：
                **◎ 軸馬: 〇番 (馬名)**
                ```text
                1頭目：〇
                2頭目：〇, 〇
                3頭目：〇, 〇, 〇, 〇, 〇, 〇, 〇
                ```

                対象データ: {target_data}
                総監督バイアス: {bias}
                予算: {budget}円
                """
                
                with st.spinner(f"🚀 高知・JRAデータを多角パース中... ({m_name})"):
                    response = model.generate_content(prompt)
                    st.session_state["res"] = response.text
            except Exception as e:
                st.error(f"解析エラー: {e}")

with col2:
    st.subheader("📊 投資指示書 (オッズ・データ分析枠完全版)")
    if st.session_state["res"]:
        st.markdown(st.session_state["res"])

st.caption("Baru Stable AI Pro v23.5 - Unstructured Odds & Deep Data Analytics Edition")
