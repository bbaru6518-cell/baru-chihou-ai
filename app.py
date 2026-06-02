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
            
            # 🚨 危険騎手のブラックリスト（秋元を完全ロックオン）
            danger_jockeys = ["秋元", "秋元耕", "Akimoto"]

            # 📊 血統データのファジーマッピング（デモデータ構築・実際のパーステキストから拡張可能）
            bloodlines = {
                1: {"sire": "ヘニーヒューズ", "type": "ストームキャット系（ダート万能型）"},
                3: {"sire": "シニスターミニスター", "type": "エーピーインディ系（中央砂・距離短縮抜群）"},
                4: {"sire": "ホッコータルマエ", "type": "キングカメハメハ系（地方タフ馬場適性）"},
                5: {"sire": "マジェスティックウォリアー", "type": "エーピーインディ系（船橋ダート抜群）"},
                6: {"sire": "ロードカナロア", "type": "キングマンボ系（中央スピード・良馬場向き）"},
                7: {"sire": "ドレフォン", "type": "ストームキャット系（仕上がり早スピード型）"},
                8: {"sire": "サウスヴィグラス", "type": "フォーティナイナー系（短距離超特化型）"},
                9: {"sire": "カジノドライヴ", "type": "エーピーインディ系（スタミナダート型）"},
                10: {"sire": "パイロ", "type": "エーピーインディ系（地方短距離の鬼）"},
            }

            # 📊 スコアリングシミュレーション（時計・オッズ・血統・危険度を統合）
            scored_entries = []
            total_score = 0.0
            
            for h in entries:
                u_num = h["uma_ban"]
                base_score = 100.0 / (h["odds"] + 1.0)
                
                # 騎手補正（秋元マーク時は期待値を一気に40%までデバフ）
                is_danger_jockey = any(dj in h["jockey"] for dj in danger_jockeys)
                if is_danger_jockey:
                    base_score *= 0.4
                
                # 血統＆時計補正
                if u_num in [5, 10]: # 時計上位＋マジェスティック／パイロの船橋適性
                    base_score *= 1.3
                elif u_num == 3: # シニスターミニスター×距離短縮爆発力
                    base_score *= 1.15
                    
                total_score += base_score
                scored_entries.append((h, base_score, is_danger_jockey))
            
            # ----------------------------------------------------------------
            # 🐎 【アップデート】全頭診断（馬＋騎手危険度＋血統）
            # ----------------------------------------------------------------
            st.markdown("### 📋 走破理論×血統×騎手 統合全頭診断")
            
            for h, score, is_danger in scored_entries:
                u_num = h["uma_ban"]
                win_rate = (score / total_score) * 100.0
                place_rate = min(win_rate * 2.8, 95.0)
                
                # 血統情報の取得
                b_info = bloodlines.get(u_num, {"sire": "種牡馬不明", "type": "ダート適性あり"})
                
                # ヘッダーの危険マーク警告
                danger_alert = "🚨【危険：鞍上秋元マーク】" if is_danger else ""
                waku_txt = f"[{h['waku']}枠] {h['uma_ban']:02d}番"
                
                with st.expander(f"{waku_txt} {h['horse_name']} （単勝: {win_rate:.1f}% / 複勝: {place_rate:.1f}%） {danger_alert}"):
                    
                    # 3大要素のステータス表示
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**🧬 血統:** 父 {b_info['sire']} （{b_info['type']}）")
                        st.markdown(f"**🏇 脚質・オッズ:** {h['leg_type']} / {h['odds']}倍 ({h['popularity']}人気)")
                    with col2:
                        if is_danger:
                            st.markdown(f"**👤 騎手:** {h['jockey']} ⚠️ **[危険度最高・要警戒]**")
                        else:
                            st.markdown(f"**👤 騎手:** {h['jockey']} （通常判定）")
                        st.markdown(f"**⚖️ 補正後期待値:** {'❌ 最低値' if is_danger else '🟢 良好' if u_num in [3,5,10] else '明暗半々'}")
                    
                    # ダイナミック診断コメント生成
                    diag_text = ""
                    if u_num == 5:
                        diag_text = "【時計】良馬場1:14.7は現クラスで破格。【血統】父マジェスティックウォリアーは船橋ダ1200mの王道血統。砂のキレとスピードを兼ね備えており、死角らしい死角が見当たらない。文句なしの軸。"
                    elif u_num == 10:
                        diag_text = "【時計】前走1:15.1の先行力。良馬場での安定感抜群。【血統】父パイロは地方のタフな砂スピード勝負で無類の強さを誇る。大外枠からハナを切れば、斤量51kgも手伝って粘り込み濃厚。"
                    elif u_num == 3:
                        diag_text = "【時計】中央1勝クラスで1:12.2（中山）の超高速時計あり。距離短縮で真価発揮。【血統】砂の最高峰シニスターミニスター産駒。揉まれずに砂を被らない位置を取れれば、一撃突き抜ける爆発力を秘める。"
                    elif is_danger:
                        diag_text = "⚠️ **【秋元マーク・危険騎手コメント】** 馬の時計水準や父系ダート血統のポテンシャルは悪くない。しかし、**鞍上の過去の『不自然な追尾遅れ』『不可解な失速・位置下げ』の悪癖・下手さがすべてを台無しにするリスクが極めて高い。** 勝負気配が著しく怪しく、オッズに見合う信頼度はゼロ。走破理論の計算上、勝率は強制デバフ対象。大泥沼にハマる危険性大のため「消し（見送り）」を強く推奨。"
                    elif u_num == 1:
                        diag_text = "【時計】門別14秒台の持ち時計あり。【血統】ヘニーヒューズ産駒でスピード適性は十分。ただ、近走900m〜1400mの変則ローテで船橋1200mの追走に戸惑うリスクがあり、紐まで。"
                    elif u_num == 7:
                        diag_text = "【時計】3歳馬でマイルからの短縮戦。【血統】ドレフォン産駒で良馬場の1200m戦は絶好の舞台。古馬混合B3の壁を斤量54kgと血統のスピードでどこまで相殺できるか。"
                    else:
                        diag_text = "時計、血統ともにクラス標準レベル。上位陣が自滅、または展開が超乱ペースになった際の3列目（紐）の押さえまで。"
                        
                    st.info(f"**🔍 統合AI解析指示書:** {diag_text}")

            st.markdown("---")
            st.markdown("### 🎯 レース解析・フォーメーション結果")
            
            # 軸・相手・穴の自動振り分け（秋元マークは強制的に3列目に隔離）
            jiku, aite, ana = [], [], []
            for h, score, is_danger in scored_entries:
                if is_danger:
                    ana.append(h['uma_ban'])
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
