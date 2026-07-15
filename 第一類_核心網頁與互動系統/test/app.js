// Story Data Object (Offline-friendly to avoid CORS issues when double-clicking HTML files)
const storyData = {
  "title": "小妤的大阪冒險之旅 (Xiaoyu's Osaka Adventure)",
  "characters": {
    "sakura": {
      "name": "小妤 (Xiaoyu)",
      "role": "主角 / 國小五年級",
      "description": "11歲，活潑可愛的國小五年級女生。愛拍照、愛分享生活，是這次旅行的記錄者。綁著長馬尾，戴著粉紅色髮夾。"
    },
    "taiga": {
      "name": "小融 (Xiaorong)",
      "role": "弟弟 / 國小四年級",
      "description": "10歲，精力過剩的國小四年級男孩。超級吃貨，對美食毫無抵抗力，特別喜歡章魚燒。戴著黃色鴨舌帽。"
    },
    "papa": {
      "name": "宏志 (Hiroshi)",
      "role": "爸爸",
      "description": "40歲，溫和但有點呆萌的爸爸。方向感極差，總是拿著地圖看反。戴著圓形眼鏡，背著大背包。"
    },
    "mama": {
      "name": "美綠 (Midori)",
      "role": "媽媽",
      "description": "38歲，理性且有條理的媽媽。擅長規劃行程與預算，是家裡的地下司令官。留著俏麗波浪短髮，戴太陽眼鏡。"
    }
  },
  "pages": [
    {
      "pageNumber": 1,
      "pageTitle": "第一天：抵達關西與道頓堀美食之旅",
      "panels": [
        {
          "panelNumber": 1,
          "image": "assets/images/p1_panel1.png",
          "description": "一家四口剛抵達關西機場大廳，小妤拿著手機和全家興奮自拍，宏志爸爸看著指示牌有些困惑。",
          "dialogues": [
            { "id": "p1_p1_d1", "speaker": "sakura", "text": "耶！大阪我們來了！第一站先去哪裡？" },
            { "id": "p1_p1_d2", "speaker": "papa", "text": "讓爸爸看看地圖，嗯……好像是走這邊？" }
          ]
        },
        {
          "panelNumber": 2,
          "image": "assets/images/p1_panel2.png",
          "description": "道頓堀繁華的街道上，巨大的螃蟹招牌十分吸睛，小融指著章魚燒攤位流口水。",
          "dialogues": [
            { "id": "p1_p2_d1", "speaker": "taiga", "text": "哇！好大的螃蟹！爸爸，我肚子餓了，我想吃章魚燒！" },
            { "id": "p1_p2_d2", "speaker": "mama", "text": "別急，媽媽已經查好最有名的一家了！" }
          ]
        },
        {
          "panelNumber": 3,
          "image": "assets/images/p1_panel3.png",
          "description": "小融塞了一大口剛起鍋的章魚燒，燙得滿臉通紅眼眶泛淚。小妤在旁邊哈哈大笑，爸爸手忙腳亂遞水。",
          "dialogues": [
            { "id": "p1_p3_d1", "speaker": "taiga", "text": "好燙！呼呼！但是超好吃！" },
            { "id": "p1_p3_d2", "speaker": "sakura", "text": "哈哈哈，小融你也吃太急了吧，嘴巴都要噴火了！" }
          ]
        },
        {
          "panelNumber": 4,
          "image": "assets/images/p1_panel4.png",
          "description": "黃昏的道頓堀運河旁，背景是經典的格力高跑跑人看板，全家人漫步在運河邊，十分愜意。",
          "dialogues": [
            { "id": "p1_p4_d1", "speaker": "mama", "text": "大阪的第一天就這麼完美，明天還有大阪城呢！" },
            { "id": "p1_p4_d2", "speaker": "papa", "text": "今晚一定要吃飽睡好，明天要走很多路喔！" }
          ]
        }
      ]
    },
    {
      "pageNumber": 2,
      "pageTitle": "第二天：大阪城探險與歷史魅力",
      "panels": [
        {
          "panelNumber": 1,
          "image": "assets/images/p2_panel1.png",
          "description": "在大阪城公園的岔路口，宏志爸爸看著地圖滿頭大汗，美綠媽媽無奈地指著他拿反的地圖。",
          "dialogues": [
            { "id": "p2_p1_d1", "speaker": "papa", "text": "咦？大阪城天守閣到底在哪個方向？明明地圖寫著直走……" },
            { "id": "p2_p1_d2", "speaker": "mama", "text": "宏志，你把地圖拿反了啦！那邊才是天守閣！" }
          ]
        },
        {
          "panelNumber": 2,
          "image": "assets/images/p2_panel2.png",
          "description": "宏偉的大阪城天守閣矗立在眼前，白牆綠瓦與金箔裝飾在陽光下熠熠生輝，小融和小妤張大嘴巴驚嘆。",
          "dialogues": [
            { "id": "p2_p2_d1", "speaker": "taiga", "text": "哇！好酷！這個城堡亮晶晶的，裡面會有忍者嗎？" },
            { "id": "p2_p2_d2", "speaker": "sakura", "text": "這可是歷史悠久的大阪城喔！快點過來，我們拍張合照！" }
          ]
        },
        {
          "panelNumber": 3,
          "image": "assets/images/p2_panel3.png",
          "description": "通往天守閣的長長石階上，小融一馬當先往上衝，爸爸累得扶著膝蓋大口喘氣，媽媽在後面幫爸爸打氣。",
          "dialogues": [
            { "id": "p2_p3_d1", "speaker": "taiga", "text": "衝啊！我要當第一名爬到頂樓！" },
            { "id": "p2_p3_d2", "speaker": "papa", "text": "小融……等等爸爸……這樓梯也太多了吧……" }
          ]
        },
        {
          "panelNumber": 4,
          "image": "assets/images/p2_panel4.png",
          "description": "天守閣頂樓展望台上，涼風吹拂，一家人眺望大阪市區的壯麗景色，小妤架起自拍棒合照。",
          "dialogues": [
            { "id": "p2_p4_d1", "speaker": "sakura", "text": "哇，風景好漂亮！大阪市區都在我們腳下呢！" },
            { "id": "p2_p4_d2", "speaker": "mama", "text": "爬上來真的很值得，爸爸你也別再喘了，看鏡頭笑一個！" }
          ]
        }
      ]
    },
    {
      "pageNumber": 3,
      "pageTitle": "第三天：日本環球影城歡樂無限與歸途",
      "panels": [
        {
          "panelNumber": 1,
          "image": "assets/images/p3_panel1.png",
          "description": "日本環球影城（USJ）的大地球前，小融戴著耀西帽子，小妤戴著葛來分多圍巾，興奮地朝大門奔跑。",
          "dialogues": [
            { "id": "p3_p1_d1", "speaker": "taiga", "text": "是瑪利歐！我要去超級任天堂世界玩！" },
            { "id": "p3_p1_d2", "speaker": "sakura", "text": "我要去哈利波特園區喝奶油啤酒！快走快走！" }
          ]
        },
        {
          "panelNumber": 2,
          "image": "assets/images/p3_panel2.png",
          "description": "在飛天翼龍雲霄飛車上，軌道劇烈翻轉。爸爸嚇得閉眼瘋狂慘叫，小妤和小融高舉雙手大呼過癮。",
          "dialogues": [
            { "id": "p3_p2_d1", "speaker": "papa", "text": "救命啊——！我為什麼會在這裡——！" },
            { "id": "p3_p2_d2", "speaker": "sakura", "text": "超好玩！太刺激了！爸爸你張開眼睛看啦！" }
          ]
        },
        {
          "panelNumber": 3,
          "image": "assets/images/p3_panel3.png",
          "description": "夕陽餘暉下，一家人坐在園區長椅上吃著小小兵爆米花，小融累得打瞌睡，媽媽笑著整理滿滿的戰利品。",
          "dialogues": [
            { "id": "p3_p3_d1", "speaker": "mama", "text": "今天買了好多紀念品，真是滿載而歸！" },
            { "id": "p3_p3_d2", "speaker": "papa", "text": "我的腿已經不是我的了，但孩子們開心就值得了。" }
          ]
        },
        {
          "panelNumber": 4,
          "image": "assets/images/p3_panel4.png",
          "description": "回程的飛機客艙裡，爸爸、媽媽與小融都在熟睡。小妤靠在窗邊，看著手機裡這幾天的歡樂合照，心滿意足地微笑。",
          "dialogues": [
            { "id": "p3_p4_d1", "speaker": "sakura", "text": "五天四夜過得好快，這次大阪之旅真的太棒了，下次還要再來！" }
          ]
        }
      ]
    }
  ]
};

// Global State variables
let currentPage = 0;
let currentAudio = null;
let isPlayingSequence = false;
let sequenceDialogues = [];
let currentSequenceIndex = 0;
let sequenceTimeout = null;
let activeSequenceButton = null;
let sequenceType = ''; // 'page' or 'panel'

// DOM Elements
const mangaPagesContainer = document.getElementById('manga-pages-container');
const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const pageIndicatorText = document.getElementById('page-text');
const dots = document.querySelectorAll('.page-indicator .dot');
const themeToggleBtn = document.getElementById('theme-toggle');
const helpBtn = document.getElementById('help-btn');
const helpModal = document.getElementById('help-modal');
const closeModalBtn = document.querySelector('.close-modal');
const startReadingBtn = document.getElementById('start-reading');
const globalAudioPlayer = document.getElementById('global-audio-player');

// Settings DOM Elements
const settingsBtn = document.getElementById('settings-btn');
const settingsModal = document.getElementById('settings-modal');
const closeSettingsModalBtn = document.querySelector('.close-settings-modal');
const audioModeSelect = document.getElementById('audio-mode-select');
const systemVoiceSettings = document.getElementById('system-voice-settings');
const voiceSpeedSlider = document.getElementById('voice-speed-slider');
const speedValueDisplay = document.getElementById('speed-value-display');

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
    renderMangaPages(storyData);
    setupEventListeners();
    setupSettingsEvents();
    
    // Load native voices
    if ('speechSynthesis' in window) {
        populateVoices();
        window.speechSynthesis.onvoiceschanged = populateVoices;
    }
});

// Load user preferred theme
function loadTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        document.body.classList.remove('dark-theme');
        themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    } else {
        document.body.classList.add('dark-theme');
        document.body.classList.remove('light-theme');
        themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
    }
}

// Render dynamic manga pages from JSON data
function renderMangaPages(data) {
    mangaPagesContainer.innerHTML = '';
    
    data.pages.forEach((page) => {
        const pageEl = document.createElement('section');
        pageEl.className = 'book-page';
        pageEl.id = `page-${page.pageNumber}`;
        pageEl.setAttribute('data-page', page.pageNumber);
        
        let panelsHTML = '';
        
        page.panels.forEach((panel) => {
            let dialoguesHTML = '';
            
            panel.dialogues.forEach((d) => {
                const charName = data.characters[d.speaker]?.name.split(' ')[0] || d.speaker;
                dialoguesHTML += `
                    <div class="dialogue-item" id="item-${d.id}" data-id="${d.id}" data-text="${d.text}" data-speaker="${d.speaker}">
                        <span class="dialogue-speaker speaker-${d.speaker}">${charName}</span>
                        <p class="dialogue-text">${d.text}</p>
                    </div>
                `;
            });
            
            panelsHTML += `
                <div class="manga-panel" id="panel-${page.pageNumber}-${panel.panelNumber}">
                    <div class="panel-header-badge">PANEL ${panel.panelNumber}</div>
                    <div class="panel-img-container">
                        <img src="${panel.image}" alt="Page ${page.pageNumber} Panel ${panel.panelNumber}" class="panel-img" loading="lazy">
                    </div>
                    <div class="panel-dialogue-box">
                        <div class="panel-dialogue-header">
                            <span class="panel-play-title"><i class="fa-solid fa-comments"></i> 繁體中文台詞</span>
                            <button class="panel-play-btn" data-page="${page.pageNumber}" data-panel="${panel.panelNumber}">
                                <i class="fa-solid fa-circle-play"></i> 播放語音
                            </button>
                        </div>
                        ${dialoguesHTML}
                    </div>
                </div>
            `;
        });
        
        pageEl.innerHTML = `
            <div class="manga-page-layout">
                <div class="manga-page-header">
                    <h2 class="manga-page-title">${page.pageTitle}</h2>
                    <div class="page-controls-top">
                        <button class="page-play-btn" data-page="${page.pageNumber}">
                            <i class="fa-solid fa-circle-play"></i> 播放整頁對白
                        </button>
                    </div>
                </div>
                <div class="manga-grid">
                    ${panelsHTML}
                </div>
            </div>
        `;
        
        mangaPagesContainer.appendChild(pageEl);
    });
    
    setupPlayButtons();
}

// Wire up events on play buttons
function setupPlayButtons() {
    // Single panel dialogue sequence play buttons
    document.querySelectorAll('.panel-play-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const pageNum = parseInt(btn.getAttribute('data-page'));
            const panelNum = parseInt(btn.getAttribute('data-panel'));
            togglePanelAutoplay(pageNum, panelNum, btn);
        });
    });

    // Page autoplay buttons
    document.querySelectorAll('.page-play-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pageNum = parseInt(btn.getAttribute('data-page'));
            togglePageAutoplay(pageNum, btn);
        });
    });
}

// Populate browser native synthesis Chinese voices
function populateVoices() {
    if (!('speechSynthesis' in window)) return;
    
    const voices = window.speechSynthesis.getVoices();
    // Filter voices that support Chinese
    const zhVoices = voices.filter(v => v.lang.includes('zh') || v.lang.includes('ZH'));
    
    const characterSelects = ['voice-sakura', 'voice-taiga', 'voice-papa', 'voice-mama'];
    
    characterSelects.forEach(id => {
        const select = document.getElementById(id);
        if (!select) return;
        
        const currentValue = select.value;
        select.innerHTML = '';
        
        if (zhVoices.length === 0) {
            const opt = document.createElement('option');
            opt.value = "";
            opt.textContent = "無本機中文語音";
            select.appendChild(opt);
            return;
        }
        
        zhVoices.forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.name;
            opt.textContent = `${v.name} (${v.lang})`;
            select.appendChild(opt);
        });
        
        // Restore selection or set smart gender defaults
        if (currentValue && Array.from(select.options).some(o => o.value === currentValue)) {
            select.value = currentValue;
        } else {
            const isFemaleSpeaker = id === 'voice-sakura' || id === 'voice-mama';
            
            // Search for female-sounding voices (e.g. Yating, Ting, Mei, Hui) or male-sounding (Zhiwei, YunJhe, Hanhan)
            let matchVoice = null;
            if (isFemaleSpeaker) {
                matchVoice = zhVoices.find(v => v.name.includes('Yating') || v.name.includes('Ting') || v.name.includes('Mei') || v.name.includes('Hui') || v.name.includes('Chen') || v.name.includes('Yu'));
            } else {
                matchVoice = zhVoices.find(v => v.name.includes('Zhiwei') || v.name.includes('Hanhan') || v.name.includes('YunJhe') || v.name.includes('Kuan') || v.name.includes('Kang') || v.name.includes('Danny'));
            }
            
            if (matchVoice) {
                select.value = matchVoice.name;
            } else if (zhVoices.length > 0) {
                select.value = zhVoices[0].name;
            }
        }
    });
}

// Handle dialogue audio playing (with Web Speech API fallback)
function playDialogue(id, text, itemNode, onEndedCallback) {
    stopAudio();
    clearAllHighlights();
    
    itemNode.classList.add('active');
    const panel = itemNode.closest('.manga-panel');
    if (panel) panel.classList.add('active');
    
    const audioMode = audioModeSelect.value;
    const speaker = itemNode.getAttribute('data-speaker');
    
    if (audioMode === 'system') {
        // Mode 2: Play custom browser native synthesis directly
        playCustomWebSpeech(text, speaker, () => {
            itemNode.classList.remove('active');
            if (panel) panel.classList.remove('active');
            if (onEndedCallback) onEndedCallback();
        });
    } else {
        // Mode 1: Play pre-generated MP3 (ms_ for Microsoft, el_ for ElevenLabs)
        const prefix = audioMode === 'ms_neural' ? 'ms_' : 'el_';
        const audioPath = `assets/audio/${prefix}${id}.mp3`;
        globalAudioPlayer.src = audioPath;
        
        // Set dynamic playback rate for Neural AI voices
        const customRate = parseFloat(voiceSpeedSlider.value);
        globalAudioPlayer.defaultPlaybackRate = customRate;
        globalAudioPlayer.playbackRate = customRate;
        globalAudioPlayer.onplay = () => {
            globalAudioPlayer.playbackRate = parseFloat(voiceSpeedSlider.value);
        };
        
        let playPromise = globalAudioPlayer.play();
        
        if (playPromise !== undefined) {
            playPromise.then(() => {
                globalAudioPlayer.onended = () => {
                    itemNode.classList.remove('active');
                    if (panel) panel.classList.remove('active');
                    if (onEndedCallback) onEndedCallback();
                };
            }).catch(err => {
                console.warn(`Local audio not found or playback failed for ${id}. Using Web Speech fallback.`, err);
                playCustomWebSpeech(text, speaker, () => {
                    itemNode.classList.remove('active');
                    if (panel) panel.classList.remove('active');
                    if (onEndedCallback) onEndedCallback();
                });
            });
        }
    }
}

// Custom SpeechSynthesis TTS with dynamic voice selection and rate/pitch modifiers
function playCustomWebSpeech(text, speaker, onEndedCallback) {
    if (!('speechSynthesis' in window)) {
        console.error('Web Speech API not supported in this browser.');
        if (onEndedCallback) onEndedCallback();
        return;
    }
    
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Load custom selected voice for speaker
    const select = document.getElementById(`voice-${speaker}`);
    const selectedVoiceName = select ? select.value : '';
    
    const voices = window.speechSynthesis.getVoices();
    const targetVoice = voices.find(v => v.name === selectedVoiceName);
    
    if (targetVoice) {
        utterance.voice = targetVoice;
        utterance.lang = targetVoice.lang;
    } else {
        // Fallback standard tw voice
        const fallback = voices.find(v => v.lang.includes('zh-TW') || v.lang.includes('zh-HK') || v.lang.includes('zh-CHT'));
        if (fallback) utterance.voice = fallback;
        utterance.lang = 'zh-TW';
    }
    
    // Load custom speed rate
    const customRate = parseFloat(voiceSpeedSlider.value);
    utterance.rate = customRate;
    
    // Load custom pitch rate
    const voicePitchSlider = document.getElementById('voice-pitch-slider');
    const customPitch = voicePitchSlider ? parseFloat(voicePitchSlider.value) : 1.0;
    utterance.pitch = customPitch;
    
    utterance.onend = () => {
        if (onEndedCallback) onEndedCallback();
    };
    
    utterance.onerror = (e) => {
        console.error('SpeechSynthesis error:', e);
        if (onEndedCallback) onEndedCallback();
    };
    
    window.speechSynthesis.speak(utterance);
}

// Play dialogue step in sequence
function playSequenceStep() {
    if (!isPlayingSequence || currentSequenceIndex >= sequenceDialogues.length) {
        stopAutoplay();
        return;
    }
    
    const d = sequenceDialogues[currentSequenceIndex];
    const item = document.getElementById(`item-${d.id}`);
    
    if (item) {
        playDialogue(d.id, d.text, item, () => {
            currentSequenceIndex++;
            if (currentSequenceIndex < sequenceDialogues.length) {
                sequenceTimeout = setTimeout(playSequenceStep, 700);
            } else {
                stopAutoplay();
            }
        });
    } else {
        currentSequenceIndex++;
        playSequenceStep();
    }
}

// Toggle Autoplay of all dialogues in a single panel
function togglePanelAutoplay(pageNum, panelNum, btn) {
    if (isPlayingSequence) {
        const wasThisBtn = activeSequenceButton === btn;
        stopAutoplay();
        if (wasThisBtn) return;
    }
    
    const pageData = storyData.pages.find(p => p.pageNumber === pageNum);
    const panelData = pageData ? pageData.panels.find(p => p.panelNumber === panelNum) : null;
    if (!panelData || !panelData.dialogues || panelData.dialogues.length === 0) return;
    
    isPlayingSequence = true;
    sequenceType = 'panel';
    activeSequenceButton = btn;
    sequenceDialogues = panelData.dialogues;
    currentSequenceIndex = 0;
    
    btn.classList.add('playing');
    btn.innerHTML = '<i class="fa-solid fa-circle-pause"></i> 停止播放';
    
    playSequenceStep();
}

// Toggle Autoplay of all dialogues on a page
function togglePageAutoplay(pageNum, btn) {
    if (isPlayingSequence) {
        const wasThisBtn = activeSequenceButton === btn;
        stopAutoplay();
        if (wasThisBtn) return;
    }
    
    const pageData = storyData.pages.find(p => p.pageNumber === pageNum);
    if (!pageData) return;
    
    isPlayingSequence = true;
    sequenceType = 'page';
    activeSequenceButton = btn;
    sequenceDialogues = [];
    
    pageData.panels.forEach(panel => {
        panel.dialogues.forEach(d => {
            sequenceDialogues.push(d);
        });
    });
    
    currentSequenceIndex = 0;
    
    btn.classList.add('playing');
    btn.innerHTML = '<i class="fa-solid fa-circle-pause"></i> 停止播放';
    
    playSequenceStep();
}

// Stop current playing audio/speech
function stopAudio() {
    globalAudioPlayer.pause();
    globalAudioPlayer.currentTime = 0;
    
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
}

// Stop the page/panel autoplay loops
function stopAutoplay() {
    isPlayingSequence = false;
    if (sequenceTimeout) {
        clearTimeout(sequenceTimeout);
        sequenceTimeout = null;
    }
    
    if (activeSequenceButton) {
        activeSequenceButton.classList.remove('playing');
        if (sequenceType === 'panel') {
            activeSequenceButton.innerHTML = `<i class="fa-solid fa-circle-play"></i> 播放語音`;
        } else {
            activeSequenceButton.innerHTML = `<i class="fa-solid fa-circle-play"></i> 播放整頁對白`;
        }
        activeSequenceButton = null;
    }
    
    clearAllHighlights();
}

// Clear all dialogue and panel visual highlights
function clearAllHighlights() {
    document.querySelectorAll('.dialogue-item').forEach(item => {
        item.classList.remove('active');
    });
    
    document.querySelectorAll('.manga-panel').forEach(panel => {
        panel.classList.remove('active');
    });
}

// Setup Event Listeners for main layout controls
function setupEventListeners() {
    prevPageBtn.addEventListener('click', prevPage);
    nextPageBtn.addEventListener('click', nextPage);
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            prevPage();
        } else if (e.key === 'ArrowRight') {
            nextPage();
        }
    });
    
    dots.forEach(dot => {
        dot.addEventListener('click', () => {
            const targetPage = parseInt(dot.getAttribute('data-page'));
            goToPage(targetPage);
        });
    });
    
    startReadingBtn.addEventListener('click', () => {
        goToPage(1);
    });
    
    themeToggleBtn.addEventListener('click', () => {
        if (document.body.classList.contains('dark-theme')) {
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
            themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
            localStorage.setItem('theme', 'light');
        } else {
            document.body.classList.remove('light-theme');
            document.body.classList.add('dark-theme');
            themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
            localStorage.setItem('theme', 'dark');
        }
    });
    
    // Help Modal events
    helpBtn.addEventListener('click', () => {
        helpModal.classList.add('active');
    });
    
    closeModalBtn.addEventListener('click', () => {
        helpModal.classList.remove('active');
    });
    
    // Character cards click to zoom modal
    const charCards = document.querySelectorAll('.char-card');
    const charModal = document.getElementById('char-modal');
    const closeCharModalBtn = document.querySelector('.close-char-modal');
    
    charCards.forEach(card => {
        card.addEventListener('click', () => {
            const charKey = card.getAttribute('data-char');
            const charInfo = storyData.characters[charKey];
            if (charInfo) {
                document.getElementById('char-modal-img').src = `assets/characters/${charKey}.png`;
                document.getElementById('char-modal-name').textContent = charInfo.name;
                document.getElementById('char-modal-role').textContent = charInfo.role;
                document.getElementById('char-modal-desc').textContent = charInfo.description;
                charModal.classList.add('active');
            }
        });
    });
    
    closeCharModalBtn.addEventListener('click', () => {
        charModal.classList.remove('active');
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === helpModal) {
            helpModal.classList.remove('active');
        }
        if (e.target === charModal) {
            charModal.classList.remove('active');
        }
    });
}

// Setup Event Listeners for settings panel
function setupSettingsEvents() {
    settingsBtn.addEventListener('click', () => {
        settingsModal.classList.add('active');
    });
    
    closeSettingsModalBtn.addEventListener('click', () => {
        settingsModal.classList.remove('active');
    });
    
    // Trigger subpanel visibility on audio mode change
    audioModeSelect.addEventListener('change', () => {
        if (audioModeSelect.value === 'system') {
            systemVoiceSettings.style.display = 'flex';
        } else {
            systemVoiceSettings.style.display = 'none';
        }
    });
    
    // Update rate slider value display
    voiceSpeedSlider.addEventListener('input', () => {
        speedValueDisplay.textContent = `${parseFloat(voiceSpeedSlider.value).toFixed(2)}x`;
    });
    
    // Update pitch slider value display
    const voicePitchSlider = document.getElementById('voice-pitch-slider');
    const pitchValueDisplay = document.getElementById('pitch-value-display');
    if (voicePitchSlider && pitchValueDisplay) {
        voicePitchSlider.addEventListener('input', () => {
            pitchValueDisplay.textContent = `${parseFloat(voicePitchSlider.value).toFixed(2)}x`;
        });
    }
    
    // Click outside to closesettings modal
    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.classList.remove('active');
        }
    });

    // Character voice audition buttons
    document.querySelectorAll('.preview-voice-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const speaker = btn.getAttribute('data-speaker');
            playCharacterPreview(speaker);
        });
    });
}

// Function to preview character voice sample based on current selected mode
function playCharacterPreview(speaker) {
    let sampleDialog = null;
    
    // Find the first dialogue belonging to this speaker in storyData
    for (const page of storyData.pages) {
        for (const panel of page.panels) {
            for (const d of panel.dialogues) {
                if (d.speaker === speaker) {
                    sampleDialog = d;
                    break;
                }
            }
            if (sampleDialog) break;
        }
        if (sampleDialog) break;
    }
    
    if (sampleDialog) {
        const audioMode = audioModeSelect.value;
        stopAudio();
        
        if (audioMode === 'system') {
            playCustomWebSpeech(sampleDialog.text, speaker);
        } else {
            const prefix = audioMode === 'ms_neural' ? 'ms_' : 'el_';
            const audioPath = `assets/audio/${prefix}${sampleDialog.id}.mp3`;
            globalAudioPlayer.src = audioPath;
            
            const customRate = parseFloat(voiceSpeedSlider.value);
            globalAudioPlayer.defaultPlaybackRate = customRate;
            globalAudioPlayer.playbackRate = customRate;
            globalAudioPlayer.onplay = () => {
                globalAudioPlayer.playbackRate = parseFloat(voiceSpeedSlider.value);
            };
            
            globalAudioPlayer.play().catch(err => {
                console.warn(`Preview play failed for ${audioPath}. Using Web Speech fallback.`, err);
                playCustomWebSpeech(sampleDialog.text, speaker);
            });
        }
    }
}

// Page Navigation Logic
function goToPage(pageIdx) {
    if (!storyData && pageIdx > 0) return;
    
    stopAutoplay();
    stopAudio();
    
    const currentPageNode = document.querySelector(`.book-page.active`);
    if (currentPageNode) {
        currentPageNode.classList.remove('active');
    }
    
    currentPage = pageIdx;
    
    const targetPageNode = document.getElementById(`page-${pageIdx}`);
    if (targetPageNode) {
        targetPageNode.classList.add('active');
        document.querySelector('.ebook-container').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    dots.forEach(dot => {
        const dotPage = parseInt(dot.getAttribute('data-page'));
        if (dotPage === pageIdx) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
    
    if (pageIdx === 0) {
        pageIndicatorText.textContent = '人物介紹';
        prevPageBtn.disabled = true;
        nextPageBtn.disabled = false;
    } else {
        pageIndicatorText.textContent = `第 ${pageIdx} 頁：${storyData.pages[pageIdx - 1].pageTitle.split('：')[0]}`;
        prevPageBtn.disabled = false;
        if (pageIdx === storyData.pages.length) {
            nextPageBtn.disabled = true;
        } else {
            nextPageBtn.disabled = false;
        }
    }
}

function prevPage() {
    if (currentPage > 0) {
        goToPage(currentPage - 1);
    }
}

function nextPage() {
    const totalPages = storyData ? storyData.pages.length : 0;
    if (currentPage < totalPages) {
        goToPage(currentPage + 1);
    }
}
