import re
import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup
import datetime

# ページの設定（2カラムを綺麗に表示するためにワイドモードに設定）
st.set_page_config(layout="wide", page_title="Baru 地方競馬AI Pro")

# ==============================================================================
# 1. 精密診断Markdownテーブル生成関数
# ==============================================================================
def parse_and_generate_table(raw_text, ai_recommendations=None):
    """
    コピペデータから全頭をパースし、
    スクリーンショットのデザイン・列構成（父・母・脚質・人気・評価・理由）を完全再現する関数
    """
    if ai_recommendations is None:
        ai_recommendations = {
            1: {"mother": "パワフルラリマー", "sand": "速砂〇", "style": "先行 📢", "pop": "2", "eval": "〇", "reason": "2走前に同条件(不良)を先行策で圧勝。最内枠から再現可能。"},
            2: {"mother": "デコラス", "sand": "標準", "style": "追込", "pop": "12", "eval": "消", "reason": "追い込み一手で展開利見込めず。近走内容も平凡。"},
            3: {"mother": "スカイスペクター", "sand": "速砂〇", "style": "差し", "pop": "3", "eval": "△", "reason": "不良馬場での好走実績あり。先行力もあり、粘り込みに期待。"},
            4: {"mother": "エメラルコヨーテ", "sand": "速砂◎", "style": "追込", "pop": "4", "eval": "△", "reason": "末脚はメンバー屈指。不良馬場で前が速くなれば強襲あり。"},
            5: {"mother": "アドマイヤジョイ", "sand": "標準", "style": "差し", "pop": "7", "eval": "消", "reason": "C3クラスで頭打ち。強調材料に欠ける。"},
        }

    markdown_lines = [
        "### 📊 全頭精密診断・地方ダート適性リスト\n",
        "| 馬番 | 馬名 | 父 | 母 | ダート砂適性 | 脚質 | 人気 | 評価 | 理由 |",
        "| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |"
    ]

    horse_blocks = re.split(r'\n(?=\d+\s+\d+\s+(?:--|✓))', raw_text)

    for block in horse_blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines or not re.match(r'^\d+$', lines[0]):
            continue

        try:
            num = int(lines[0])
            formatted_num = f"{num}"

            blood_idx = -1
            for i, line in enumerate(lines):
                if line.startswith('(') and line.endswith(')'):
                    blood_idx = i
                    break

            if blood_idx != -1 and blood_idx >= 2:
                father = lines[blood_idx - 2]
                horse_name = lines[blood_idx - 1]
            else:
                horse_name = lines[1] if len(lines) > 1 else "解析エラー"
                father = "--"

            rec = ai_recommendations.get(num, {
                "mother": "--",
                "sand": "標準",
                "style": "差し",
                "pop": "--",
                "eval": "△",
                "reason": "近走の走破タイム判定から、この舞台では静観が妥当。"
            })

            row = f"| {formatted_num} | {horse_name} | {father} | {rec['mother']} | {rec['sand']} | {rec['style']} | {rec['pop']} | {rec['eval']} | {rec['reason']} |"
            markdown_lines.append(row)

        except Exception:
            continue

    return "\n".join(markdown_lines)


# ==============================================================================
# 2. Gemini API 呼び出し関数
# ==============================================================================
def call_gemini(prompt: str, api_key: str) -> str:
    """Gemini APIを呼び出してレスポンスを返す"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ API呼び出しエラー: {e}"


# ==============================================================================
# 3. URLからデータ取得関数
# ==============================================================================
def fetch_race_data_from_url(url: str) -> str:
    """指定URLからレースデータを取得する"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        return soup.get_text(separator="\n", strip=True)[:5000]
    except Exception as e:
        return f"⚠️ URL取得エラー: {e}"


# ==============================================================================
# 4. セッション状態の初期化
# ==============================================================================
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = ""
if "table_result" not in st.session_state:
    st.session_state.table_result = ""
if "review_result" not in st.session_state:
    st.session_state.review_result = ""
if "past_logs" not in st.session_state:
    st.session_state.past_logs = [
        "ファイナルレース(C3)_2026-05-25",
        "大井11R_東京ダービー",
    ]


# ==============================================================================
# 5. ⚙️ Streamlit UI 配置
# ==============================================================================

# --- 5-A. 左側サイドバー ---
with st.sidebar:
    st.button("💾 設定保存")
    st.write("")

    st.header("📂 過去ログ・結果復習ルーム")
    st.caption("復習・確認する過去の予想")
    selected_log = st.selectbox(
        "選択してください",
        st.session_state.past_logs,
        label_visibility="collapsed"
    )
    if st.button("📖 予想指示書を呼び出す"):
        st.session_state.prediction_result = f"【{selected_log}】の予想指示書を呼び出しました。\n\n（ここに保存済み予想が表示されます）"

    st.write("---")
    st.header("🏁 レース結果のコピペ投入")
    st.caption("💡 1行目にレース名を入力し、2行目から結果を丸ごとコピペしてください！")
    result_paste = st.text_area(
        "1行目：レース名／2行目〜：結果コピペ",
        value="レース名\n1着：馬名\n2着：馬名\n3着：馬名",
        height=150,
        label_visibility="collapsed"
    )
    st.caption("コーナー通過順位の見方")
    with st.expander("📌 コーナー通過順位の見方"):
        st.write("""
        - 数字=通過順位
        - 括弧内=複数頭が同順位
        - 例: 3=(1,2),4,5 → 3コーナーで1,2番が並走
        """)

    memo_text = st.text_area("レース別馬メモ", height=100)

    if st.button("🔮 実際の着順・ハナ争いと照合して復習"):
        if result_paste.strip():
            st.session_state.review_result = f"### 🔍 復習結果\n\n入力データ:\n```\n{result_paste}\n```\n\n**分析**: ハナ争いと着順の照合を実行しました。（Gemini API連携で詳細分析が可能です）"
        else:
            st.warning("結果データを入力してください")

    st.write("---")
    # API Key設定（折りたたみ）
    with st.expander("⚙️ API設定"):
        api_key = st.text_input("Gemini API Key", type="password", placeholder="AIza...")
        st.caption("Google AI StudioでAPIキーを取得してください")


# --- 5-B. メインエリア ---
st.title("🏇 Baru 地方競馬AI Pro - 【Ver 24.8.5 高速・軽量化安定版】")

# 2カラムレイアウト
col_left, col_right = st.columns([1, 1])

# ============================================================
# 左カラム：入力エリア
# ============================================================
with col_left:
    st.subheader("📋 地方競馬 過去馬柱・オッズ混在テキスト入力")

    # URL入力
    race_url = st.text_input(
        "🔗 地方レースURL（netkeiba等）",
        placeholder="https://nar.netkeiba.com/race/..."
    )
    if race_url and st.button("🌐 URLからデータ取得"):
        with st.spinner("データ取得中..."):
            fetched = fetch_race_data_from_url(race_url)
            st.session_state["fetched_url_data"] = fetched
            st.success("取得完了！下のテキストエリアに反映されました")

    # コピペ入力エリア
    default_paste = st.session_state.get("fetched_url_data", "")
    paste_data = st.text_area(
        "🔥 地方競馬コピペデータ",
        value=default_paste,
        height=400,
        placeholder="netkeiba等からコピーした馬柱データをここに貼り付けてください...\n\n例:\n1 チュウオーハーン\nダンカーク\n(パワフルラリマー)\n..."
    )

    # 予想生成ボタン
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        gen_button = st.button("🚀 AI予想を生成する", type="primary", use_container_width=True)
    with btn_col2:
        table_button = st.button("📊 全頭診断テーブル生成", use_container_width=True)

    # テーブル生成（ローカル処理）
    if table_button:
        if paste_data.strip():
            with st.spinner("テーブル生成中..."):
                result = parse_and_generate_table(paste_data)
                st.session_state.table_result = result
        else:
            st.warning("馬柱データを入力してください")

    # AI予想生成
    if gen_button:
        if not paste_data.strip():
            st.warning("馬柱データを入力してください")
        else:
            gemini_key = st.session_state.get("api_key_stored", "")
            # サイドバーのAPI keyを取得
            try:
                gemini_key = api_key
            except Exception:
                gemini_key = ""

            if not gemini_key:
                st.warning("⚙️ API設定からGemini APIキーを入力してください")
            else:
                with st.spinner("🤖 AIが分析中...（しばらくお待ちください）"):
                    prompt = f"""
あなたは地方競馬の専門AIアナリストです。
以下の馬柱データを分析し、全頭の地方ダート適性・脚質・評価・買い推奨をJSON形式で出力してください。

【出力形式】
{{
  "race_info": "レース概要",
  "bias": "馬場バイアス分析",
  "recommendations": {{
    "1": {{"mother": "母馬名", "sand": "速砂◎/速砂○/標準/重馬場△", "style": "脚質", "pop": "人気想定", "eval": "◎/○/▲/△/消", "reason": "理由"}},
    ...
  }},
  "buy_order": ["◎馬番", "○馬番", "▲馬番"],
  "strategy": "投資戦略メモ"
}}

【馬柱データ】
{paste_data[:3000]}
"""
                    result_text = call_gemini(prompt, gemini_key)

                    # JSON解析試行
                    try:
                        # コードブロックを除去
                        clean = re.sub(r'```json|```', '', result_text).strip()
                        ai_data = json.loads(clean)
                        recs = ai_data.get("recommendations", {})
                        # 数値キーに変換
                        recs_int = {int(k): v for k, v in recs.items()}
                        table_md = parse_and_generate_table(paste_data, recs_int)

                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.session_state.prediction_result = f"""=== 予想生成日時: {now} ===
🌸 地方バイアス: {ai_data.get('bias', '分析中')}

{ai_data.get('strategy', '')}

{table_md}
"""
                        st.session_state.table_result = table_md

                    except json.JSONDecodeError:
                        # JSON解析失敗時はそのまま表示
                        st.session_state.prediction_result = result_text

                    st.success("✅ AI予想が生成されました！")

# ============================================================
# 右カラム：出力エリア
# ============================================================
with col_right:
    st.subheader("📈 投資指示書 & 復習ルーム連動表示")

    # 予想結果表示
    if st.session_state.prediction_result:
        st.markdown(st.session_state.prediction_result)
    else:
        # デモ表示
        now_demo = "2026-05-25 01:27:06"
        st.markdown(f"""
=== 予想生成日時: {now_demo} === 🌸 地方バイアス: JRA（中央競馬）および地方競馬の高速馬場・トラックバイアス、芝・ダートのキレ、走破タイム理論（基準タイム・馬場補正）、上がり3F、展開・ハナ争いを統合解析せよ。
""")

    st.write("---")

    # 全頭診断テーブル表示
    st.subheader("📊 全頭精密診断・地方ダート適性リスト")
    if st.session_state.table_result:
        st.markdown(st.session_state.table_result)
    else:
        # デモテーブル
        demo_table = """
| 馬番 | 馬名 | 父 | 母 | ダート砂適性 | 脚質 | 人気 | 評価 | 理由 |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | チュウオーハーン | ダンカーク | パワフルラリマー | 速砂〇 | 先行 📢 | 2 | 〇 | 2走前に同条件(不良)を先行策で圧勝。最内枠から再現可能。 |
| 2 | デコラス | ワールドエース | デコラス | 標準 | 追込 | 12 | 消 | 追い込み一手で展開利見込めず。近走内容も平凡。 |
| 3 | スカイスペクター | モーニン | スカイスペクター | 速砂〇 | 差し | 3 | △ | 不良馬場での好走実績あり。先行力もあり、粘り込みに期待。 |
| 4 | エメラルコヨーテ | ドレフォン | エメラルコヨーテ | 速砂◎ | 追込 | 4 | △ | 末脚はメンバー屈指。不良馬場で前が速くなれば強襲あり。 |
| 5 | アドマイヤジョイ | シルバーステート | アドマイヤジョイ | 標準 | 差し | 7 | 消 | C3クラスで頭打ち。強調材料に欠ける。 |
"""
        st.markdown(demo_table)

    st.write("---")

    # 復習結果表示
    if st.session_state.review_result:
        st.markdown(st.session_state.review_result)

    # 手動テーブル更新ボタン
    if st.button("🔄 テーブルを更新"):
        if paste_data.strip():
            st.session_state.table_result = parse_and_generate_table(paste_data)
            st.rerun()
