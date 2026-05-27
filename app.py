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
LOG_DIR = "racing_logs_local"
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
st.set_page_config(page_title="Baru AI Local Pro v24.8.9", layout="wide", initial_sidebar_state="expanded")
st.title("🏇 Baru 地方競馬AI Pro - 【Ver 24.8.9 紐＆レイアウト完全修正版】")

with st.sidebar:
    st.header("⚙️ 総監督ルーム（地方レース指令部）")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（地方砂質・補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("1レース予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("地方競馬専用の設定を保存しました。")

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
        st.caption("💡 1行目にレース名を入力し、2行目から結果を丸ごとコピペしてください！")
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
                    raw_title = lines[0].strip() if lines else "地方レース結果"
                    cleaned_title = clean_filename(raw_title)
                    
                    with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                        past_prediction = f.read()
                        
                    p_1 = "あなたは総監督Baruの右腕競馬AIだ。当時の予想指示書と実際のレース結果を突き合わせ、短く簡潔に箇条書きで猛省レポートを作成せよ。\n\n"
                    p_2 = f"【タイトル】最上部に見出し「### 🏁 {raw_title} 答え合わせ・戦果照合」を出力せよ。\n\n"
                    p_3 = "【地方解析掟】\n1. コーナー通過順から、ハナ争いのズレを炙り出せる分析を行え。\n2. 地方競馬場特有の砂質影響の読みのズレを猛省せよ。\n3. 次回に向けバイアス設定をどう微調整すべきか簡潔に導け。\n\n"
                    p_4 = f"【出力フォーマット】\n### 🏁 {raw_title} 答え合わせ・戦果照合\n配当結果整理\n\n### 🧠 地方砂質×ハナ争いのズレ解剖\n簡潔な展開分析\n\n### 🛠️ 次回に向けたAIロジック微調整案\n具体的アドバイス\n\n"
                    p_5 = f"---\n【当時の予想指示書】:\n{past_prediction}\n\n【実際のレース結果コピペ】:\n{result_copypaste}"
                    
                    review_prompt = p_1 + p_2 + p_3 + p_4 + p_5

                    with st.spinner("地方のズレから猛省・復習中..."):
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
                        st.success(f"💾 ファイル名を「{new_filename}」に変更し保存しました！")
                        st.rerun()
                except Exception as e:
                    st.error(f"復習解析エラー: {e}")
    else:
        st.info("まだ保存された地方予想ログはありません。")

if "res" not in st.session_state:
    st.session_state["res"] = ""

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("📋 地方競馬 過去馬柱・オッズ混在テキスト入力")
    url_input = st.text_input("🔗 地方レースURL（netkeiba等）")
    manual_data = st.text_area("✍️ 地方競馬コピペデータ", height=500)
    
    if st.button("🚀 地方構造解剖・ダートデータ解析開始"):
        try:
            target_data = ""
            if url_input:
                with st.spinner("地方レースデータをスクレイピング中..."):
                    headers = {"User-Agent": "Mozilla/5.0"}
                    res = requests.get(url_input, headers=headers)
                    res.encoding = res.apparent_encoding
                    soup = BeautifulSoup(res.text, "html.parser")
                    main_data = soup.find_all("table")
                    for table in main_data:
                        target_data += table.get_text(separator="\n", strip=True) + "\n"
                    target_data = target_data[:15000]
            else:
                target_data = manual_data[:15000]

            if not api_key or not target_data:
                st.error("必要なデータが不足しています")
            else:
                genai.configure(api_key=api_key)
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                model = genai.GenerativeModel(m_name)
                
                base_instruction = """あなたは地方競馬をハックする競馬AIであり、総監督Baruの絶対的右腕だ。
入力されたテキストデータから各馬の能力・脚質を完全に解剖し、無駄を極限まで省いた鋭い勝負指示書を最速で作成せよ。

【データ解剖・出力の絶対ルール】
1. 前置き、挨拶、まとめの雑談は一切禁止。即座に出力フォーマットを開始せよ。
2. 理由や分析セクションは、要点のみを鋭い箇条書きでコンパクトに記述し、冗長な表現を徹底的に排除せよ。

【出力フォーマット】
### 📊 全頭精密診断・地方ダート適性リスト
必ず以下の列（単勝勝率・複勝勝率を含む）を持つMarkdownテーブル形式で今回の出走馬を全頭出力せよ。
| 馬番 | 馬名 | 単勝勝率(%) | 複勝勝率(%) | ダート砂適性 | 脚質 | 人気 | 評価 | 理由 |
※【脚質】列には、「逃げ🔥」「先行📢」「差し」「追込」の印をつけよ。
※評価は（◎、○、▲、△、注、消）で厳選せよ。

### 📈 地方走破タイム・砂質トラックバイアス深層データ分析
1. 【地方走破理論・スピード指数分析】: 馬場状態からタイム・指数が優秀な上位3頭を箇条書きで。
2. 【地方小回り・ハナ争い完全看破】: 1角までにハナを叩く「逃げ🔥」馬の特定と展開予測。
3. 【移籍・外厩・叩き一変シグナル】: 激走気配がある下剋上穴馬の特定。
4. 【地方コース×血統マトリクス】: コースの砂質に最も合致する特注配合馬。

### 💰 三連複フォーメーション：厳選15点指示書
投資効率を最大化する【合計15点】のフォーメーションを強制生成せよ。

【買い目構築に関する絶対鉄則】
地方競馬は小回りかつ先行・逃げ馬が粘り込む確率が極めて高い。そのため、テーブル内で【逃げ🔥】または【先行📢】と判定した馬は、いかなる場合も必ず「3頭目（紐馬）」の対象馬番に最低1頭以上は強制的に組み込むロジックを展開せよ。

【表示に関する超重要指令】
Streamlitの仕様で改行が半角スペースに潰れるバグを回避するため、フォーメーション各行の末尾に、必ずHTMLの改行タグである「<br>」を直接付与して出力せよ。コードブロック（```）等で囲むのは一切禁止とする。

(フォーマット例)
◎ 軸馬: 〇番 (馬名)<br>
1頭目: 〇番<br>
2頭目: 〇番, 〇番, 〇番<br>
3頭目: 〇番, 〇番, 〇番, 〇番, 〇番, 〇番, 〇番<br>"""

                prompt = base_instruction + f"\n対象データ: {target_data}\n総監督バイアス: {bias}\n予算: {budget}円"

                with st.spinner(f"🚀 地方小回り展開・砂適性をマッピング中... ({m_name})"):
                    response = model.generate_content(prompt)
                    output_text = response.text
                    st.session_state["res"] = output_text
                    
                    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    with open(os.path.join(LOG_DIR, f"地方3連複15点_{now_str}.txt"), "w", encoding="utf-8") as log_f:
                        log_f.write(f"=== 予想生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n🧠 地方バイアス: {bias}\n\n" + output_text)
                    st.toast("💾 地方予想ログを保存しました！", icon="💾")
                    st.rerun()
        except Exception as e:
            st.error(f"解析エラー: {e}")

with col2:
    st.subheader("📊 投資指示書 ＆ 復習ルーム連動表示")
    if st.session_state["res"]:
        st.markdown(st.session_state["res"], unsafe_allow_html=True)
st.caption("Baru Stable AI Local Pro v24.8.9 - HTML LineBreak & FrontRunner-Optimized Edition")
