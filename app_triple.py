import streamlit as st
import google.generativeai as genai
import json
import os
import datetime
import re

# --- 設定保存・ログ管理 ---
CONFIG_FILE = "baru_triple_config.json"
LOG_DIR = "racing_logs_triple"
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
        "b": "トリプル馬単対象地方レース（主に後半3R）のトラックバイアス, 砂質, 1角ポジション争い, 絶対に崩れない軸馬の選定, および逆転候補の展開利・ハナ争いを統合解析せよ。"
    }

def clean_filename(name):
    if not name:
        return ""
    clean = re.sub(r'[\\/*?:"<>| \t]', '_', name.strip())
    return clean[:50]

cfg = load_cfg()
st.set_page_config(page_title="Baru トリプル馬単専用機 v24.8.5", layout="wide", initial_sidebar_state="expanded")
st.title("🏇 Baru トリプル馬単専用機 - 【Ver 24.8.5 高速・軽量化安定版】")

# --- サイドバー ---
with st.sidebar:
    st.header("⚙️ 総監督ルーム（司令部）[Triple]")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（トリプル馬単補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("1レース予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("トリプル馬単専用設定を保存しました。")

    st.divider()

    # 過去ログ
    st.header("📂 過去ログ復習 [Triple]")
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)

    if log_files:
        selected_log = st.selectbox("復習・確認する対象レース", log_files)

        if st.button("📖 予想指示書を呼び出す"):
            with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                st.session_state["res"] = f.read()
            st.success(f"{selected_log} を読み込みました！")

        st.divider()

        # 結果照合
        st.subheader("🏁 レース結果の照合")
        st.caption("💡 1行目にレース名、2行目から結果をコピペ")
        result_copypaste = st.text_area("1行目：レース名 / 2行目〜：結果コピペ", height=200, key="result_input")

        if st.button("🚨 馬単の着順・ハナ争いと照合して復習"):
            if not api_key or not result_copypaste.strip():
                st.error("APIキーと結果データが必要です")
            elif "res" not in st.session_state or not st.session_state["res"]:
                st.error("先に予想指示書を呼び出してください")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash-lite")

                    lines = result_copypaste.splitlines()
                    raw_title = lines[0].strip() if lines else "対象レース結果"
                    cleaned_title = clean_filename(raw_title)

                    with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                        past_prediction = f.read()

                    review_prompt = f"""あなたは総監督Baruの右腕競馬AIだ。提示されたトリプル馬単対象レースの予想指示書と、実際のレース結果を徹底的に突き合わせ、簡潔に箇条書きで猛省レポートを作成せよ。

【タイトル】最上部に見出し「### 🏁 {raw_title} 戦果照合」を出力せよ。

【馬単解析掟】
1. 1着・2着の入線パターンとコーナー通過順から、想定外のズレを炙り出せ。
2. 馬単高配当を演出した人気薄の激走理由（地方砂質・トラックバイアス）の読みのズレを猛省せよ。
3. 次回トリプル馬単を仕留めるため、バイアス設定をどう微調整すべきか簡潔に導け。

【出力フォーマット】
### 🏁 {raw_title} 戦果照合
馬単払戻金および戦果の整理

### 🧠 1着2着・ハナ争いのズレ解剖
馬単の着順に直結した地方小回り展開・バイアスのズレ分析

### 🛠️ 次回制覇へのAIロジック微調整案
地方ダート補正や馬場バイアスの具体的アドバイス

---
【当時の予想指示書】:
{past_prediction}

【実際のレース結果コピペ】:
{result_copypaste}"""

                    with st.spinner("1・2着展開のズレから猛省・復習中..."):
                        response = model.generate_content(review_prompt, generation_config={"max_output_tokens": 2000})
                        review_result = "\n\n" + "="*20 + f" 🏁 {raw_title} 復習ログ " + "="*20 + "\n" + response.text

                        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_filename = f"{cleaned_title}_{now_str}.txt"
                        new_path = os.path.join(LOG_DIR, new_filename)
                        full_content = past_prediction + review_result

                        with open(new_path, "w", encoding="utf-8") as nf:
                            nf.write(full_content)

                        old_path = os.path.join(LOG_DIR, selected_log)
                        if old_path != new_path and os.path.exists(old_path):
                            os.remove(old_path)

                        st.session_state["res"] = full_content
                        st.success(f"💾 「{new_filename}」として保存しました！")
                        st.rerun()
                except Exception as e:
                    st.error(f"復習解析エラー: {e}")
    else:
        st.info("まだ保存された予想ログはありません。")

# --- メインエリア ---

# セッション初期化
if "res" not in st.session_state:
    st.session_state["res"] = ""
for i in range(1, 4):
    if f"race{i}" not in st.session_state:
        st.session_state[f"race{i}"] = ""

# 3レース個別入力タブ
st.subheader("📋 トリプル馬単対象 3レース個別データ入力")

tabs = st.tabs(["🏇 第1レース", "🏇 第2レース", "🏇 第3レース"])
race_labels = ["第1レース", "第2レース", "第3レース"]

for i, tab in enumerate(tabs, start=1):
    with tab:
        st.session_state[f"race{i}"] = st.text_area(
            f"✍️ {race_labels[i-1]}の馬柱・オッズ",
            value=st.session_state[f"race{i}"],
            height=350,
            key=f"input_race{i}",
            placeholder=f"{race_labels[i-1]}の出馬表、オッズ、馬場状態などをコピペしてください",
        )

# 入力状況
st.divider()
filled = [i for i in range(1, 4) if st.session_state.get(f"race{i}", "").strip()]
empty  = [i for i in range(1, 4) if not st.session_state.get(f"race{i}", "").strip()]

col_status, col_btn = st.columns([2, 1])
with col_status:
    if filled:
        st.success(f"✅ 入力済み: 第{', 第'.join(map(str, filled))}レース")
    if empty:
        st.warning(f"⚠️ 未入力: 第{', 第'.join(map(str, empty))}レース")

with col_btn:
    run_btn = st.button("🚀 構造解剖＆勝負指示書生成", type="primary", use_container_width=True)

# --- AI解析 ---
if run_btn:
    if not api_key:
        st.error("Gemini APIキーを入力してください")
    elif not filled:
        st.error("少なくとも1レース分のデータを入力してください")
    else:
        # 3レースデータ結合
        combined = ""
        for i in range(1, 4):
            data = st.session_state.get(f"race{i}", "").strip()
            if data:
                combined += f"\n\n【{race_labels[i-1]}】\n{data}"
            else:
                combined += f"\n\n【{race_labels[i-1]}】\n（データなし）"

        base_instruction = """あなたはトリプル馬単を完全ハックするプロ競馬AIであり、総監督Baruの絶対的右腕だ。
トリプル馬単とは【3レース連続で馬単（1着・2着の順番通り）を当てる】馬券である。
入力された3レース分のデータから人気・枠番・馬番・馬名・オッズ・通過順を完全に解剖し、地方ダート戦で馬単の「1着・2着」を絶対に逃さない鋭い勝負指示書を最速で作成せよ。

【絶対ルール】
1. 前置き・挨拶・まとめの雑談は一切禁止。即座に出力フォーマットを開始せよ。
2. 地方競馬の馬単で1着に突き抜ける能力（スピード・ハナ奪取率）と、2着に粘り込む地方馬場バイアス適性を最重要視せよ。
3. 理由や分析は要点のみを鋭い箇条書きでコンパクトに記述し、冗長な表現を徹底的に排除せよ。
4. 各レース（第1・第2・第3）それぞれについて以下のフォーマットで出力せよ。

【各レースの出力フォーマット（第1・第2・第3レース共通）】

### 🏇 [レース名] 解剖

#### 📊 全頭精密診断・馬単適性リスト
| 馬番 | 馬名 | 脚質 | 人気 | 評価 | 1着2着への決定打 |
（評価は ◎○▲△注消 で厳選。脚質は 逃げ🔥/先行📢/差し/追込）

#### 📈 連対圏（1,2着）深層分析
1. 【1着候補】: 1着に突き抜ける上位3頭
2. 【2着粘り込み】: 1角ポジションから2着に粘る逃げ先行馬
3. 【穴馬】: 人気薄ながら2着以内に突っ込むポテンシャルがある馬

#### 💰 馬単フォーメーション（計12点）
1着：◎○の2頭
2着：◎○▲△注から厳選7頭（1着指定馬含む）
計算式：2頭 × 6頭 ＝ 12点

**🏆 馬単フォーメーション指示（計12点）**
1着：〇番, 〇番
2着：〇番, 〇番, 〇番, 〇番, 〇番, 〇番, 〇番

---
"""

        prompt = base_instruction + f"\n対象データ（3レース分）:\n{combined}\n\n総監督バイアス: {bias}\n1レース予算: {budget}円"

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash-lite")

            with st.spinner("🚀 連対圏（1,2着）をマッピング中..."):
                response = model.generate_content(prompt, generation_config={"max_output_tokens": 4000})
                output_text = response.text
                st.session_state["res"] = output_text

                now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(os.path.join(LOG_DIR, f"トリプル馬単12点_{now_str}.txt"), "w", encoding="utf-8") as log_f:
                    log_f.write(f"=== 予想生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n🧠 トリプルバイアス: {bias}\n\n" + output_text)
                st.toast("💾 予想ログを保存しました！", icon="💾")

        except Exception as e:
            st.error(f"解析エラー: {e}")

# --- 結果表示 ---
if st.session_state["res"]:
    st.divider()
    st.subheader("📊 予想指示書 ＆ 復習ルーム連動表示")
    st.markdown(st.session_state["res"])

st.caption("🏇 Baru トリプル馬単専用機 - 【Ver 24.8.5 高速・軽量化安定版】")
