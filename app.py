import pandas as pd


def generate_barus_formation(race_data, data_analysis_top3):
    """バル式・データ分析救済型フォーメーション生成ロジック

    Args:
        race_data (pd.DataFrame): 馬番、馬名、AIスコア、脚質などのデータ
        data_analysis_top3 (list): netkeibaデータ分析画面の上位3頭の馬番
    """
    print("=== バル式・走破AI 馬券構築システム ===")
    print(f"【netkeibaデータ分析上位馬】: {data_analysis_top3}\n")

    # 1. AIスコア順にソート
    df_sorted = race_data.sort_values(by="ai_score", ascending=False).copy()

    # 2. 基本的な軸・相手・ヒモの選定（走破タイムAIのスコアベース）
    # スコア上位2頭を「軸候補」
    jiku_candidates = df_sorted.iloc[0:2]["uma_ban"].tolist()
    # スコア3〜4番手を「相手候補」
    aite_candidates = df_sorted.iloc[2:4]["uma_ban"].tolist()
    # スコア5〜9番手を「ヒモ候補」
    himo_candidates = df_sorted.iloc[4:9]["uma_ban"].tolist()

    print(f" [AI初期診断] 軸: {jiku_candidates}, 相手: {aite_candidates}, ヒモ: {himo_candidates}")

    # 3. 🔥【今回の教訓ロジック】データ分析上位馬の強制救済
    saved_horses = []
    all_selected = set(jiku_candidates + aite_candidates + himo_candidates)

    for uma in data_analysis_top3:
        if uma not in all_selected:
            # どこにも選ばれていない場合、強制的にヒモ（3列目）に追加
            himo_candidates.append(uma)
            saved_horses.append(uma)

    if saved_horses:
        print(f" ⚠️【データ救済発動】分析上位馬 {saved_horses} をヒモに強制追加しました。")
    else:
        print(" ✨ データ分析上位馬はすべてAI推奨馬に含まれています。")

    # 4. 最終的なフォーメーションの出力
    print("\n=== 最終推奨フォーメーション（3連複/3連単） ===")
    print(f" 1列目（軸）  : {jiku_candidates}")
    print(f" 2列目（相手）: {aite_candidates}")
    print(f" 3列目（ヒモ）: {himo_candidates}")


# ==========================================
# 船橋7Rを模したテストデータでの実行
# ==========================================
if __name__ == "__main__":
    # 模擬出走馬データ（AIスコアは走破タイム理論に基づく算出値と仮定）
    # 12番ゼンダンクラージュは近走不振でAIスコアが低かった状態を再現
    data = {
        "uma_ban": [1, 4, 7, 8, 9, 10, 11, 12, 13, 14],
        "uma_name": [
            "ウインアザレア",
            "リュウノアスリート",
            "サンタアナウインド",
            "シンキングファーザ",
            "ジョーエスポワール",
            "コスモミツボシ",
            "アイディアル",
            "ゼンダンクラージュ",
            "リアルガチ",
            "ヴィクトリーロワ",
        ],
        "ai_score": [
            65.2,
            58.0,
            78.5,
            82.1,
            61.4,
            72.0,
            55.3,
            42.1,
            80.3,
            59.8,
        ],  # 12番は下位
    }

    race_df = pd.DataFrame(data)

    # スクリーンショット 2026-06-02 175349.png にあった「データ上位3頭」の馬番を入力
    # ※ 船橋7Rの画面より：1番、10番、12番
    netkeiba_top3 = [1, 10, 12]

    # フォーメーション生成
    generate_barus_formation(race_df, netkeiba_top3)
