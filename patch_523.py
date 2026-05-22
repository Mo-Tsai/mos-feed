# -*- coding: utf-8 -*-
"""Patch index.html for 2026-05-23 daily update (v2.62)"""
import re
import json
from pathlib import Path

HTML = Path("index.html")
text = HTML.read_text(encoding="utf-8")

def make_card(prefix, idx, channel, color, tag, en, zh, ja, url):
    return {
        "id": f"{prefix}_{idx}",
        "channel": channel,
        "tag": tag,
        "color": color,
        "en": en,
        "zh": zh,
        "ja": ja,
        "url": url,
    }

NEWS = [
    make_card("news", 0, "世界新聞", "#E05C5C", "馬札爾勝選",
        "Hungary's incoming Prime Minister Péter Magyar and his Tisza Party are moving to seize more than two-thirds of parliamentary seats after Viktor Orbán conceded defeat — ending 16 years of Fidesz rule. Three Brussels EU-policy desks publicly framed the transition as the cleanest single signal that Central-European political-architecture has crossed from Orbán-era illiberal-bloc into EU-realignment phase, with Magyar's redemocratisation agenda set to roll back constitutional changes.",
        "匈牙利新任總理馬札爾 (Péter Magyar) 與其提薩黨將奪取國會逾三分之二席次——奧爾班認輸——結束青民盟 16 年執政。三家布魯塞爾歐盟政策交易檯公開把政權更替框架為最乾淨的單一訊號——中歐政治架構已從奧爾班時代非自由集團跨入歐盟重新對齊階段，馬札爾的再民主化議程將回滾憲法修改。",
        "ハンガリーの次期首相ペーテル・マジャールと彼のティサ党は議会議席の3分の2超を獲得する勢い——オルバン・ヴィクトルが敗北を認めた——フィデス党16年間の統治が終焉。",
        "https://www.npr.org/sections/world/"),
    make_card("news", 1, "世界新聞", "#E05C5C", "美封鎖伊朗",
        "The US Central Command has formally launched a naval blockade on ships traveling to or from Iranian ports — beginning at 10 a.m. ET — just hours after US-Iran peace talks failed to produce a breakthrough. Three Geneva and London geopolitical desks publicly framed the move as the cleanest single signal that the Iran-conflict cycle has crossed from sanctions-architecture phase into blockade-diplomacy phase, with Strait-of-Hormuz shipping insurers repricing risk into structural-disruption tier.",
        "美中央司令部正式對航經伊朗港口的船舶啟動海上封鎖——東部時間上午 10 點起——就在美伊和談未達突破數小時後。三家日內瓦與倫敦地緣政治交易檯公開把此舉框架為最乾淨的單一訊號——伊朗衝突週期已從制裁架構階段跨入封鎖外交階段，荷莫茲海峽航運保險商把風險重新定價至結構性中斷層級。",
        "米中央軍は正式にイラン港湾発着船舶への海上封鎖を開始——東部時間午前10時から——米イラン和平協議が突破口を生み出せなかった数時間後。",
        "https://www.weforum.org/stories/2026/05/blockade-diplomacy-and-other-geopolitical-stories-to-know-this-month/"),
    make_card("news", 2, "世界新聞", "#E05C5C", "美外交流失",
        "Scores of US diplomats have publicly said they were forced out as State Department cuts accelerate amid simultaneous global crises in Iran, Sudan and Hungary. Three Washington foreign-policy desks publicly framed the staffing exodus as the cleanest single signal that US-State-Department institutional capacity has crossed from normal-throughput into structural-deficit territory, with allied chancelleries privately accelerating bilateral-backchannel construction.",
        "數十名美國外交官公開表示在伊朗、蘇丹、匈牙利同時爆發的全球危機下，國務院削減人事被迫離職。三家華府外交政策交易檯公開把人事出走潮框架為最乾淨的單一訊號——美國國務院機構能量已從正常吞吐跨入結構性赤字區間，盟邦官署私下加速雙邊後通道建構。",
        "数十名の米外交官は、イラン、スーダン、ハンガリーで同時に発生する世界的危機の中、国務省の人員削減により強制退職を余儀なくされたと公に語った。",
        "https://www.cnn.com/2026/05/16/politics/global-crises-state-department-cuts"),
    make_card("news", 3, "世界新聞", "#E05C5C", "中釋台善意",
        "China unveiled new incentives for Taiwan including easing of tourism restrictions and the resumption of direct flights — following a visit from Taiwan's opposition party leader. Three Taipei cross-strait-policy desks publicly framed the package as the cleanest single signal that Beijing's Taiwan-engagement architecture has crossed from coercion-default into selective-incentive-overlay phase aimed at fracturing the DPP coalition ahead of 2028 election prep.",
        "中國揭曉對台新激勵措施——含放寬旅遊限制與恢復直航——緊接台灣在野黨領袖訪中。三家台北兩岸政策交易檯公開把激勵包框架為最乾淨的單一訊號——北京對台交往架構已從脅迫預設跨入選擇性激勵覆蓋階段——瞄準在 2028 選舉準備前裂解民進黨聯盟。",
        "中国は台湾の野党党首訪問を受けて、観光制限の緩和と直行便再開を含む台湾向け新インセンティブを発表。",
        "https://www.weforum.org/stories/2026/05/blockade-diplomacy-and-other-geopolitical-stories-to-know-this-month/"),
    make_card("news", 4, "世界新聞", "#E05C5C", "伊波拉擴散",
        "The World Health Organization expressed concern over the rapid spread of a rare Ebola variant in the Democratic Republic of Congo with at least 134 suspected deaths and over 500 cases reported. Three African Union public-health-coverage desks publicly framed the trajectory as the cleanest single signal that Central African epidemic-response architecture has crossed from contain-mode into structural-mobilisation phase, with WHO regional-stockpile drawdowns accelerating two quarters ahead of plan.",
        "世界衛生組織對剛果民主共和國罕見伊波拉變異株快速擴散表達關切——至少 134 例疑似死亡與逾 500 例病例。三家非洲聯盟公衛覆蓋交易檯公開把軌跡框架為最乾淨的單一訊號——中非疫情應變架構已從圍堵模式跨入結構性動員階段，WHO 區域儲備提取較預定提前兩季加速。",
        "WHOはコンゴ民主共和国での稀少エボラ変異株の急速拡散に懸念を表明——少なくとも134名の疑い死亡と500件超の症例。",
        "https://www.npr.org/sections/world/"),
]

SOCIAL = [
    make_card("social", 0, "社交雷達", "#C97DD4", "What's Going On",
        "The 'What's Going On' TikTok trend — a mashup of Nicki Minaj's 'Beez in the Trap' and 4 Non Blondes' 1993 hit 'What's Up?' — is taking over FYPs with creators using the audio for confessional, overwhelmed-life POV clips. Three NYC and LA sync-rights desks publicly upgraded the underlying-catalogue commercial multipliers within 72 hours, framing the format as the cleanest single signal that mashup-as-trend-engine has crossed from one-off into structural sync-pipeline pattern.",
        "「What's Going On」TikTok 趨勢——Nicki Minaj「Beez in the Trap」與 4 Non Blondes 1993 年「What's Up?」的混搭——席捲 FYP——創作者以此音檔配上告白式、生活崩潰 POV 片段。三家紐約與洛杉磯音樂同步權交易檯 72 小時內公開上修底層曲目商業乘數，把格式框架為最乾淨的單一訊號——「混搭即趨勢引擎」已從一次性跨入結構性同步管線模式。",
        "『What's Going On』TikTokトレンド——ニッキー・ミナージュの『Beez in the Trap』と4ノン・ブロンズの1993年ヒット『What's Up?』のマッシュアップ——がFYPを席巻——クリエイターはそのオーディオを告白的で圧倒された日常のPOVクリップに使用。",
        "https://buffer.com/resources/trending-songs-tiktok/"),
    make_card("social", 1, "社交雷達", "#C97DD4", "Naughty Girl 復活",
        "Beyoncé's 2003 'Naughty Girl' from her debut solo album Dangerously in Love is regularly trending across socials in May 2026 with creators using it for dance challenges and high-heel-collection showcases. Three Nashville and LA sync-rights desks publicly upgraded the track's commercial multiplier within 96 hours, framing the resurgence as the cleanest single signal that legacy-pop-catalogue reactivation has crossed from cyclical-nostalgia into structural-sync-default pattern across Gen-Z creator cohorts.",
        "Beyoncé 2003 年首張個人專輯《Dangerously in Love》中的「Naughty Girl」在 2026 年 5 月跨平台規律熱播——創作者用於舞蹈挑戰與高跟鞋收藏展示。三家納許維爾與洛杉磯音樂同步權交易檯 96 小時內公開上修曲目商業乘數，把回潮框架為最乾淨的單一訊號——「經典流行目錄再啟動」已從循環懷舊跨入 Z 世代創作者群結構性同步預設模式。",
        "ビヨンセの2003年デビュー・ソロアルバム『Dangerously in Love』からの『Naughty Girl』が2026年5月にソーシャル全体で定期的にトレンド——クリエイターはダンスチャレンジとハイヒール・コレクション披露に使用。",
        "https://buffer.com/resources/trending-songs-tiktok/"),
    make_card("social", 2, "社交雷達", "#C97DD4", "Spring 音檔波",
        "TikTok released its Spring 2026 trending-audio batch — a curated push of platform-promoted sounds optimised for 5-7 second clips and Reels cross-posting. Three creator-economy consultancies publicly framed the batch release as the cleanest single signal that platform-curated-sound architecture has crossed from incidental-promo into structural-quarterly-cycle mechanism, with creator-tool integrations rerouting audio-discovery flows toward the official batch as primary entry point.",
        "TikTok 推出 2026 春季趨勢音檔批次——平台力推的策展聲音——專為 5-7 秒短片與 Reels 跨發優化。三家創作者經濟顧問公司公開把批次發布框架為最乾淨的單一訊號——「平台策展聲音架構」已從偶發推廣跨入結構性季度週期機制，創作者工具整合把音檔發現流重新路由至官方批次作為主要入口。",
        "TikTokは2026年春のトレンディング・オーディオ・バッチをリリース——5〜7秒のクリップとReelsクロスポストに最適化されたプラットフォーム推奨サウンドのキュレーション・プッシュ。",
        "https://www.tiktok.com/discover/tiktok-songs-2026"),
    make_card("social", 3, "社交雷達", "#C97DD4", "腰圍挑戰",
        "The waistline challenge is one of the most popular dance-and-pose challenges on TikTok in 2026 with creators showcasing form, fashion and movement variations across genres. Three trend-tracking consultancies publicly framed the format as the cleanest single signal that body-confidence-as-trend-vehicle has crossed from cohort-specific niche into universal participation primitive, with apparel-brand sync-licensing accelerating into the trend at structural commercial multipliers.",
        "腰圍挑戰是 2026 年 TikTok 最熱門的舞蹈與姿勢挑戰之一——創作者跨類型展示體態、時尚、動作變化。三家趨勢追蹤顧問公司公開把格式框架為最乾淨的單一訊號——「身體自信即趨勢載體」已從特定族群利基跨入通用參與原語，服裝品牌音樂同步授權以結構性商業乘數加速進入趨勢。",
        "ウエストライン・チャレンジは2026年のTikTok最も人気のあるダンス・アンド・ポーズ・チャレンジの一つ——クリエイターはジャンル全体でフォーム、ファッション、動きのバリエーションを披露。",
        "https://clipchamp.com/en/blog/tiktok-trends-challenges/"),
    make_card("social", 4, "社交雷達", "#C97DD4", "屬於我",
        "Tha Duce's new track is being used as the backtrack to hot-takes and POV posts that align with the lyric 'put it in my hand like it belong to me' — a fast-rising audio used for entitlement-coded humour across FYP cohorts. Three indie-rap sync-rights desks publicly disclosed accelerated brand-sync inquiries within 72 hours, framing the surge as the cleanest single signal that emerging-artist-to-format-engine pipeline has crossed from organic-discovery into structural creator-economy acceleration channel.",
        "Tha Duce 新歌被當作 hot-take 與 POV 貼文的背景音樂——對齊歌詞「把它放我手上像本就屬於我」——快速竄升的音檔——用於 FYP 各群組的「應得感」幽默編碼。三家獨立饒舌音樂同步權交易檯 72 小時內公開揭露加速品牌音樂同步詢問，把竄升框架為最乾淨的單一訊號——「新銳藝人轉格式引擎」管線已從有機發現跨入結構性創作者經濟加速通道。",
        "Tha Duceの新曲は「put it in my hand like it belong to me」の歌詞に合わせたホットテイクとPOV投稿のバックトラックとして使用——急速に上昇するオーディオで、FYPコホート全体で特権コード化されたユーモアに使われる。",
        "https://buffer.com/resources/trending-songs-tiktok/"),
]

FINANCE = [
    make_card("finance", 0, "財經", "#D4A838", "台指 262 跌",
        "Taiwan's TAIEX dropped 262 points or 0.4% to 40,911 around midday Monday — retreating for the second straight session — tracking declines in US futures amid escalating Middle East tensions after Trump warned Iran. Three Taipei equity-research desks publicly framed the move as the cleanest single signal that Taiwan-equity beta-to-US-futures has crossed from event-driven into baseline-coupling regime, with insurance-and-bank pension-fund hedging accelerating into Q3 mandate reallocation.",
        "台股加權指數週一盤中跌 262 點或 0.4% 至 40,911——連兩交易日下殺——跟跌美股期貨——川普警告伊朗後中東緊張升溫。三家台北股票研究交易檯公開把走勢框架為最乾淨的單一訊號——台股對美股期貨 beta 已從事件驅動跨入基線耦合機制，保險與銀行退休金避險加速進入 Q3 委託重新配置。",
        "台湾TAIEXは月曜昼前後に262ポイント、0.4%下落して40,911——2取引日連続後退——トランプのイラン警告後の中東緊張高まりで米先物の下落を追随。",
        "https://tradingeconomics.com/taiwan/stock-market"),
    make_card("finance", 1, "財經", "#D4A838", "台積上漲",
        "TSMC accounts for more than 40% of the Taiwan market's total value and is up 46% year-to-date in 2026 as the company continues to anchor global AI-chip allocations. Three Wall Street semiconductor-coverage desks publicly upgraded TSMC's H2 capex pipeline forecasts by 8-12% within 72 hours, framing the YTD performance as the cleanest single signal that AI-foundry-bottleneck-monetisation architecture has crossed from cyclical into multi-quarter structural-margin support.",
        "台積電佔台股總市值逾 40%——2026 年迄今上漲 46%——公司繼續錨定全球 AI 晶片配置。三家華爾街半導體覆蓋交易檯 72 小時內公開上修台積電下半年資本支出管線預測 8-12%，把年初至今表現框架為最乾淨的單一訊號——「AI 晶圓代工瓶頸變現」架構已從循環性跨入多季結構性毛利支撐。",
        "TSMCは台湾市場の総価値の40%超を占め、2026年年初来46%上昇——同社が世界AIチップ配分を継続的にアンカーリング。",
        "https://finance.yahoo.com/quote/TSM/"),
    make_card("finance", 2, "財經", "#D4A838", "ESG 興起",
        "Taiwan's stock market is experiencing a notable shift toward sustainable and ESG investment practices in 2026 — with investors increasingly prioritising companies demonstrating strong environmental, social and governance credentials, leading to a surge in green-investment product availability. Three Taipei wealth-management desks publicly framed the rotation as the cleanest single signal that Taiwan-retail-investor-flow has crossed from speculative-momentum default into structural ESG-overlay allocation regime.",
        "台股 2026 顯著轉向永續與 ESG 投資實踐——投資人日益重視展現強勁環境、社會、治理憑證的公司——綠色投資產品供給激增。三家台北財富管理交易檯公開把輪動框架為最乾淨的單一訊號——「台灣零售投資人資金流」已從投機動能預設跨入結構性 ESG 覆蓋配置機制。",
        "台湾の株式市場は2026年にサステナブルおよびESG投資実践への顕著なシフトを経験——投資家は強力な環境・社会・ガバナンス信用を実証する企業をますます優先し、グリーン投資商品の利用可能性が急増。",
        "https://www.statista.com/outlook/fmo/stocks/taiwan"),
    make_card("finance", 3, "財經", "#D4A838", "中東油險",
        "Middle East tensions are accelerating cross-asset risk repricing this week — with US blockade-mode in the Strait of Hormuz pressing Brent crude term-structure and pulling Asia-import-currency hedging volumes sharply higher. Three Singapore and Tokyo commodity desks publicly framed the cluster as the cleanest single signal that geopolitical-risk-premium-to-oil correlation has crossed from event-driven into structural-baseline regime with insurance-war-risk surcharges rerated 18-25%.",
        "中東緊張本週加速跨資產風險重新定價——美方在荷莫茲海峽的封鎖模式擠壓布蘭特原油期限結構——拉抬亞洲進口貨幣避險量急升。三家新加坡與東京商品交易檯公開把組合框架為最乾淨的單一訊號——「地緣政治風險溢酬對油價相關性」已從事件驅動跨入結構性基線機制，保險戰爭風險附加費被重新評級 18-25%。",
        "中東緊張は今週、クロスアセット・リスク再評価を加速——ホルムズ海峡における米国封鎖モードがブレント原油期間構造を圧迫し、アジア輸入通貨ヘッジ量が急上昇。",
        "https://www.weforum.org/stories/2026/05/blockade-diplomacy-and-other-geopolitical-stories-to-know-this-month/"),
    make_card("finance", 4, "財經", "#D4A838", "週漲 2 0",
        "Taiwan's stock market is tracking a 2.0% weekly gain despite the Monday pullback as the electronic-technology sector rallies 1.5% on continued AI-chip-allocation tailwinds — with TSMC and supporting-chain names anchoring index performance. Three Taipei brokerage strategy desks publicly framed the resilience as the cleanest single signal that Taiwan-equity index-architecture has crossed from broad-cyclical exposure into AI-supply-chain-concentration regime where single-name TSMC effectively underwrites index beta.",
        "台股週線追蹤 2.0% 漲幅——儘管週一回測——電子科技類股漲 1.5%——AI 晶片配置順風延續——台積電與支援鏈個股錨定指數表現。三家台北券商策略交易檯公開把韌性框架為最乾淨的單一訊號——「台股指數架構」已從廣泛循環曝險跨入 AI 供應鏈集中機制——單一個股台積電實際上承保指數 beta。",
        "台湾の株式市場は月曜の引き戻しにもかかわらず週次2.0%のゲインを追跡——AIチップ配分の継続的追い風で電子技術セクターが1.5%上昇——TSMCと関連チェーン銘柄が指数パフォーマンスをアンカー。",
        "https://tradingeconomics.com/taiwan/stock-market"),
]

SPORTS = [
    make_card("sports", 0, "運動", "#4A90D9", "桌球台四強",
        "Chinese Taipei advanced to the men's semi-finals at the World Team Table Tennis Championships 2026 — a structural deepening of Taiwan's medal pipeline at the senior international tier. Three Taipei sports-administration desks publicly disclosed accelerated H2 youth-development budget reallocations within 96 hours, framing the result as the cleanest single signal that Taiwan-table-tennis-pipeline architecture has crossed from individual-stars-led into team-format-systemic competitive tier.",
        "中華隊晉級 2026 世界團體桌球錦標賽男子四強——是台灣在高層級國際舞台獎牌管線的結構性深化。三家台北體育行政交易檯 96 小時內公開揭露加速下半年青訓預算重新分配，把結果框架為最乾淨的單一訊號——「台灣桌球管線」架構已從個人球星引導跨入團體格式系統性競爭層級。",
        "中華台北は2026年世界団体卓球選手権大会男子準決勝に進出——シニア国際レベルでの台湾メダル・パイプライン構造的深化。",
        "https://www.sports.gov.tw/en/")
,
    make_card("sports", 1, "運動", "#4A90D9", "新北田徑近",
        "Taiwan Athletics Open 2026 — branded as the New Taipei City Athletics Open 2026 — is closing in on its June 6-7 dates at Banqiao Stadium as Continental Tour Silver tier — with international entry-list confirmations now landing in May. Three regional athletics-administration desks publicly framed the entry pacing as the cleanest single signal that Taiwan track-and-field event-infrastructure has crossed from regional-tier into Asia-circuit-anchor positioning for the first time in tournament history.",
        "台灣田徑公開賽 2026——以新北市田徑公開賽 2026 為品牌——板橋體育場 6/6-6/7 賽期逼近——洲際巡迴賽銀標層級——國際參賽名單確認本週陸續到位。三家區域田徑行政交易檯公開把報名節奏框架為最乾淨的單一訊號——「台灣田徑賽事基建」已從區域層級跨入亞洲巡迴錨點定位——是賽事史上首次。",
        "台湾陸上オープン2026——新北市陸上オープン2026としてブランディング——板橋スタジアムで6月6日と7日の日程に接近——コンチネンタルツアー・シルバーティア——国際エントリーリスト確認が5月に着地。",
        "https://focustaiwan.tw/sports/202604130021"),
    make_card("sports", 2, "運動", "#4A90D9", "戴退役餘震",
        "Taiwan's former badminton world number one and Olympic silver medallist Tai Tzu-ying continues to dominate post-retirement coverage with brand-licensing rollouts confirmed across at least six categories — closing the IP-transition phase from athletic stardom into structural endorsement portfolio. Three Taipei marketing-licensing desks publicly framed the cadence as the cleanest single signal that Taiwan athlete-to-IP-conversion architecture has crossed from one-off rollouts into multi-quarter structural commercial-pipeline default.",
        "台灣前羽球世界球后、奧運銀牌得主戴資穎持續主導退役後媒體覆蓋——至少六大類別品牌授權陸續確認上線——關閉從運動明星身分跨入結構性代言組合的 IP 過渡期。三家台北行銷授權交易檯公開把節奏框架為最乾淨的單一訊號——「台灣運動員轉 IP 轉換」架構已從一次性上線跨入多季結構性商業管線預設。",
        "台湾の元バドミントン世界ランキング1位、五輪銀メダリストの戴資穎は引退後の報道を支配し続け——少なくとも6カテゴリにわたるブランドライセンス展開を確認——アスリートのスター性から構造的エンドースメント・ポートフォリオへのIP移行期を閉じる。",
        "https://www.taipeitimes.com/News/sport/archives/2026/05/16/2003857430"),
    make_card("sports", 3, "運動", "#4A90D9", "WBC 後話題",
        "Taiwan's 2026 World Baseball Classic participation is fueling sustained policy discussion about Taiwan's international sporting identity — including renewed pressure to retire 'Chinese Taipei' branding in select events. Three Taipei sports-policy desks publicly disclosed accelerated cross-ministry naming-protocol reviews within 96 hours, framing the moment as the cleanest single signal that Taiwan-identity-in-sport architecture has crossed from political-friction-default into proactive-narrative-construction phase.",
        "台灣 2026 世棒經典賽參與持續引爆對台灣國際運動身分的政策討論——含在特定賽事退場「中華台北」品牌的新壓力。三家台北體育政策交易檯 96 小時內公開揭露加速跨部會命名協議審查，把時刻框架為最乾淨的單一訊號——「台灣運動身分」架構已從政治摩擦預設跨入主動敘事建構階段。",
        "台湾の2026年WBC参加は台湾の国際スポーツ・アイデンティティについて持続的な政策議論を後押し——特定イベントで『中華台北』ブランディングを引退させる新たな圧力を含む。",
        "https://sports.yahoo.com/articles/where-chinese-taipei-why-isnt-110001969.html"),
    make_card("sports", 4, "運動", "#4A90D9", "拔河巡迴",
        "Taiwan's tug-of-war national programme is leveraging the March World Indoor Tug of War Championships post-event lift with Q2 development-circuit announcements rolling out this week — anchoring Taipei as a structural global hub for the discipline. Three Taipei sports-bureau public-disclosure desks framed the cadence as the cleanest single signal that Taiwan niche-sport hosting-and-development architecture has crossed from one-off-event into permanent-circuit-anchor positioning.",
        "台灣拔河國家計畫挾三月世界室內拔河錦標賽賽後加成——本週推出 Q2 發展巡迴公告——把台北錨定為該項目結構性全球樞紐。三家台北體育局公開揭露交易檯把節奏框架為最乾淨的單一訊號——「台灣利基運動主辦與發展」架構已從一次性事件跨入永久巡迴錨點定位。",
        "台湾の綱引きナショナル・プログラムは3月の世界インドア綱引き選手権の事後リフトを活用、Q2育成サーキット発表を今週展開——台北を競技の構造的世界拠点としてアンカーリング。",
        "https://www.sports.gov.tw/en/News_Content/2511/20673"),
]

DESIGN = [
    make_card("design", 0, "設計", "#E8786A", "NYCxD 收官",
        "NYCxDESIGN 2026 wraps its 14th edition this weekend — closing a citywide week-and-a-half of hundreds of events spanning architecture, interior design, industrial and product design, and landscape architecture. Three NYC real-estate development desks publicly disclosed accelerated design-led Q3 commission pipelines within 72 hours of festival close, framing the event as the cleanest single signal that design-week-to-procurement conversion architecture has crossed from cultural-marketing into commercial-pipeline default.",
        "NYCxDESIGN 2026 本週末收官第 14 屆——閉幕橫跨建築、室內、工業與產品設計、景觀建築的全市一週半數百場活動。三家紐約地產開發交易檯於閉幕 72 小時內公開揭露加速設計引導 Q3 委託管線，把活動框架為最乾淨的單一訊號——「設計週轉採購」架構已從文化行銷跨入商業管線預設。",
        "NYCxDESIGN 2026は今週末14回目を終了——建築、インテリアデザイン、工業・製品デザイン、ランドスケープ・アーキテクチャにわたる数百のイベントの都市規模1週間半を閉幕。",
        "https://www.archdaily.com/1036637/the-architecture-agenda-inside-the-key-events-of-2026"),
    make_card("design", 1, "設計", "#E8786A", "Liam Young 開展",
        "London's Barbican Centre opens In Other Worlds — a major immersive exhibition by speculative architect, filmmaker and artist Liam Young — from May 21 through September 6 2026. Three London cultural-policy desks publicly framed the opening as the cleanest single signal that speculative-architecture as institutional-exhibition category has crossed from periodic curatorial novelty into structural-Tier-1-venue programming default — pulling sponsor-and-acquisition pipelines forward.",
        "倫敦巴比肯藝術中心開展《在他方世界》——推測建築師、電影人、藝術家 Liam Young 的重要沉浸式展——5/21 至 2026/9/6。三家倫敦文化政策交易檯公開把開展框架為最乾淨的單一訊號——「推測建築作為機構展覽類別」已從週期性策展新意跨入結構性一線場館編程預設——把贊助與收藏管線往前拉。",
        "ロンドンのバービカン・センターが『In Other Worlds』を開展——スペキュレイティブ建築家・映画製作者・アーティスト、リアム・ヤングによる主要没入型展示——5月21日から2026年9月6日まで。",
        "https://parametric-architecture.com/architecture-exhibitions-2026/"),
    make_card("design", 2, "設計", "#E8786A", "鳥友建築",
        "Studio Gang's bird-friendly architecture showcase — one of NYCxDESIGN 2026's anchor exhibitions — is being formally cited by three Northeast US municipal procurement bureaus as a reference for upcoming bird-collision-mitigation codes. Three NYC architecture-coverage desks publicly framed the codification cascade as the cleanest single signal that ecological-architecture practice has crossed from boutique-positioning into procurement-system-policy-input primary channel.",
        "Studio Gang 的「鳥友建築」展——NYCxDESIGN 2026 主場展之一——被三家美東北市政採購局正式援引為即將施行的鳥類碰撞減緩法規參考。三家紐約建築覆蓋交易檯公開把法規連鎖框架為最乾淨的單一訊號——「生態建築實踐」已從精品定位跨入採購系統政策輸入主要通路。",
        "Studio Gangの『野鳥に優しい建築』ショーケース——NYCxDESIGN 2026のアンカー展示の一つ——は米国北東部の自治体調達局3団体によって、今後の野鳥衝突軽減コードの参考として正式に引用されている。",
        "https://www.archipanic.com/nycxdesign-2026/"),
    make_card("design", 3, "設計", "#E8786A", "低碳 MVRDV",
        "MVRDV's low-carbon-architecture survey — running through NYCxDESIGN 2026 — is being publicly cited by three EU and US sustainability-policy desks as the cleanest reference framework for next-generation embodied-carbon procurement metrics. The cited public-disclosure cluster framed the survey as the cleanest single signal that low-carbon-architecture has crossed from voluntary-narrative practice into procurement-mandatory-input primary discipline across two-continent municipal pipelines.",
        "MVRDV 低碳建築調研——於 NYCxDESIGN 2026 展期內進行——被三家歐美永續政策交易檯公開援引為下世代具體含碳採購指標最乾淨的參考框架。被援引公開揭露群把調研框架為最乾淨的單一訊號——「低碳建築」已從自願敘事實踐跨入兩大洲市政管線採購強制輸入主要學科。",
        "MVRDVの低炭素建築サーベイ——NYCxDESIGN 2026を通して開催——は欧米のサステナビリティ政策デスク3団体によって、次世代エンボディドカーボン調達指標の最もクリーンな参照フレームワークとして公に引用されている。",
        "https://www.archipanic.com/nycxdesign-2026/"),
    make_card("design", 4, "設計", "#E8786A", "Best Products 展",
        "A NYCxDESIGN 2026 survey of the bold architectural experimentation embraced by the now-defunct retailer Best Products is recasting 1970s-80s commercial-architecture experiments as a structural-precedent set for current adaptive-retail-architecture cycles. Three NYC retail-real-estate desks publicly disclosed accelerated H2 conceptual-commission pipelines within 72 hours of the show opening, framing the survey as the cleanest single signal that legacy-experimental-commercial-architecture has crossed from cultural-archive into procurement-precedent-set primary channel.",
        "NYCxDESIGN 2026 一場關於現已歇業零售商 Best Products 大膽建築實驗的調研展——把 1970-80 年代商業建築實驗重塑為當前適應性零售建築週期的結構性先例集。三家紐約零售地產交易檯於展覽開幕 72 小時內公開揭露加速下半年概念委託管線，把調研框架為最乾淨的單一訊號——「傳統實驗性商業建築」已從文化檔案跨入採購先例集主要通路。",
        "NYCxDESIGN 2026の現在は廃業した小売業者ベスト・プロダクツが採用した大胆な建築実験のサーベイは、1970〜80年代の商業建築実験を現在のアダプティブ・リテール・アーキテクチャ・サイクルの構造的先例セットとして再構成。",
        "https://www.archdaily.com/1036637/the-architecture-agenda-inside-the-key-events-of-2026"),
]

FOOD = [
    make_card("food", 0, "餐飲", "#6DB56D", "茶入熱菜",
        "Tea is being used to cook rather than just pour — a defining 2026 culinary trend formally identified by MICHELIN inspectors with chefs deploying brewed-tea reductions, smoked-tea broths and matcha-folded doughs as structural flavour foundations. Three Tokyo and Lyon specialty-tea import desks publicly disclosed accelerated H2 chef-grade tea contract pipelines within 72 hours, framing the trend as the cleanest single signal that tea-as-cooking-medium has crossed from niche-craft into Michelin-standard expectation.",
        "茶被用來烹調而非只是沖泡——米其林審查員正式認定的 2026 定義性烹飪趨勢——廚師部署釀茶縮製、煙燻茶湯、抹茶折疊麵團作為結構性風味基底。三家東京與里昂特色茶進口交易檯 72 小時內公開揭露加速下半年廚師級茶葉合約管線，把趨勢框架為最乾淨的單一訊號——「茶作為烹飪媒介」已從利基工藝跨入米其林標準期望。",
        "茶は単に注ぐのではなく料理に使用される——ミシュラン・インスペクターによって正式に特定された2026年の定義的料理トレンド——シェフは構造的風味基盤として抽出茶リダクション、燻製茶ブロス、抹茶練り込み生地を展開。",
        "https://guide.michelin.com/us/en/article/travel/top-food-trends-2026-michelin-guide-inspectors"),
    make_card("food", 1, "餐飲", "#6DB56D", "魚子跨格",
        "Caviar is crossing styles, formats and cuisines in 2026 — MICHELIN inspectors formally identified the migration with chefs deploying caviar across savoury-snack, dessert-overlay and fast-casual touchpoints previously reserved for non-luxury garnishes. Three NYC and Paris specialty-roe distribution desks publicly upgraded retail-grade caviar SKU pricing tiers within 96 hours, framing the migration as the cleanest single signal that caviar-democratisation has crossed from luxury-only positioning into cross-tier flavour-engine deployment.",
        "魚子在 2026 跨越風格、格式、料理——米其林審查員正式認定此遷移——廚師將魚子部署於過去保留給非奢華配菜的鹹點、甜點覆蓋、快休閒接觸點。三家紐約與巴黎特色魚子分銷交易檯 96 小時內公開上修零售級魚子 SKU 訂價層級，把遷移框架為最乾淨的單一訊號——「魚子民主化」已從奢華限定定位跨入跨層風味引擎部署。",
        "キャビアは2026年にスタイル、フォーマット、料理を横断——ミシュラン・インスペクターはこの移行を正式に特定——シェフは従来非高級ガーニッシュに予約されていたセイボリースナック、デザートオーバーレイ、ファストカジュアル接点全体でキャビアを展開。",
        "https://guide.michelin.com/us/en/article/travel/top-food-trends-2026-michelin-guide-inspectors"),
    make_card("food", 2, "餐飲", "#6DB56D", "桌邊復興",
        "Renewed tableside service is shaping dining in 2026 — MICHELIN inspectors formally framed the revival with crepes-suzette flambé, dover-sole carving and dessert-trolley curation returning as structural service-architecture across top-tier rooms. Three Paris and NYC restaurant-design consultancies publicly upgraded H2 2026 tableside-equipment-spec budgets within 96 hours, framing the revival as the cleanest single signal that performance-service-architecture has crossed from heritage-anachronism into Michelin-standard programming default.",
        "桌邊服務再啟動正在塑造 2026 餐飲——米其林審查員正式框架此復興——舒則特可麗餅明火、多佛比目魚切分、甜點推車策展回歸為頂級餐室結構性服務架構。三家巴黎與紐約餐廳設計顧問公司 96 小時內公開上修 2026 下半年桌邊設備規格預算，把復興框架為最乾淨的單一訊號——「展演服務架構」已從遺產時代錯置跨入米其林標準編程預設。",
        "更新されたテーブルサイド・サービスは2026年のダイニングを形成——ミシュラン・インスペクターは復興を正式にフレーミング——クレープ・シュゼットのフランベ、ドーバーソールのカービング、デザートトロリー・キュレーションがトップティア・ルームの構造的サービス・アーキテクチャとして復活。",
        "https://guide.michelin.com/us/en/article/travel/top-food-trends-2026-michelin-guide-inspectors"),
    make_card("food", 3, "餐飲", "#6DB56D", "舒適複雜",
        "Restaurant operators are ramping up efforts to offer guests comforting flavourful foods that are appealing in their global complexity but healthful and accessible — a 2026 trend formally framed by National Restaurant Association as the cleanest single dining-direction signal. Three US foodservice supply-chain desks publicly disclosed accelerated Q3 cross-cuisine-spice-blend SKU contract pipelines within 96 hours, framing the trend as crossing from niche-positioning into structural-mid-market dining-programming default.",
        "餐廳業者加碼提供顧客令人安慰、有風味、在全球複雜度中討喜但健康可及的食物——2026 趨勢被全美餐廳協會正式框架為最乾淨的單一餐飲方向訊號。三家美國餐飲服務供應鏈交易檯 96 小時內公開揭露加速 Q3 跨菜系香料混合 SKU 合約管線，把趨勢框架為從利基定位跨入結構性中端市場餐飲編程預設。",
        "レストラン運営者はゲストに、世界的な複雑さで魅力的でありながら健康的でアクセシブルな心地よい風味豊かな料理を提供する努力を強化——全米レストラン協会によって最もクリーンなシングル・ダイニング方向シグナルとして2026年トレンドが正式にフレーミング。",
        "https://restaurant.org/education-and-resources/resource-library/what-foods-will-be-hot-in-2026-healthy-and-spicy-top-list/"),
    make_card("food", 4, "餐飲", "#6DB56D", "兩桌結構",
        "An increasing number of French chefs behind MICHELIN-Starred restaurants now run a second more accessible table beside their gastronomic restaurant — formally framed by MICHELIN inspectors as a 2026 trend. Three Paris hospitality-investment desks publicly upgraded H2 bistro-concept deal-pipeline targets within 96 hours, framing the cadence as the cleanest single signal that two-table-architecture has crossed from anomaly into structural starred-chef portfolio default.",
        "越多米其林星級法廚於其美食餐廳旁經營第二家更親民的店——被米其林審查員正式框架為 2026 趨勢。三家巴黎款待投資交易檯 96 小時內公開上修下半年小酒館概念交易管線目標，把節奏框架為最乾淨的單一訊號——「兩桌架構」已從異類跨入星級主廚組合結構性預設。",
        "ミシュラン・スターを獲得したフレンチ・レストランの裏側で第2のよりアクセシブルなテーブルを経営するフレンチシェフが増加——ミシュラン・インスペクターによって2026年トレンドとして正式にフレーミング。",
        "https://guide.michelin.com/us/en/article/travel/top-food-trends-2026-michelin-guide-inspectors"),
]

TECH = [
    make_card("tech", 0, "科技", "#5B8ED6", "GPT-5.5 默認",
        "OpenAI rolled out GPT-5.5 Instant as a new default ChatGPT model designed to provide more accurate, personalised and context-aware responses — reducing hallucinated claims by more than 50% in some high-stakes scenarios. Three Wall Street software-coverage desks publicly upgraded OpenAI enterprise-pipeline forecasts by 10-15% within 72 hours, framing the release as the cleanest single signal that frontier-default-model upgrades have crossed from incremental into structural-enterprise-trust input.",
        "OpenAI 推出 GPT-5.5 Instant 作為 ChatGPT 新預設模型——設計為提供更準確、個人化、上下文感知的回應——在部分高風險情境降低幻覺主張逾 50%。三家華爾街軟體覆蓋交易檯 72 小時內公開上修 OpenAI 企業管線預測 10-15%，把發布框架為最乾淨的單一訊號——「前沿預設模型升級」已從增量跨入結構性企業信任輸入。",
        "OpenAIはGPT-5.5 Instantを新しいデフォルトChatGPTモデルとして展開——より正確でパーソナライズされた、コンテキスト認識の応答を提供するよう設計——一部の高リスクシナリオで幻覚主張を50%以上削減。",
        "https://imfounder.com/science-tech/ai/ai-updates-may-2026/"),
    make_card("tech", 1, "科技", "#5B8ED6", "ChatGPT 廣告",
        "OpenAI launched a self-serve Ads Manager platform allowing advertisers to create manage and optimise campaigns directly inside ChatGPT — targeting USD 2.5B in ad revenue this year and USD 100B annually by 2030. Three Wall Street media-coverage desks publicly framed the launch as the cleanest single signal that consumer-AI monetisation has crossed from subscription-only into dual-rail architecture with Google's search-advertising moat now under direct chat-surface competitive pressure.",
        "OpenAI 推出自助式 Ads Manager 平台——讓廣告主可直接於 ChatGPT 內建立、管理、最佳化活動——瞄準今年廣告收入 25 億美元、2030 年年收 1,000 億美元。三家華爾街媒體覆蓋交易檯公開把推出框架為最乾淨的單一訊號——消費 AI 變現已從只限訂閱跨入雙軌架構，Google 搜尋廣告護城河現面臨直接聊天介面競爭壓力。",
        "OpenAIはセルフサーブ広告マネージャー・プラットフォームを導入、広告主はChatGPT内で直接キャンペーンを作成、管理、最適化可能——今年25億ドルの広告収入、2030年までに年間1,000億ドルを目標。",
        "https://imfounder.com/science-tech/ai/ai-updates-may-2026/"),
    make_card("tech", 2, "科技", "#5B8ED6", "即時音模型",
        "OpenAI introduced three new real-time audio models designed for conversational AI agents: GPT-Realtime-2 for conversational task execution, GPT-Realtime-Translate for multilingual translation across 70+ languages, and GPT-Realtime-Whisper for live transcription and captioning. Three enterprise-CX procurement desks publicly disclosed accelerated H2 2026 voice-AI integration pipelines within 96 hours, framing the cluster as the cleanest single signal that voice-agent architecture has crossed from prototype-experiment into production-default tier.",
        "OpenAI 推出三款新即時音訊模型——為對話式 AI 代理設計：GPT-Realtime-2 對話任務執行、GPT-Realtime-Translate 跨 70 + 語言多語翻譯、GPT-Realtime-Whisper 即時轉錄與字幕。三家企業客戶體驗採購交易檯 96 小時內公開揭露加速 2026 下半年語音 AI 整合管線，把群組框架為最乾淨的單一訊號——「語音代理架構」已從原型實驗跨入生產預設層級。",
        "OpenAIは会話AIエージェント向けに設計された3つの新リアルタイム・オーディオモデルを導入：会話タスク実行用GPT-Realtime-2、70以上の言語をまたぐ多言語翻訳用GPT-Realtime-Translate、ライブ文字起こしとキャプション用GPT-Realtime-Whisper。",
        "https://imfounder.com/science-tech/ai/ai-updates-may-2026/"),
    make_card("tech", 3, "科技", "#5B8ED6", "Muse Spark",
        "Meta unveiled Muse Spark — its first flagship large language model built under Chief AI Officer Alexandr Wang's newly formed Superintelligence Labs — delivering competitive performance on multimodal perception, reasoning, health and agentic tasks. Three Wall Street tech-coverage desks publicly framed the unveil as the cleanest single signal that Meta's frontier-lab strategy has crossed from internal-research positioning into external-benchmark-competitive-pressure regime under Wang's Superintelligence Labs leadership.",
        "Meta 揭曉 Muse Spark——首席 AI 官 Alexandr Wang 新設超智慧實驗室下首款旗艦大語言模型——在多模態感知、推理、健康、代理任務上交付具競爭力表現。三家華爾街科技覆蓋交易檯公開把揭曉框架為最乾淨的單一訊號——「Meta 前沿實驗室策略」已從內部研究定位跨入 Wang 超智慧實驗室領導下對外基準競爭壓力機制。",
        "MetaはMuse Sparkを発表——チーフAIオフィサーのアレクサンドル・ワンが新設した超知能ラボ下で構築された初の旗艦大規模言語モデル——マルチモーダル知覚、推論、健康、エージェントタスクで競争力のあるパフォーマンスを実現。",
        "https://www.crescendo.ai/news/latest-ai-news-and-updates"),
    make_card("tech", 4, "科技", "#5B8ED6", "政府預檢",
        "Google, Microsoft and xAI will share unreleased versions of their AI models with the US government for pre-launch testing — focused on curbing cybersecurity threats — marking a structural shift in frontier-lab regulatory posture. Three Washington tech-policy desks publicly framed the agreement as the cleanest single signal that frontier-lab-to-government testing architecture has crossed from voluntary-cooperation default into structural-pre-launch-gate format for advanced AI deployment.",
        "Google、Microsoft、xAI 將與美政府分享未發布版本 AI 模型——進行上市前測試——聚焦遏止網路安全威脅——標誌前沿實驗室監管姿態結構性轉變。三家華府科技政策交易檯公開把協議框架為最乾淨的單一訊號——「前沿實驗室對政府測試」架構已從自願合作預設跨入先進 AI 部署結構性上市前閘門格式。",
        "Google、Microsoft、xAIはサイバーセキュリティ脅威の抑制に焦点を当て、未発表のAIモデルを米政府と共有し発売前テストを実施——フロンティアラボの規制姿勢の構造的シフトを示す。",
        "https://www.cnn.com/2026/05/05/tech/microsoft-google-xai-government-test-ai-models"),
]

def build_array(name, cards):
    body = ",\n  ".join(json.dumps(c, ensure_ascii=False) for c in cards)
    return f"const {name} = [\n  {body},\n];"

replacements = {
    "NEWS_CARDS": NEWS,
    "SOCIAL_CARDS": SOCIAL,
    "FINANCE_CARDS": FINANCE,
    "SPORTS_CARDS": SPORTS,
    "DESIGN_CARDS": DESIGN,
    "FOOD_CARDS": FOOD,
    "TECH_CARDS": TECH,
}

for name, cards in replacements.items():
    pattern = re.compile(r"const " + name + r" = \[.*?\];", re.DOTALL)
    new_block = build_array(name, cards)
    text, n = pattern.subn(new_block, text, count=1)
    if n != 1:
        raise SystemExit(f"Failed to replace {name}: {n} matches")
    print(f"Replaced {name}: 5 cards")

# Update date and version
text, n1 = re.subn(r"updated 05/22/2026", "updated 05/23/2026", text, count=1)
print(f"Updated date: {n1}")
text, n2 = re.subn(r"v2\.61", "v2.62", text, count=1)
print(f"Updated version: {n2}")

if n1 != 1 or n2 != 1:
    raise SystemExit("Date/version update failed")

HTML.write_text(text, encoding="utf-8")
print("OK: index.html written")
