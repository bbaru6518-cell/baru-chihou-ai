import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

# --- 設定保存機能 ---
CONFIG_FILE = "baru_pro_config.json"
LOG_DIR = "racing_logs_standard"
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
        "b": "JRA（中央競馬）および地方競馬の高速馬場・トラックバイアス、芝・ダートのキレ、走破タイム理論（基準タイム・馬場補正）、上がり3F、展開・ハナ争いを統合解析せよ。"
    }

def clean_filename(name):
    if not name:
        return ""
    clean = re.sub(r'[\\/*?:"<>| \t]', '_', name.strip())
    return clean[:50]

cfg = load_cfg()
st.set_page_config(page_title="Baru AI Pro v24.8", layout="wide", initial_sidebar_state="expanded")
st.title("🏇 Baru 競馬AI Pro - 【Ver 24.8 ファイル名連動・自己学習型】")

with st.sidebar:
    st.header("⚙️ 総監督ルーム（通常レース指令部）")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（馬場・補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("1レース予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("通常レースの設定を保存しました。")

    # 📂 過去ログ呼び出し ＆ 復習ルーム
    st.markdown("---")
    st.header("📂 過去ログ・結果復習ルーム")
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)
    
    if log_files:
        selected_log = st.selectbox("復習・確認する過去の予想", log_files)
        
        if st.button("📖 予想指示書を呼び出す"):
            with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                st.session_state["res"] = f.read()
            st.success(f"{selected_log} を読み込みました！")
            
        st.markdown("---")
        st.subheader("🏁 レース結果のコピペ投入")
        st.caption("💡 1行目にレース名やタイトル（例：大井11R 帝王賞）を入力し、2行目から結果を丸ごとコピペしてください！ファイル名がそのレース名に生まれ変わります。")
        result_copypaste = st.text_area("1行目：レース名 / 2行目〜：結果コピペ", height=200)
        
        if st.button("🚨 実際の着順・ハナ争いと照合して復習"):
            if not api_key or not result_copypaste.strip():
                st.error("APIキーと結果データが必要です")
            else:
                try:
                    genai.configure(api_key=api_key)
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                    model = genai.GenerativeModel(m_name)
                    
                    lines = result_copypaste.splitlines()
                    raw_title = lines[0].strip() if lines else "通常レース結果"
                    cleaned_title = clean_filename(raw_title)
                    
                    with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                        past_prediction = f.read()
                        
                    # ⭕ 【究極のバグ対策】全角カッコや特殊文字によるPython文字列エラーを避けるため、パーツに分けて結合する安全方式に変更
                    p_1 = "あなたは総監督Baruの右腕AIだ。提示された当時の予想指示書と、実際のレース結果コピペを徹底的に突き合わせ、超精密な反省レポートを作成せよ。\n\n"
                    p_2 = f"【重要：タイトル認識】最上部には必ず総監督が指定したタイトル「{raw_title}」を引用して「### 🏁 {raw_title} 答え合わせ・戦果照合」という見出しからスタートせよ。\n\n"
                    p_3 = "【解析掟】\n1. 通過順データから想定外の逃げ先行馬の動きや予測したハナ争いのズレを炙り出せ。\n2. タイム補正やトラックバイアスが結果にどう影響したか、AI側の読みのズレを猛省せよ。\n3. 次回同じコースで勝負する際、バイアスやスピード指数をどう微調整すべきか具体的な改善策を導け。\n\n"
                    p_4 = f"【出力フォーマット】\n### 🏁 {raw_title} 答え合わせ・戦果照合\n的中や配当結果の整理\n\n### 🧠 展開・ハナ争いのズレ解剖\nコーナー通過順からの展開分析\n\n### 🛠️ 次回に向けたAIロジック微調整案\nスピード補正や馬場バイアスの具体的アドバイス\n\n"
                    p_5 = f"---\n【当時の予想指示書】:\n{past_prediction}\n\n【実際のレース結果コピペ】:\n{result_copypaste}"
                    
                    review_prompt = p_1 + p_2 + p_3 + p_4 + p_5

                    with st.spinner("実際の着順・コーナー通過順から猛省・復習中..."):
                        response = model.generate_content(review_prompt)
                        review_result = "\n\n" + "="*20 + f" 🏁 {raw_title} 復習ログ " + "="*20 + "\n" + response.text
                        
                        old_path = os.path.join(LOG_DIR, selected_log)
                        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_filename = f"{cleaned_title}_{now_str}.txt"
                        new_path = os.path.join(LOG_DIR, new_filename)
                        
                        full_content = past_prediction + review_result
                        with open(new_path, "w", encoding="utf-8") as nf:
                            nf.write(full_content)
                        
                        if old_path != new_path and os.path.exists(old_path):
                            os.remove(old_path)
                            
                        st.session_state["res"] = full_content
                        st.success(f"💾 ファイル名を「{new_filename}」に変更し、復習ログを完全保存しました！")
                        st.rerun()
                except Exception as e:
                    st.error(f"復習解析エラー: {e}")
    else:
        st.info("まだ保存された予想ログはありません。")

if "res" not in st.session_state:
    st.session_state["res"] = ""

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("📋 9走馬柱・オッズ混在テキスト入力")
    url_input = st.text_input("🔗 レースURL")
    manual_data = st.text_area("✍️ netkeibaコピペデータ", height=500)
    
    if st.button("🚀 構造解剖・多角データ解析開始"):
        try:
            target_data = ""
            if url_input:
                with st.spinner("レースデータをスクレイピング中..."):
                    headers = {"User-Agent": "Mozilla/5.0"}
                    res = requests.get(url_input, headers=headers)
                    res.encoding = res.apparent_encoding
                    soup = BeautifulSoup(res.text, "html.parser")
                    main_data = soup.find_all("table")
                    for table in main_data:
                        target_data += table.get_text(separator="\n", strip=True) + "\n"
                    target_data = target_data[:50000]
            else:
                target_data = manual_data

            if not api_key or not target_data:
                st.error("必要なデータが不足しています")
            else:
                genai.configure(api_key=api_key)
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                model = genai.GenerativeModel(m_name)
                
                base_instruction = """あなたは中央競馬（JRA）および地方競馬を統括する競馬AIであり、総監督Baruの絶対的右腕だ。
入力されたテキストデータから人気・枠・馬番・馬名・オッズ・過去の通過順を完全に解剖し、逃げ・先行馬の有利不利を見抜いた勝負指示書を作成せよ。

【データ解剖における絶対掟】
1. 過去9走の通過順データ（例: 1-1-1 や 11-10-8 等）や、データ分析テキスト内の「有利な脚質：逃げ」などの文脈から、今回の出走馬の脚質を「逃げ」「先行」「差し」「追込」に超精密に分類せよ。
2. 特に、ハナを叩きそうな「逃げ」馬、好位をキープする「先行」馬にはマーク（印）をつけ、展開面での有利不利を可視化せよ。

【出力フォーマット】
以下の3つのセクション構成のみを出力せよ。余計な前置きや挨拶は一切禁止する。

### 📊 全頭精密診断・血統適性リスト
必ず以下の列を持つMarkdownテーブル形式で今回の出走馬を全頭出力せよ。
| 馬番 | 馬名 | 父 | 母 | 血統適性 | 脚質 | 人気 | 評価 | 理由 |
※【脚質】列には、「逃げ🔥」「先行📢」「差し」「追込」のように、逃げ・先行馬がひと目でわかるよう絵文字付きで印をつけよ！
※評価は（◎、○、▲、△、注、消）で厳選せよ。

### 📈 走破タイム・トラックバイアス深層データ分析
1. 【走破理論・スピード指数分析】: 距離・コース・今回の馬場状態（不・重など）から、走破タイムの基準値・補正値が最も優秀な上位3頭。
2. 【展開・ハナ争い完全看破】: 今回ハナを叩く可能性が最も高い「逃げ🔥」馬の特定と、その馬が作るペース予想（ハイ/ミドル/スロー）。それによって展開利を受ける「先行📢」馬や差し馬の力関係。
3. 【激走のシグナル（上積みチェック）】: 過去9走の馬体重の変動、レース間隔の実績、調教評価から、今回「完全叩き一変」の激走気配がある下剋上穴馬。
4. 【血統×コースマトリクス】: 開催競馬場・コースのリーディングサイアー実績に最も合致する特注配合馬。

### 💰 三連複フォーメーション：厳選15点指示書
投資効率を最大化する【合計15点】のフォーメーションを強制生成せよ。
 - 1頭目（軸馬）：◎（1頭）
 - 2頭目（対抗）：○や▲から「厳選した2頭」のみを指定
 - 3頭目（紐・穴）：◎、○、▲、△、注を含めた「合計7頭」を指定
※計算式 : 1頭 × 2頭 × (7頭 - 2頭) ＝ 【15点】に完全固定。

フォーマット例：
**◎ 軸馬: 〇番 (馬名)**
1頭目：〇
2頭目：〇, 〇
3頭目：〇, 〇, 〇, 〇, 〇, 〇, 〇"""

                prompt = base_instruction + f"\n対象データ: {target_data}\n総監督バイアス: {bias}\n予算: {budget}円"

                with st.spinner(f"🚀 展開・脚質をマッピング中... ({m_name})"):
                    response = model.generate_content(prompt)
                    output_text = response.text
                    st.session_state["res"] = output_text
                    
                    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    with open(os.path.join(LOG_DIR, f"3連複15点_{now_str}.txt"), "w", encoding="utf-8") as log_f:
                        log_f.write(f"=== 予想生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n🧠 バイアス: {bias}\n\n" + output_text)
                    st.toast("💾 予想ログを仮保存しました！結果復習時にファイル名が自動変更されます。", icon="💾")
                    st.rerun()
        except Exception as e:
            st.error(f"解析エラー: {e}")

with col2:
    st.subheader("📊 投資指示書 ＆ 復習ルーム連動表示")
    if st.session_state["res"]:
        st.markdown(st.session_state["res"])
st.caption("Baru Stable AI Pro v24.8 - Filename Sync Edition")
