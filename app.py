import streamlit as st
import re

# 1. 画面の基本設定
st.set_page_config(page_title="Baru競馬AI Pro", page_icon="🎯", layout="wide")

st.title("🎯 Baru競馬AI Pro 〜研究者レベル最終進化版〜")
st.write("ネット競馬コピペデータ自動パース・インサイダーオッズ歪み・秋元フィルター完全統合システム")
st.markdown("---")

# ----------------------------------------------------
# 2. データの入力エリア（画面の左サイドバー）
# ----------------------------------------------------
st.sidebar.header("🛠 レース条件設定")
venue = st.sidebar.selectbox("競馬場", ["船橋", "大井", "川崎", "浦和"], index=0)
race_num = st.sidebar.number_input("レース番号", min_value=1, max_value=12, value=3)
race_class = st.sidebar.selectbox("クラス", ["C3", "C2", "C1", "B3", "A2", "重賞"], index=0)

st.sidebar.markdown("---")

st.sidebar.header("📋 netkeiba 出馬表コピペ入力")
pasted_data = st.sidebar.text_area(
    "サイトのテキストを丸ごとここに貼り付けてください",
    height=300,
    placeholder="3R C3二組下選抜馬...\n11--\nモズアスコット...\n(コマンズ)..."
)

# ----------------------------------------------------
# 🌟 ネット競馬縦型コピーデータ専用・超高度パースロジック
# ----------------------------------------------------
def parse_netkeiba_vertical(text):
    if not text.strip():
        return []
    
    # 馬番 (例: "11--" や "22--" や "810--") でテキストを分割
    # ※ネット競馬のコピペ特徴：馬番の後ろに「--」がつくか、8枠10番だと「810--」となる
    raw_blocks = re.split(r'\n(\d+)--\s*\n', text)
    
    if len(raw_blocks) < 3:
        return []
    
    parsed_entries = []
    
    # 分割されたブロックをループ処理 (最初のブロックはレース情報ヘッダーなので飛ばす)
    for i in range(1, len(raw_blocks), 2):
        raw_num = raw_blocks[i]
        block_content = raw_blocks[i+1] if i+1 < len(raw_blocks) else ""
        
        # 馬番の整形 (例: "810" の場合は最後の2桁 "10" を馬番とする)
        if len(raw_num) >= 3 and raw_num.startswith(('1','2','3','4','5','6','7','8')):
            maruban = int(raw_num[1:])
        else:
            maruban = int(raw_num)
            
        lines = [line.strip() for line in block_content.split('\n') if line.strip()]
        if not lines:
            continue
            
        # --- 各変数の初期化 ---
        jockey = "不明"
        kyashitsu = "差"
        tan_odds = 99.0
        ninki = 10
        time_score = 70.0 # デフォルト値
        
        # --- 脚質の抽出 (塊の上部にある「逃」「先」「差」「追」を検出) ---
        for line in lines[:10]:
            if line in ["逃", "先", "先行", "逃げ", "差", "差し", "追", "追い込み"]:
                kyashitsu = line
                if kyashitsu == "先": kyashitsu = "先行"
                if kyashitsu == "逃": kyashitsu = "逃げ"
                if kyashitsu == "差": kyashitsu = "差し"
                if kyashitsu == "追": kyashitsu = "追い込み"
                break
                
        # --- オッズと人気の抽出 (例: "28.3(8人気)" を探す) ---
        odds_pattern = re.compile(r'([\d.]+)\((\d+)人気\)')
        for line in lines:
            match = odds_pattern.search(line)
            if match:
                tan_odds = float(match.group(1))
                ninki = int(match.group(2))
                break
                
        # --- 騎手名の抽出 ---
        # オッズが書かれている行の「次の行」か「2行下」に騎手名が来ることが多い
        # または、おなじみの穴騎手リストや減量騎手、カタカナ以外で判定
        known_jockeys = ['藤江渉', '福原杏', '沖響主', '山口達', '笠野雄', '濱田達', '山林堂', '加藤雄', '吉留孝', '本橋孝', '古岡勇', '秋元耕']
        for line in lines:
            # 既知の騎手リストに前方一致するかチェック
            for kj in known_jockeys:
                if line.startswith(kj):
                    jockey = kj
                    break
            if jockey != "不明":
                break
        
        # 登録がない騎手の場合のフォールバック（54.02026... のような斤量+日付行の直前の2〜4文字を狙う）
        if jockey == "不明":
            for idx, line in enumerate(lines):
                if re.search(r'\d{2}\.\d\d{4}', line): # "56.02026..." のようなパターン
                    if idx > 0 and len(lines[idx-1]) <= 4 and not lines[idx-1].endswith('kg'):
                        jockey = lines[idx-1]
                        break

        # --- 走破タイム（タイムスコア）の抽出 ---
        # 過去走の「ダ1400 1:35.0」のような表記から、一番最近のタイムを取得してスコア化
        time_pattern = re.compile(r'ダ\d+\s+(\d+):(\d+\.\d+)')
        times = []
        for line in lines:
            match = time_pattern.search(line)
            if match:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                total_seconds = minutes * 60 + seconds
                times.append(total_seconds)
        
        if times:
            # 直近のレース（最初に見つかったタイム）を基準に、走破AIの仮スコアを算出
            # 1500mや1400mの基準秒から、速ければ高いスコアにするロジック
            base_time = 100.0  # 基準秒
            latest_time = times[0]
            # タイムが短い(速い)ほどスコアが高くなる計算式
            time_score = round(100 - (latest_time - base_time) * 2, 1)
            # スコアの範囲を現実的な 60〜98 に収める調整
            if time_score > 98: time_score = 98.0
            if time_score < 60: time_score = 60.0
        else:
            time_score = 75.0 # タイムが取れなかった場合は平均値を付与
            
        # 複勝下限オッズは単勝オッズから統計的に自動逆算(1/4〜1/3)
        fuku_odds_min = round(max(1.1, tan_odds * 0.25), 1)

        parsed_entries.append({
            'maruban': maruban,
            'jockey': jockey,
            'kyashitsu': kyashitsu,
            'tan_odds': tan_odds,
            'fuku_odds_min': fuku_odds_min,
            'time_score': time_score,
            'ninki': ninki
        })
        
    return parsed_entries

# ----------------------------------------------------
# データの読み込み実行
# ----------------------------------------------------
entries = parse_netkeiba_vertical(pasted_data)

if pasted_data.strip() and not entries:
    st.sidebar.error("⚠️ パースに失敗しました。データの形式が変更された可能性があります。")
elif not pasted_data.strip():
    st.sidebar.info("💡 現在はテスト用の自動デモデータを読み込んでいます。実際のレース時はここに貼り付けてください。")
    # デフォルトの船橋3Rテストデータ
    entries = [
        {'maruban': 11, 'ninki': 8,  'tan_odds': 28.3, 'fuku_odds_min': 4.5, 'time_score': 74.0, 'jockey': '藤江渉',   'kyashitsu': '差し'},
        {'maruban': 2,  'ninki': 5,  'tan_odds': 15.8, 'fuku_odds_min': 3.2, 'time_score': 79.0, 'jockey': '福原杏',   'kyashitsu': '差し'},
        {'maruban': 3,  'ninki': 11, 'tan_odds': 74.0, 'fuku_odds_min': 7.2, 'time_score': 65.0, 'jockey': '沖響主',   'kyashitsu': '追い込み'},
        {'maruban': 4,  'ninki': 2,  'tan_odds': 4.5,  'fuku_odds_min': 1.5, 'time_score': 88.0, 'jockey': '山口達',   'kyashitsu': '差し'},
        {'maruban': 5,  'ninki': 3,  'tan_odds': 8.9,  'fuku_odds_min': 2.1, 'time_score': 91.5, 'jockey': '笠野雄',   'kyashitsu': '追い込み'},
        {'maruban': 6,  'ninki': 7,  'tan_odds': 22.2, 'fuku_odds_min': 4.0, 'time_score': 76.0, 'jockey': '濱田達',   'kyashitsu': '追い込み'},
        {'maruban': 7,  'ninki': 10, 'tan_odds': 72.8, 'fuku_odds_min': 2.5, 'time_score': 80.0, 'jockey': '山林堂',   'kyashitsu': '追い込み'},
        {'maruban': 8,  'ninki': 9,  'tan_odds': 59.1, 'fuku_odds_min': 6.0, 'time_score': 71.0, 'jockey': '加藤雄',   'kyashitsu': '差し'},
        {'maruban': 9,  'ninki': 6,  'tan_odds': 17.0, 'fuku_odds_min': 3.5, 'time_score': 85.0, 'jockey': '吉留孝',   'kyashitsu': '差し'},
        {'maruban': 10, 'ninki': 4,  'tan_odds': 14.1, 'fuku_odds_min': 3.0, 'time_score': 82.0, 'jockey': '本橋孝',   'kyashitsu': '追い込み'},
        {'maruban': 11, 'ninki': 1,  'tan_odds': 1.6,  'fuku_odds_min': 1.1, 'time_score': 95.0, 'jockey': '古岡勇',   'kyashitsu': '差し'},
    ]

# ----------------------------------------------------
# 3. AIコア解析ロジック & 結果表示
# ----------------------------------------------------
if entries:
    # 読み込まれた馬の一覧を綺麗にテーブル表示（デバッグ・確認用）
    st.subheader("📋 AIが自動認識した出走馬データ一覧")
    st.dataframe(entries, use_container_width=True)

    front_runners = len([h for h in entries if h['kyashitsu'] in ['逃げ', '先行']])
    odds_1st_list = [h['tan_odds'] for h in entries if h['ninki'] == 1]
    odds_3rd_list = [h['tan_odds'] for h in entries if h['ninki'] == 3]
    
    odds_1st = odds_1st_list[0] if odds_1st_list else 2.0
    odds_3rd = odds_3rd_list[0] if odds_3rd_list else 6.0
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

    # 人気順にソート
    sorted_horses = sorted(entries, key=lambda x: x['ninki'])
    total_horses = len(sorted_horses)

    # --- 【1番：1列目（軸）】 ---
    zone1_pool = sorted_horses[:4]
    horse_1st_list = [h for h in zone1_pool if h['ninki'] == 1]
    horse_1st = horse_1st_list[0] if horse_1st_list else sorted_horses[0]
    remaining_zone1 = [h for h in zone1_pool if h['maruban'] != horse_1st['maruban']]
    
    first_row = [horse_1st['maruban']]
    if remaining_zone1:
        best_time_horse = max(remaining_zone1, key=lambda x: x['time_score'])
        if best_time_horse['jockey'] != '秋元耕成':
            first_row.append(best_time_horse['maruban'])
    first_row.sort()

    # --- 【2番：2列目（相手）】 ---
    zone2_pool = sorted_horses[3:8] if total_horses >= 8 else sorted_horses[1:]
    second_row = [h['maruban'] for h in zone2_pool if h['jockey'] != '秋元耕成']
    second_row.sort()

    # --- 【3番：3列目（穴紐フィルター）】 ---
    zone3_pool = sorted_horses[max(0, total_horses-5):]
    third_row = []
    ana_jockey_master = ['山林堂', '吉留孝', '古岡勇', '加藤雄', '藤江渉', '笠野雄']

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
                st.code(f"⚠️ 馬番:{h['maruban']:02d} ({h['jockey']}) -> 採用 [{', '.join(reasons)}]", language="text")
            else:
                st.text(f"💤 馬番:{h['maruban']:02d} ({h['jockey']}) -> 武器不足で見送り")
                
        third_row.sort()

    # ----------------------------------------------------
    # 4. 点数計算＆マークシート配置出力
    # ----------------------------------------------------
    st.markdown("---")
    st.subheader("🎯 【最終出力】Baru式・3連複フォーメーション配置（投票画面用）")

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
        def format_row(row_list):
            return "　".join([f"{num:02d}" for num in row_list])

        st.code(f"1番（軸）　　 🔴【 {format_row(first_row)} 】", language="text")
        st.code(f"2番（相手）　 🔵【 {format_row(second_row)} 】", language="text")
        st.code(f"3番（穴紐）　 🟢【 {format_row(third_row)} 】", language="text")
        st.markdown("---")
