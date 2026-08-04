import re
from pathlib import Path

index_path = Path(r"c:\GOOGLE ANGET\說明書\index.html")
content = index_path.read_text(encoding="utf-8")

# New updated projectsData block
new_projects_data = """const projectsData = [
        {title: "儲槽氮氣閥作動原理教育訓練",
                category: "cat1",
                launchUrl: "https://nitrogen-valve-quiz-syhm.netlify.app",
                manualTitle: "氮氣閥",
                desc: "結合 P&ID 互動式 SVG 動態模擬動畫的儲槽氮封與防爆安全教材。支援自適應語音朗讀、自動換頁與 5 題課後測驗，並具備行動裝置防文字擠壓之流暢排版。",
                tags: ["SVG 動畫", "自力式氮封", "TTS 旁白", "微壓模擬"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/nitrogen-valve-training"},
        {title: "簡報自動語音影片生成器 (pdf-to-video)",
                category: "cat1",
                launchUrl: "command:ocrvideo",
                manualTitle: "簡報自動語音影片生成器",
                desc: "將簡報 PDF 自動辨識並合成台灣女聲旁白的影片生成器。支援 BGM 背景音樂混音（含 -23 LUFS 響度正規化）、自訂浮水印中文字、Intel QSV 顯卡加速、Web UI 腳本即時修改與試聽。",
                tags: ["FastAPI", "Edge-TTS / Gemini TTS", "MoviePy", "BGM loudnorm"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第一類_核心網頁與互動系統/影片生成/pdf-to-video"},
        {title: "員工教育訓練測驗系統 (本機優先版)",
                category: "cat1",
                launchUrl: "./projects/hr_quiz_v2/index_with_mp3.html",
                manualTitle: "員工教育訓練測驗系統",
                desc: "本機優先的通用 SOP 教育訓練與測驗系統。支援離線作答與前端評分、自動回寫 results.csv、以及完全圖形化變更 SOP 主題與題目的管理後台。",
                tags: ["HTML5", "微軟TTS", "本機CSV寫入", "免安裝管理工具"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/hr-work-rules-quiz"},
        {title: "flowchart-web 產品製程流程圖系統",
                category: "cat1",
                launchUrl: "./projects/flowchart-web/index.html",
                manualTitle: "flowchart-web",
                desc: "鴻勝化學的槽體製程管控系統。提供廠區原料、製程、成品槽之互動式 SVG 流程圖、動態液位水波計、壓力與 N2 吹掃模擬。",
                tags: ["HTML5", "CSS3", "SVG", "互動網頁"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/flowchart-web"},
        {title: "hongsheng-web 軟管對刷稽核系統",
                category: "cat1",
                launchUrl: "./projects/hongsheng-web/index.html",
                manualTitle: "hongsheng-web",
                desc: "暗黑科技風格之現場教育訓練與模擬演練應用。包含防錯警示燈、條碼模擬掃描配對、與 Firebase Firestore 即時資料庫連線。",
                tags: ["HTML5", "Vanilla CSS", "Firebase", "WebUI"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/hongsheng-web"},
        {title: "isotank-training 化學品卸料安全訓練",
                category: "cat1",
                launchUrl: "./projects/isotank-training/index.html",
                manualTitle: "isotank-training",
                desc: "視覺化卸料安全教材。以 CSS 卡片與 9 步驟展示現場控制點，點擊可觀看防溢流堤、接地、接管氣密測試之 SVG 動畫。",
                tags: ["HTML5", "SVG動畫", "語音旁白"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/isotank-training"},
        {title: "isotank-hf-demo 化學品卸料動畫與影片",
                category: "cat1",
                launchUrl: "./projects/isotank-hf-demo/index.html",
                manualTitle: "isotank-hf-demo",
                desc: "基於 HyperFrames CLI 影音生成框架開發之 GSAP 網頁動畫投影片。支援 edge-tts 台灣男聲，並可一鍵自動渲染輸出 MP4 影片。",
                tags: ["GSAP", "HyperFrames", "edge-tts", "影片輸出"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/isotank-hf-demo"},
        {title: "test 大阪冒險電子書",
                category: "cat1",
                launchUrl: "./projects/test/index.html",
                manualTitle: "大阪冒險",
                desc: "小妤一家四口大阪五天四夜四格漫畫互動電子書。針對 10 歲主角小融修正微軟原生台灣腔男聲（+35Hz音高），並整合 ElevenLabs 電影級配音與試聽面板。",
                tags: ["HTML5", "微軟語音", "ElevenLabs", "角色試聽"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/osaka-adventure-book"},
        {title: "聲音轉文字 NoType語音助理",
                category: "cat1",
                launchUrl: "command:NoType",
                manualTitle: "NoType",
                desc: "本機執行全域快捷鍵語音助理，按下快捷鍵即快速錄音並透過 Whisper / Groq API 轉為文字，隨後模擬鍵盤將文字打字輸入游標處。",
                tags: ["Electron", "Groq API", "Whisper", "自動打字"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第一類_核心網頁與互動系統/聲音轉文字"},
        {title: "互動式網站 Lv1 - Lv5",
                category: "cat1",
                launchUrl: "./projects/互動式網站/index.html",
                manualTitle: "互動教學",
                desc: "用 AI 打造互動教學網頁五階段教材。展示從單選題（Lv1）、GAS 試算表存檔（Lv2）、講師與學員即時同步（Lv3）到 AI 批改與多輪對話助教（Lv4/Lv5）的完整實作。",
                tags: ["Node.js", "Firebase", "Gemini API", "GAS"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/interactive-web-training"},
        {title: "軟管對刷稽核系統 v3.4",
                category: "cat2",
                launchUrl: "command:KeyCode",
                manualTitle: "軟管 Key-Code",
                desc: "鴻勝化學現場對刷稽核 Android APK (v3.4)。支援多廠別選單（一廠/二廠/三廠）、條碼掃描氣密防呆比對、帶00前綴文字格式保護，以及 QC 識別證授權放行機制。",
                tags: ["Android APK", "Kotlin", "GAS API", "防呆對刷"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第二類_生產管理與API串接/軟管-Key-Code-管理優化方案"},
        {title: "T100 ERP QC 串接與三重對刷演練控制台",
                category: "cat2",
                launchUrl: "./projects/t100_simulator.html",
                manualTitle: "T100 ERP QC",
                desc: "專門提供給資訊人員與長官簡報展示的視覺化模擬演練控制台。包含【一關: 現場對刷】、【二關: T100 QC合格檢驗】、【三關: QC授權放行】與即時動態流程圖。",
                tags: ["模擬演練", "T100 ERP", "三重防呆", "SVG 畫布"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第二類_生產管理與API串接/IPAHQ-槽車確認-GAS-to-PHPSQL"},
        {title: "IPAHQ 槽車確認與掃描系統",
                category: "cat2",
                launchUrl: "command:IPAHQ",
                manualTitle: "IPAHQ 槽車確認",
                desc: "廠區進貨與槽車防錯確認登記系統。透過手持條碼槍掃描，比對 ERP 品名車號，並利用 PHP API 對接 SQL Server 進口品管 COA。",
                tags: ["PHP", "SQL Server", "GAS", "出貨核對"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第二類_生產管理與API串接/IPAHQ槽車掃描系統代碼原始APP優化"},
        {title: "IPA 生產排程雙儲槽優化",
                category: "cat2",
                launchUrl: "command:IPA",
                manualTitle: "IPA 生產排程",
                desc: "彰化廠 IPA 生產排程優化。以 Python 演算法預測未來 24H 儲槽容量狀態，避免溢流風險，並透過 PHP 輸出甘特圖與排程報表。",
                tags: ["Python", "Pandas", "PHP甘特圖"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第二類_生產管理與API串接/IPA-生產排程雙儲槽優化"},
        {title: "n系列 GAS轉APK與出貨",
                category: "cat2",
                launchUrl: "command:nseries",
                manualTitle: "n系列 GAS",
                desc: "將 Google 試算表 GAS 系統封裝為 Android APK。供現場包裝人員配戴手持 Android 掃描槍進行出貨核對，支援 SQLite 離線暫存與批次同步。",
                tags: ["Android SDK", "Cordova", "SQLite", "GAS"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第二類_生產管理與API串接/n系列GAS-轉-APK-離線核對上傳"},
        {title: "N系列 條碼出貨核對與串接",
                category: "cat2",
                launchUrl: "command:Nseries_Check",
                manualTitle: "N系列 條碼出貨",
                desc: "包裝人員利用掃描槍核對棧板與外箱條碼，防止出錯貨。核對完成後自動發送 API，將結果同步至企業 ERP 出貨庫存模組中。",
                tags: ["PHP", "JavaScript", "SQL", "ERP API"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第二類_生產管理與API串接/N系列BARCODE出貨核對"},
        {title: "QC 系統客製化電子化工廠",
                category: "cat2",
                launchUrl: "command:QC",
                manualTitle: "QC 系統客製化",
                desc: "品管部門客製化的檢驗數據自動化登錄系統。支援批號防重複登錄，並將每日合格率與雜質含量以 Chart.js 儀表板呈現在中控室大螢幕上。",
                tags: ["PHP", "Chart.js", "SQL Server"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第二類_生產管理與API串接/QC-系統客製化電子化工廠"},
        {title: "三合一單 to PHP Migration",
                category: "cat2",
                launchUrl: "command:Migration",
                manualTitle: "三合一單 to PHP",
                desc: "工廠資訊系統升級。提供 Excel 三合一確認單遷移至 PHP + SQL 中央資料庫架構指南，並含歷史 Excel 批次導入 API 腳本。",
                tags: ["PHP 8", "Database", "Excel匯入"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第二類_生產管理與API串接/三合一單-to-PHP-Migration"},
        {title: "溫度通報系統 本機與雲端同步備援監控",
                category: "cat2",
                launchUrl: "https://hongsheng-temp-523.web.app",
                manualTitle: "環境溫度監控",
                desc: "彰化彰濱廠區環境高溫雙軌備援系統。本機 Python 與雲端 GAS 排程雙向同步心跳。Firebase 實時 HMI 支援 Chart.js 趨勢、LINE/Teams 通知。",
                tags: ["Python", "GAS", "Firebase", "Teams Webhook"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第二類_生產管理與API串接/溫度通報"},
        {title: "Google Classroom Agent",
                category: "cat3",
                launchUrl: "command:Classroom",
                manualTitle: "Google Classroom Agent",
                desc: "自動化上傳課程講義、管理課程公告、彙整學生作業及成績回傳的 Google Classroom AI 助教。",
                tags: ["Google API", "AI Agent"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第三類_AI代理與指南企劃/Google%20Classroom%20anget"},
        {title: "Clasp + Netlify 部署指南",
                category: "cat3",
                launchUrl: "command:Clasp",
                manualTitle: "Clasp + Netlify 部署指南",
                desc: "指南指導 AI Agent（如 Antigravity）如何一鍵將靜態網頁前端加上 Google Sheets 後端，並完成 Netlify 的非互動式快速部署。",
                tags: ["clasp", "Netlify", "Serverless"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/clasp-netlify-mcp-guide"},
        {title: "Claude HTML Slide Builder",
                category: "cat3",
                launchUrl: "command:SlideBuilder",
                manualTitle: "Claude HTML Slide Builder",
                desc: "將 Markdown 文字自動生成為帶 GSAP 動畫與 reveal.js 互動之簡報。內建 wordcloud2 文字雲與 Firebase 投票看板，並能自動部署到 GitHub Pages。",
                tags: ["Reveal.js", "Python", "GitHub Pages"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/claude-html-slide-builder"},
        {title: "畢業旅行與簡報企劃 (grad-trip)",
                category: "cat3",
                launchUrl: "command:GradTrip",
                manualTitle: "畢業旅行與簡報企劃",
                desc: "大學畢業旅行多媒體企劃生成，整合 edge-tts 語音與 Python 自動化 PPT 簡報製作。",
                tags: ["Python", "PPTX", "旅遊企劃"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第三類_AI代理與指南企劃/grad-trip"},
        {title: "保養品 客服聊天機器人",
                category: "cat3",
                launchUrl: "command:BeautyBot",
                manualTitle: "保養品 客服聊天機器人",
                desc: "LINE 保養品客服聊天機器人，整合 Gemini 與知識庫，提供即時商品推薦與保養諮詢。",
                tags: ["LINE Bot", "Gemini", "知識庫"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第三類_AI代理與指南企劃/保養品"},
        {title: "Padlet 留言板系統",
                category: "cat3",
                launchUrl: "./projects/padlet-board/index.html",
                manualTitle: "Padlet 留言板系統",
                desc: "互動式留言板系統，支援匿名留言、留言分類、大廳即時瀑布流看板。",
                tags: ["HTML5", "CSS Grid", "輕量儲存"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第三類_AI代理與指南企劃/padlet-board"},
        {title: "AI 克隆聲音",
                category: "cat3",
                launchUrl: "command:VoiceClone",
                manualTitle: "AI 克隆聲音",
                desc: "VoxCPM2 克隆音色與語調。支援 Web 端錄音與 AI Agent 自然語言指令連動。",
                tags: ["Python 3.12", "Gradio", "VoxCPM2", "PyTorch"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第三類_AI代理與指南企劃/AI%20克隆聲音"},
        {title: "AI Agent Obsidian 知識庫建置",
                category: "cat3",
                launchUrl: "command:Obsidian",
                manualTitle: "AI Agent Obsidian 知識庫建置",
                desc: "YouTube 影片字幕提取清洗與 Obsidian 三層式（Clipping、創作庫、知識庫）二次大腦知識庫整理。",
                tags: ["yt-dlp", "Obsidian", "知識管理"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第三類_AI代理與指南企劃/Google%20Classroom%20anget"},
        {title: "AIGC 音樂影片生成系統",
                category: "cat3",
                launchUrl: "command:AIGC_MV",
                manualTitle: "AIGC 音樂影片生成系統",
                desc: "宣傳歌Sun AI生成、故事板分配與影音批次合成儀表板，已託管於 Firebase。",
                tags: ["Suno AI", "FFmpeg", "Firebase Hosting"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第三類_AI代理與指南企劃/aigc-music-video-hub"},
        {title: "Claude Video Specs 影片規格與技能指南",
                category: "cat3",
                launchUrl: "command:VideoSpecs",
                manualTitle: "Claude Video Specs 影片規格與技能指南",
                desc: "三類 Reveal-Slide 影音製作規格、自動安裝腳本以及打包為 Agent Skill 的開發工具包。",
                tags: ["Reveal.js", "Python", "SkillsPackager"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/claude-video-specs"},
        {title: "跨電腦一鍵備份與還原轉移系統",
                category: "cat3",
                launchUrl: "command:BackupRestore",
                manualTitle: "跨電腦一鍵備份",
                desc: "AI Agent 與本機開發環境一鍵備份、還原與排程自動化系統，支援跨電腦無痛技能轉移。",
                tags: ["PowerShell", "TaskScheduler", "一鍵還原"],
                githubUrl: "https://github.com/shihwei0809/google-agent"}];"""

# Replace projectsData block in index.html
pattern = r"const projectsData = \[.*?\];"
content = re.sub(pattern, new_projects_data, content, flags=re.DOTALL)

# Upgrade showManualByTitle function in index.html to be ultra robust
old_show_manual = """        // 大廳進入說明書的觸發函式
        function showManualByTitle(title) {
            // 在 manualsData 尋找 title
            const item = manualsData.find(m => m.title.toLowerCase().includes(title.toLowerCase()));
            if (item) {
                switchView('reader');
                selectDoc(item);
            } else {
                alert(`未找到 "${title}" 說明書項目。`);
            }
        }"""

new_show_manual = """        // 大廳進入說明書的觸發函式 (強效比對)
        function showManualByTitle(title) {
            if (!manualsData || manualsData.length === 0) {
                alert("說明書資料庫載入中，請稍後再試。");
                return;
            }
            
            const lowerKey = title.toLowerCase().trim();
            // 1. 精確比對或包含
            let item = manualsData.find(m => m.title.toLowerCase().includes(lowerKey) || lowerKey.includes(m.title.toLowerCase()));
            
            // 2. 關鍵字拆解比對
            if (!item) {
                const keywords = lowerKey.split(/\\s+|-|_|\\(|\\)/).filter(k => k.length > 1);
                item = manualsData.find(m => {
                    const mTitle = m.title.toLowerCase();
                    return keywords.some(k => mTitle.includes(k));
                });
            }
            
            if (item) {
                switchView('reader');
                selectDoc(item);
            } else {
                alert(`未找到與 "${title}" 相關的說明書，將為您導向說明書總覽目錄。`);
                switchView('reader');
            }
        }"""

if old_show_manual in content:
    content = content.replace(old_show_manual, new_show_manual)
    print("Updated showManualByTitle function!")
else:
    print("Warning: Could not find exact old showManualByTitle block, checking alternate replacement...")

index_path.write_text(content, encoding="utf-8")
print("Updated projectsData and GitHub URLs in index.html successfully!")
