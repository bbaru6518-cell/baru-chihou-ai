import streamlit as st
import re

# 1. 画面設定
st.set_page_config(page_title="Baru競馬AI Pro", page_icon="🎯", layout="wide")
st.title("🎯 Baru競馬AI Pro 〜研究者レベル最終進化版〜")
st.write("ネット競馬コピペデータ自動パース・インサイダーオッズ歪み・秋元フィルター完全統合システム")
st.markdown("---")

# 2. サイドバー
st.sidebar.header("🛠 レース条件設定")
venue = st.sidebar.selectbox("競馬場", ["船橋", "大井", "川崎", "浦和"], index=0)
race_num = st.sidebar.number_input("レース番号", min_value=1, max_value=12, value=4)
race_class = st.sidebar.selectbox("クラス", ["C3", "C2", "C1", "B3", "A2", "重賞"], index=0)

st.sidebar.markdown("---")
st.sidebar.header("📋 netkeiba 出馬表コピペ入力")
pasted_data = st.sidebar.text_area(
    "サイトのテキストを丸ごとここに貼り付けてください",
    height=300,
    placeholder="1  1  \n--\nヤマカツエース\n..."
)

start_analysis = st.sidebar.button("🚀 レース解析を実行", type="primary")

# ----------------------------------------------------
# 【修正版パーサー】
# 実際のnetkeibaコピペ形式に対応:
#   「枠番 \t 馬番 \t ...\n--\n...馬データ...」
# ----------------------------------------------------
def parse_netkeiba_v2(text):
    if not text.strip():
        return []

    # 前処理
    cleaned = text.replace('\xa0', ' ').replace('\u3000', ' ')
    # ダッシュ類を統一（ただし「--」区切りを残すため慎重に）
    cleaned = re.sub(r'[–—―─−]', '-', cleaned)

    # ブロック区切りの検出:「枠番 \t 馬番 \t ... 改行 --」
    # ネットkeiba形式: "1 \t 1 \t\n--" または "1\t1\t\n--"
    block_pattern = re.compile(
        r'(\d+)\s*\t\s*(\d+)\s*\t[^\n]*\n\s*--',
        re.MULTILINE
    )
    matches = list(block_pattern.finditer(cleaned))

    if not matches:
        # フォールバック: 「数字--」形式（旧形式）
        fallback_pattern = re.compile(r'(\d+)-{2,}', re.MULTILINE)
        matches_fb = list(fallback_pattern.finditer(cleaned))
        if not matches_fb:
            return []
        # 旧形式で処理
        return _parse_old_format(cleaned, matches_fb)

    entries = []
    for idx, m in enumerate(matches):
        waku   = int(m.group(1))
        umaban = int(m.group(2))

        block_start = m.end()
        block_end   = matches[idx + 1].start() if idx + 1 < len(matches) else len(cleaned)
        block       = cleaned[block_start:block_end]
        lines       = [l.strip() for l in block.split('\n') if l.strip()]

        # ── オッズ・人気 ──────────────────
        tan_odds = 99.0
        ninki    = 10
        odds_pat = re.compile(r'([\d.]+)\s*\((\d+)人気\)')
        for line in lines:
            mo = odds_pat.search(line)
            if mo:
                tan_odds = float(mo.group(1))
                ninki    = int(mo.group(2))
                break

        # ── 脚質 ──────────────────────────
        kyashitsu = "差し"
        for line in lines[:15]:
            if line in ["逃", "逃げ"]:          kyashitsu = "逃げ";    break
            if line in ["先", "先行"]:           kyashitsu = "先行";    break
            if line in ["差", "差し"]:           kyashitsu = "差し";    break
            if line in ["追", "追い込み", "追込"]: kyashitsu = "追い込み"; break

        # ── 騎手名（「牝/牡/騸 + 年齢 + 毛色 + 騎手名」の行） ────
        jockey = "不明"
        jockey_pat = re.compile(r'[牡牝騸]\d+[^\s]*\s+(.+)')
        for line in lines:
            mj = jockey_pat.match(line)
            if mj:
                jockey = mj.group(1).strip()
                break

        # ── 直近タイムスコア ──────────────
        time_score = 75.0
        time_pat   = re.compile(r'ダ\d+\s+(\d+):(\d+\.\d+)')
        times = []
        for line in lines:
            mt = time_pat.search(line)
            if mt:
                t = int(mt.group(1)) * 60 + float(mt.group(2))
                times.append(t)
        if times:
            t0 = times[0]
            time_score = round(100 - (t0 - 75.0) * 2, 1)
            time_score = max(60.0, min(98.0, time_score))

        fuku_odds_min = round(max(1.1, tan_odds * 0.25), 1)

        entries.append({
            'waku':         waku,
            'maruban':      umaban,
            'jockey':       jockey,
            'kyashitsu':    kyashitsu,
            'tan_odds':     tan_odds,
            'fuku_odds_min': fuku_odds_min,
            'time_score':   time_score,
            'ninki':        ninki,
        })

        if len(entries) >= 16:
            break

    return entries


def _parse_old_format(cleaned, matches):
    """旧形式（数字--）のフォールバックパーサー"""
    entries = []
    for idx, match in enumerate(matches):
        raw_num = match.group(1).strip()
        start_pos = match.end()
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(cleaned)
        block_content = cleaned[start_pos:end_pos]

        umaban = int(raw_num[1:]) if len(raw_num) >= 3 else int(raw_num)
        lines = [l.strip() for l in block_content.split('\n') if l.strip()]
        if not lines:
            continue

        jockey = "不明"
        kyashitsu = "差し"
        tan_odds = 99.0
        ninki = 10
        time_score = 75.0

        for line in lines[:10]:
            if line in ["逃", "逃げ"]: kyashitsu = "逃げ"; break
            if line in ["先", "先行"]: kyashitsu = "先行"; break
            if line in ["差", "差し"]: kyashitsu = "差し"; break
            if line in ["追", "追い込み"]: kyashitsu = "追い込み"; break

        odds_pattern = re.compile(r'([\d.]+)\s*\(\s*(\d+)\s*人気\s*\)')
        for line in lines[:20]:
            mo = odds_pattern.search(line)
            if mo:
                tan_odds = float(mo.group(1))
                ninki = int(mo.group(2))
                break

        fuku_odds_min = round(max(1.1, tan_odds * 0.25), 1)
        entries.append({
            'waku': 0, 'maruban': umaban,
            'jockey': jockey, 'kyashitsu': kyashitsu,
            'tan_odds': tan_odds, 'fuku_odds_min': fuku_odds_min,
            'time_score': time_score, 'ninki': ninki,
        })
        if len(entries) >= 16:
            break
    return entries


# ----------------------------------------------------
# 3. メイン処理
# ----------------------------------------------------
if pasted_data.strip() and start_analysis:
    entries = parse_netkeiba_v2(pasted_data)
    if not entries:
        st.error("⚠️ パースに失敗しました。データをそのままコピペしたか確認してください。")
        entries = []
else:
    if not pasted_data.strip():
        st.info("💡 左のテキストエリアにデータを貼り付けて「🚀 レース解析を実行」を押してください。現在はデモデータを表示中。")
    else:
        st.warning("👈 データを貼り付けたら、左サイドバー下の「🚀 レース解析を実行」ボタンを押してください！")

    # デモデータ（Document 2 の実際の馬に合わせて更新）
    entries = [
        {'waku': 1, 'maruban': 1,  'ninki': 10, 'tan_odds': 238.1, 'fuku_odds_min': 4.5,  'time_score': 71.0, 'jockey': '臼井健',   'kyashitsu': '差し'},
        {'waku': 2, 'maruban': 2,  'ninki': 5,  'tan_odds': 22.4,  'fuku_odds_min': 5.6,  'time_score': 73.0, 'jockey': '古岡勇',   'kyashitsu': '追い込み'},
        {'waku': 3, 'maruban': 3,  'ninki': 1,  'tan_odds': 1.2,   'fuku_odds_min': 1.1,  'time_score': 95.0, 'jockey': '矢野貴',   'kyashitsu': '先行'},
        {'waku': 4, 'maruban': 4,  'ninki': 3,  'tan_odds': 9.8,   'fuku_odds_min': 2.5,  'time_score': 85.0, 'jockey': '岡村健',   'kyashitsu': '差し'},
        {'waku': 5, 'maruban': 5,  'ninki': 7,  'tan_odds': 53.6,  'fuku_odds_min': 3.5,  'time_score': 76.0, 'jockey': '本田紀',   'kyashitsu': '差し'},
        {'waku': 6, 'maruban': 6,  'ninki': 9,  'tan_odds': 156.2, 'fuku_odds_min': 3.2,  'time_score': 67.0, 'jockey': '笠野雄',   'kyashitsu': '差し'},
        {'waku': 7, 'maruban': 7,  'ninki': 8,  'tan_odds': 85.3,  'fuku_odds_min': 6.0,  'time_score': 70.0, 'jockey': '椿聡太',   'kyashitsu': '追い込み'},
        {'waku': 7, 'maruban': 8,  'ninki': 4,  'tan_odds': 18.0,  'fuku_odds_min': 4.0,  'time_score': 82.0, 'jockey': '池谷匠',   'kyashitsu': '先行'},
        {'waku': 8, 'maruban': 9,  'ninki': 2,  'tan_odds': 5.9,   'fuku_odds_min': 1.8,  'time_score': 88.0, 'jockey': '仲野光',   'kyashitsu': '差し'},
        {'waku': 8, 'maruban': 10, 'ninki': 6,  'tan_odds': 35.4,  'fuku_odds_min': 2.8,  'time_score': 74.0, 'jockey': '沖響主',   'kyashitsu': '追い込み'},
    ]

# ----------------------------------------------------
# 4. 解析 & 表示
# ----------------------------------------------------
if entries:
    st.subheader("📋 AIが自動認識した出走馬データ一覧")
    st.dataframe(entries, use_container_width=True)

    front_runners = len([h for h in entries if h['kyashitsu'] in ['逃げ', '先行']])
    odds_1st = next((h['tan_odds'] for h in entries if h['ninki'] == 1), 2.0)
    odds_3rd = next((h['tan_odds'] for h in entries if h['ninki'] == 3), 6.0)
    odds_gap = odds_3rd - odds_1st

    turbulence_score = 0
    if race_class == 'C3':   turbulence_score += 25
    if front_runners >= 5:   turbulence_score += 40
    elif front_runners <= 2: turbulence_score -= 20
    if odds_gap < 5.0:       turbulence_score += 20

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 レース構造解析結果")
        st.write(f"先行馬数: {front_runners}頭 ／ 1番人気オッズ: {odds_1st} ／ オッズ差: {odds_gap:.1f}")
        if turbulence_score >= 60:
            st.error(f"判定: 🔥 大荒れ警戒（スコア: {turbulence_score}点）")
        elif 20 <= turbulence_score < 60:
            st.warning(f"判定: ⚖️ 中穴傾向（スコア: {turbulence_score}点）")
        else:
            st.success(f"判定: 🟢 ガチガチ本命（スコア: {turbulence_score}点）")

    sorted_horses = sorted(entries, key=lambda x: x['ninki'])
    total_horses  = len(sorted_horses)

    # ── 1列目（軸） ─────────────────────────
    zone1_pool = sorted_horses[:4]
    horse_1st  = sorted_horses[0]
    remaining  = [h for h in zone1_pool if h['maruban'] != horse_1st['maruban']]
    first_row  = [horse_1st['maruban']]
    if remaining:
        best = max(remaining, key=lambda x: x['time_score'])
        if best['jockey'] != '秋元耕成':
            first_row.append(best['maruban'])
    first_row.sort()

    # ── 2列目（相手） ────────────────────────
    zone2_pool = sorted_horses[3:8] if total_horses >= 8 else sorted_horses[1:]
    second_row = sorted([h['maruban'] for h in zone2_pool if h['jockey'] != '秋元耕成'])

    # ── 3列目（穴紐フィルター） ───────────────
    zone3_pool = sorted_horses[max(0, total_horses - 5):]
    third_row  = []
    ana_jockeys = ['山林堂', '吉留孝', '古岡勇', '加藤雄', '藤江渉', '笠野雄']

    with col2:
        st.subheader("🔎 大穴ゾーン個別インサイダー解析")
        for h in zone3_pool:
            if h['jockey'] == '秋元耕成':
                st.text(f"❌ 馬番:{h['maruban']:02d} -> 強制排除")
                continue
            reasons = []
            if h['tan_odds'] >= 25.0 and h['fuku_odds_min'] <= 3.5:
                reasons.append("複勝歪み")
            if h['jockey'] in ana_jockeys:
                reasons.append(f"穴騎手({h['jockey']})")
            if turbulence_score >= 60:
                reasons.append("大荒れ救済")
            if reasons:
                third_row.append(h['maruban'])
                st.code(f"⚠️ 馬番:{h['maruban']:02d} -> 採用 [{', '.join(reasons)}]", language="text")

    third_row.sort()

    # ── 5. フォーメーション出力 ────────────────
    st.markdown("---")
    st.subheader("🎯 【最終出力】Baru式・3連複フォーメーション配置")

    final_tickets = set()
    for r1 in first_row:
        for r2 in second_row:
            for r3 in third_row:
                combo = tuple(sorted({r1, r2, r3}))
                if len(combo) == 3:
                    final_tickets.add(combo)
    sorted_tickets = sorted(final_tickets)

    st.success(f"🔥 【合計購入点数: {len(sorted_tickets)} 点】")

    if sorted_tickets:
        def fmt(lst): return "　".join(f"{n:02d}" for n in sorted(set(lst)))
        st.code(f"1番（軸）　　 🔴【 {fmt(first_row)} 】",  language="text")
        st.code(f"2番（相手）　 🔵【 {fmt(second_row)} 】", language="text")
        st.code(f"3番（穴紐）　 🟢【 {fmt(third_row)} 】",  language="text")

        st.subheader("🎫 全買い目一覧")
        cols = st.columns(4)
        for i, t in enumerate(sorted_tickets):
            cols[i % 4].write(f"{t[0]:02d}-{t[1]:02d}-{t[2]:02d}")
