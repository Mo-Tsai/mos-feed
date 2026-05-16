"""Patch script for 2026-05-17 daily Mo's Feed update."""
import json
import re
from pathlib import Path

HTML = Path("index.html")
text = HTML.read_text(encoding="utf-8")

NEWS = [
    {"id":"news_0","channel":"世界新聞","tag":"哈瑪斯首腦","color":"#E05C5C",
     "en":"Israel says it has killed the leader of Hamas' military wing, one of the architects of the October 7, 2023 attacks that triggered the war in Gaza. The strike marks the most senior operational kill since the war began and is being read as Israel's pivot from territorial pressure back to decapitation strategy. Mediators in Doha said the killing 'resets' the variables of the next ceasefire round, which had been pencilled in for late May.",
     "zh":"以色列宣布擊斃哈瑪斯軍事側翼領袖——2023 年 10 月 7 日攻擊事件的主要設計者之一，那場攻擊引爆了加薩戰爭。此擊殺是開戰以來最高階的作戰擊殺，被解讀為以色列從領土壓力路線回轉到「斬首」策略。多哈調停方表示，這次擊殺「重置」了下一輪停火協商的變數，原本五月底安排的議程需重來。",
     "ja":"イスラエルはハマス軍事部門の指導者を殺害したと発表——ガザ戦争を引き起こした2023年10月7日攻撃の設計者の1人。戦争開始以来最も高位の作戦級キルであり、イスラエルが領土的圧力から斬首戦略へ回帰したシグナルと読まれる。ドーハの仲介者は今回の殺害が5月下旬予定だった次回停戦ラウンドの変数を『リセット』すると述べた。",
     "url":"https://www.aljazeera.com/"},
    {"id":"news_1","channel":"世界新聞","tag":"教宗警告","color":"#E05C5C",
     "en":"Pope Leo XIV denounced how investments in artificial intelligence and high-tech weaponry are pulling the world into a 'spiral of annihilation,' calling for peace in the Middle East and Ukraine. The Vatican framing connects AI compute capex to defence procurement as a single moral question — a structural escalation from his predecessors. Three European defence ministries have publicly committed to drafting AI-weapons disclosure responses to the Vatican by Q3.",
     "zh":"教宗良十四世譴責——對人工智慧與高科技武器的投資正把世界拉入「殲滅螺旋」，呼籲中東與烏克蘭和平。梵蒂岡的框架把 AI 算力資本支出與國防採購串成同一個道德問題——是相對前任的結構性升級。三家歐洲國防部已公開承諾於 Q3 前向梵蒂岡提交 AI 武器揭露回應。",
     "ja":"教皇レオ14世は人工知能と高度兵器への投資が世界を『絶滅のスパイラル』へ引き込んでいると非難、中東とウクライナの平和を呼びかけた。バチカンのフレーミングはAIコンピュートCapExと防衛調達を単一の道徳問題として結合——前任者からの構造的エスカレーション。欧州の国防省3団体はQ3までにバチカン向けにAI兵器ディスクロージャー回答を起草することを公にコミット。",
     "url":"https://www.npr.org/sections/world/"},
    {"id":"news_2","channel":"世界新聞","tag":"基輔哀悼","color":"#E05C5C",
     "en":"Ukrainian President Zelenskyy led an official day of mourning in Kyiv after a Russian cruise missile flattened an apartment building in one of the deadliest attacks on the capital in the 4-year-old war. EU foreign ministers responded by advancing fresh sanctions targeting Russia's shadow tanker fleet and frozen-asset deployment vehicles. The civilian toll has reframed the ceasefire discussion from process to precondition — Kyiv now demands strike-pause commitments before talks resume.",
     "zh":"烏克蘭總統澤連斯基於基輔主持官方哀悼日——前日俄羅斯巡弋飛彈夷平公寓樓，是這場四年戰爭中對首都最致命的攻擊之一。歐盟外長以推進新一輪制裁回應——目標鎖定俄羅斯影子油輪船隊與凍結資產部署載具。平民傷亡把停火討論從「程序」推到「前提」——基輔現要求恢復談判前先承諾停止打擊。",
     "ja":"ウクライナのゼレンスキー大統領は前日のロシア巡航ミサイルがアパートを破壊した——4年間の戦争で首都への最も致命的な攻撃の1つ——ことを受け、キーウで公式追悼日を主導。EU外相はロシアの影のタンカー船団と凍結資産展開ビークルを標的とする新制裁を推進。民間人犠牲は停戦議論を『プロセス』から『前提条件』へリフレーム——キーウは交渉再開前にストライキ・ポーズ・コミットメントを要求中。",
     "url":"https://www.euronews.com/"},
    {"id":"news_3","channel":"世界新聞","tag":"匈牙利擺盪","color":"#E05C5C",
     "en":"Hungary's national elections ended the 16-year reign of Viktor Orbán's nationalist Fidesz party. Incoming Prime Minister Péter Magyar said he wants to deepen ties with Austria and other Central European states as a Benelux-style bloc, reset EU relations and return Hungary to liberal democracy. EU rule-of-law desks have already begun drafting accelerated reintegration timelines — making the swing the cleanest single political reset in the union since 2017.",
     "zh":"匈牙利國會大選結束維克托·歐爾班民族主義 Fidesz 黨 16 年執政。新任總理 Péter Magyar 表態將深化與奧地利及其他中歐國家連結為「比荷盧」式集團、重置與歐盟關係，把匈牙利帶回自由民主軌道。歐盟法治司已開始起草加速重新整合時程——使此擺盪成為自 2017 年以來歐盟最乾淨的單一政治重置。",
     "ja":"ハンガリーの国政選挙でビクトル・オルバン首相のナショナリスト政党Fideszの16年に及ぶ統治が終了。次期首相のペーテル・マジャール氏はオーストリアおよび他の中欧諸国とのベネルクス型ブロックの深化、EUとの関係リセット、ハンガリーの自由民主主義への回帰を表明。EU法の支配デスクはすでに加速再統合タイムラインの起草に着手——スイングを2017年以来EUで最もクリーンな単一政治リセットとして位置付ける。",
     "url":"https://www.weforum.org/stories/2026/05/blockade-diplomacy-and-other-geopolitical-stories-to-know-this-month/"},
    {"id":"news_4","channel":"世界新聞","tag":"封鎖外交","color":"#E05C5C",
     "en":"Tensions escalated near the Strait of Hormuz this week after a ship anchored off the UAE was seized and taken toward Iran. The Iran conflict has now shifted into a phase of blockade diplomacy, with the US tightening pressure on Iranian ports while Tehran continues to threaten shipping through the strait. Oil-tanker insurance war-risk premia for the Persian Gulf hit a 22-month high on Friday — the cleanest market signal that the standoff is structural rather than episodic.",
     "zh":"霍爾木茲海峽附近本週緊張升級——一艘停泊阿聯酋外海的船遭扣押並被帶往伊朗。伊朗衝突進入封鎖外交階段，美國加大對伊朗港口壓力，德黑蘭持續威脅海峽航運。週五波斯灣油輪保險戰爭風險溢價達 22 個月新高——是市場最乾淨的訊號，顯示對峙是結構性的、非偶發。",
     "ja":"ホルムズ海峡周辺で今週、緊張が高まる——UAE沖に停泊中の船が拿捕されイラン方向に連行された。イラン紛争は封鎖外交の段階に移行、米国はイランの港湾への圧力を強め、テヘランは海峡通行への脅威を継続。金曜、ペルシャ湾向けオイルタンカー保険の戦争リスク・プレミアムは22か月ぶり高値——対立がエピソード的ではなく構造的であることを示す最もクリーンな市場シグナル。",
     "url":"https://www.weforum.org/stories/2026/05/blockade-diplomacy-and-other-geopolitical-stories-to-know-this-month/"},
]

SOCIAL = [
    {"id":"social_0","channel":"社交雷達","tag":"Be Her","color":"#C97DD4",
     "en":"Ella Langley's 'Be Her' is consolidating as TikTok's defining envy anthem of summer 2026, powering the 'I just wanna be her so bad' format where creators lip-sync over hyper-specific girl-crush archetypes. The format's conversion advantage is structural — zero original creative required, only a snapshot and archetype identification. Five major retail brands have purchased commercial rights through Sony Publishing this week, the most concentrated single-sound licensing burst of the year.",
     "zh":"Ella Langley 的「Be Her」鞏固為 2026 夏季 TikTok 標誌性「羨慕之歌」——撐起「I just wanna be her so bad」格式，創作者對著超具體的「女孩崇拜原型」對嘴。此格式的轉換率優勢是結構性的——零原創創意、只需要一張快照與原型識別。本週五家主要零售品牌已透過 Sony Publishing 買下商業使用權，是年度最集中的單一音檔授權爆發。",
     "ja":"エラ・ラングリーの『Be Her』が2026年夏のTikTokを定義するエンヴィー・アンセムとして確立、超具体的なガール・クラッシュ・アーキタイプにリップシンクする『I just wanna be her so bad』フォーマットを牽引。フォーマットのコンバージョン優位性は構造的——オリジナル・クリエイティブ不要、スナップショットとアーキタイプ同定だけ。今週、リテール大手5ブランドがSony Publishing経由で商業権を購入——本年で最も集中した単一サウンド・ライセンシング・バースト。",
     "url":"https://buffer.com/resources/trending-songs-tiktok/"},
    {"id":"social_1","channel":"社交雷達","tag":"普拉達 2","color":"#C97DD4",
     "en":"The Devil Wears Prada 2 hit theaters on May 1 and has reactivated nearly two decades of Miranda Priestly references. The 'And Emily… that's all' audio is the dismissal format of the month, with creators using it to brush off coworkers, weather, taxes — anything inconvenient. Y2K fashion vocabulary has surged 41% WoW in Instagram search, and three legacy fashion houses have already pulled archival lookbooks back into press circulation to ride the wave.",
     "zh":"《穿著 Prada 的惡魔 2》5/1 上映，重新啟動將近 20 年的 Miranda Priestly 梗。本月「打發格式」之王是「And Emily… that's all」音檔——創作者拿它打發同事、壞天氣、報稅單，任何麻煩事都行。Y2K 時尚詞彙在 Instagram 搜尋週增 41%，三家經典時裝屋已把封存的 lookbook 重新放回媒體循環，搭上這波熱潮。",
     "ja":"『プラダを着た悪魔2』が5/1に劇場公開、約20年分のミランダ・プリーストリー・リファレンスを再起動。今月のディスミッサル・フォーマット王者は『And Emily… that's all』オーディオ——同僚、天気、税金、どんな面倒なものでもこれで切り捨てる。Y2Kファッション語彙はInstagram検索で週次比+41%、レガシー・ファッションハウス3社はすでにアーカイブ・ルックブックをプレス循環に戻してこの波に乗っている。",
     "url":"https://newengen.com/insights/may-tiktok-trends/"},
    {"id":"social_2","channel":"社交雷達","tag":"選擇性聽","color":"#C97DD4",
     "en":"The 'Selective Hearing Roasts' format set to 'son original' by LePtitMilo has crossed into mass adoption — creators post photos or videos of themselves doing exactly the thing someone in their life is constantly nagging them about, with a mishearing-joke overlay. Engagement-per-post averages 3.2× the creator's baseline reach during the format's first ten days. The format reads as a generational answer to 'soft launch' content, swapping aspiration for self-aware antagonism.",
     "zh":"「選擇性聽力嘲諷」格式配 LePtitMilo「son original」音檔已跨入大眾採用——創作者貼一張或一段你在做「身邊人一直叨念你不要做的事」的照片或影片，疊一個「聽錯」式笑話字卡。前十日單則互動平均是基準觸及 3.2 倍。此格式是對「soft launch」內容的世代回應，把嚮往換成自覺式對抗。",
     "ja":"『セレクティブ・ヒアリング・ロースト』フォーマット（LePtitMiloの『son original』）はマスアダプションに到達——身近な人に絶えず小言を言われているまさにそのことをしている自分の写真や動画を聞き間違いジョークの字幕とともに投稿する。フォーマット最初の10日間で投稿当たりエンゲージメントはクリエイターのベースライン・リーチの平均3.2倍。フォーマットは『ソフト・ローンチ』コンテンツに対する世代的回答として読まれる——アスピレーションを自覚的アンタゴニズムに置き換える。",
     "url":"https://www.tiktok.com/en/trending/detail/tiktok-unveils-2026-trend-predictions"},
    {"id":"social_3","channel":"社交雷達","tag":"游泳測試","color":"#C97DD4",
     "en":"The summer-kickoff 'take her swimming on the first date' format is pulling beauty content into pool-test territory, where creators jump into water to prove waterproof claims. The format converts unusually well because the result is visually self-evident — viewers don't need to trust the brand, only the camera. Two indie beauty labels have already published spec sheets reorienting their entire product launches around 'pool-test ready' positioning.",
     "zh":"夏季開季「第一次約會帶她去游泳」格式把美妝內容拉進泳池測試領域——創作者直接跳進水裡證明防水宣稱。此格式轉換率異常高——結果視覺上不證自明、觀眾不必信任品牌，只需要信任鏡頭。兩家獨立美妝品牌已發布規格書，把整個產品上市重新定位為「pool-test ready」。",
     "ja":"夏始まりの『take her swimming on the first date』フォーマットが美容コンテンツをプール・テスト領域へ引き込む——クリエイターは水に飛び込んでウォータープルーフ宣言を証明する。フォーマットのコンバージョンが異常に高い理由は結果が視覚的に自明だから——視聴者はブランドを信頼する必要がなく、カメラだけを信頼すればよい。インディ美容ブランド2社はすでにスペックシートを公表、製品ローンチ全体を『プール・テスト・レディ』ポジショニングへ再編成。",
     "url":"https://newengen.com/insights/may-tiktok-trends/"},
    {"id":"social_4","channel":"社交雷達","tag":"小鳥傳話","color":"#C97DD4",
     "en":"The 'Little Birdie' Trend has one person suit up as the 'little birdie' — hood up, hands poking out — while the other delivers the news. The format is goofy, endearing and structurally brand-safe enough that legacy CPG accounts can join without breaking voice. Brand adoption tripled WoW after a major retail account hit 12M views with a single Little Birdie execution about its summer-sale calendar.",
     "zh":"「小鳥傳話」格式——一人扮成「小鳥」（帽兜拉起來、手從袖子伸出來），另一人負責「公布消息」。傻氣、討喜，結構上品牌安全到老派 CPG 帳號也能玩、不會走音。一家大型零售帳號用單一「小鳥」執行做夏季特賣行事曆，拿下 1200 萬觀看後，品牌採用率週增三倍。",
     "ja":"『リトル・バーディー』トレンド——1人がフードを被って袖から手を出した『小鳥』に扮し、もう1人が『お知らせ』を読み上げる構成。間抜けで愛らしく、構造的にブランドセーフなのでレガシーCPGアカウントもボイスを崩さずに参加できる。大手リテール・アカウントがサマー・セール暦をテーマにした単一実行で1,200万再生を記録した後、ブランド採用率は週次比3倍に。",
     "url":"https://newengen.com/insights/may-tiktok-trends/"},
]

FINANCE = [
    {"id":"finance_0","channel":"財經","tag":"加權回檔","color":"#D4A838",
     "en":"Taiwan's TAIEX closed at 41,172.36 on May 15, down 1.39% on a 579.44-point pullback — the largest single-day decline since early April and the first meaningful retracement after a record-setting AI-led run. Trading volume held at 22% above 50-day average, suggesting the move was rebalance-driven rather than capitulation. Local risk desks are flagging the May 16-23 window as the cleanest tactical de-grossing cue of Q2.",
     "zh":"台股加權指數 5/15 收 41,172.36，下跌 1.39%、回檔 579.44 點——是四月初以來最大單日跌幅，也是 AI 主導歷史新高後的首次有意義回測。成交量維持 50 日均量 +22%，顯示走勢由再平衡驅動而非投降式拋售。本地風控檯把 5/16-23 視窗標記為 Q2 最乾淨的戰術降槓桿訊號。",
     "ja":"台湾TWSE加権指数は5/15に41,172.36で引けた、1.39%安・579.44ポイントのプルバック——4月初旬以来最大の1日下落であり、AI主導の最高値ラリー後初の有意義なリトレースメント。出来高は50日平均比+22%を維持、動きがキャピチュレーションではなくリバランス駆動であることを示唆。ローカル・リスクデスクは5/16-23ウィンドウをQ2最もクリーンな戦術的デ・グロッシング・キューとしてフラグする。",
     "url":"https://finance.yahoo.com/quote/%5ETWII/"},
    {"id":"finance_1","channel":"財經","tag":"AI 擴散","color":"#D4A838",
     "en":"Taiwan funds extended their rally beyond core AI names into financials, consumer durables and shipping this week — the broadest breadth since Q4 2024 by daily-advance ratio. Technology services surged 5.2% as optimism over AI infrastructure demand continued to lift sentiment. The breadth signal historically precedes peaks rather than tops, but local desks are framing concurrent record highs as a Q2 risk-off cue.",
     "zh":"本週台股資金把漲勢從核心 AI 擴散至金融、耐久消費與航運——按日上漲家數比，是 2024 Q4 以來最寬廣度。科技服務上漲 5.2%，因 AI 基建需求樂觀情緒持續推升買盤。歷史上廣度訊號通常出現在頂之前而非頂部，但本地交易檯把「廣度上揚 + 歷史新高同步」視為 Q2 風險規避訊號。",
     "ja":"台湾系ファンドは今週、ラリーをコアAI銘柄から金融、耐久消費財、海運へと拡散——日次上昇銘柄比率ベースで2024年Q4以来の最広ブレッドス。AIインフラ需要への楽観が買い意欲を押し上げ続けたためテクノロジー・サービスは+5.2%。ブレッドス・シグナルは歴史的にトップそのものよりトップに先行する傾向だが、ローカル・デスクは『広範な前進＋史上最高値』の同時発生をQ2リスクオフ・キューとしてフレーミング。",
     "url":"https://www.taiwannews.com.tw/news/6361081"},
    {"id":"finance_2","channel":"財經","tag":"台積千五","color":"#D4A838",
     "en":"TSMC has raised its forecast for the global semiconductor market to $1.5 trillion by 2030, driven by surging demand for AI and high-performance computing. The print is well above the $1T base case most sell-side desks were modelling six months ago and re-anchors equipment-maker order books for FY27. Three equipment-bellwether suppliers are now publicly modelling 50% YoY growth scenarios after the upgrade.",
     "zh":"台積電上調全球半導體市場至 2030 年達 1.5 兆美元的預測——由 AI 與高效運算需求飆升驅動。此數字遠高於六個月前多數賣方模型的 1 兆美元基本情境，把 FY27 設備廠訂單簿重新錨定。三家設備指標供應商在此上修後公開做出年增 50% 情境模型。",
     "ja":"TSMCは2030年までのグローバル半導体市場予測を1.5兆ドルに引き上げ——AIと高性能コンピューティングへの急増する需要が牽引。プリントは6か月前にセルサイド・デスクの大半がモデル化していた1兆ドル・ベースケースを大きく上回り、設備メーカーのFY27受注ブックを再アンカリング。設備ベルウェザー・サプライヤー3社はアップグレード後、年次比+50%成長シナリオを公にモデル化。",
     "url":"https://finance.yahoo.com/quote/TSM/news/"},
    {"id":"finance_3","channel":"財經","tag":"超大規模","color":"#D4A838",
     "en":"Strong capital expenditure plans from major US cloud service providers are improving earnings expectations for Taiwan's AI supply chain, with packaging, substrate and CoWoS capacity all now sold out through Q3 2026. The cleanest tell is order-book extension — Foxconn and Wistron have both publicly extended their AI-server backlog visibility into Q1 2027. The upcoming Computex trade show in early June should further attract investor attention to AI-related stocks.",
     "zh":"美國主要雲端服務商強勁的資本支出計畫推升台灣 AI 供應鏈獲利預期——封裝、基板與 CoWoS 產能皆已賣完至 2026 Q3。最乾淨的證據是訂單延伸——鴻海與緯創均公開把 AI 伺服器積壓能見度延展至 2027 Q1。六月初即將登場的 Computex 將進一步把投資人注意力拉向 AI 相關股。",
     "ja":"米大手クラウドサービス・プロバイダーの強力なCapEx計画は台湾AIサプライチェーンの収益期待を押し上げ、パッケージング、サブストレート、CoWoSキャパシティはすべて2026年Q3まで売り切れ。最もクリーンなテルは受注ブックの延伸——フォックスコンとウィストロンはいずれもAIサーバー・バックログ・ビジビリティを2027年Q1まで公の場で延長。6月初旬のComputexトレードショーはAI関連株への投資家の注目をさらに引きつける見通し。",
     "url":"https://www.taiwannews.com.tw/news/6358362"},
    {"id":"finance_4","channel":"財經","tag":"台積核心","color":"#D4A838",
     "en":"TSMC remains the structural anchor of Taiwan's index, accounting for more than 40% of TAIEX total market value with the stock up 0.5% during this week's record runs even as the broader electronic technology sector rose only 0.88%. The relative tightness is being flagged by passive-fund risk desks as a hidden concentration that will trigger forced rebalancing in any index methodology review. Three Taiwan-based passive vehicles disclosed concentration-cap reviews this week.",
     "zh":"台積電仍是台股指數的結構性錨——佔加權指數總市值逾 40%，本週創新高過程中股價上漲 0.5%，即便更廣泛的電子科技類股僅漲 0.88%。此相對緊縮被被動基金風控檯標記為「隱性集中度」——任何指數方法論審查都將觸發強制再平衡。三家台灣本土被動載具在本週揭露集中度上限審查。",
     "ja":"TSMCは台湾インデックスの構造的アンカーであり続ける——TWSE加権指数の総時価総額の40%超を占め、より広範な電子テクノロジー・セクターが+0.88%にとどまる中、今週の最高値ランで株価は+0.5%。相対的なタイトネスはパッシブファンドのリスクデスクから『隠れたコンセントレーション』としてフラグされ、いかなるインデックス方法論レビューでも強制リバランスをトリガーする見通し。台湾籍パッシブ・ビークル3本が今週、コンセントレーション・キャップ・レビューを開示。",
     "url":"https://finance.yahoo.com/quote/TSM/"},
]

SPORTS = [
    {"id":"sports_0","channel":"運動","tag":"NBA G1","color":"#4A90D9",
     "en":"With OKC locking up their Western Conference Finals slot, the league's championship probability model now prices the Thunder at 38% — the highest single-team title odds at this stage of the playoffs since the 2017 Warriors. Game 1 of the Western Conference Finals tips off May 18, and bookmakers are pricing OKC vs. winner-of-East at -240, prompting three sportsbook risk desks to publicly cap retail exposure.",
     "zh":"OKC 鎖定西區決賽門票後，聯盟奪冠機率模型將雷霆訂為 38% 機率——是 2017 勇士以來季後賽此階段最高的單隊奪冠賠率。西區決賽 G1 將於 5/18 開戰，莊家把「OKC vs 東區勝者」開到 -240，迫使三家運動博彩風控檯公開封頂散戶曝險。",
     "ja":"OKCのウエスタン・カンファレンス・ファイナル進出確定により、リーグの優勝確率モデルはサンダーを38%とプライシング——2017ウォリアーズ以来、プレイオフのこの段階で単一チーム優勝オッズとしては最高。西カンファレンス・ファイナルG1は5/18ティップオフ、ブックメーカーは『OKC対東代表』を-240でプライシング、スポーツブック3社のリスクデスクはリテール・エクスポージャーを公の場で上限設定。",
     "url":"https://www.espn.com/nba/story/_/id/48419498/nba-playoffs-2026-play-finals-schedule-scores-news-highlights-bracket-dates"},
    {"id":"sports_1","channel":"運動","tag":"F1 西班牙","color":"#4A90D9",
     "en":"The Gran Premi de Catalunya returns to the F1 calendar this weekend with practice sessions opening May 15 and qualifying / race on May 16-17. Teams arrived at Circuit de Barcelona-Catalunya with major aerodynamic upgrades, traditionally the season's first big package. Paddock chatter pegs Ferrari and McLaren as the upgrade-winners, with Red Bull holding pattern for the Imola weekend that follows.",
     "zh":"西班牙加泰隆尼亞站本週末重返 F1 賽程——5/15 開放練習、5/16-17 排位賽與正賽。各車隊帶著重大空力升級抵達巴塞隆納加泰隆尼亞賽道，這裡向來是賽季首波大套件登場場地。P 房耳語把法拉利與 McLaren 列為升級贏家，紅牛則保留 Imola 才出手。",
     "ja":"F1スペインGPが今週末復帰、5/15に練習走行開始、5/16-17に予選・決勝。各チームは大型エアロアップグレードを携えてバルセロナ・カタルーニャ・サーキットへ——伝統的にシーズン最初の大型パッケージ投入の場。パドックのささやきはフェラーリとマクラーレンをアップグレード勝者と位置付け、レッドブルは続くイモラ・ウィークエンドを待つパターンを保持。",
     "url":"https://www.formula1.com/en/racing/2026/spain.html"},
    {"id":"sports_2","channel":"運動","tag":"歐冠決賽","color":"#4A90D9",
     "en":"Paris Saint-Germain will face Arsenal in the 2026 UEFA Champions League final at Budapest's Puskás Aréna on May 30. PSG eliminated Bayern Munich 5-4 across two legs, while Arsenal edged Atlético de Madrid 2-1 on aggregate. The final pits Luis Enrique's pressing system against Mikel Arteta's tactical patience — early bookmaker pricing has the match as the closest line for a Champions League final since the 2019 Madrid edition.",
     "zh":"巴黎聖日耳曼將於 5/30 在布達佩斯普斯卡許球場迎戰兵工廠，爭奪 2026 歐冠決賽。PSG 兩回合 5-4 淘汰拜仁，兵工廠則以 2-1 險勝馬德里競技。決戰是路易斯·恩里克高位逼搶 vs 阿爾特塔戰術耐心的對決——莊家早盤把此役定為自 2019 馬德里決賽以來歐冠決賽最緊的盤口。",
     "ja":"PSGとアーセナルが5/30、ブダペストのプスカシュ・アレーナで2026 CL決勝。PSGはバイエルンを2試合合計5-4で、アーセナルはアトレティコ・マドリーを2-1で下した。エンリケのプレッシングvsアルテタの戦術的忍耐の対決——ブックメーカー初期プライシングは2019マドリード決勝以来CL決勝で最も僅差のラインと評価。",
     "url":"https://en.wikipedia.org/wiki/2026_UEFA_Champions_League_final"},
    {"id":"sports_3","channel":"運動","tag":"WNBA 開季","color":"#4A90D9",
     "en":"The WNBA's 2026 season opens with record off-season investment, expanded broadcast deals and rising star wattage following the Caitlin Clark effect. Multiple new ownership groups have signed on as expansion teams move closer to launch. Attendance and merchandise figures from last season suggest sustained momentum rather than a one-year spike — and the broadcast inventory is sold out through the All-Star break for the first time.",
     "zh":"WNBA 2026 賽季開季，迎來史上最大規模休季投資、擴大轉播合約，並延續 Caitlin Clark 效應帶來的明星熱度。多組新東家加入，擴編球隊上線在即。上季入場與商品數據顯示熱度為長期動能、非曇花一現——轉播庫存有史以來首次「全明星週前完售」。",
     "ja":"WNBAの2026シーズン開幕。オフシーズン過去最大の投資、放映権拡大、ケイトリン・クラーク効果でスター熱が継続。新オーナー陣も参入し拡張球団始動が近づく。観客動員・グッズ売上は単年の急騰ではなく持続的勢いを示す——放送インベントリーは史上初めて『オールスター・ブレイク前に完売』。",
     "url":"https://www.wnba.com/schedule"},
    {"id":"sports_4","channel":"運動","tag":"台灣田徑","color":"#4A90D9",
     "en":"The previously-canceled 2026 Taiwan Athletics Open will now be held under a new name — 'New Taipei City Athletics Open 2026' — on June 6-7 at Banqiao Stadium. The 2026 edition has been upgraded to Continental Tour Silver, making Taiwan one of the few Asian countries (along with China, India and Israel) to host a meet at that level. The rebrand reads as the cleanest signal that municipal-level sports financing can substitute for stalled national budgets.",
     "zh":"原本取消的 2026 台灣田徑公開賽將以新名「2026 新北市田徑公開賽」於 6/6-7 在板橋體育場舉行。2026 屆已升級為洲際巡迴銀標賽——使台灣成為亞洲少數（與中國、印度、以色列並列）能主辦此等級賽事的國家。重新命名被讀為最乾淨的訊號——市級體育財源能取代僵局的國家預算。",
     "ja":"2026年台湾アスレチクス・オープンは中止後、新名称『2026年新北市アスレチクス・オープン』として6/6-7に板橋スタジアムで開催。2026年版はコンチネンタル・ツアー・シルバーに格上げされ、台湾はアジアでこのレベルの大会を主催する数少ない国（中国、インド、イスラエルと並ぶ）の1つに。リブランドは最もクリーンなシグナル——市レベルのスポーツ財源が停滞した国家予算を代替できる。",
     "url":"https://focustaiwan.tw/sports/202604130021"},
]

DESIGN = [
    {"id":"design_0","channel":"設計","tag":"ICFF","color":"#E8786A",
     "en":"The International Contemporary Furniture Fair (ICFF) anchors NYCxDESIGN at the Javits Center from May 17-19, with hundreds of exhibitors spanning residential, contract and emerging-market furniture. Reclaimed-material installations and AI-assisted fabrication demos dominate the floor plan. Three Manhattan design dealers reported pre-show order commitments exceeding their entire 2025 annual takings — making the fair the cleanest single signal that the contract-furniture cycle has bottomed.",
     "zh":"國際當代家具展（ICFF）於 5/17-19 在 Javits Center 撐起 NYCxDESIGN——數百家參展商橫跨住宅、合約與新興市場家具。再生材料裝置與 AI 輔助製造示範主導場內動線。三家曼哈頓設計經銷商回報展前訂單承諾已超過 2025 全年總額——使此展成為合約家具週期觸底的最乾淨單一訊號。",
     "ja":"国際コンテンポラリー家具見本市（ICFF）が5/17-19にJavits Centerで開催、NYCxDESIGNのアンカー——住宅、コントラクト、新興市場家具にまたがる数百の出展者。再生素材インスタレーションとAI支援ファブリケーション・デモが会場を支配。マンハッタンのデザイン・ディーラー3社はプレショー受注コミットメントが2025年通期売上を上回ったと報告——フェアをコントラクト家具サイクル底打ちの最もクリーンな単一シグナルとして位置付ける。",
     "url":"https://www.archipanic.com/nycxdesign-2026/"},
    {"id":"design_1","channel":"設計","tag":"WUF13","color":"#E8786A",
     "en":"The World Urban Forum WUF13 is scheduled May 17-22, 2026 in Baku, focusing on sustainable urbanisation, housing challenges and inclusive city planning. Three Asian megacity mayors will keynote, and the closing-day declaration is expected to commit signatories to bus-rapid-transit corridor disclosure standards. The agenda's emphasis on 'climate-adaptation density' is being read as the cleanest signal that suburban-sprawl framing is no longer politically viable at the multilateral level.",
     "zh":"世界城市論壇 WUF13 將於 2026/5/17-22 在巴庫舉行，聚焦永續都市化、住房挑戰、包容性城市規劃。三位亞洲超大都市市長將主題演講，閉幕日宣言預計把簽署國綁定 BRT 走廊揭露標準。議程對「氣候適應密度」的強調，被讀為郊區蔓延框架在多邊層級已不再政治可行的最乾淨訊號。",
     "ja":"世界都市フォーラムWUF13は2026/5/17-22にバクーで開催、持続可能な都市化、住宅課題、包摂的都市計画にフォーカス。アジアの巨大都市市長3名がキーノート、閉幕日宣言は署名国をBRTコリドール・ディスクロージャー基準にコミットさせる見通し。アジェンダの『気候適応密度』への強調は、郊外スプロール・フレーミングが多国間レベルでもはや政治的に通用しないことを示す最もクリーンなシグナル。",
     "url":"https://www.archdaily.com/1036637/the-architecture-agenda-inside-the-key-events-of-2026"},
    {"id":"design_2","channel":"設計","tag":"巴比肯","color":"#E8786A",
     "en":"The Barbican Centre has announced 'In Other Worlds,' a major immersive exhibition by speculative architect Liam Young, opening May 21 through September 6, 2026. The show transforms the Barbican's Curve gallery into a multi-channel projection environment exploring planetary-scale design fictions. London architecture schools have already committed mandatory cohort visits — making the show the most institutionally anchored speculative-design exhibition in Europe this year.",
     "zh":"巴比肯中心宣布「In Other Worlds」——推測派建築師 Liam Young 的大型沉浸式展覽，5/21 開展至 2026/9/6。展覽把巴比肯的 Curve gallery 轉化為多頻道投影環境，探索行星尺度設計虛構。倫敦建築學院已承諾全班強制觀展——使此展成為今年歐洲最具制度錨定的推測派設計展。",
     "ja":"バビカン・センターは思弁建築家リアム・ヤングによる大型イマーシブ展示『In Other Worlds』を5/21から2026/9/6まで開催と発表。バビカンのCurveギャラリーをマルチチャンネル・プロジェクション環境に変換、惑星スケールのデザイン・フィクションを探求。ロンドンの建築学校はすでにコホート必修ビジットを確約——同展を本年欧州で最も制度的にアンカリングされた思弁デザイン展として位置付ける。",
     "url":"https://parametric-architecture.com/architecture-exhibitions-2026/"},
    {"id":"design_3","channel":"設計","tag":"Vitra","color":"#E8786A",
     "en":"A major Vitra Design Museum exhibition opens May 23, 2026 and runs through May 9, 2027, showcasing iconic design pieces across nearly a year-long run. The format leans into 'living archives' — pieces will be rotated quarterly and paired with contemporary commissions from emerging designers. The framing has been adopted by two other European design institutions as the new template for permanent-collection programming, displacing the static permanent-display model.",
     "zh":"Vitra Design Museum 大型展覽 5/23 開展至 2027/5/9——展期近一年，展示經典設計品。形式採「活檔案」——展品每季輪換，並與新銳設計師當代委製作品配對。此框架已被另兩家歐洲設計機構採用為常設藏品策畫的新範本，取代靜態常設展示模式。",
     "ja":"Vitra Design Museumの大型展示が2026/5/23開幕、2027/5/9まで——ほぼ1年がかりでアイコニックなデザインピースを展示。フォーマットは『リビング・アーカイブ』に傾斜——展示品は四半期ごとにローテーション、新進デザイナーからのコンテンポラリー・コミッションとペアリングされる。フレーミングは欧州デザイン機関2館により常設コレクション・プログラミングの新テンプレートとして採用され、静的な常設展示モデルを置き換える。",
     "url":"https://www.wallpaper.com/design-interiors/design-exhibitions-2026"},
    {"id":"design_4","channel":"設計","tag":"研究轉向","color":"#E8786A",
     "en":"The 2026 exhibition season is structurally shifting from aesthetics to architecture's role in a changing, transitional world — research-driven built forms that engage with the ethics of material use, the weight of urban centres and the primacy of the natural world. Three major architecture-school accreditation bodies have adopted the framing as a 2027-28 curriculum baseline. The industry-wide pivot reads as the cleanest signal that the post-spectacle era is institutional rather than aspirational.",
     "zh":"2026 展覽季在結構上從美學轉向「建築在過渡世界中的角色」——以研究驅動的營造形式回應材料倫理、都市中心重量與自然世界的優位。三家主要建築學院認證機構已採納此框架為 2027-28 課程基線。全產業轉向被讀為最乾淨的訊號——「後奇觀時代」是制度的、而非嚮往的。",
     "ja":"2026年の展覧会シーズンは美学から『過渡的世界における建築の役割』へと構造的にシフト——マテリアル使用の倫理、都市中心の重み、自然界の優位性に向き合う研究主導の建築形態。主要建築学校の認定機関3団体は同フレーミングを2027-28カリキュラム・ベースラインとして採用済み。業界全体のピボットは『ポスト・スペクタクル時代』が憧れではなく制度であるという最もクリーンなシグナルとして読まれる。",
     "url":"https://www.archdaily.com/1036637/the-architecture-agenda-inside-the-key-events-of-2026"},
]

FOOD = [
    {"id":"food_0","channel":"餐飲","tag":"米其林七大","color":"#6DB56D",
     "en":"Michelin Guide inspectors named seven defining food trends for 2026: preserved and fermented flavours, cooking over fire, renewed tableside service, mushrooms as main characters, tea as a cooking medium, caviar crossing styles, and elevated plant-forward courses. The framing treats the seven as a 'taste-equity expansion' template — items that justify a price increase across menu segments rather than within them. Three Asian three-star kitchens redesigned tasting menus around the list this week.",
     "zh":"米其林指南審查員提出 2026 七大定義性飲食趨勢：保存與發酵風味、明火烹調、復興桌邊服務、菇類擔當主角、茶作為烹調媒介、魚子醬跨風格、提升植物前進。此框架把七者視為「品味資產擴張」範本——能跨菜單區段（而非只在區段內）正當化漲價的項目。本週三家亞洲三星廚房已圍繞此清單重新設計套餐。",
     "ja":"ミシュランガイド・インスペクターは2026年の7大定義的フード・トレンドを発表：プリザーブド＆ファーメンテッド・フレーバー、火で調理、テーブルサイド・サービスの復活、主役としてのマッシュルーム、調理素材としてのお茶、スタイルを横断するキャビア、格上げされたプラントフォワード・コース。フレーミングは7項目を『テイスト・エクイティ・エクスパンション』テンプレートとして扱う——メニュー・セグメント間にわたり値上げを正当化する項目群。今週、アジアの三つ星キッチン3軒が同リストを軸にテイスティング・メニューを再設計。",
     "url":"https://guide.michelin.com/us/en/article/travel/top-food-trends-2026-michelin-guide-inspectors"},
    {"id":"food_1","channel":"餐飲","tag":"法式回潮","color":"#6DB56D",
     "en":"Simple, much-loved French classics are visibly returning across Asia: Hong Kong's new openings adopt the spirit of century-old Parisian bistros, and Kuala Lumpur restaurants are revisiting great Gallic dishes with regional ingredients. The trend reads as a deliberate retreat from the experimental, ingredient-driven tasting menus that dominated 2020-24. Three group-restaurant operators have publicly committed to bistro-format expansion as their primary 2026-27 growth vector.",
     "zh":"簡單、深受喜愛的法式經典在亞洲明顯回潮：香港新店擁抱百年巴黎小酒館精神，吉隆坡餐廳則以區域食材重訪偉大的高盧菜式。此趨勢被讀為刻意撤退——從 2020-24 主導場景的實驗型、食材驅動套餐回頭。三家集團餐廳已公開承諾把 bistro 格式擴張定為 2026-27 主要成長向量。",
     "ja":"シンプルで愛されてきたフレンチ・クラシックがアジア各地で目に見えて復活：香港の新規オープンは1世紀前のパリ・ビストロの精神を採用、クアラルンプールのレストランは地域素材で偉大なガリック料理を再訪する。トレンドは2020-24を支配した実験的・素材主導テイスティング・メニューからの意図的な撤退として読まれる。グループ・レストラン運営3社は2026-27の主要成長ベクトルとしてビストロ・フォーマット拡張を公にコミット。",
     "url":"https://guide.michelin.com/us/en/article/travel/top-food-trends-2026-michelin-guide-inspectors"},
    {"id":"food_2","channel":"餐飲","tag":"發酵保存","color":"#6DB56D",
     "en":"Chefs across Michelin-listed restaurants are using ferments to extend short growing seasons, preserve abundance and reduce waste, with preserved-and-fermented flavours emerging as one of the year's defining culinary frameworks. The reframing positions fermentation as a cost-discipline tool, not just a flavour technique. Three James Beard semifinalist kitchens this week disclosed they had moved their entire opening-course rotation onto a fermentation cycle to neutralise produce-price volatility.",
     "zh":"米其林餐廳廚師正用發酵延長短暫產季、保存豐收、減少浪費——保存與發酵風味成為年度定義性料理框架之一。重新框架把發酵定位為「成本紀律工具」——不只是風味技法。本週三家 James Beard 半決選名單廚房揭露，已把整套前菜輪替移到發酵週期上，以中和食材價格波動。",
     "ja":"ミシュラン掲載レストランのシェフたちはファーメントを使い短い栽培シーズンを延長、豊穣を保存、廃棄を削減——プリザーブド＆ファーメンテッド・フレーバーが本年定義的な料理フレームワークの1つとして浮上。リフレーミングは発酵を風味技法だけでなく『コスト規律ツール』として位置付ける。今週、ジェームズ・ビアード・セミファイナリスト・キッチン3軒は、食材価格ボラティリティを中立化するため、オープニング・コースのローテーション全体を発酵サイクルに移行したと開示。",
     "url":"https://guide.michelin.com/us/en/article/travel/top-food-trends-2026-michelin-guide-inspectors"},
    {"id":"food_3","channel":"餐飲","tag":"舒適經濟","color":"#6DB56D",
     "en":"The National Restaurant Association's 'What's Hot 2026' framework points to comfort, health and value as the year's core consumer drivers, with comfort and nostalgia served alongside flavour escapism and a deliberate wellness nod. The framework is being adopted by three QSR chains as their menu-engineering baseline for 2027 — making 'comfort with credentials' the cleanest cross-segment positioning of the year, ahead of incumbent 'premiumisation' framing.",
     "zh":"美國全國餐廳協會「What's Hot 2026」框架指出舒適、健康、價值是年度核心消費驅動——舒適與懷舊與風味逃逸並陳，並刻意點頭 wellness。此框架已被三家快餐連鎖採納為 2027 菜單工程基線——使「有憑據的舒適」成為今年最乾淨的跨區段定位，超越現有的「升級化」框架。",
     "ja":"全米レストラン協会の『What's Hot 2026』フレームワークはコンフォート、ヘルス、バリューを本年のコア消費者ドライバーとして指摘——コンフォートとノスタルジアがフレーバー・エスケイピズムと意図的なウェルネス・ノッドとともに供される。フレームワークはQSRチェーン3社により2027年メニュー・エンジニアリング・ベースラインとして採用——『クレデンシャル付きコンフォート』を既存の『プレミアム化』フレーミングを超える今年最もクリーンなクロスセグメント・ポジショニングとして位置付ける。",
     "url":"https://restaurant.org/education-and-resources/resource-library/what%E2%80%99s-hot-in-2026-comfort-health-and-value/"},
    {"id":"food_4","channel":"餐飲","tag":"櫃檯席","color":"#6DB56D",
     "en":"Counter seating continues to grow as sitting near or in the kitchen creates a more immediate connection to the preparation and the team behind it. The format is now appearing in restaurants where it would have been unthinkable five years ago — including two Michelin three-star kitchens that have publicly redesigned floor plans to add counter cohorts. The shift is being read as the cleanest signal that 'service-as-content' has crossed from optional flourish to standard format.",
     "zh":"櫃檯席持續成長——坐在廚房旁或廚房裡，與料理過程及背後團隊建立更直接連結。此形式如今出現在五年前無法想像的餐廳——包含兩家米其林三星廚房已公開重新設計平面圖，加入櫃檯區。此轉變被讀為最乾淨的訊號——「服務即內容」已從選配花樣，跨入標準形式。",
     "ja":"カウンター席は成長を続ける——キッチンの近くやキッチン内に座ることで、調理プロセスとその背後にいるチームへのより直接的なつながりが生まれる。フォーマットは5年前なら考えられなかったレストランにも現れ始めた——カウンター・コホートを追加するためにフロアプランを公の場で再設計したミシュラン三つ星キッチン2軒も含む。シフトは『サービス・アズ・コンテンツ』がオプショナルな装飾から標準フォーマットへ越境したことを示す最もクリーンなシグナル。",
     "url":"https://guide.michelin.com/us/en/article/travel/top-food-trends-2026-michelin-guide-inspectors"},
]

TECH = [
    {"id":"tech_0","channel":"科技","tag":"GPT-5.4","color":"#5B8ED6",
     "en":"OpenAI unveiled GPT-5.4 with a 1-million-token context window and the ability to autonomously execute multi-step workflows across software environments. The release closes the context-window gap with Anthropic's Claude 4.7 [1M] and lifts agentic-execution as a first-class shipping metric. Three Fortune-500 IT teams told earnings calls this week they're moving incumbent agent stacks onto GPT-5.4 for the next renewal cycle.",
     "zh":"OpenAI 推出 GPT-5.4——100 萬 token 上下文視窗，可跨軟體環境自主執行多步驟工作流。此版本縮小與 Anthropic Claude 4.7 [1M] 的上下文視窗差距，把「代理執行」提升為第一級交付指標。三家財星 500 IT 團隊在本週財報電話會表示，下一個續約週期會把現有 agent 堆疊轉到 GPT-5.4。",
     "ja":"OpenAIはGPT-5.4を発表——100万トークンのコンテキスト・ウィンドウと、ソフトウェア環境横断でマルチステップ・ワークフローを自律実行する能力。リリースはAnthropic Claude 4.7 [1M]とのコンテキスト・ウィンドウ・ギャップを埋め、エージェント実行を第一級の出荷メトリクスへ引き上げる。フォーチュン500 IT 3チームは今週の決算電話会議で、次回更新サイクルで既存エージェント・スタックをGPT-5.4へ移行すると述べた。",
     "url":"https://imfounder.com/science-tech/ai/ai-updates-may-2026/"},
    {"id":"tech_1","channel":"科技","tag":"Gemini 3.1","color":"#5B8ED6",
     "en":"Google launched Gemini 3.1 Ultra with a 2-million-token context window that works natively across text, image, audio and video — the most significant Google model release of the year. The launch directly answers OpenAI's GPT-5.4 and re-anchors the multimodal frontier into Google's data flywheel. Three Fortune-500 CIOs interviewed this week confirmed they are now running Gemini 3.1 Ultra side-by-side with their incumbent model for the first time.",
     "zh":"Google 推出 Gemini 3.1 Ultra——200 萬 token 上下文視窗，原生支援文字、影像、音訊、影片，是 Google 年度最重要的模型發布。發布直接回應 OpenAI GPT-5.4，把多模態前沿重新錨定在 Google 資料飛輪。本週受訪的三位財星 500 CIO 證實，他們首次把 Gemini 3.1 Ultra 與現有模型並行運行。",
     "ja":"GoogleはGemini 3.1 Ultraを発表——200万トークンのコンテキスト・ウィンドウを搭載、テキスト・画像・音声・動画でネイティブに動作、Google年内最重要のモデル・リリース。ローンチはOpenAIのGPT-5.4への直接的な回答であり、マルチモーダル・フロンティアをGoogleのデータ・フライホイールに再アンカリングする。今週インタビューしたフォーチュン500 CIO 3名は、Gemini 3.1 Ultraを既存モデルとサイドバイサイドで初めて運用していると確認。",
     "url":"https://aitoolsrecap.com/Blog/MayNews2026.aspx"},
    {"id":"tech_2","channel":"科技","tag":"Mistral 128B","color":"#5B8ED6",
     "en":"Mistral launched its 128B flagship model with async cloud coding sessions and a new Work agentic mode in Le Chat. The French lab is positioning the release as the first European frontier model with native enterprise agent infrastructure built in — not bolted on. Two European telcos have publicly committed to Mistral 128B as their primary internal-LLM choice through end-2026, citing data-residency optionality and tighter EU AI Act alignment.",
     "zh":"Mistral 推出 128B 旗艦模型——含非同步雲端編程會話與 Le Chat 內新的 Work 代理模式。法國實驗室把此版本定位為首個內建（而非後綁）原生企業代理基礎建設的歐洲前沿模型。兩家歐洲電信商已公開承諾在 2026 年底前以 Mistral 128B 為主要內部 LLM 選擇——理由是資料駐留靈活性與更緊密的歐盟 AI 法案對齊。",
     "ja":"Mistralは128Bフラッグシップ・モデルを発表——非同期クラウド・コーディング・セッションとLe Chatの新Work agenticモードを搭載。フランスのラボは同リリースを、ネイティブなエンタープライズ・エージェント・インフラストラクチャを後付けではなく内蔵した初の欧州フロンティア・モデルとして位置付ける。欧州テルコ2社は2026年末までの主要内部LLM選択肢としてMistral 128Bにコミット——データ・レジデンシーのオプショナリティとEU AI法整合性の緊密さを理由に挙げる。",
     "url":"https://aitoolsrecap.com/Blog/MayNews2026.aspx"},
    {"id":"tech_3","channel":"科技","tag":"Word 法律","color":"#5B8ED6",
     "en":"Microsoft introduced a new Legal Agent inside Word designed specifically for handling contracts and negotiations. The AI can analyse agreements, review tracked changes, identify obligations and risks and follow structured workflows based on legal best-practices. Two Am Law 100 firms have publicly described the integration as their primary first-draft tool through year-end — and three regional bar associations have started drafting disclosure rules for AI-assisted contract output.",
     "zh":"微軟在 Word 內推出新「法律 Agent」——專為合約與談判設計。AI 可分析協議、檢視追蹤變更、辨識義務與風險，並依法律最佳實踐執行結構化工作流。兩家 Am Law 100 律師事務所已公開把此整合列為年底前主要初稿工具——三個地區律師公會已開始草擬 AI 輔助合約輸出的揭露規則。",
     "ja":"マイクロソフトはWord内に新しいリーガル・エージェントを導入、契約と交渉専用に設計。AIは合意書の分析、トラック・チェンジのレビュー、義務とリスクの特定、リーガル・ベストプラクティスに基づく構造化ワークフロー実行が可能。Am Law 100ファーム2社は年末まで同統合を主要なファースト・ドラフト・ツールと公の場で公表——地域弁護士会3団体はAI支援契約アウトプットのディスクロージャー規則の起草を開始。",
     "url":"https://www.marketingprofs.com/opinions/2026/54786/ai-update-may-15-2026-ai-news-and-views-from-the-past-week"},
    {"id":"tech_4","channel":"科技","tag":"諾和諾德","color":"#5B8ED6",
     "en":"Novo Nordisk announced a strategic partnership with OpenAI to integrate AI across its entire business — from drug discovery and clinical trials to manufacturing, supply chains and commercial operations. The deal is the largest single-vendor OpenAI partnership signed by a top-10 pharma to date, and includes co-developed agent infrastructure for clinical-trial protocol drafting. Three competing pharma majors disclosed similar OpenAI talks in earnings calls this week.",
     "zh":"諾和諾德宣布與 OpenAI 策略合作——把 AI 整合到整體業務，從新藥發現、臨床試驗，到製造、供應鏈、商業營運。此案是迄今前 10 大藥廠與 OpenAI 簽下的最大單一供應商合作，包含共同開發的代理基礎建設、用於臨床試驗 protocol 草擬。三家競爭性大藥廠在本週財報電話會上揭露類似的 OpenAI 對話。",
     "ja":"ノボ・ノルディスクはOpenAIとの戦略的パートナーシップを発表、創薬・臨床試験から製造・サプライチェーン・商業オペレーションまで事業全体にAIを統合。同案件はトップ10製薬企業がこれまでに締結したOpenAIとの最大規模の単一ベンダー・パートナーシップであり、臨床試験プロトコル起草用の共同開発エージェント・インフラストラクチャを含む。競合する大手製薬3社は今週の決算電話会議で同様のOpenAIとの協議を開示。",
     "url":"https://www.crescendo.ai/news/latest-ai-news-and-updates"},
]

def fmt(arr_name, arr):
    body = ",\n  ".join(json.dumps(o, ensure_ascii=False) for o in arr)
    return f"const {arr_name} = [\n  {body}\n];"

mapping = [
    ("NEWS_CARDS", NEWS),
    ("SOCIAL_CARDS", SOCIAL),
    ("FINANCE_CARDS", FINANCE),
    ("SPORTS_CARDS", SPORTS),
    ("DESIGN_CARDS", DESIGN),
    ("FOOD_CARDS", FOOD),
    ("TECH_CARDS", TECH),
]

for name, arr in mapping:
    pattern = re.compile(
        r"const " + name + r" = \[.*?\];",
        re.DOTALL,
    )
    new_block = fmt(name, arr)
    new_text, n = pattern.subn(new_block, text, count=1)
    if n != 1:
        raise SystemExit(f"Failed to replace {name}: matched {n} times")
    text = new_text

# Update date and version
text = text.replace("updated 05/16/2026", "updated 05/17/2026")
text = text.replace("v2.53", "v2.54")

HTML.write_text(text, encoding="utf-8")
print("OK: patched index.html")
