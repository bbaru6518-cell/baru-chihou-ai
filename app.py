import streamlit as st
import google.generativeai as genai
import os
import datetime

# --- 設定 ---
LOG_DIR = "racing_logs_chihou"
os.makedirs(LOG_DIR, exist_ok=True)
st.set_page_config(page_title="Baru 地方競馬AI Pro", layout="wide")

# ==============================================================================
# 地方競馬特化：定数定義
# ==============================================================================

# 地方競馬場リスト
CHIHOU_TRACKS = [
    "大井", "川崎", "船橋", "浦和",  # 南関東
    "金沢", "笠松", "名古屋",          # 中部
    "園田", "姫路",                    # 近畿
    "高知", "佐賀",                    # 西日本
    "盛岡", "水沢",                    # 北日本
    "帯広（ばんえい）",
]

# 地方競馬場ごとのトラックバイアス特性
TRACK_BIAS = {
    "大井": "直線長め・外差し届く。砂が重めで前が止まりやすい。",
    "川崎": "小回り・内前有利。逃げ・先行馬天国。砂が軽く速い。",
    "船橋": "平坦・砂重め。差し馬も届く。外枠不利の傾向。",
    "浦和": "超小回り・極端な内前有利。逃げ残り多発。",
    "金沢": "砂が深め・前残り。差し届かないケース多い。",
    "笠松": "小回り・前有利。砂軽め・速い時計。",
    "名古屋": "平坦・砂深め。逃げ・先行有利。",
    "園田": "小回り・砂軽め。内前有利が顕著。",
    "高知": "砂深め・前残り。時計かかる。",
    "佐賀": "平坦・砂が重め。差しも届く。",
    "盛岡": "芝コースあり・ダートは差し届く。",
    "水沢": "砂重め・前残り傾向。",
    "帯広（ばんえい）": "ばんえい競馬専用。体重・パワー重視。",
}

# ==============================================================================
# 地方競馬特化プロンプト生成関数
# ==============================================================================
def build_chihou_prompt(manual_data: str, track: str, condition: str, distance: str, grade: str) -> str:
    bias_info = TRACK_BIAS.get(track, "トラックバイアス情報なし")

    return f"""
【地方競馬場情報】
- 競馬場: {track}
- 馬場状態: {condition}
- 距離: {distance}
- クラス: {grade}
- トラックバイアス特性: {bias_info}

【今回の馬柱・オッズデータ（netkeiba/地方競馬ナビ等）】
{manual_data}

===========================================================
【⚙️ 地方競馬特化：総監督絶対厳守ロジック】
===========================================================

■ RULE 1: 地方ダート砂適性スクリーニング
地方競馬のダートは中央競馬と砂質・深さが異なる。以下を必ず判定せよ：
- 「速砂◎」: 川崎・笠松など軽砂コースで連対実績あり → 最大加算
- 「速砂〇」: 軽砂コースでの好走経験あり
- 「標準」: 中央ダートのみの実績
- 「重馬場△」: 良馬場専門、道悪で極端に落とす傾向
投入データに砂質適性情報がある場合は必ず参照・反映せよ。

■ RULE 2: 地方競馬場バイアス適用
{track}の特性（{bias_info}）を踏まえ、脚質・枠番の有利不利を必ずスコアに反映せよ。
特に小回りコース（川崎・浦和・園田等）では逃げ・先行馬のボーナスを大幅加算すること。

■ RULE 3: 地方馬 vs 中央転入馬の判定
- 中央から転入初戦の馬：地方ダートの砂適応に1〜2走かかるケースが多い。過大評価を禁止。
- 地方生え抜きで同コース実績が豊富な馬：コース適性ボーナスを加算せよ。
- ただし、中央でも地方ダートと類似条件（砂深め・時計かかる）で好走実績がある場合は例外とする。

■ RULE 4: ナイター・開催時間帯バイアス
地方競馬はナイター開催が多く、夜間の気温低下により砂が締まって速い時計が出やすくなる。
ナイター開催の場合、先行馬の評価をさらに1段階引き上げよ。

■ RULE 5: 死んだふり下剋上馬（地方版・上がり最速爆弾）の検知
近走成績が崩れていても、以下の激走ファクターを満たす伏兵馬は爆弾馬として検知せよ：
- 条件A: 過去2〜3走以内に上がり3FがメンバーTOP2の末脚実績がある馬
- 条件B: 中央・別地区からの転入で、このコース・距離への適性が高い馬
- 条件C: クラス降級初戦（明らかに能力上位でも凡走が続いた馬が格下げ初戦）
上記該当馬は「激走警戒馬（注）」として紐3列目に必ず強制配置せよ。

■ RULE 6: データ上位馬スクリーニング
投入データ内に「データ上位馬」「連対率上位」「このコースが得意な馬」等のセクションがある場合、
そこに含まれる馬を軸馬・相手筆頭（◎〇▲）の最有力候補として評価パラメータを大きく加算せよ。

■ RULE 7: 地方競馬クラス体系対応
地方競馬のクラス（C3→C2→C1→B→A→重賞）を正しく把握し、
クラス昇級初戦・降級初戦の馬は適切に評価を補正せよ。

===========================================================
【出力フォーマット（必須）】
===========================================================

### 🏟️ {track} / {distance} / {condition} / {grade} 地方競馬統合解析

**📍 コースバイアス診断**: （{track}の今日の特性・有利な脚質・枠番傾向を1〜2行で）

---

### 📊 全頭精密診断・地方ダート適性リスト
| 馬番 | 馬名 | 父 | ダート砂適性 | 脚質 | 人気 | 評価 | 診断コメント（中央転入/地方生え抜き/下剋上爆弾の場合は明記） |
| --- | --- | --- | --- | --- | --- | --- | --- |

---

### 💰 総監督への投資指示書

**◎ 軸馬（本命）**: 馬番・馬名 - 理由
**○ 対抗**: 馬番・馬名 - 理由
**▲ 単穴**: 馬番・馬名 - 理由
**△ 紐**: 馬番・馬名
**注（爆弾）**: 馬番・馬名 - 激走ファクター

**【推奨買い目】**
- 3連複フォーメーション: ◎ × ○▲ × ○▲△注
- 3連単: ◎→○▲→○▲△注
- ワイド保険: ◎-○、◎-▲

**【総評・展開予想】**
（ハナ争い・ペース・展開のシナリオを2〜3行で）
"""


def build_review_prompt(prediction: str, result_input: str) -> str:
    race_name = result_input.splitlines()[0] if result_input.splitlines() else "対象レース"
    return f"""
【総監督からの命令：地方競馬レース結果の答え合わせと徹底反省】

あなたが出力した【予想指示書】と、実際の【レース結果】を照合し、以下の基準で猛反省を行え。

1. 軸馬（◎〇▲）の成否 - 馬券圏内（3着以内）にきたか？
2. 死んだふり下剋上馬（注）の生存確認 - 激走/凡走の理由を地方ダート特性から推測せよ
3. 地方コースバイアスの答え合わせ - 想定した前残り/差し展開と実際は一致したか？
4. 中央転入馬の適応状況 - 砂適性の見立ては正しかったか？

【提出された現在の予想指示書】
{prediction}

【実際のレース結果（コピペデータ）】
{result_input}

【出力フォーマット】
### 🏁 {race_name} - 地方競馬統合反省レポート
- **総合評価**: （大的中 / 軸合致も紐抜け / 展開不一致による大敗 など）

#### 📊 着順答え合わせ
| 印 | 馬名 | 事前評価 | 実際の着順 | 上がり3F（結果） | 反省・要因分析 |
| --- | --- | --- | --- | --- | --- |

#### 🏟️ 地方コースバイアス振り返り
- 想定と実際の差：（前残り/差し決着の予想精度）
- 砂適性判定の精度：

#### 🧠 次回に向けたロジック修正点（総監督への進言）
- （地方ダート特有の教訓を箇条書き。中央転入馬の扱い方、ナイターバイアスの精度等）
"""


# ==============================================================================
# セッション初期化
# ==============================================================================
if "res" not in st.session_state:
    st.session_state["res"] = ""

# ==============================================================================
# サイドバー
# ==============================================================================
with st.sidebar:
    st.header("⚙️ 総監督司令部")
    api_key = st.text_input("Gemini API KEY", type="password")

    st.subheader("🏟️ レース条件設定")
    selected_track = st.selectbox("競馬場", CHIHOU_TRACKS)
    selected_condition = st.selectbox("馬場状態", ["良", "稍重", "重", "不良"])
    selected_distance = st.text_input("距離", placeholder="例: 1400m")
    selected_grade = st.selectbox("クラス", ["C3", "C2", "C1", "B", "A", "重賞", "その他"])

    st.divider()

    st.subheader("🎯 統合解析基準（常時適用）")
    st.info("""
    以下を全頭診断に統合：
    - 地方ダート砂適性（軽砂/重砂）
    - コースバイアス（小回り/前残り等）
    - 中央転入馬 vs 地方生え抜き
    - ナイター時間帯補正
    - 走破タイム・上がり3F
    - ハナ争い・展開シナリオ
    """)

    st.divider()

    # 過去ログ
    st.header("📂 過去ログ・結果復習ルーム")
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)
    if log_files:
        selected_log = st.selectbox("復習・確認する過去の予想", log_files)
        if st.button("📖 予想指示書を呼び出す"):
            with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                st.session_state["res"] = f.read()
            st.rerun()
    else:
        st.caption("まだログがありません")

    st.divider()

    # レース結果コピペ
    st.header("🏁 レース結果のコピペ投入")
    st.caption("💡 1行目にレース名を入力し、2行目から結果を丸ごとコピペしてください！")
    race_result_input = st.text_area("1行目：レース名 / 2行目〜：結果コピペ", height=200)

    if st.button("🚨 実際の着順・ハナ争いと照合して復習"):
        if not api_key:
            st.error("APIキーを入力してください")
        elif not race_result_input:
            st.error("結果データをコピペしてください")
        elif not st.session_state["res"]:
            st.error("まず予想を実行するか、過去ログを呼び出してください")
        else:
            try:
                with st.spinner("実際のレース結果と照合中..."):
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    prompt = build_review_prompt(st.session_state["res"], race_result_input)
                    response = model.generate_content(prompt)
                    st.session_state["res"] = response.text
                st.rerun()
            except Exception as e:
                st.error(f"反省解析エラー: {e}")

    st.divider()

# ==============================================================================
# メインエリア
# ==============================================================================
st.title("🏇 Baru 地方競馬AI Pro - 統合解析司令部")
st.caption("💡 netkeiba・地方競馬ナビ等の馬柱・オッズ・データ分析画面を丸ごとコピペしてください。")

manual_data = st.text_area(
    "✍️ 馬柱・オッズデータ入力（データ分析傾向・過去走も含む）",
    height=350,
    placeholder="ここにネット競馬等からコピーしたテキストを貼り付けてください...\n\n含めると精度UP:\n- 馬柱（過去走・タイム・上がり3F）\n- オッズ\n- データ分析（コース・馬場・間隔別成績）\n- 調教タイム（あれば）"
)

if st.button("🚀 地方競馬統合解析実行", type="primary"):
    if not api_key:
        st.error("APIキーを入力してください")
    elif not manual_data.strip():
        st.error("馬柱データを入力してください")
    else:
        try:
            with st.spinner(f"🏟️ {selected_track} / {selected_distance} / {selected_condition} を統合解析中..."):
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                prompt = build_chihou_prompt(
                    manual_data,
                    selected_track,
                    selected_condition,
                    selected_distance,
                    selected_grade
                )
                response = model.generate_content(prompt)
                st.session_state["res"] = response.text

                # ログ自動保存
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                fname = f"{selected_track}_{selected_distance}_{selected_grade}_{now}.txt"
                header = f"=== 予想生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n"
                header += f"競馬場: {selected_track} / {selected_distance} / {selected_condition} / {selected_grade}\n\n"
                with open(os.path.join(LOG_DIR, fname), "w", encoding="utf-8") as f:
                    f.write(header + response.text)

            st.rerun()
        except Exception as e:
            st.error(f"解析エラー: {e}")

# 結果表示
if st.session_state["res"]:
    st.markdown(st.session_state["res"])
