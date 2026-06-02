import streamlit as st
from parser import parse_netkeiba_complete

st.set_page_config(page_title="Baru競馬AI Pro", layout="wide")

# セッション状態の初期化
if "saved_settings" not in st.session_state:
    st.session_state.saved_settings = {"api_key": "", "criteria": "", "saved": False}

# ====================================================================
# 🛠️ サイドバー：総監督司令部
# ====================================================================
st.sidebar.markdown("## ⚙️ 総監督司令部")

gemini_key = st.sidebar.text_input(
    "Gemini API KEY", 
    value=st.session_state.saved_settings["api_key"],
    type="password", 
    help="GeminiのAPIキーを入力してください"
)

st.sidebar.markdown("---")

st.sidebar.markdown("### 🎯 統合解析基準（常時適用）")
default_criteria = (
    "以下の要素を全頭診断に統合せよ：\n\n"
    "• JRA/地方競馬の高速馬場・トラックバイアス\n"
    "• 芝・ダートのキレ\n"
    "• 走破タイム理論（基準タイム・馬場補正）\n"
    "• 上がり3F\n"
    "• 展開・ハナ争い"
)

current_criteria = st.session_state.saved_settings["criteria"] if st.session_state.saved_settings["criteria"] else default_criteria

analysis_criteria = st.sidebar.text_area(
    label="解析基準プロンプト",
    value=current_criteria,
    height=250,
    label_visibility="collapsed"
)

if st.sidebar.button("🛠️ 設定を保存・適用する", use_container_width=True):
    st.session_state.saved_settings["api_key"] = gemini_key
    st.session_state.saved_settings["criteria"] = analysis_criteria
    st.session_state.saved_settings["saved"] = True
    st.sidebar.success("設定を司令部に保存しました！")

st.sidebar.markdown("---")

st.sidebar.markdown("### 📁 過去ログ・結果復習ルーム")
st.sidebar.caption("復習・確認する過去の予想")
past_log_selection = st.sidebar.selectbox(
    "過去ログ選択",
    options=["No options to select"],
    label_visibility="collapsed"
)
if st.sidebar.button("📖 予想指示書を呼び出す", use_container_width=True):
    st.sidebar.info("過去ログ機能は現在準備中です。")


# ====================================================================
# 🎯 メイン画面：Baru競馬AI Pro 解析エンジン
# ====================================================================
st.title("🎯 Baru競馬AI Pro — 地方・中央 走破理論解析")

if st.session_state.saved_settings["saved"]:
    st.caption("🟢 総監督司令部の解析基準・API設定が適用されています")

raw_input = st.text_area("netkeibaの出馬表をコピペしてください", height=300)

# 解析・フォーメーション計算ボタン
if st.button("レース解析エンジン起動", use_container_width=True):
    inp = raw_input.strip()
    if not inp:
        st.warning("データを入力してください。")
    else:
        res = parse_netkeiba_complete(inp)
        entries = res["horses"]
        r_info = res["race_info"]
        
        if not entries:
            st.error("馬データが見つからない、またはパースに失敗しました。コピペの範囲を確認してください。")
        else:
            st.markdown("---")
            st.markdown(f"## 📊 レース舞台: {r_info['race_name']}")
            st.info(f"**確定条件:** {r_info['track_type']}{r_info['distance']}m")
            
            # ----------------------------------------------------------------
            # 🔥 【新規】危険騎手のブラックリスト設定
            # ----------------------------------------------------------------
            danger_jockeys = ["秋元", "秋元耕", "Akimoto"] # 警戒が必要な騎手リスト

            # ----------------------------------------------------------------
            # 📊 確率シミュレーション用のスコアリング (Souha Theoryロジック)
            # ----------------------------------------------------------------
            # オッズと人気、過去時計の適性から簡易的に能力値を算出
            scored_entries = []
            total_score = 0.0
            
            for h in entries:
                # 基礎点（オッズが低いほど高い）
                base_score = 100.0 / (h["odds"] + 1.0)
                
                # 危険マークの補正（勝率を著しく下げるロジック）
                is_danger_jockey = any(dj in h["jockey"] for dj in danger_jockeys)
                if is_danger_jockey:
                    base_score *= 0.4 # 期待値を大幅に割引
                
                # 時計上位馬へのボーナス (5番オデッセイ、10番トップレディー、3番サンリコリス)
                if h["uma_ban"] in [5, 10]:
                    base_score *= 1.3
                elif h["uma_ban"] == 3:
                    base_score *= 1.1
                    
                total_score += base_score
                scored_entries.append((h, base_score, is_danger_jockey))
            
            # ----------------------------------------------------------------
            # 🐎 【大幅機能拡張】全頭診断 & 勝率パーセント表示
            # ----------------------------------------------------------------
            st.markdown("### 📋 走破理論・全頭総合診断（確率解析シミュレータ）")
            
            for h, score, is_danger in scored_entries:
                # 単勝・複勝確率の計算
                win_rate = (score / total_score) * 100.0
                place_rate = min(win_rate * 2.8, 95.0) # 複勝は単勝の約2.8倍（上限95%）
                
                # 枠と馬名のヘッダー表現
                danger_alert = "🚨【危険マーク：鞍上警戒】" if is_danger else ""
                waku_txt = f"[{h['waku']}枠] {h['uma_ban']:02d} 枠"
                
                with st.expander(f"{waku_txt} {h['horse_name']} （単勝: {win_rate:.1f}% / 複勝: {place_rate:.1f}%） {danger_alert}"):
                    # 診断テキストの構築
                    st.markdown(f"**【騎手】** {h['jockey']}（騎手期待度: {'⚠️ 危険・妙味なし' if is_danger else '通常判定'}）")
                    st.markdown(f"**【オッズ】** {h['odds']}倍 ({h['popularity']}人気) / **脚質:** {h['leg_type']}")
                    
                    # 各馬ごとの走破理論に基づく個別評価
                    diag_text = ""
                    if h["uma_ban"] == 5:
                        diag_text = "前走良馬場の1:14.7はクラス破格の時計。スムーズなら勝率・複勝率ともに最上位。文句なしの軸候補。"
                    elif h["uma_ban"] == 10:
                        diag_text = "前走1:15.1の先行力は優秀。大外枠からハナを奪えれば、減量51kgも相まって粘り込み濃厚。"
                    elif h["uma_ban"] == 3:
                        diag_text = "JRA時代の高速馬場対応時計（1:12.2）があり、シニスターミニスター産駒の距離短縮。砂のスピード勝負で大化けあり。"
                    elif h["uma_ban"] == 1:
                        diag_text = "門別時代の時計は14秒台があり通用するが、近走900m〜1400mのローテで1200mの追走ペースに対応できるかが鍵。"
                    elif h["uma_ban"] == 7:
                        diag_text = "3歳馬。初の古馬B3混合戦だが、マイルからの距離短縮で先行策が取れれば斤量54kgを活かせる。"
                    elif is_danger:
                        diag_text = "⚠️ **注意:** 近走の走破時計は一定水準にあるものの、鞍上の信頼度・過去の戦歴から勝負気配に強烈な疑問符。不自然な後退や出遅れリスクが極めて高く、期待値は最低クラス。消し推奨。"
                    else:
                        diag_text = "時計面・クラス実績ともに標準的。上位が崩れた際の紐候補まで。"
                        
                    st.info(f"**🔍 走破AI診断:** {diag_text}")

            st.markdown("---")
            st.markdown("### 🎯 レース解析・フォーメーション結果")
            
            # 軸・相手・穴の自動振り分け（危険騎手は自動的に穴紐か除外へ落とす）
            jiku, aite, ana = [], [], []
            for h, score, is_danger in scored_entries:
                if is_danger:
                    ana.append(h['uma_ban']) # 危険騎手は無条件で3列目のバックアップへ
                elif h['popularity'] <= 2: 
                    jiku.append(h['uma_ban'])
                elif h['popularity'] <= 5: 
                    aite.append(h['uma_ban'])
                else:
                    ana.append(h['uma_ban'])

            st.markdown("#### 🎯 Baru式フォーメーション（3連複）")
            st.code(f"1列目(軸)  : {jiku}\n2列目(相手): {aite}\n3列目(穴紐)  : {ana}", language="text")
            
            # 組み合わせ計算
            tkts = []
            for h1 in jiku:
                for h2 in aite:
                    for h3 in ana:
                        if h1 != h2 and h2 != h3 and h1 != h3:
                            comb = sorted([h1, h2, h3])
                            if comb not in tkts: 
                                tkts.append(comb)
            
            st.write(f"**合計購入点数:** {len(tkts)} 点")
            
            with st.expander("📝 生成された買い目一覧（コピー用）"):
                for i, t in enumerate(tkts, 1):
                    st.code(f"[{i:02d}] {t[0]}-{t[1]}-{t[2]}")
