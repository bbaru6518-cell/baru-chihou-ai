import streamlit as st

# 画面の基本設定
st.set_page_config(page_title="Baru競馬AI Pro", page_icon="🎯", layout="wide")

st.title("🎯 Baru競馬AI Pro 〜研究者レベル最終進化版〜")
st.write("インサイダーオッズ歪み・穴騎手・秋元フィルター完全統合システム")
st.markdown("---")

# ----------------------------------------------------
# 1. データの入力エリア（画面側で自由に変更可能）
# ----------------------------------------------------
st.sidebar.header("🛠 レース条件設定")
venue = st.sidebar.selectbox("競馬場", ["船橋", "大井", "川崎", "浦和"])
race_num = st.sidebar.number_input("レース番号", min_value=1, max_value=12, value=3)
race_class = st.sidebar.selectbox("クラス", ["C3", "C2", "C1", "B3", "A2", "重賞"])

st.sidebar.markdown("---")
st.sidebar.write("💡 実際のオッズや騎手を画面でシミュレーションできます")

# セッション状態に出馬表データを格納（実際の船橋3Rベース＋秋元騎手）
if 'entries' not in st.session_state:
    st.session_state.entries = [
        {'maruban': 11, 'ninki': 1,  'tan_odds': 1.6,  'fuku_odds_min': 1.1, 'time_score': 95.0, 'jockey': '古岡勇樹', 'kyashitsu': '先行'},
        {'maruban': 4,  'ninki': 2,  'tan_odds': 4.5,  'fuku_odds_min': 1.5, 'time_score': 88.0, 'jockey': '山口達弥', 'kyashitsu': '逃げ'},
        {'maruban': 5,  'ninki': 3,  'tan_odds': 8.9,  'fuku_odds_min': 2.1, 'time_score': 91.5, 'jockey': '笠野雄大', 'kyashitsu': '先行'},
        {'maruban': 10, 'ninki': 4,  'tan_odds': 14.1, 'fuku_odds_min': 3.0, 'time_score': 82.0, 'jockey': '本橋孝太', 'kyashitsu': '差し'},
        {'maruban': 2,  'ninki': 5,  'tan_odds': 15.8, 'fuku_odds_min': 3.2, 'time_score': 79.0, 'jockey': '福原杏',   'kyashitsu': '差し'},
        {'maruban': 9,  'ninki': 6,  'tan_odds': 17.0, 'fuku_odds_min': 3.5, 'time_score': 85.0, 'jockey': '吉留孝司', 'kyashitsu': '差し'},
        {'maruban': 6,  'ninki': 7,  'tan_odds': 22.2, 'fuku_odds_min': 4.0, 'time_score': 76.0, 'jockey': '濱田達也', 'kyashitsu': '先行'},
        {'maruban': 1,  'ninki': 8,  'tan_odds': 28.3, 'fuku_odds_min': 4.5, 'time_score': 74.0, 'jockey': '藤江渉',   'kyashitsu': '追い込み'},
        {'maruban': 8,  'ninki': 9,  'tan_odds': 59.1, 'fuku_odds_min': 6.0, 'time_score': 71.0, 'jockey': '加藤雄真', 'kyashitsu': '逃げ'},
        {'maruban': 7,  'ninki': 10, 'tan_odds': 72.8, 'fuku_odds_min': 2.5, 'time_score': 80.0, 'jockey': '山林堂信', 'kyashitsu': '差し'},
        {'maruban': 3,  'ninki': 11, 'tan_odds': 74.0, 'fuku_odds_min': 7.2, 'time_score': 65.0, 'jockey': '秋元耕成', 'kyashitsu': '差し'},
    ]

entries = st.session_state.entries

# ----------------------------------------------------
# 2. AIコア解析ロジック
# ----------------------------------------------------
# 2-1. 波乱度予測
front_runners = len([h for h in entries if h['kyashitsu'] in ['逃げ', '先行']])
odds_1st = [h['tan_odds'] for h in entries if h['ninki'] == 1][0]
odds_3rd = [h['tan_odds'] for h in entries if h['ninki'] == 3][0]
odds_gap = odds_3rd - odds_1st

turbulence_score = 0
if race_class == 'C3': turbulence_score += 25
if front_runners >= 5:  turbulence_score += 40
elif front_runners <= 2: turbulence_score -= 20
if odds_gap < 5.0:      turbulence_score += 20

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 レース構造解析結果")
    if turbulence_score >= 60:
        st.error(f"判定: 🔥 大荒れ警戒（スコア: {turbulence_score}点）")
        st.info("💡 戦略: 3列目に大穴・歪み馬を全流しして万馬券をハメにいきます。")
    elif 20 <= turbulence_score < 60:
        st.warning(f"判定: ⚖️ 中穴傾向（スコア: {turbulence_score}点）")
        st.info("💡 戦略: 2列目の4〜8番人気を厚めに。バランス型の布陣。")
    else:
        st.success(f"判定: 🟢 ガチガチ本命（スコア: {turbulence_score}点）")
        st.info("💡 戦略: 1番人気を固定し、点数を極限まで絞るか見送り。")

# 2-2. 各列の選定ロジック
sorted_horses = sorted(entries, key=lambda x: x['ninki'])
total_horses = len(sorted_horses)

# 【1列目】
zone1_pool = sorted_horses[:4]
horse_1st = [h for h in zone1_pool if h['ninki'] == 1][0]
remaining_zone1 = [h for h in zone1_pool if h['ninki'] != 1]
best_time_horse = max(remaining_zone1, key=lambda x: x['time_score'])

first_row = [horse_1st['maruban']]
if best_time_horse['jockey'] != '秋元耕成':
    first_row.append(best_time_horse['maruban'])
else:
    runner_up = sorted(remaining_zone1, key=lambda x: x['time_score'], reverse=True)[1]
    first_row.append(runner_up['maruban'])
first_row.sort()

# 【2列目】
zone2_pool = sorted_horses[3:8]
second_row = [h['maruban'] for h in zone2_pool if h['jockey'] != '秋元耕成']
second_row.sort()

# 【3列目】
zone3_pool = sorted_horses[max(0, total_horses-5):]
third_row = []
ana_jockey_master = ['山林堂信', '吉留孝司', '古岡勇樹', '加藤雄真', '藤江渉', '笠野雄大']

with col2:
    st.subheader("🔎 大穴ゾーン個別インサイダー解析")
    for h in zone3_pool:
        if h['jockey'] == '秋元耕成':
            st.text(f"❌ 馬番:{h['maruban']:02d} ({h['jockey']}) -> 秋元フィルターで強制排除")
            continue
        
        is_selected = False
        reasons = []
        if h['tan_odds'] >= 25.0 and h['fuku_odds_min'] <= 3.5:
            is_selected = True
            reasons.append("複勝大口歪み")
        if h['jockey'] in ana_jockey_master:
            is_selected = True
            reasons.append(f"穴騎手({h['jockey']})")
        if turbulence_score >= 60:
            is_selected = True
            reasons.append("大荒れ救済")
            
        if is_selected:
            third_row.append(h['maruban'])
            st.code(f"⚠️ 馬番:{h['maruban']:02d} ({h['jockey']}) -> 採用 [{', '.join(reasons)}]")
        else:
            st.text(f"💤 馬番:{h['maruban']:02d} ({h['jockey']}) -> 武器不足で見送り")
            
    third_row.sort()

# ----------------------------------------------------
# 3. フォーメーション組み合わせ生成＆グループ表示（UI最適化）
# ----------------------------------------------------
st.markdown("---")
st.subheader("🎯 【最終出力】Baru式・最適化3連複フォーメーション")

col_f1, col_f2, col_f3 = st.columns(3)
col_f1.metric("1列目（軸）", ", ".join(map(str, first_row)))
col_f2.metric("2列目（相手）", ", ".join(map(str, second_row)))
col_f3.metric("3列目（穴紐）", ", ".join(map(str, third_row)))

final_tickets = set()
for r1 in first_row:
    for r2 in second_row:
        for r3 in third_row:
            if r1 != r2 and r1 != r3 and r2 != r3:
                ticket = tuple(sorted([r1, r2, r3]))
                final_tickets.add(ticket)
                
sorted_tickets = sorted(list(final_tickets))

st.success(f"🔥 重複目を自動排除した【合計購入点数: {len(sorted_tickets)} 点】")

if sorted_tickets:
    # 軸馬ごとにブロックを分けてきれいに並べる
    for jiku in first_row:
        st.markdown(f"### 🐴 【{jiku}番 軸】の組み合わせ")
        
        # この軸馬が含まれる馬券のみを抽出し、昇順で確定
        jiku_tickets = [t for t in sorted_tickets if jiku in t]
        
        # 1行に4点ずつ、すっきり縦一列の流れを作る
        cols = st.columns(4)
        for idx, t in enumerate(jiku_tickets):
            with cols[idx % 4]:
                st.code(f"🎟 {t[0]:02d} - {t[1]:02d} - {t[2]:02d}", language="text")
else:
    st.warning("買い目が生成されませんでした。条件を緩和してください。")
