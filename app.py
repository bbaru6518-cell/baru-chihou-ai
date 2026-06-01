import streamlit as st
import re

# 1. 画面の基本設定
st.set_page_config(page_title="Baru競馬AI Pro", page_icon="🎯", layout="wide")

st.title("🎯 Baru競馬AI Pro 〜研究者レベル最終進化版〜")
st.write("netkeibaコピペ完全対応・逃げ穴激走軸固定・秋元フィルター統合システム")
st.markdown("---")

# ----------------------------------------------------
# 2. データの入力エリア（画面の左サイドバー）
# ----------------------------------------------------
st.sidebar.header("🛠 レース条件設定")
venue = st.sidebar.selectbox("競馬場", ["船橋", "大井", "川崎", "浦和"], index=0)
race_num = st.sidebar.number_input("レース番号", min_value=1, max_value=12, value=1)
race_class = st.sidebar.selectbox("クラス", ["3歳", "C3", "C2", "C1", "B3", "A2", "重賞"], index=0)

st.sidebar.markdown("---")

st.sidebar.header("📋 netkeiba 出馬表・結果コピペ入力")
pasted_data = st.sidebar.text_area(
    "サイトのテキストを丸ごとここに貼り付けてください",
    height=250,
    placeholder="データを貼り付けてください"
)

# 🔥 【新機能】パース確認モードのスイッチ
st.sidebar.markdown("---")
st.sidebar.header("⚙️ システム診断")
debug_mode = st.sidebar.checkbox("🔍 パース確認モードをONにする", value=False, help="AIがコピペテキストのどの行からデータを拾ったか可視化します")

# 解析ボタン
start_analysis = st.sidebar.button("🚀 レース解析を実行", type="primary")

# ----------------------------------------------------
# 🌟 パースロジック（ログ収集機能付き）
# ----------------------------------------------------
def parse_netkeiba_v7(text, debug=False):
    if not text.strip():
        return [], []
        
    debug_logs = []
    cleaned_text = re.sub(r'[\s\t\xa0\u3000]+', ' ', text)
    
    # 1. コーナー通過順位の先行抽出
    escape_heavy_users = set()
    corner_history_matches = re.findall(r'(?:1|2|3|4)コーナー\s*([\d,\(\)\-]+)', cleaned_text)
    for history in corner_history_matches:
        first_horse = re.match(r'^(\d+)', history)
        if first_horse:
            escape_heavy_users.add(int(first_horse.group(1)))
            if debug:
                debug_logs.append(f"【コーナー順位検知】最初のコーナー先頭馬番: {first_horse.group(1)}")
            
    parsed_entries = []
    ana_jockey_master = ['山林堂', '吉留孝', '古岡勇', '加藤雄', '藤江渉', '笠野雄', '木間塚', '篠谷葵', '岡村健', '山中悠']
    all_jockeys = ana_jockey_master + ['川島正', '和田譲', '小杉亮', '町田直', '野澤憲', '山本大', '秋元耕']

    raw_lines = text.split('\n')
    for idx, line in enumerate(raw_lines):
        line_str = line.strip()
        if not line_str:
            continue
            
        # 騎手判定
        found_jockey = "不明"
        for jk in all_jockeys:
            if jk in line_str:
                found_jockey = jk
                break
                
        if found_jockey == "不明":
            continue
            
        # オッズ判定
        odds_candidates = re.findall(r'\b(\d+\.\d+)\b', line_str)
        tan_odds = 99.0
        if odds_candidates:
            for cand in odds_candidates:
                if f":{cand}" not in line_str:
                    tan_odds = float(cand)
                    break

        # 人気判定
        ninki = 10
        ninki_candidates = re.findall(r'\b(\d{1,2})\b', line_str)
        if len(ninki_candidates) >= 2:
            for num in reversed(ninki_candidates):
                if int(num) <= 18 and int(num) != int(tan_odds):
                    ninki = int(num)
                    break

        # 馬番判定
        left_side = line_str.split(found_jockey)[0]
        maruban_matches = re.findall(r'\b(\d{1,2})\b', left_side)
        if not maruban_matches:
            if debug:
                debug_logs.append(f"❌ 行 {idx+1}: 騎手({found_jockey})は見つかりましたが馬番の特定に失敗しました。 -> `{line_str[:30]}...`刻み")
            continue
        maruban = int(maruban_matches[-1])

        # 脚質・過去の逃げ先行実績
        kyashitsu = "差し"
        reason_kyashitsu = "デフォルト割り当て"
        if maruban in escape_heavy_users or "逃" in line_str or "先" in line_str:
            kyashitsu = "逃げ・先行（実績あり）"
            reason_kyashitsu = "テキスト内の『逃・先』キーワード"
        elif "1-" in line_str or "2-" in line_str or "3-" in line_str:
            kyashitsu = "逃げ・先行（実績あり）"
            reason_kyashitsu = "過去走通過順位が3番手以内"
        elif maruban == 1:
            kyashitsu = "逃げ・先行（実績あり）"
            reason_kyashitsu = "馬番1番特別補正（前残り警戒）"

        # タイムスコア
        time_score = 75.0
        time_match = re.search(r'(\d):(\d{2}\.\d)', line_str)
        if time_match:
            min_val = int(time_match.group(1))
            sec_val = float(time_match.group(2))
            total_sec = min_val * 60 + sec_val
            time_score = round(100 - (total_sec - 75.0) * 2, 1)
            time_score = max(60.0, min(98.0, time_score))

        fuku_odds_min = round(max(1.1, tan_odds * 0.25), 1)

        if debug:
            debug_logs.append(f"✅ 行 {idx+1} 成功解析 -> 馬番:{maruban:02d} | 騎手:{found_jockey} | 単勝:{tan_odds}倍({ninki}人) | 脚質:{kyashitsu} (根拠: {reason_kyashitsu})")

        if not any(h['maruban'] == maruban for h in parsed_entries):
            parsed_entries.append({
                'maruban': maruban,
                'jockey': found_jockey,
                'kyashitsu': kyashitsu,
                'tan_odds': tan_odds,
                'fuku_odds_min': fuku_odds_min,
                'time_score': time_score,
                'ninki': ninki
            })

    return sorted(parsed_entries, key=lambda x: x['maruban']), debug_logs

# ----------------------------------------------------
# 3. メイン処理と確認モードの表示
# ----------------------------------------------------
entries = []
logs = []

if pasted_data.strip() and start_analysis:
    entries, logs = parse_netkeiba_v7(pasted_data, debug=debug_mode)
    
    # パース確認モードがONの場合、最上部にログを展開
    if debug_mode:
        st.subheader("🔍 AIパース診断ログ（データ抽出の裏舞台）")
        with st.expander("詳細なパースログを確認（ここをクリックして展開）", expanded=True):
            if logs:
                for log in logs:
                    if "✅" in log:
                        st.text(log)
                    else:
                        st.warning(log)
            else:
                st.error("テキストは入力されましたが、馬データ（騎手やオッズ等）が1行も抽出できませんでした。")
                
    if not entries:
        st.error("⚠️ パースに失敗しました。左サイドバーの『パース確認モードをONにする』をチェックして、原因を特定してください。")
else:
    if not pasted_data.strip():
        st.info("💡 左のテキストエリアにデータを貼り付けて「🚀 レース解析を実行」を押してください。現在はデモデータを表示中。")
    else:
        st.warning("👈 データを貼り付けたら、左サイドバーの下にある「🚀 レース解析を実行」ボタンを押してください！")
        
    # 初期デモデータ
    entries = [
        {'maruban': 1,  'ninki': 7,  'tan_odds': 45.5, 'fuku_odds_min': 11.4, 'time_score': 95.6, 'jockey': '篠谷葵',   'kyashitsu': '逃げ・先行（実績あり）'},
        {'maruban': 2,  'ninki': 10, 'tan_odds': 168.7,'fuku_odds_min': 42.2, 'time_score': 67.6, 'jockey': '小杉亮',   'kyashitsu': '追い込み'},
        {'maruban': 3,  'ninki': 8,  'tan_odds': 54.1, 'fuku_odds_min': 13.5, 'time_score': 60.0, 'jockey': '町田直',   'kyashitsu': '差し'},
        {'maruban': 4,  'ninki': 5,  'tan_odds': 23.0, 'fuku_odds_min': 5.8,  'time_score': 95.2, 'jockey': '和田譲',   'kyashitsu': '差し'},
        {'maruban': 5,  'ninki': 2,  'tan_odds': 4.0,  'fuku_odds_min': 1.0,  'time_score': 97.6, 'jockey': '岡村健',   'kyashitsu': '追い込み'},
        {'maruban': 6,  'ninki': 1,  'tan_odds': 1.3,  'fuku_odds_min': 1.1,  'time_score': 97.8, 'jockey': '川島正',   'kyashitsu': '差し'},
        {'maruban': 7,  'ninki': 11, 'tan_odds': 170.4,'fuku_odds_min': 42.6, 'time_score': 89.8, 'jockey': '野澤憲',   'kyashitsu': '差し'},
        {'maruban': 8,  'ninki': 4,  'tan_odds': 22.2, 'fuku_odds_min': 5.5,  'time_score': 96.0, 'jockey': '山中悠',   'kyashitsu': '差し'},
        {'maruban': 9,  'ninki': 6,  'tan_odds': 41.2, 'fuku_odds_min': 10.3, 'time_score': 60.0, 'jockey': '山本大',   'kyashitsu': '差し'},
        {'maruban': 10, 'ninki': 9,  'tan_odds': 62.0, 'fuku_odds_min': 15.5, 'time_score': 95.2, 'jockey': '木間塚',   'kyashitsu': '追い込み'},
        {'maruban': 11, 'ninki': 3,  'tan_odds': 10.7, 'fuku_odds_min': 2.7,  'time_score': 94.4, 'jockey': '古岡勇',   'kyashitsu': '追い込み'},
    ]

# ----------------------------------------------------
# 4. AIコア解析ロジック & バルさん専用フォーメーション
# ----------------------------------------------------
if entries:
    st.subheader("📋 AIが自動認識した出走馬データ一覧")
    st.dataframe(entries, use_container_width=True)

    front_runners_list = [h for h in entries if "逃げ" in h['kyashitsu'] or "先行" in h['kyashitsu']]
    front_runners = len(front_runners_list)
    
    odds_1st_list = [h['tan_odds'] for h in entries if h['ninki'] == 1]
    odds_1st = odds_1st_list[0] if odds_1st_list else 2.0

    sorted_horses = sorted(entries, key=lambda x: x['ninki'])

    # 軸固定アルゴリズム
    first_row = []
    escape_reasons = []

    escape_ana_horses = [
        h for h in entries 
        if ("逃げ" in h['kyashitsu'] or "先行" in h['kyashitsu']) and h['tan_odds'] >= 10.0
    ]

    if escape_ana_horses:
        for target in escape_ana_horses:
            first_row.append(target['maruban'])
            escape_reasons.append(f"🐴 馬番:{target['maruban']:02d}（{target['jockey']}）[前残り・激走穴軸に選定！]")
    else:
        first_row = [sorted_horses[0]['maruban']]
        escape_reasons.append(f"🟢 逃げ穴馬不在のため、1番人気 馬番:{first_row[0]:02d} を軸に設定しました。")

    first_row = sorted(list(set(first_row)))

    second_row = [h['maruban'] for h in sorted_horses[0:5] if h['maruban'] not in first_row and h['jockey'] != '秋元耕成']
    second_row = sorted(list(set(second_row[:4])))

    third_row = []
    ana_jockey_master = ['山林堂', '吉留孝', '古岡勇', '加藤雄', '藤江渉', '笠野雄', '木間塚', '篠谷葵', '岡村健', '山中悠']

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👑 軸馬・展開セレクション")
        for reason in escape_reasons:
            st.warning(reason)

    with col2:
        st.subheader("🔎 大穴ゾーン個別インサイダー解析")
        for h in entries:
            if h['jockey'] == '秋元耕成':
                continue
                
            is_selected = False
            reasons = []
            
            if h['ninki'] <= 5:
                is_selected = True; reasons.append("実力上位")
            else:
                hit_count = 0
                if h['tan_odds'] >= 20.0 and h['fuku_odds_min'] <= (h['tan_odds'] * 0.22):
                    hit_count += 1; reasons.append("複勝歪み")
                if h['jockey'] in ana_jockey_master:
                    hit_count += 1; reasons.append(f"穴特化騎手")
                if h['time_score'] >= 93.0:
                    hit_count += 1; reasons.append("好タイム")
                if "逃げ" in h['kyashitsu'] or "先行" in h['kyashitsu']:
                    hit_count += 1; reasons.append("前残り警戒")
                
                if hit_count >= 1:
                    is_selected = True
                
            if is_selected:
                third_row.append(h['maruban'])
                st.code(f"⚠️ 馬番:{h['maruban']:02d} -> 紐採用 [{', '.join(reasons)}]", language="text")
                
        third_row = sorted(list(set(third_row)))

    # 5. 点数計算＆フォーメーション出力
    st.markdown("---")
    st.subheader("🎯 【最終出力】Baru式・3連複フォーメーション配置")

    final_tickets = set()
    for r1 in first_row:
        for r2 in second_row:
            for r3 in third_row:
                if r1 != r2 and r1 != r3 and r2 != r3:
                    ticket = tuple(sorted([r1, r2, r3]))
                    final_tickets.add(ticket)
    sorted_tickets = sorted(list(final_tickets))

    st.success(f"🔥 【合計購入点数: {len(sorted_tickets)} 点】")

    if sorted_tickets:
        def format_row(row_list): return "　".join([f"{num:02d}" for num in list(set(row_list))])
        st.code(f"1番（軸）　　 🔴【 {format_row(first_row)} 】", language="text")
        st.code(f"2番（相手）　 🔵【 {format_row(second_row)} 】", language="text")
        st.code(f"3番（穴紐）　 🟢【 {format_row(third_row)} 】", language="text")
