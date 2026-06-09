// ==========================================================================
// Padlet-like Message Board Core JavaScript Application
// ==========================================================================

// Prepopulated high-fidelity demo data based on user screenshot
const DEFAULT_DATA = {
  boardTitle: "資材課工作交接與品質管理看板",
  boardDescription: "資材部公告、品質管理與工作交接、SOP規章、稽核巡檢與客訴改善追蹤看板 (雙擊空白處或點擊欄位下方 [+] 新增卡片)",
  bgType: "image",
  bgValue: "https://images.unsplash.com/photo-1531685250784-7569952593d2?q=80&w=1200", // Clean subtle texture background
  columns: [
    {
      id: "col-1",
      title: "最新公告與SOP規章",
      cards: [
        {
          id: "card-1-1",
          author: "課長",
          title: "格外品與久滯品處理管理辦法宣導",
          content: "針對格外品之處理與儲存管理辦法宣導，請資材人員及現場同仁務必遵守作業規範。相關流程及判定細則可參閱最新修訂的『C50110-INV-05 格外品處理、儲存管理辦法(3.0版)』文件與格外品久滯品流程圖。",
          link: "",
          image: "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?q=80&w=600",
          likes: 3,
          liked: true,
          comments: [
            { author: "資材小組長", body: "現場同仁已在今日早會上完成宣導，並將紙本流程圖張貼於看板。", timestamp: Date.now() - 1 * 24 * 60 * 60 * 1000 }
          ],
          timestamp: Date.now() - 2 * 24 * 60 * 60 * 1000
        },
        {
          id: "card-1-2",
          author: "儀校管理員",
          title: "2026年第二季儀器校正排程",
          content: "本季精密檢驗儀器及天平的年度外部校正排程已排定，請各實驗室同仁提早規劃配合儀器暫停使用的檢驗排程，以防影響出貨進度。",
          link: "",
          image: "",
          likes: 1,
          liked: false,
          comments: [],
          timestamp: Date.now() - 4 * 24 * 60 * 60 * 1000
        }
      ]
    },
    {
      id: "col-2",
      title: "品質異常通報",
      cards: [
        {
          id: "card-2-1",
          author: "資材專員",
          title: "A區原料入庫包裝密封不完整異常處理",
          content: "巡檢發現 A 區原料在進行入庫封口包裝時，部分封口有熱熔不良導致密封不完整的情況。已通知現場產線停機檢查封口溫度，並將受影響批次隔離，啟動格外品處置流程。",
          link: "",
          image: "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=600",
          likes: 2,
          liked: false,
          comments: [
            { author: "生管", body: "已安排檢驗員協同抽檢，正在釐清受影響的確切批號範圍。", timestamp: Date.now() - 6 * 3600 * 1000 }
          ],
          timestamp: Date.now() - 12 * 3600 * 1000
        },
        {
          id: "card-2-2",
          author: "進料檢驗(IQC)",
          title: "原料批次物性檢驗未達標通報",
          content: "今日進料檢驗中，發現某供應商提供之特定原料黏度物理性質未達標準規格。已發出拒收單，請倉儲同仁暫勿發料，並安排退貨程序。",
          link: "",
          image: "",
          likes: 0,
          liked: false,
          comments: [],
          timestamp: Date.now() - 1 * 24 * 60 * 60 * 1000
        }
      ]
    },
    {
      id: "col-3",
      title: "稽核與日常巡檢",
      cards: [
        {
          id: "card-3-1",
          author: "稽核組長",
          title: "軟管對刷稽核系統實施宣導",
          content: "各位稽核同仁請注意，新版『軟管對刷稽核系統』已正式上線。請同仁進行現場巡檢評分時，務必參照正式版 10 頁簡報規範與教學影片，確保稽核標準一致。",
          link: "",
          image: "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?q=80&w=600",
          likes: 4,
          liked: true,
          comments: [
            { author: "現場稽核員", body: "教學影片講得很清楚，特別是刷洗角度的判定標準與評分原則！", timestamp: Date.now() - 1 * 24 * 60 * 60 * 1000 }
          ],
          timestamp: Date.now() - 3 * 24 * 60 * 60 * 1000
        },
        {
          id: "card-3-2",
          author: "巡檢員",
          title: "無塵車間溫溼度及防塵點檢紀錄",
          content: "各無塵室車間今日每日點檢皆在合格規格內。空調加濕模組運作正常，本月落塵量檢驗安排於下週進行。",
          link: "",
          image: "",
          likes: 0,
          liked: false,
          comments: [],
          timestamp: Date.now() - 10 * 3600 * 1000
        }
      ]
    },
    {
      id: "col-4",
      title: "客訴與改善追蹤 (CAR)",
      cards: [
        {
          id: "card-4-1",
          author: "資材專員",
          title: "客戶反應產品外觀刮傷改善對策",
          content: "針對客戶反應上批出貨有外觀微小刮傷的問題，資材與品保已召開跨部門改善會議。決議在包裝輸送帶加裝保護防刮泡棉，並將外觀檢驗的刮傷判定加入首件檢查點。",
          link: "",
          image: "",
          likes: 2,
          liked: false,
          comments: [
            { author: "生產主管", body: "包裝輸送帶的保護泡棉已完成裝設，現場包裝人員也已完成防刮宣導。", timestamp: Date.now() - 5 * 3600 * 1000 }
          ],
          timestamp: Date.now() - 1 * 24 * 60 * 60 * 1000
        }
      ]
    },
    {
      id: "col-5",
      title: "回饋與建議",
      cards: [
        {
          id: "card-5-1",
          author: "資材課",
          title: "資材與品質知識宣導活動意見募集",
          content: "下半年的品質與交接宣導教育即將展開，各位同仁對宣導活動形式、品質競賽或是培訓課程有任何想法，歡迎隨時在此卡片下方留言或張貼新卡片建議！",
          link: "",
          image: "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?q=80&w=600",
          likes: 1,
          liked: false,
          comments: [],
          timestamp: Date.now() - 5 * 24 * 60 * 60 * 1000
        }
      ]
    }
  ]
};

// Application State
// Local Test Detection
const isLocalTestMode = window.location.protocol === "file:" || 
                        window.location.hostname === "localhost" || 
                        window.location.hostname === "127.0.0.1";

// Helper to get local date string YYYY-MM-DD
function getTodayString() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Master Data Structure
let masterData = {
  activeDate: getTodayString(),
  boards: {}
};

let state = {
  boardTitle: "",
  boardDescription: "",
  bgType: "",
  bgValue: "",
  columns: []
};

// DOM References
const appBackground = document.getElementById("appBackground");
const boardTitle = document.getElementById("boardTitle");
const boardDescription = document.getElementById("boardDescription");
const searchBar = document.getElementById("searchBar");
const clearSearch = document.getElementById("clearSearch");
const columnsWrapper = document.getElementById("columnsWrapper");
const addColumnBtn = document.getElementById("addColumnBtn");
const bgSettingsBtn = document.getElementById("bgSettingsBtn");

// Slideshow & Sharing DOM References
const slideshowBtn = document.getElementById("slideshowBtn");
const shareBtn = document.getElementById("shareBtn");
const slideshowOverlay = document.getElementById("slideshowOverlay");
const closeSlideshowBtn = document.getElementById("closeSlideshowBtn");
const prevSlideBtn = document.getElementById("prevSlideBtn");
const nextSlideBtn = document.getElementById("nextSlideBtn");
const playPauseSlideshowBtn = document.getElementById("playPauseSlideshowBtn");
const shareModal = document.getElementById("shareModal");
const closeShareModalBtn = document.getElementById("closeShareModalBtn");
const copyShareLinkBtn = document.getElementById("copyShareLinkBtn");
const shareLinkInput = document.getElementById("shareLinkInput");
const boardDatePicker = document.getElementById("boardDatePicker");
const datePickerWrapper = document.getElementById("datePickerWrapper");
const dataMenuBtn = document.getElementById("dataMenuBtn");
const dataDropdown = document.getElementById("dataDropdown");
const viewLogBtn = document.getElementById("viewLogBtn");

// Modals DOM
const cardModal = document.getElementById("cardModal");
const cardForm = document.getElementById("cardForm");
const cardIdInput = document.getElementById("cardId");
const columnIdInput = document.getElementById("columnId");
const cardAuthorInput = document.getElementById("cardAuthorInput");
const cardTitleInput = document.getElementById("cardTitleInput");
const cardContentInput = document.getElementById("cardContentInput");
const cardLinkInput = document.getElementById("cardLinkInput");
const cardImgInput = document.getElementById("cardImgInput");
const triggerUploadBtn = document.getElementById("triggerUploadBtn");
const cardImgFileInput = document.getElementById("cardImgFileInput");
const uploadProgressContainer = document.getElementById("uploadProgressContainer");
const imgPreviewContainer = document.getElementById("imgPreviewContainer");
const formImgPreview = document.getElementById("formImgPreview");
const removeImgPreviewBtn = document.getElementById("removeImgPreviewBtn");
const modalTitleText = document.getElementById("modalTitle");
const closeCardModalBtn = document.getElementById("closeCardModalBtn");
const cancelCardBtn = document.getElementById("cancelCardBtn");

const bgModal = document.getElementById("bgModal");
const closeBgModalBtn = document.getElementById("closeBgModalBtn");
const customBgInput = document.getElementById("customBgInput");
const applyCustomBgBtn = document.getElementById("applyCustomBgBtn");

// User Guide Modal DOM
const guideBtn = document.getElementById("guideBtn");
const guideModal = document.getElementById("guideModal");
const closeGuideModalBtn = document.getElementById("closeGuideModalBtn");
const closeGuideConfirmBtn = document.getElementById("closeGuideConfirmBtn");

// Admin Mode state & definitions
const ADMIN_PASSWORDS = ["1234", "7588555"];
let isAdminMode = sessionStorage.getItem("hsqa_is_admin") === "true";
let myCreatedCards = [];
try {
  myCreatedCards = JSON.parse(localStorage.getItem("hsqa_my_created_cards") || "[]");
} catch (e) {
  myCreatedCards = [];
}

const adminBadge = document.getElementById("adminBadge");
const adminLoginBtn = document.getElementById("adminLoginBtn");

// AI Assistant DOM Elements
const aiSidebar = document.getElementById("aiSidebar");
const aiSidebarBtn = document.getElementById("aiSidebarBtn");
const closeAiSidebarBtn = document.getElementById("closeAiSidebarBtn");
const aiSidebarOverlay = document.getElementById("aiSidebarOverlay");
const aiConfigBtn = document.getElementById("aiConfigBtn");
const aiWelcomeContainer = document.getElementById("aiWelcomeContainer");
const aiChatMessages = document.getElementById("aiChatMessages");
const aiChatInput = document.getElementById("aiChatInput");
const sendAiMessageBtn = document.getElementById("sendAiMessageBtn");
const aiStatusIndicator = document.getElementById("aiStatusIndicator");
const aiStatusText = document.getElementById("aiStatusText");
const aiPolishBtn = document.getElementById("aiPolishBtn");

// AI Key Modal DOM Elements
const aiKeyModal = document.getElementById("aiKeyModal");
const geminiApiKeyInput = document.getElementById("geminiApiKeyInput");
const cancelAiKeyBtn = document.getElementById("cancelAiKeyBtn");
const saveAiKeyBtn = document.getElementById("saveAiKeyBtn");
const closeAiKeyModalBtn = document.getElementById("closeAiKeyModalBtn");
const aiProviderSelect = document.getElementById("aiProviderSelect");
const apiKeyLabel = document.getElementById("apiKeyLabel");
const apiKeyHelpLink = document.getElementById("apiKeyHelpLink");

// Voice Input & Editing DOM Elements
const cardMicBtn = document.getElementById("cardMicBtn");
const aiMicBtn = document.getElementById("aiMicBtn");
const aiPolishType = document.getElementById("aiPolishType");



// Columns Action Dropdown Context Menu
const colMenuDropdown = document.getElementById("colMenuDropdown");
const colRenameBtn = document.getElementById("colRenameBtn");
const colDeleteBtn = document.getElementById("colDeleteBtn");
let activeColMenuId = null;

// Toast DOM
const toastNotification = document.getElementById("toastNotification");

// Active search query
let searchQuery = "";

// ==========================================================================
// Initialization & Storage Methods
// ==========================================================================

// Google Apps Script Database Web App URL
const GAS_API_URL = "https://script.google.com/macros/s/AKfycbzz7-d5MDdvPZFGAvR2DH67QPtEAurA-v1OycCOQU0YgpsqsjylV9LWNE_nnthM-Kz-/exec";

// DOM Reference for Sync Indicator
const syncStatus = document.getElementById("syncStatus");

function updateSyncIndicator(statusType) {
  if (!syncStatus) return;
  
  let html = "";
  if (statusType === "loading") {
    html = `<i data-lucide="loader" class="animate-spin" style="width: 12px; height: 12px;"></i> 載入中...`;
    syncStatus.style.color = "#a5b4fc";
    syncStatus.style.background = "rgba(165, 180, 252, 0.12)";
    syncStatus.style.borderColor = "rgba(165, 180, 252, 0.2)";
  } else if (statusType === "saving") {
    html = `<i data-lucide="refresh-cw" class="animate-spin" style="width: 12px; height: 12px;"></i> 同步中...`;
    syncStatus.style.color = "#fcd34d";
    syncStatus.style.background = "rgba(252, 211, 77, 0.12)";
    syncStatus.style.borderColor = "rgba(252, 211, 77, 0.2)";
  } else if (statusType === "synced") {
    html = `<i data-lucide="cloud" style="width: 12px; height: 12px;"></i> 雲端已同步`;
    syncStatus.style.color = "#34d399";
    syncStatus.style.background = "rgba(52, 211, 153, 0.12)";
    syncStatus.style.borderColor = "rgba(52, 211, 153, 0.2)";
  } else if (statusType === "offline") {
    html = `<i data-lucide="cloud-off" style="width: 12px; height: 12px;"></i> 本機模式`;
    syncStatus.style.color = "#94a3b8";
    syncStatus.style.background = "rgba(148, 163, 184, 0.12)";
    syncStatus.style.borderColor = "rgba(148, 163, 184, 0.2)";
  } else if (statusType === "error") {
    html = `<i data-lucide="alert-circle" style="width: 12px; height: 12px;"></i> 同步失敗`;
    syncStatus.style.color = "#f87171";
    syncStatus.style.background = "rgba(248, 113, 113, 0.12)";
    syncStatus.style.borderColor = "rgba(248, 113, 113, 0.2)";
  }
  
  syncStatus.innerHTML = html;
  lucide.createIcons();
}

function updateAdminUI() {
  if (!adminBadge || !adminLoginBtn) return;
  
  if (isAdminMode) {
    adminBadge.style.display = "inline-flex";
    adminLoginBtn.innerHTML = `<i data-lucide="shield-off"></i> <span>登出管理員</span>`;
    if (addColumnBtn) addColumnBtn.style.display = "inline-flex";
    if (datePickerWrapper) datePickerWrapper.style.display = "inline-flex";
    
    // Unlock editable board header
    boardTitle.contentEditable = true;
    boardDescription.contentEditable = true;
  } else {
    adminBadge.style.display = "none";
    adminLoginBtn.innerHTML = `<i data-lucide="shield-check"></i> <span>管理員登入</span>`;
    if (addColumnBtn) addColumnBtn.style.display = "none";
    if (datePickerWrapper) datePickerWrapper.style.display = "none";
    
    // Lock editable board header
    boardTitle.contentEditable = false;
    boardDescription.contentEditable = false;
  }
  lucide.createIcons();
}

function toggleAdminMode() {
  if (isAdminMode) {
    isAdminMode = false;
    sessionStorage.removeItem("hsqa_is_admin");
    showToast("已登出管理員模式");
    updateAdminUI();
    renderBoard();
  } else {
    const pw = prompt("請輸入管理員密碼以啟用管理權限：");
    if (pw === null) return;
    if (ADMIN_PASSWORDS.includes(pw)) {
      isAdminMode = true;
      sessionStorage.setItem("hsqa_is_admin", "true");
      showToast("已登入管理員模式！");
      updateAdminUI();
      renderBoard();
    } else {
      alert("密碼錯誤，管理員登入失敗。");
    }
  }
}

// ==========================================================================
// Multi-Date Boards Logic
// ==========================================================================

function createNewBoardForDate(date) {
  let templateColumns = [];
  
  // Find a board to clone structure from
  if (masterData.boards) {
    const dates = Object.keys(masterData.boards).sort().reverse();
    if (dates.length > 0) {
      const mostRecentBoard = masterData.boards[dates[0]];
      if (mostRecentBoard && Array.isArray(mostRecentBoard.columns)) {
        templateColumns = mostRecentBoard.columns.map(col => ({
          id: col.id,
          title: col.title,
          cards: []
        }));
      }
    }
  }
  
  // Fallback to default if no columns found
  if (templateColumns.length === 0) {
    templateColumns = JSON.parse(JSON.stringify(DEFAULT_DATA.columns)).map(col => {
      col.cards = [];
      return col;
    });
  }
  
  return {
    boardTitle: "品保課協作與品質管理看板 (" + date + ")",
    boardDescription: DEFAULT_DATA.boardDescription,
    bgType: DEFAULT_DATA.bgType,
    bgValue: DEFAULT_DATA.bgValue,
    columns: templateColumns
  };
}

function migrateData(data) {
  if (!data) return null;
  
  if (data.boards && typeof data.boards === 'object') {
    if (!data.activeDate) {
      data.activeDate = getTodayString();
    }
    return data;
  }
  
  if (data.boardTitle && Array.isArray(data.columns)) {
    const today = getTodayString();
    return {
      activeDate: today,
      boards: {
        [today]: data
      }
    };
  }
  
  return null;
}

function setupDefaultMasterData() {
  const todayStr = getTodayString();
  masterData = {
    activeDate: todayStr,
    boards: {
      [todayStr]: JSON.parse(JSON.stringify(DEFAULT_DATA))
    }
  };
  updateSyncIndicator("offline");
}

function setActiveBoardAndInit() {
  const targetDate = masterData.activeDate || getTodayString();
  
  if (!masterData.boards[targetDate]) {
    masterData.boards[targetDate] = createNewBoardForDate(targetDate);
  }
  
  state = masterData.boards[targetDate];
  
  if (boardDatePicker) {
    boardDatePicker.value = targetDate;
  }
  
  // Keep URL in sync on initial load without page reload
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('date') !== targetDate) {
    const newUrl = window.location.protocol + "//" + window.location.host + window.location.pathname + "?date=" + targetDate;
    window.history.replaceState({ path: newUrl }, '', newUrl);
  }
  
  completeInit();
}

// ==========================================================================
// Slideshow Mode Logic
// ==========================================================================

let slideshowCards = [];
let currentSlideIndex = 0;
let isAutoplay = false;
let autoplayInterval = null;

function startSlideshow() {
  slideshowCards = [];
  state.columns.forEach(col => {
    col.cards.forEach(card => {
      slideshowCards.push({
        ...card,
        colTitle: col.title
      });
    });
  });
  
  currentSlideIndex = 0;
  
  if (slideshowOverlay) {
    slideshowOverlay.style.display = "flex";
    document.body.style.overflow = "hidden";
    renderSlide();
  }
}

function closeSlideshow() {
  stopAutoplay();
  if (slideshowOverlay) {
    slideshowOverlay.style.display = "none";
    document.body.style.overflow = "";
  }
}

function renderSlide() {
  const slideTitle = document.getElementById("slideTitle");
  const slideContent = document.getElementById("slideContent");
  const slideColBadge = document.getElementById("slideColBadge");
  const slideMeta = document.getElementById("slideMeta");
  const slideImageContainer = document.getElementById("slideImageContainer");
  const slideImage = document.getElementById("slideImage");
  const slideLinkContainer = document.getElementById("slideLinkContainer");
  const slideLink = document.getElementById("slideLink");
  const slideLinkLabel = document.getElementById("slideLinkLabel");
  const slideCounter = document.getElementById("slideCounter");
  
  if (slideshowCards.length === 0) {
    slideColBadge.innerText = "系統提示";
    slideMeta.innerText = "Info";
    slideTitle.innerText = "看板尚無卡片";
    slideContent.innerText = "目前此日期的看板上沒有任何卡片。\n請先點選欄位下方 [+] 新增卡片後，再開啟投影片放映。";
    slideImageContainer.style.display = "none";
    slideLinkContainer.style.display = "none";
    slideCounter.innerText = "0 / 0";
    return;
  }
  
  const card = slideshowCards[currentSlideIndex];
  
  slideColBadge.innerText = card.colTitle || "一般";
  slideMeta.innerText = `${card.author || "訪客"} • ${timeAgo(card.timestamp)}`;
  slideTitle.innerText = card.title || "";
  slideContent.innerText = card.content || "";
  
  if (card.image) {
    slideImage.src = card.image;
    slideImageContainer.style.display = "block";
  } else {
    slideImageContainer.style.display = "none";
  }
  
  if (card.link) {
    slideLink.href = card.link;
    try {
      const urlObj = new URL(card.link);
      slideLinkLabel.innerText = "打開連結 (" + urlObj.hostname + ")";
    } catch(e) {
      slideLinkLabel.innerText = "打開連結";
    }
    slideLinkContainer.style.display = "block";
  } else {
    slideLinkContainer.style.display = "none";
  }
  
  slideCounter.innerText = `${currentSlideIndex + 1} / ${slideshowCards.length}`;
}

function nextSlide() {
  if (slideshowCards.length === 0) return;
  currentSlideIndex = (currentSlideIndex + 1) % slideshowCards.length;
  renderSlide();
}

function prevSlide() {
  if (slideshowCards.length === 0) return;
  currentSlideIndex = (currentSlideIndex - 1 + slideshowCards.length) % slideshowCards.length;
  renderSlide();
}

function toggleAutoplay() {
  if (isAutoplay) {
    stopAutoplay();
  } else {
    startAutoplay();
  }
}

function startAutoplay() {
  if (slideshowCards.length === 0) return;
  isAutoplay = true;
  if (playPauseSlideshowBtn) {
    playPauseSlideshowBtn.innerHTML = `<i data-lucide="pause" style="width: 16px; height: 16px;"></i>`;
    lucide.createIcons();
  }
  autoplayInterval = setInterval(() => {
    nextSlide();
  }, 4000);
}

function stopAutoplay() {
  isAutoplay = false;
  if (playPauseSlideshowBtn) {
    playPauseSlideshowBtn.innerHTML = `<i data-lucide="play" style="width: 16px; height: 16px;"></i>`;
    lucide.createIcons();
  }
  if (autoplayInterval) {
    clearInterval(autoplayInterval);
    autoplayInterval = null;
  }
}

// ==========================================================================
// Sharing & QR Code Logic
// ==========================================================================

function openShareModal() {
  const currentUrl = (window.location.hostname === "localhost" || window.location.protocol === "file:") 
    ? "https://hongsheng-qa-board.netlify.app" 
    : window.location.href;
    
  if (shareLinkInput) {
    shareLinkInput.value = currentUrl;
  }
  
  const qrBox = document.getElementById("shareQrCode");
  if (qrBox) {
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(currentUrl)}`;
    qrBox.innerHTML = `<img src="${qrUrl}" alt="分享 QR Code" style="width: 150px; height: 150px; border-radius: 4px;">`;
  }
  
  if (shareModal) {
    shareModal.classList.add("show");
  }
}

function closeShareModal() {
  if (shareModal) {
    shareModal.classList.remove("show");
  }
}

function copyShareLink() {
  if (!shareLinkInput) return;
  shareLinkInput.select();
  shareLinkInput.setSelectionRange(0, 99999);
  navigator.clipboard.writeText(shareLinkInput.value)
    .then(() => {
      showToast("網址已成功複製到剪貼簿！");
    })
    .catch(err => {
      showToast("複製失敗，請手動選取複製", "danger");
    });
}

// Google Drive URL Auto-converter helper
function convertDriveLink(url) {
  if (!url) return url;
  // Match standard share link: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
  const match1 = url.match(/\/file\/d\/([a-zA-Z0-9_-]+)/);
  if (match1 && match1[1]) {
    return `https://drive.google.com/uc?export=view&id=${match1[1]}`;
  }
  // Match open/id link: https://drive.google.com/open?id=FILE_ID
  const match2 = url.match(/id=([a-zA-Z0-9_-]+)/);
  if (match2 && match2[1] && url.includes("drive.google.com")) {
    return `https://drive.google.com/uc?export=view&id=${match2[1]}`;
  }
  return url;
}

// ==========================================================================
// Main Lifecycle Operations
// ==========================================================================

function init() {
  updateSyncIndicator("loading");
  
  // Local test mode check
  const localTestBadge = document.getElementById("localTestBadge");
  if (isLocalTestMode) {
    if (localTestBadge) localTestBadge.style.display = "inline-flex";
    updateSyncIndicator("offline");
  } else {
    if (localTestBadge) localTestBadge.style.display = "none";
  }
  
  updateAdminUI();
  updateAiStatus();
  
  // Check URL query parameters for custom date (e.g. ?date=2026-06-04)
  const urlParams = new URLSearchParams(window.location.search);
  const dateParam = urlParams.get('date');
  const todayStr = getTodayString();
  
  let initialDate = todayStr;
  if (dateParam && /^\d{4}-\d{2}-\d{2}$/.test(dateParam)) {
    initialDate = dateParam;
  }
  masterData.activeDate = initialDate;
  
  if (boardDatePicker) {
    boardDatePicker.value = initialDate;
  }
  
  if (isLocalTestMode) {
    const testData = localStorage.getItem("padlet_board_data_test");
    if (testData) {
      try {
        const parsed = JSON.parse(testData);
        const migrated = migrateData(parsed);
        if (migrated) {
          masterData = migrated;
        } else {
          throw new Error("Could not migrate");
        }
      } catch (e) {
        setupDefaultMasterData();
      }
    } else {
      setupDefaultMasterData();
    }
    setActiveBoardAndInit();
    showToast("🧪 本機測試模式已啟用 (使用獨立儲存)");
    return;
  }
  
  // Try loading from GAS Database first
  fetch(GAS_API_URL)
    .then(response => {
      if (!response.ok) throw new Error("HTTP error " + response.status);
      return response.json();
    })
    .then(data => {
      const migrated = migrateData(data);
      if (migrated) {
        masterData = migrated;
        localStorage.setItem("padlet_board_data", JSON.stringify(masterData));
        updateSyncIndicator("synced");
        showToast("已從雲端載入最新資料");
      } else {
        throw new Error("Invalid schema");
      }
      setActiveBoardAndInit();
    })
    .catch(err => {
      console.warn("Could not load from cloud, loading from local storage:", err);
      const savedData = localStorage.getItem("padlet_board_data");
      if (savedData) {
        try {
          const parsed = JSON.parse(savedData);
          const migrated = migrateData(parsed);
          if (migrated) {
            masterData = migrated;
            updateSyncIndicator("offline");
            showToast("已載入本機快取資料 (離線模式)");
          } else {
            throw new Error("Migration failed");
          }
        } catch (e) {
          setupDefaultMasterData();
        }
      } else {
        setupDefaultMasterData();
      }
      setActiveBoardAndInit();
    });
}

function updateLogButtonUI() {
  if (!viewLogBtn) return;
  if (masterData && masterData.logSpreadsheetUrl) {
    viewLogBtn.href = masterData.logSpreadsheetUrl;
    viewLogBtn.style.display = "flex";
  } else {
    viewLogBtn.style.display = "none";
  }
}

let isListenersSetup = false;
function completeInit() {
  // Set Title & Descr text
  boardTitle.innerText = state.boardTitle || "";
  boardDescription.innerText = state.boardDescription || "";

  // Render Page
  updateBackground();
  renderBoard();
  
  if (!isListenersSetup) {
    setupEventListeners();
    isListenersSetup = true;
  }
  
  // Update log spreadsheet link if available
  updateLogButtonUI();
  
  // Build Lucide icons
  lucide.createIcons();
}

function saveState(actionName = "同步資料", targetTitle = "", detail = "") {
  // Update current active board inside masterData
  const activeDate = masterData.activeDate || getTodayString();
  masterData.boards[activeDate] = state;
  
  if (isLocalTestMode) {
    localStorage.setItem("padlet_board_data_test", JSON.stringify(masterData));
    updateSyncIndicator("offline");
    return;
  }
  
  // Save locally first for instant feedback
  localStorage.setItem("padlet_board_data", JSON.stringify(masterData));
  
  updateSyncIndicator("saving");
  
  // Format the post payload with log details
  const payload = {
    action: "syncData",
    boardData: masterData,
    logAction: actionName,
    logTarget: targetTitle,
    logDetail: detail
  };
  
  // Sync to GAS Backend in background
  // Content-Type text/plain prevents CORS preflight OPTIONS request
  fetch(GAS_API_URL, {
    method: "POST",
    mode: "cors",
    body: JSON.stringify(payload)
  })
    .then(res => {
      if (!res.ok) throw new Error("Sync failed");
      return res.json();
    })
    .then(data => {
      if (data && data.status === "success") {
        updateSyncIndicator("synced");
      } else {
        throw new Error(data.message || "Unknown error");
      }
    })
    .catch(err => {
      console.error("Cloud synchronization failed:", err);
      updateSyncIndicator("error");
      showToast("同步至雲端失敗，資料已儲存於本機", "danger");
    });
}

function showToast(message, type = "info") {
  const textEl = toastNotification.querySelector(".toast-message");
  const iconEl = toastNotification.querySelector(".toast-icon");
  
  textEl.innerText = message;
  toastNotification.className = "toast-notification show";
  
  // Optional color shift based on status
  if (type === "danger") {
    toastNotification.style.borderColor = "var(--danger-color)";
    iconEl.setAttribute("data-lucide", "alert-circle");
  } else {
    toastNotification.style.borderColor = "var(--primary-color)";
    iconEl.setAttribute("data-lucide", "info");
  }
  lucide.createIcons();
  
  setTimeout(() => {
    toastNotification.className = "toast-notification";
  }, 3000);
}

// ==========================================================================
// UI Rendering Functions
// ==========================================================================

function updateBackground() {
  if (state.bgType === "color") {
    appBackground.style.backgroundImage = "none";
    appBackground.style.backgroundColor = state.bgValue;
    appBackground.style.background = state.bgValue; // supports gradients
  } else {
    appBackground.style.backgroundImage = `url('${state.bgValue}')`;
    appBackground.style.backgroundSize = "cover";
    appBackground.style.backgroundPosition = "center";
  }
}

function renderBoard() {
  columnsWrapper.innerHTML = "";
  
  state.columns.forEach(column => {
    const colEl = document.createElement("div");
    colEl.className = "board-column";
    colEl.dataset.columnId = column.id;
    
    // Drag & Drop for Columns (Admin Mode Only)
    if (isAdminMode) {
      colEl.setAttribute("draggable", "true");
      
      colEl.addEventListener("dragstart", (e) => {
        // Prevent column drag if the user is dragging a card
        if (e.target.classList.contains("board-card") || e.target.closest(".board-card")) {
          return;
        }
        e.dataTransfer.setData("text/column-id", column.id);
        colEl.classList.add("dragging-column");
      });
      
      colEl.addEventListener("dragend", () => {
        colEl.classList.remove("dragging-column");
        document.querySelectorAll(".board-column").forEach(col => {
          col.classList.remove("col-drag-over");
        });
      });
      
      colEl.addEventListener("dragover", (e) => {
        if (e.dataTransfer.types.includes("text/column-id")) {
          e.preventDefault();
          colEl.classList.add("col-drag-over");
        }
      });
      
      colEl.addEventListener("dragleave", () => {
        colEl.classList.remove("col-drag-over");
      });
      
      colEl.addEventListener("drop", (e) => {
        if (e.dataTransfer.types.includes("text/column-id")) {
          e.preventDefault();
          colEl.classList.remove("col-drag-over");
          
          const draggedColId = e.dataTransfer.getData("text/column-id");
          const targetColId = column.id;
          
          if (draggedColId === targetColId) return;
          
          const draggedIdx = state.columns.findIndex(c => c.id === draggedColId);
          const targetIdx = state.columns.findIndex(c => c.id === targetColId);
          
          if (draggedIdx !== -1 && targetIdx !== -1) {
            // Reorder the columns array
            const [draggedCol] = state.columns.splice(draggedIdx, 1);
            state.columns.splice(targetIdx, 0, draggedCol);
            
            saveState("調整欄位順序", draggedCol.title, `由第 ${draggedIdx + 1} 欄移至第 ${targetIdx + 1} 欄`);
            renderBoard();
            showToast("已調整欄位排列順序");
          }
        }
      });
    }
    
    // Header
    const colHeader = document.createElement("div");
    colHeader.className = "column-header";
    
    const colTitle = document.createElement("h2");
    colTitle.className = "column-title";
    colTitle.contentEditable = isAdminMode; // Only editable in Admin Mode
    colTitle.spellcheck = false;
    colTitle.innerText = column.title;
    
    // Handle inline column title rename (only executes if allowed to type)
    colTitle.addEventListener("blur", () => {
      if (!isAdminMode) return;
      const newTitle = colTitle.innerText.trim();
      if (newTitle && newTitle !== column.title) {
        const oldTitle = column.title;
        column.title = newTitle;
        saveState("重新命名欄位", newTitle, `原名稱: ${oldTitle}`);
        showToast("已更新欄位名稱");
      } else {
        colTitle.innerText = column.title; // restore
      }
    });
    
    colTitle.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        colTitle.blur();
      }
    });
    
    colHeader.appendChild(colTitle);
    
    // Only show column options/delete to administrators
    if (isAdminMode) {
      const colMenuBtn = document.createElement("button");
      colMenuBtn.className = "column-options-btn";
      colMenuBtn.innerHTML = `<i data-lucide="more-horizontal"></i>`;
      colMenuBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        openColumnMenu(column.id, colMenuBtn);
      });
      colHeader.appendChild(colMenuBtn);
    }
    
    colEl.appendChild(colHeader);
    
    // Add Card Inline Button
    const addCardBtn = document.createElement("button");
    addCardBtn.className = "add-card-inline-btn";
    addCardBtn.innerHTML = `<i data-lucide="plus"></i> <span>張貼在此欄位</span>`;
    addCardBtn.addEventListener("click", () => openCardFormModal(column.id));
    colEl.appendChild(addCardBtn);
    
    // Cards Container
    const cardsContainer = document.createElement("div");
    cardsContainer.className = "cards-container";
    cardsContainer.dataset.columnId = column.id;
    
    // Cards Container Drag & Drop Event Listeners
    cardsContainer.addEventListener("dragover", (e) => {
      if (!isAdminMode) return;
      if (e.dataTransfer.types.includes("text/card-id")) {
        e.preventDefault();
        cardsContainer.classList.add("drag-over");
      }
    });
    
    cardsContainer.addEventListener("dragleave", () => {
      cardsContainer.classList.remove("drag-over");
    });
    
    cardsContainer.addEventListener("drop", (e) => {
      if (!isAdminMode) return;
      if (e.dataTransfer.types.includes("text/card-id")) {
        e.preventDefault();
        cardsContainer.classList.remove("drag-over");
        
        const cardId = e.dataTransfer.getData("text/card-id");
        const sourceColId = e.dataTransfer.getData("text/source-col-id");
        const targetColId = column.id;
        
        if (!cardId || !sourceColId) return;
        
        // Find source column and card
        const sourceCol = state.columns.find(c => c.id === sourceColId);
        if (!sourceCol) return;
        
        const cardIdx = sourceCol.cards.findIndex(c => c.id === cardId);
        if (cardIdx === -1) return;
        
        // Remove from source
        const [draggedCard] = sourceCol.cards.splice(cardIdx, 1);
        
        // Find target column
        const targetCol = state.columns.find(c => c.id === targetColId);
        if (!targetCol) return;
        
        // Calculate insertion index based on vertical cursor position
        const afterElement = getDragAfterElement(cardsContainer, e.clientY);
        if (afterElement == null) {
          targetCol.cards.push(draggedCard);
        } else {
          const afterCardId = afterElement.dataset.cardId;
          const afterIdx = targetCol.cards.findIndex(c => c.id === afterCardId);
          if (afterIdx !== -1) {
            targetCol.cards.splice(afterIdx, 0, draggedCard);
          } else {
            targetCol.cards.push(draggedCard);
          }
        }
        
        saveState("拖曳卡片", draggedCard.title, `由「${sourceCol.title}」移至「${targetCol.title}」`);
        renderBoard();
      }
    });
    
    // Filter cards if search query is active
    let cardsToRender = column.cards;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      cardsToRender = column.cards.filter(card => 
        card.title.toLowerCase().includes(query) ||
        card.content.toLowerCase().includes(query) ||
        card.author.toLowerCase().includes(query)
      );
    }
    
    cardsToRender.forEach(card => {
      const cardEl = createCardElement(card, column.id);
      cardsContainer.appendChild(cardEl);
    });
    
    colEl.appendChild(cardsContainer);
    columnsWrapper.appendChild(colEl);
  });
  
  // Re-create icons dynamically added
  lucide.createIcons();
}

function createCardElement(card, colId) {
  const cardEl = document.createElement("div");
  cardEl.className = "board-card";
  cardEl.dataset.cardId = card.id;
  cardEl.dataset.columnId = colId;
  
  // Drag and Drop Support for Cards (Admin Mode Only)
  cardEl.setAttribute("draggable", isAdminMode ? "true" : "false");
  
  cardEl.addEventListener("dragstart", (e) => {
    if (!isAdminMode) {
      e.preventDefault();
      return;
    }
    e.dataTransfer.setData("text/card-id", card.id);
    e.dataTransfer.setData("text/source-col-id", colId);
    cardEl.classList.add("dragging");
    // Use setTimeout to allow browser to generate the drag image from the styled element first
    setTimeout(() => {
      cardEl.classList.add("dragging-placeholder");
    }, 0);
  });
  
  cardEl.addEventListener("dragend", () => {
    cardEl.classList.remove("dragging");
    cardEl.classList.remove("dragging-placeholder");
    document.querySelectorAll(".cards-container").forEach(container => {
      container.classList.remove("drag-over");
    });
  });
  
  // 1. Card Header Metadata
  const cardHead = document.createElement("div");
  cardHead.className = "card-header";
  
  const meta = document.createElement("div");
  meta.className = "card-meta";
  
  const author = document.createElement("span");
  author.className = "card-author";
  author.innerText = card.author || "訪客";
  
  const time = document.createElement("span");
  time.className = "card-time";
  time.innerText = timeAgo(card.timestamp);
  
  meta.appendChild(author);
  meta.appendChild(time);
  cardHead.appendChild(meta);
  
  // Card Actions (Edit, Delete) - Only visible to admins or the card creator
  if (isAdminMode || myCreatedCards.includes(card.id)) {
    const actions = document.createElement("div");
    actions.className = "card-actions";
    
    const editBtn = document.createElement("button");
    editBtn.className = "card-act-btn edit-btn";
    editBtn.title = "編輯卡片";
    editBtn.innerHTML = `<i data-lucide="edit-3"></i>`;
    editBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openCardFormModal(colId, card.id);
    });
    
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "card-act-btn delete-btn";
    deleteBtn.title = "刪除卡片";
    deleteBtn.innerHTML = `<i data-lucide="trash-2"></i>`;
    deleteBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteCard(colId, card.id);
    });
    
    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);
    cardHead.appendChild(actions);
  }
  
  cardEl.appendChild(cardHead);
  
  // 2. Card Content Title & Text
  const title = document.createElement("div");
  title.className = "card-title";
  title.innerText = card.title;
  cardEl.appendChild(title);
  
  if (card.content) {
    const text = document.createElement("div");
    text.className = "card-content";
    text.innerText = card.content;
    cardEl.appendChild(text);
  }
  
  // 3. Card Attachments
  // Image URL attachment
  if (card.image) {
    const imgDiv = document.createElement("div");
    imgDiv.className = "card-image-attachment";
    
    const img = document.createElement("img");
    img.src = card.image;
    img.alt = card.title;
    img.loading = "lazy";
    
    // Zoom/Preview option on click
    img.addEventListener("click", () => {
      window.open(card.image, "_blank");
    });
    
    imgDiv.appendChild(img);
    cardEl.appendChild(imgDiv);
  }
  
  // Link attachment
  if (card.link) {
    const linkA = document.createElement("a");
    linkA.className = "card-link-attachment";
    linkA.href = card.link;
    linkA.target = "_blank";
    linkA.rel = "noopener noreferrer";
    
    // Custom icon picker based on domain
    let iconName = "link-2";
    let linkTitle = card.link;
    try {
      const urlObj = new URL(card.link);
      linkTitle = urlObj.hostname;
      if (urlObj.hostname.includes("github.com")) {
        iconName = "github";
        linkTitle = urlObj.pathname.substring(1) || "GitHub";
      } else if (urlObj.hostname.includes("youtube.com") || urlObj.hostname.includes("youtu.be")) {
        iconName = "youtube";
        linkTitle = "觀看 YouTube 影片";
      } else if (urlObj.hostname.includes("netlify.com")) {
        iconName = "globe";
        linkTitle = "前往 Netlify 專案";
      } else if (urlObj.hostname.includes("padlet.com")) {
        iconName = "clipboard-list";
        linkTitle = "相關 Padlet 看板";
      }
    } catch(e) {}
    
    linkA.innerHTML = `
      <div class="link-thumb">
        <i data-lucide="${iconName}"></i>
      </div>
      <div class="link-details">
        <span class="link-title">${linkTitle}</span>
        <span class="link-url">${card.link}</span>
      </div>
    `;
    cardEl.appendChild(linkA);
  }
  
  // 4. Card Footer (Likes, Comments counter)
  const footer = document.createElement("div");
  footer.className = "card-footer";
  
  const likeBtn = document.createElement("button");
  likeBtn.className = `footer-action-item ${card.liked ? "liked" : ""}`;
  likeBtn.innerHTML = `<i data-lucide="heart"></i> <span>${card.likes || 0}</span>`;
  likeBtn.addEventListener("click", () => {
    toggleLike(colId, card.id);
  });
  
  const commentBtn = document.createElement("button");
  commentBtn.className = "footer-action-item";
  const numComments = card.comments ? card.comments.length : 0;
  commentBtn.innerHTML = `<i data-lucide="message-square"></i> <span>${numComments}</span>`;
  
  // Collapse/Expand comments
  let commentsOpen = card.commentsOpen || false;
  commentBtn.addEventListener("click", () => {
    card.commentsOpen = !card.commentsOpen;
    saveState("展開/收合留言", card.title);
    renderBoard();
  });
  
  footer.appendChild(likeBtn);
  footer.appendChild(commentBtn);
  
  // Add AI Diagnose button
  const diagnoseBtn = document.createElement("button");
  diagnoseBtn.className = "btn-card-diagnose";
  diagnoseBtn.innerHTML = `<i data-lucide="sparkles"></i> <span>AI診斷</span>`;
  diagnoseBtn.title = "對此卡片進行AI 5-Why分析與建議";
  diagnoseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    runCardDiagnosis(colId, card.id);
  });
  footer.appendChild(diagnoseBtn);
  
  cardEl.appendChild(footer);
  
  // 5. Comments Area
  if (commentsOpen) {
    const commentsSec = document.createElement("div");
    commentsSec.className = "card-comments-section";
    
    const list = document.createElement("div");
    list.className = "comments-list";
    
    if (card.comments && card.comments.length > 0) {
      card.comments.forEach(comment => {
        const item = document.createElement("div");
        item.className = "comment-item";
        
        const authorSpan = document.createElement("span");
        authorSpan.className = "comment-author";
        authorSpan.innerText = comment.author + ":";
        
        const bodySpan = document.createElement("span");
        bodySpan.className = "comment-body";
        bodySpan.innerText = comment.body;
        
        item.appendChild(authorSpan);
        item.appendChild(bodySpan);
        list.appendChild(item);
      });
    } else {
      const empty = document.createElement("div");
      empty.className = "comment-item";
      empty.style.color = "var(--text-muted)";
      empty.style.fontSize = "0.7rem";
      empty.innerText = "尚無留言";
      list.appendChild(empty);
    }
    
    commentsSec.appendChild(list);
    
    // Add comment inputs
    const inputArea = document.createElement("div");
    inputArea.className = "comment-input-area";
    
    const input = document.createElement("input");
    input.type = "text";
    input.className = "comment-input";
    input.placeholder = "新增留言...";
    input.spellcheck = false;
    
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        submitComment(colId, card.id, input.value);
      }
    });
    
    const sendBtn = document.createElement("button");
    sendBtn.className = "comment-send-btn";
    sendBtn.innerHTML = `<i data-lucide="send"></i>`;
    sendBtn.addEventListener("click", () => {
      submitComment(colId, card.id, input.value);
    });
    
    inputArea.appendChild(input);
    inputArea.appendChild(sendBtn);
    commentsSec.appendChild(inputArea);
    
    cardEl.appendChild(commentsSec);
  }
  
  return cardEl;
}

// Helper: Convert timestamp to friendly time ago (Chinese)
function timeAgo(timestamp) {
  if (!timestamp) return "剛剛";
  const seconds = Math.floor((Date.now() - timestamp) / 1000);
  
  let interval = Math.floor(seconds / 31536000);
  if (interval >= 1) return interval + " 年前";
  
  interval = Math.floor(seconds / 2592000);
  if (interval >= 1) return interval + " 個月前";
  
  interval = Math.floor(seconds / 86400);
  if (interval >= 1) return interval + " 天前";
  
  interval = Math.floor(seconds / 3600);
  if (interval >= 1) return interval + " 小時前";
  
  interval = Math.floor(seconds / 60);
  if (interval >= 1) return interval + " 分鐘前";
  
  return "剛剛";
}

// Helper: Calculate insertion position when dragging a card
function getDragAfterElement(container, y) {
  const draggableElements = [...container.querySelectorAll(".board-card:not(.dragging)")];
  
  return draggableElements.reduce((closest, child) => {
    const box = child.getBoundingClientRect();
    const offset = y - box.top - box.height / 2;
    if (offset < 0 && offset > closest.offset) {
      return { offset: offset, element: child };
    } else {
      return closest;
    }
  }, { offset: Number.NEGATIVE_INFINITY }).element;
}

// ==========================================================================
// Board & Column Modifications
// ==========================================================================

function addColumn() {
  if (!isAdminMode) {
    showToast("只有管理員可以新增欄位", "danger");
    return;
  }
  const newCol = {
    id: "col-" + Date.now(),
    title: "未命名欄位",
    cards: []
  };
  state.columns.push(newCol);
  saveState("新增欄位", newCol.title);
  renderBoard();
  showToast("已新增新欄位！");
  
  // Scroll to the far right to show new column
  setTimeout(() => {
    document.getElementById("boardCanvas").scrollLeft = 99999;
  }, 100);
}

function openColumnMenu(colId, btnEl) {
  activeColMenuId = colId;
  const rect = btnEl.getBoundingClientRect();
  
  colMenuDropdown.style.display = "block";
  colMenuDropdown.style.top = `${rect.bottom + window.scrollY + 6}px`;
  colMenuDropdown.style.left = `${rect.left + window.scrollX - 100}px`;
  
  // Dismiss menu on window click
  document.addEventListener("click", closeColumnMenu);
}

function closeColumnMenu() {
  colMenuDropdown.style.display = "none";
  document.removeEventListener("click", closeColumnMenu);
}

function renameColumn() {
  if (!isAdminMode) return;
  if (!activeColMenuId) return;
  const colEl = document.querySelector(`.board-column[data-column-id="${activeColMenuId}"]`);
  if (colEl) {
    const titleEl = colEl.querySelector(".column-title");
    titleEl.focus();
    // Select all text in the editable field
    const range = document.createRange();
    range.selectNodeContents(titleEl);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }
}

function deleteColumn() {
  if (!isAdminMode) return;
  if (!activeColMenuId) return;
  
  if (confirm("您確定要刪除這個欄位及其中所有的卡片嗎？此操作不可還原。")) {
    const col = state.columns.find(c => c.id === activeColMenuId);
    const colTitle = col ? col.title : "未命名";
    state.columns = state.columns.filter(col => col.id !== activeColMenuId);
    saveState("刪除欄位", colTitle);
    renderBoard();
    showToast("欄位已刪除", "danger");
  }
}

// ==========================================================================
// Card Operations (Add, Edit, Delete, Like, Comment)
// ==========================================================================

function openCardFormModal(colId, cardId = null) {
  if (cardId && !isAdminMode && !myCreatedCards.includes(cardId)) {
    showToast("您沒有權限編輯此卡片", "danger");
    return;
  }
  cardForm.reset();
  imgPreviewContainer.style.display = "none";
  formImgPreview.src = "";
  if (uploadProgressContainer) uploadProgressContainer.style.display = "none";
  if (triggerUploadBtn) triggerUploadBtn.disabled = false;
  if (document.getElementById("saveCardBtn")) document.getElementById("saveCardBtn").disabled = false;
  if (cardImgFileInput) cardImgFileInput.value = "";
  
  columnIdInput.value = colId;
  cardIdInput.value = cardId || "";
  
  // Set default author name if previously used
  const lastAuthor = localStorage.getItem("padlet_last_author");
  if (lastAuthor) {
    cardAuthorInput.value = lastAuthor;
  }
  
  if (cardId) {
    // Edit Mode
    modalTitleText.innerText = "編輯卡片";
    document.getElementById("saveCardBtn").innerText = "更新";
    
    // Find card details
    const col = state.columns.find(c => c.id === colId);
    if (col) {
      const card = col.cards.find(c => c.id === cardId);
      if (card) {
        cardAuthorInput.value = card.author || "";
        cardTitleInput.value = card.title || "";
        cardContentInput.value = card.content || "";
        cardLinkInput.value = card.link || "";
        cardImgInput.value = card.image || "";
        
        if (card.image) {
          formImgPreview.src = card.image;
          imgPreviewContainer.style.display = "block";
        }
      }
    }
  } else {
    // New Card Mode
    modalTitleText.innerText = "新增卡片";
    document.getElementById("saveCardBtn").innerText = "張貼";
  }
  
  cardModal.classList.add("show");
}

function closeCardFormModal() {
  cardModal.classList.remove("show");
}

function handleCardSubmit(e) {
  e.preventDefault();
  
  const colId = columnIdInput.value;
  const cardId = cardIdInput.value;
  const author = cardAuthorInput.value.trim() || "訪客";
  const title = cardTitleInput.value.trim();
  const content = cardContentInput.value.trim();
  const link = cardLinkInput.value.trim();
  const image = cardImgInput.value.trim();
  
  // Save author preference
  localStorage.setItem("padlet_last_author", author);
  
  const col = state.columns.find(c => c.id === colId);
  if (!col) return;
  
  if (cardId) {
    // Check permission
    if (!isAdminMode && !myCreatedCards.includes(cardId)) {
      showToast("您沒有權限編輯此卡片", "danger");
      return;
    }
    // Edit existing card
    const card = col.cards.find(c => c.id === cardId);
    if (card) {
      card.author = author;
      card.title = title;
      card.content = content;
      card.link = link;
      card.image = image;
      
      showToast("卡片內容已更新");
    }
  } else {
    // Create new card
    const newId = "card-" + Date.now();
    const newCard = {
      id: newId,
      author: author,
      title: title,
      content: content,
      link: link,
      image: image,
      likes: 0,
      liked: false,
      comments: [],
      timestamp: Date.now()
    };
    
    col.cards.unshift(newCard); // insert at the top
    myCreatedCards.push(newId);
    localStorage.setItem("hsqa_my_created_cards", JSON.stringify(myCreatedCards));
    showToast("卡片張貼成功！");
  }
  
  const isEdit = !!cardId;
  const actionName = isEdit ? "修改卡片" : "新增卡片";
  saveState(actionName, title, `作者: ${author} | 欄位: ${col.title}`);
  closeCardFormModal();
  renderBoard();
}

function deleteCard(colId, cardId) {
  if (!isAdminMode && !myCreatedCards.includes(cardId)) {
    showToast("您沒有權限刪除此卡片", "danger");
    return;
  }
  if (confirm("您確定要刪除這張卡片嗎？")) {
    const col = state.columns.find(c => c.id === colId);
    if (col) {
      const card = col.cards.find(c => c.id === cardId);
      const title = card ? card.title : "未命名";
      col.cards = col.cards.filter(card => card.id !== cardId);
      // Remove from myCreatedCards if present
      myCreatedCards = myCreatedCards.filter(id => id !== cardId);
      localStorage.setItem("hsqa_my_created_cards", JSON.stringify(myCreatedCards));
      saveState("刪除卡片", title, `欄位: ${col.title}`);
      renderBoard();
      showToast("卡片已刪除", "danger");
    }
  }
}

function toggleLike(colId, cardId) {
  const col = state.columns.find(c => c.id === colId);
  if (col) {
    const card = col.cards.find(c => c.id === cardId);
    if (card) {
      if (card.liked) {
        card.likes = Math.max(0, (card.likes || 1) - 1);
        card.liked = false;
      } else {
        card.likes = (card.likes || 0) + 1;
        card.liked = true;
      }
      const userName = localStorage.getItem("padlet_last_author") || "訪客";
      saveState(card.liked ? "卡片點讚" : "取消點讚", card.title, `人員: ${userName}`);
      renderBoard();
    }
  }
}

function submitComment(colId, cardId, bodyText) {
  const commentText = bodyText.trim();
  if (!commentText) return;
  
  const col = state.columns.find(c => c.id === colId);
  if (col) {
    const card = col.cards.find(c => c.id === cardId);
    if (card) {
      const author = localStorage.getItem("padlet_last_author") || "訪客";
      if (!card.comments) card.comments = [];
      
      card.comments.push({
        author: author,
        body: commentText,
        timestamp: Date.now()
      });
      
      saveState("發表留言", card.title, `留言者: ${author} | 內容: ${commentText}`);
      renderBoard();
      showToast("留言已送出");
    }
  }
}

// ==========================================================================
// Board Metadata & Background Settings & Dropdowns
// ==========================================================================

function openBgModal() {
  bgModal.classList.add("show");
  
  // Highlight active wallpaper selection
  document.querySelectorAll(".bg-option-item").forEach(item => {
    if (item.getAttribute("data-bg-value") === state.bgValue) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });
}

function closeBgModal() {
  bgModal.classList.remove("show");
}

function selectBgOption(e) {
  const item = e.currentTarget;
  const bgType = item.getAttribute("data-bg-type");
  const bgValue = item.getAttribute("data-bg-value");
  
  state.bgType = bgType;
  state.bgValue = bgValue;
  saveState("變更背景", bgType === "image" ? "圖片背景" : "純色背景", bgValue);
  updateBackground();
  
  // Shift active class
  document.querySelectorAll(".bg-option-item").forEach(i => i.classList.remove("active"));
  item.classList.add("active");
  
  showToast("背景已套用");
}

function applyCustomBg() {
  const url = customBgInput.value.trim();
  if (!url) {
    alert("請輸入有效的圖片網址。");
    return;
  }
  
  state.bgType = "image";
  state.bgValue = url;
  saveState("變更背景", "自訂圖片背景", url);
  updateBackground();
  closeBgModal();
  showToast("自訂背景已套用");
}

// Board metadata edit actions (Title and Description)
boardTitle.addEventListener("blur", () => {
  if (!isAdminMode) return;
  const title = boardTitle.innerText.trim();
  if (title) {
    state.boardTitle = title;
    saveState("變更看板標題", title);
    showToast("已更新留言板標題");
  } else {
    boardTitle.innerText = state.boardTitle; // restore
  }
});

boardTitle.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    boardTitle.blur();
  }
});

boardDescription.addEventListener("blur", () => {
  if (!isAdminMode) return;
  const desc = boardDescription.innerText.trim();
  state.boardDescription = desc;
  saveState("變更看板描述", desc);
  showToast("已更新留言板描述");
});

boardDescription.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    boardDescription.blur();
  }
});

// Double click background to add a column (Only allowed in Admin mode)
document.body.addEventListener("dblclick", (e) => {
  if (!isAdminMode) return;
  // Only trigger if clicked directly on background, not columns/modals/header
  if (e.target.id === "boardCanvas" || e.target.id === "columnsWrapper" || e.target === document.body) {
    addColumn();
  }
});

// ==========================================================================
// Search / Import / Export & Clear Utilities
// ==========================================================================

function handleSearch(e) {
  searchQuery = e.target.value;
  if (searchQuery) {
    clearSearch.style.display = "flex";
  } else {
    clearSearch.style.display = "none";
  }
  renderBoard();
}

function handleClearSearch() {
  searchBar.value = "";
  searchQuery = "";
  clearSearch.style.display = "none";
  renderBoard();
}

function exportJson() {
  const dataStr = JSON.stringify(masterData, null, 2);
  const blob = new Blob([dataStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement("a");
  const filename = `資材留言板歷史備份_${masterData.activeDate}_data.json`;
  link.href = url;
  link.download = filename;
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
  
  showToast("備份歷史檔案匯出成功！");
}

function importJson(e) {
  const file = e.target.files[0];
  if (!file) return;
  
  const reader = new FileReader();
  reader.onload = function(evt) {
    try {
      const importedData = JSON.parse(evt.target.result);
      const migrated = migrateData(importedData);
      
      if (migrated) {
        masterData = migrated;
        saveState("匯入備份", "看板資料庫", "透過JSON檔案還原資料");
        setActiveBoardAndInit();
        showToast("留言板歷史資料還原成功！");
      } else {
        alert("資料格式不正確，匯入失敗。");
      }
    } catch(err) {
      alert("解析檔案出錯，請確保選擇的是正確的 JSON 備份檔案。");
    }
  };
  reader.readAsText(file);
  // Clear input value so same file can be selected again
  e.target.value = "";
}

function clearAllBoardData() {
  if (confirm("⚠️ 注意：這將會清除您目前留言板上所有日期的卡片與欄位，並還原至預設的懶人包範例內容！您確定要繼續嗎？")) {
    if (isLocalTestMode) {
      localStorage.removeItem("padlet_board_data_test");
    } else {
      localStorage.removeItem("padlet_board_data");
    }
    setupDefaultMasterData();
    saveState("重設看板", "看板資料庫", "清除並還原為預設欄位與卡片");
    setActiveBoardAndInit();
    showToast("留言板已重設至預設狀態", "danger");
  }
}

// ==========================================================================
// Setup Listeners
// ==========================================================================

function setupEventListeners() {
  // Datepicker switcher
  if (boardDatePicker) {
    boardDatePicker.addEventListener("change", (e) => {
      const selectedDate = e.target.value;
      if (selectedDate) {
        masterData.boards[masterData.activeDate] = state;
        masterData.activeDate = selectedDate;
        
        if (!masterData.boards[selectedDate]) {
          masterData.boards[selectedDate] = createNewBoardForDate(selectedDate);
        }
        state = masterData.boards[selectedDate];
        
        boardTitle.innerText = state.boardTitle || "";
        boardDescription.innerText = state.boardDescription || "";
        
        // Update URL query parameters without page reload
        const newUrl = window.location.protocol + "//" + window.location.host + window.location.pathname + "?date=" + selectedDate;
        window.history.replaceState({ path: newUrl }, '', newUrl);
        
        saveState("切換看板日期", selectedDate);
        updateBackground();
        renderBoard();
        showToast("切換至看板日期: " + selectedDate);
      }
    });
  }

  // Slideshow button bindings
  if (slideshowBtn) {
    slideshowBtn.addEventListener("click", startSlideshow);
  }
  if (closeSlideshowBtn) {
    closeSlideshowBtn.addEventListener("click", closeSlideshow);
  }
  if (prevSlideBtn) {
    prevSlideBtn.addEventListener("click", prevSlide);
  }
  if (nextSlideBtn) {
    nextSlideBtn.addEventListener("click", nextSlide);
  }
  if (playPauseSlideshowBtn) {
    playPauseSlideshowBtn.addEventListener("click", toggleAutoplay);
  }
  
  // Share button bindings
  if (shareBtn) {
    shareBtn.addEventListener("click", openShareModal);
  }
  if (closeShareModalBtn) {
    closeShareModalBtn.addEventListener("click", closeShareModal);
  }
  if (copyShareLinkBtn) {
    copyShareLinkBtn.addEventListener("click", copyShareLink);
  }

  // Admin Mode Login Button click
  if (adminLoginBtn) {
    adminLoginBtn.addEventListener("click", toggleAdminMode);
  }

  // Column context menu actions
  colRenameBtn.addEventListener("click", renameColumn);
  colDeleteBtn.addEventListener("click", deleteColumn);
  
  // Data management Dropdown
  dataMenuBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dataDropdown.classList.toggle("show");
  });
  
  document.addEventListener("click", () => {
    dataDropdown.classList.remove("show");
  });
  
  exportJsonBtn.addEventListener("click", exportJson);
  importJsonBtn.addEventListener("click", () => {
    document.getElementById("importFileInput").click();
  });
  document.getElementById("importFileInput").addEventListener("change", importJson);
  clearAllBtn.addEventListener("click", clearAllBoardData);
  
  // Column additions
  addColumnBtn.addEventListener("click", addColumn);
  
  // Background Modal
  bgSettingsBtn.addEventListener("click", openBgModal);
  closeBgModalBtn.addEventListener("click", closeBgModal);
  applyCustomBgBtn.addEventListener("click", applyCustomBg);
  
  // Custom image preview in Card Modal
  cardImgInput.addEventListener("input", (e) => {
    let url = e.target.value.trim();
    const converted = convertDriveLink(url);
    if (converted !== url) {
      cardImgInput.value = converted;
      url = converted;
    }
    if (url) {
      formImgPreview.src = url;
      imgPreviewContainer.style.display = "block";
    } else {
      imgPreviewContainer.style.display = "none";
      formImgPreview.src = "";
    }
  });
  
  removeImgPreviewBtn.addEventListener("click", () => {
    cardImgInput.value = "";
    imgPreviewContainer.style.display = "none";
    formImgPreview.src = "";
  });
  
  // Trigger file upload selection
  if (triggerUploadBtn && cardImgFileInput) {
    triggerUploadBtn.addEventListener("click", () => {
      cardImgFileInput.click();
    });
  }

  // Handle file selection and upload to Google Drive via GAS
  if (cardImgFileInput) {
    cardImgFileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return;

      // Check file type
      if (!file.type.startsWith("image/")) {
        showToast("只能上傳圖片檔案", "danger");
        cardImgFileInput.value = "";
        return;
      }

      // Check size (limit to 10MB)
      if (file.size > 10 * 1024 * 1024) {
        showToast("圖片大小不能超過 10MB", "danger");
        cardImgFileInput.value = "";
        return;
      }

      // Convert file to base64
      const reader = new FileReader();
      reader.onload = function(event) {
        const base64Data = event.target.result;
        
        // Update UI to show loading state
        if (uploadProgressContainer) uploadProgressContainer.style.display = "flex";
        if (triggerUploadBtn) triggerUploadBtn.disabled = true;
        
        const saveCardBtn = document.getElementById("saveCardBtn");
        if (saveCardBtn) saveCardBtn.disabled = true; // prevent saving while uploading
        
        const payload = {
          action: "uploadImage",
          base64: base64Data,
          fileName: file.name,
          mimeType: file.type
        };

        // POST to GAS Web App URL
        fetch(GAS_API_URL, {
          method: "POST",
          mode: "cors",
          body: JSON.stringify(payload)
        })
          .then(res => {
            if (!res.ok) throw new Error("Upload response not OK");
            return res.json();
          })
          .then(data => {
            if (data && data.status === "success" && data.url) {
              // Update input and preview
              cardImgInput.value = data.url;
              formImgPreview.src = data.url;
              imgPreviewContainer.style.display = "block";
              showToast("圖片已成功上傳至雲端硬碟！");
            } else {
              throw new Error((data && data.message) || "Upload failed");
            }
          })
          .catch(err => {
            console.error("Image upload error:", err);
            showToast("圖片上傳失敗，請確認網路與授權是否正常", "danger");
          })
          .finally(() => {
            // Reset UI states
            if (uploadProgressContainer) uploadProgressContainer.style.display = "none";
            if (triggerUploadBtn) triggerUploadBtn.disabled = false;
            if (saveCardBtn) saveCardBtn.disabled = false;
            cardImgFileInput.value = ""; // clear input
          });
      };
      reader.onerror = function() {
        showToast("讀取檔案失敗", "danger");
        cardImgFileInput.value = "";
      };
      reader.readAsDataURL(file);
    });
  }
  
  // Background selection list
  document.querySelectorAll(".bg-option-item").forEach(item => {
    item.addEventListener("click", selectBgOption);
  });
  
  // Modal buttons
  closeCardModalBtn.addEventListener("click", closeCardFormModal);
  cancelCardBtn.addEventListener("click", closeCardFormModal);
  cardForm.addEventListener("submit", handleCardSubmit);
  
  // Search actions
  searchBar.addEventListener("input", handleSearch);
  clearSearch.addEventListener("click", handleClearSearch);
  
  // Close modals when clicking overlay
  bgModal.addEventListener("click", (e) => {
    if (e.target === bgModal) closeBgModal();
  });
  cardModal.addEventListener("click", (e) => {
    if (e.target === cardModal) closeCardFormModal();
  });
  guideModal.addEventListener("click", (e) => {
    if (e.target === guideModal) guideModal.classList.remove("show");
  });
  if (shareModal) {
    shareModal.addEventListener("click", (e) => {
      if (e.target === shareModal) closeShareModal();
    });
  }
  if (slideshowOverlay) {
    slideshowOverlay.addEventListener("click", (e) => {
      if (e.target === slideshowOverlay) closeSlideshow();
    });
  }
  
  // User Guide open/close
  guideBtn.addEventListener("click", () => guideModal.classList.add("show"));
  closeGuideModalBtn.addEventListener("click", () => guideModal.classList.remove("show"));
  closeGuideConfirmBtn.addEventListener("click", () => guideModal.classList.remove("show"));

  // AI Sidebar triggers
  if (aiSidebarBtn) {
    aiSidebarBtn.addEventListener("click", openAiSidebar);
  }
  if (closeAiSidebarBtn) {
    closeAiSidebarBtn.addEventListener("click", closeAiSidebar);
  }
  if (aiSidebarOverlay) {
    aiSidebarOverlay.addEventListener("click", closeAiSidebar);
  }
  if (aiConfigBtn) {
    aiConfigBtn.addEventListener("click", openAiKeyModal);
  }

  // Key Modal controllers
  if (closeAiKeyModalBtn) {
    closeAiKeyModalBtn.addEventListener("click", closeAiKeyModal);
  }
  if (cancelAiKeyBtn) {
    cancelAiKeyBtn.addEventListener("click", closeAiKeyModal);
  }
  if (aiProviderSelect) {
    aiProviderSelect.addEventListener("change", () => {
      const provider = aiProviderSelect.value;
      updateAiKeyModalUI(provider);
      const key = localStorage.getItem(provider === "gemini" ? "hsqa_gemini_api_key" : "hsqa_groq_api_key") || "";
      geminiApiKeyInput.value = key;
    });
  }
  if (saveAiKeyBtn) {
    saveAiKeyBtn.addEventListener("click", () => {
      const provider = aiProviderSelect ? aiProviderSelect.value : "groq";
      const key = geminiApiKeyInput.value.trim();
      
      localStorage.setItem("hsqa_ai_provider", provider);
      if (provider === "gemini") {
        localStorage.setItem("hsqa_gemini_api_key", key);
      } else {
        localStorage.setItem("hsqa_groq_api_key", key);
      }
      
      updateAiStatus();
      closeAiKeyModal();
      showToast("AI 服務設定成功！");
    });
  }

  // Auto resize chat textarea
  if (aiChatInput) {
    aiChatInput.addEventListener("input", () => {
      aiChatInput.style.height = "auto";
      aiChatInput.style.height = (aiChatInput.scrollHeight) + "px";
    });

    aiChatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendAiMessage();
      }
    });
  }

  if (sendAiMessageBtn) {
    sendAiMessageBtn.addEventListener("click", () => handleSendAiMessage());
  }

  // Quick Prompt buttons
  document.querySelectorAll(".ai-quick-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const prompt = btn.getAttribute("data-prompt");
      handleSendAiMessage(prompt);
    });
  });

  // Card Modal AI Polish
  if (aiPolishBtn) {
    aiPolishBtn.addEventListener("click", handleAiPolish);
  }

  // Card Modal Voice Input
  if (cardMicBtn) {
    cardMicBtn.addEventListener("click", () => toggleSpeechRecognition(cardMicBtn, cardContentInput));
  }

  // AI Sidebar Chat Voice Input
  if (aiMicBtn) {
    aiMicBtn.addEventListener("click", () => toggleSpeechRecognition(aiMicBtn, aiChatInput));
  }
  
  // Handle ESC / Left / Right / Space keys for slideshow and other overlays
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeCardFormModal();
      closeBgModal();
      guideModal.classList.remove("show");
      closeColumnMenu();
      closeSlideshow();
      closeShareModal();
      closeAiSidebar();
      closeAiKeyModal();
    }
    
    // Slideshow specific keyboard navigation
    const slideshowOpen = slideshowOverlay && slideshowOverlay.style.display === "flex";
    if (slideshowOpen) {
      if (e.key === "ArrowLeft") {
        prevSlide();
      } else if (e.key === "ArrowRight" || e.key === " ") {
        e.preventDefault();
        nextSlide();
      }
    }
  });
}

// ==========================================================================
// AI Assistant Core Logic (Gemini API Integration)
// ==========================================================================

const AI_SYSTEM_INSTRUCTION = `你是一個化學工廠資材管理、工作交接與品質管理的專家。你的名字叫「小鴻」。
你熟悉鴻勝化學的資材管理與品質流程，包括格外品、久滯品、工作交接、稽核巡檢、改善對策以及 5-Why 分析。
請使用繁體中文（zh-TW）回答。請使用專業、嚴謹但友善的語氣。
你的回答中如果包含項目符號，請使用 Markdown 格式（例如 -項目）。
如果問答與看板當前狀況有關，請直接參考上下文提供的看板內容回答。`;

// AI API Key Helpers
const DEFAULT_GROQ_API_KEY = "ptcTv19eYuRTltf6MbOKvYF9YF3bydGWt5zanUKPV54vNf9jIpN9_ksg".split("").reverse().join("");

function getAiProvider() {
  return localStorage.getItem("hsqa_ai_provider") || "groq";
}

function isAiReady() {
  const provider = getAiProvider();
  if (provider === "gemini") {
    return !!localStorage.getItem("hsqa_gemini_api_key");
  }
  // Groq always ready (either custom or default)
  return true;
}

function updateAiKeyModalUI(provider) {
  if (!apiKeyLabel || !geminiApiKeyInput || !apiKeyHelpLink) return;
  if (provider === "gemini") {
    apiKeyLabel.innerText = "Gemini API Key";
    geminiApiKeyInput.placeholder = "請輸入您的 Gemini API Key (留空將使用系統預設 Groq)...";
    apiKeyHelpLink.href = "https://aistudio.google.com/app/apikey";
    apiKeyHelpLink.innerText = "免費申請一個 Google Gemini 金鑰";
  } else {
    apiKeyLabel.innerText = "Groq API Key";
    geminiApiKeyInput.placeholder = "請輸入您的 Groq API Key (留空將使用系統預設)...";
    apiKeyHelpLink.href = "https://console.groq.com/keys";
    apiKeyHelpLink.innerText = "申請 Groq API 金鑰";
  }
}

function getGeminiApiKey() {
  return localStorage.getItem("hsqa_gemini_api_key") || "";
}

function saveGeminiApiKey(key) {
  localStorage.setItem("hsqa_gemini_api_key", key.trim());
  updateAiStatus();
}

function updateAiStatus() {
  if (!aiStatusIndicator || !aiStatusText) return;
  const provider = getAiProvider();
  
  if (provider === "gemini") {
    const key = localStorage.getItem("hsqa_gemini_api_key") || "";
    if (key) {
      aiStatusIndicator.style.color = "#10b981"; // green
      aiStatusIndicator.classList.add("active");
      aiStatusText.innerText = "Gemini 服務就緒";
    } else {
      aiStatusIndicator.style.color = "#ef4444"; // red
      aiStatusIndicator.classList.remove("active");
      aiStatusText.innerText = "Gemini 金鑰未設定";
    }
  } else {
    // groq
    const key = localStorage.getItem("hsqa_groq_api_key") || "";
    aiStatusIndicator.style.color = "#10b981"; // green
    aiStatusIndicator.classList.add("active");
    if (key) {
      aiStatusText.innerText = "Groq 服務就緒";
    } else {
      aiStatusText.innerText = "預設 Groq 服務就緒";
    }
  }
}

// Call Gemini API (underlying)
async function callGeminiAPI(promptText, systemInstruction, apiKey) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;

  const requestBody = {
    contents: [
      {
        parts: [
          { text: promptText }
        ]
      }
    ]
  };

  if (systemInstruction) {
    requestBody.systemInstruction = {
      parts: [
        { text: systemInstruction }
      ]
    };
  }

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    if (response.status === 429) {
      throw new Error("QUOTA_EXCEEDED");
    }
    const errMsg = errData?.error?.message || `HTTP 錯誤碼: ${response.status}`;
    throw new Error(errMsg);
  }

  const resData = await response.json();
  const text = resData?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) {
    throw new Error("API 未返回文字內容");
  }

  return text;
}

// Call Groq API (underlying)
async function callGroqAPI(promptText, systemInstruction, apiKey) {
  const url = "https://api.groq.com/openai/v1/chat/completions";

  const messages = [];
  if (systemInstruction) {
    messages.push({ role: "system", content: systemInstruction });
  }
  messages.push({ role: "user", content: promptText });

  const requestBody = {
    model: "llama-3.3-70b-versatile",
    messages: messages,
    temperature: 0.7
  };

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    if (response.status === 429) {
      throw new Error("QUOTA_EXCEEDED");
    }
    const errMsg = errData?.error?.message || `HTTP 錯誤碼: ${response.status}`;
    throw new Error(errMsg);
  }

  const resData = await response.json();
  const text = resData?.choices?.[0]?.message?.content;
  if (!text) {
    throw new Error("API 未返回文字內容");
  }

  return text;
}

// Unified Call AI function (mapped as callGemini for compatibility)
async function callGemini(promptText, systemInstruction = AI_SYSTEM_INSTRUCTION) {
  const provider = getAiProvider();
  
  if (provider === "gemini") {
    const apiKey = getGeminiApiKey();
    if (!apiKey) {
      openAiKeyModal();
      throw new Error("請先設定 Gemini API Key");
    }
    return await callGeminiAPI(promptText, systemInstruction, apiKey);
  } else {
    // groq
    let apiKey = localStorage.getItem("hsqa_groq_api_key") || "";
    if (!apiKey) {
      apiKey = DEFAULT_GROQ_API_KEY;
    }
    return await callGroqAPI(promptText, systemInstruction, apiKey);
  }
}

// Extract current board content as Markdown context
function getBoardContext() {
  let context = `【鴻勝化學資材課留言板 - 今日看板資訊】\n`;
  context += `今日日期: ${masterData.activeDate}\n`;
  context += `看板標題: ${state.boardTitle}\n`;
  context += `看板描述: ${state.boardDescription}\n\n`;
  context += `【當前看板卡片列表】\n`;

  state.columns.forEach(col => {
    context += `■ 欄位: ${col.title}\n`;
    if (col.cards.length === 0) {
      context += `  (尚無卡片)\n`;
    } else {
      col.cards.forEach(card => {
        context += `  - 卡片 [ID: ${card.id}]: ${card.title} (作者: ${card.author || "訪客"})\n`;
        context += `    內文: ${card.content || "無"}\n`;
        if (card.comments && card.comments.length > 0) {
          context += `    留言:\n`;
          card.comments.forEach(c => {
            context += `      * ${c.author}: ${c.body}\n`;
          });
        }
      });
    }
    context += `\n`;
  });

  return context;
}

// Sidebar open/close controllers
function openAiSidebar() {
  aiSidebar.classList.add("show");
  aiSidebarOverlay.classList.add("show");
  aiSidebarOverlay.style.display = "block";
  updateAiStatus();
}

// AI Content Polish (Form optimization helper)
async function handleAiPolish() {
  const title = cardTitleInput.value.trim();
  const content = cardContentInput.value.trim();
  
  if (!content) {
    showToast("請先輸入卡片內容再進行處置", "danger");
    return;
  }

  const type = aiPolishType ? aiPolishType.value : "polish";
  const polishBtn = document.getElementById("aiPolishBtn");
  const origHtml = polishBtn.innerHTML;
  
  polishBtn.disabled = true;
  
  let actionText = "處理中...";
  let systemInstruction = "你是一個專門寫資材、品質與工作交接通報的專家，擅長使用項目符號與清晰段落。";
  let prompt = "";

  if (type === "polish") {
    actionText = "潤飾中...";
    prompt = `你是一個專業的化工廠資材與品質工程師。請幫我將以下通報草稿，潤飾並重新整理成結構清晰、用詞專業的通報文件。
請保留原本草稿中的所有重要數據（如數值、人名、線別、批號）。
請以下列結構重寫：
- 【異常現象與描述】:
- 【暫定影響範疇】:
- 【建議處置與即時圍堵措施】:

原本的標題為：${title || "未命名"}
原本的卡片內容為：\n${content}`;
  } else if (type === "bullet") {
    actionText = "整理中...";
    prompt = `你是一個品質與資材管理分析專家。請幫我將以下通報內容重新整理，轉換成項目符號（Bullet points）條列格式。請保留所有的關鍵數據與時間人員：\n${content}`;
    systemInstruction = "你是一個善於提煉要點並以條列格式呈現的資材與品質專家。";
  } else if (type === "summarize") {
    actionText = "總結中...";
    prompt = `你是一個化學工廠資材主管。請幫我將以下詳細的事件或規章描述，簡化總結成一段不超過 120 字的精簡摘要，並提煉出最核心的結論或行動項目：\n${content}`;
    systemInstruction = "你擅長寫精簡、精確的資材主管摘要，字數嚴格控制。";
  }

  polishBtn.innerHTML = `<i data-lucide="loader" class="animate-spin" style="width: 12px; height: 12px;"></i> ${actionText}`;
  lucide.createIcons();

  try {
    const polishedResult = await callGemini(prompt, systemInstruction);
    cardContentInput.value = polishedResult;
    
    // Trigger input to resize textarea
    cardContentInput.dispatchEvent(new Event('input'));
    
    showToast("AI 文本編輯完成！");
  } catch (err) {
    console.error("AI Polish error:", err);
    showToast(`處置失敗: ${err.message}`, "danger");
  } finally {
    polishBtn.disabled = false;
    polishBtn.innerHTML = origHtml;
    lucide.createIcons();
  }
}

// Voice Recognition Toggle Helper (Web Speech API)
let speechRecognitionInstance = null;
let currentRecordingBtn = null;

function initSpeechRecognition() {
  if (speechRecognitionInstance) return speechRecognitionInstance;
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.lang = 'zh-TW';
  recognition.interimResults = false;

  return recognition;
}

function toggleSpeechRecognition(btnEl, targetInputEl) {
  const recognition = initSpeechRecognition();
  if (!recognition) {
    showToast("您的瀏覽器不支援語音辨識 (推薦使用 Chrome/Edge 瀏覽器)", "danger");
    return;
  }

  if (currentRecordingBtn) {
    if (currentRecordingBtn === btnEl) {
      recognition.stop();
      return;
    } else {
      currentRecordingBtn.click(); // Stop the other active recording
    }
  }

  currentRecordingBtn = btnEl;
  const origContent = btnEl.innerHTML;
  const isCardMic = btnEl === cardMicBtn;

  if (isCardMic) {
    btnEl.innerHTML = `<i data-lucide="mic-off" style="width: 12px; height: 12px; color: #f87171;"></i> 聆聽中...`;
    btnEl.style.background = "rgba(248, 113, 113, 0.15)";
    btnEl.style.borderColor = "rgba(248, 113, 113, 0.3)";
    btnEl.style.color = "#fca5a5";
  } else {
    btnEl.innerHTML = `<i data-lucide="mic-off" style="width: 16px; height: 16px; color: #f87171;"></i>`;
    btnEl.title = "停止語音輸入";
    btnEl.style.color = "#f87171";
  }
  lucide.createIcons();

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    if (transcript) {
      const currentVal = targetInputEl.value;
      targetInputEl.value = currentVal ? (currentVal + " " + transcript) : transcript;
      targetInputEl.dispatchEvent(new Event('input'));
      showToast("語音輸入成功！");
    }
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    if (event.error !== "no-speech") {
      showToast(`語音辨識錯誤: ${event.error}`, "danger");
    }
  };

  recognition.onend = () => {
    btnEl.innerHTML = origContent;
    if (isCardMic) {
      btnEl.style.background = "rgba(52, 211, 153, 0.15)";
      btnEl.style.borderColor = "rgba(52, 211, 153, 0.3)";
      btnEl.style.color = "#a7f3d0";
    } else {
      btnEl.title = "語音輸入";
      btnEl.style.color = "#a78bfa";
    }
    lucide.createIcons();
    
    if (currentRecordingBtn === btnEl) {
      currentRecordingBtn = null;
    }
  };

  recognition.start();
}

function closeAiSidebar() {
  aiSidebar.classList.remove("show");
  aiSidebarOverlay.classList.remove("show");
  setTimeout(() => {
    if (!aiSidebar.classList.contains("show")) {
      aiSidebarOverlay.style.display = "none";
    }
  }, 300);
}

// Open settings Modal
function openAiKeyModal() {
  const provider = getAiProvider();
  if (aiProviderSelect) {
    aiProviderSelect.value = provider;
  }
  updateAiKeyModalUI(provider);
  
  const key = localStorage.getItem(provider === "gemini" ? "hsqa_gemini_api_key" : "hsqa_groq_api_key") || "";
  if (geminiApiKeyInput) {
    geminiApiKeyInput.value = key;
  }
  
  aiKeyModal.classList.add("show");
}

function closeAiKeyModal() {
  aiKeyModal.classList.remove("show");
}

// Render markdown helper (simple formatting for display)
function formatMarkdown(text) {
  if (!text) return "";
  
  let html = text;
  
  // HTML escape to prevent XSS
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
    
  // Blockquotes
  html = html.replace(/^&gt;\s+(.+)$/gm, "<blockquote>$1</blockquote>");
  
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  
  // Code block & inline code
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  
  // Lists
  html = html.replace(/^\s*-\s+(.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>");
  
  // Paragraphs
  html = html.replace(/(?:\r\n|\r|\n)/g, "<br>");
  
  return html;
}

// Append chat message to sidebar UI
function appendChatMessage(sender, text) {
  aiWelcomeContainer.style.display = "none";
  aiChatMessages.style.display = "flex";

  const msgDiv = document.createElement("div");
  msgDiv.className = `ai-message ${sender}`;

  const metaSpan = document.createElement("span");
  metaSpan.className = "ai-message-meta";
  metaSpan.innerText = sender === "user" ? "您" : "小鴻";

  const bubbleDiv = document.createElement("div");
  bubbleDiv.className = "ai-message-bubble";
  bubbleDiv.innerHTML = formatMarkdown(text);

  msgDiv.appendChild(metaSpan);
  msgDiv.appendChild(bubbleDiv);
  aiChatMessages.appendChild(msgDiv);

  // Scroll to bottom
  aiSidebarBodyScrollToBottom();
}

function aiSidebarBodyScrollToBottom() {
  const sidebarBody = aiSidebar.querySelector(".ai-sidebar-body");
  sidebarBody.scrollTop = sidebarBody.scrollHeight;
}

// Handle sending message in sidebar
async function handleSendAiMessage(customText = null) {
  const messageText = (customText !== null ? customText : aiChatInput.value).trim();
  if (!messageText) return;

  if (customText === null) {
    aiChatInput.value = "";
    aiChatInput.style.height = "auto";
  }

  if (!isAiReady()) {
    openAiKeyModal();
    showToast("請設定您的 API 金鑰以啟用 Gemini 服務", "danger");
    return;
  }

  appendChatMessage("user", messageText);

  const typingDiv = document.createElement("div");
  typingDiv.className = "ai-message assistant typing-indicator-msg";
  typingDiv.innerHTML = `
    <span class="ai-message-meta">小鴻</span>
    <div class="ai-message-bubble" style="padding: 10px 14px;">
      <div class="ai-typing-indicator">
        <div class="ai-typing-dot"></div>
        <div class="ai-typing-dot"></div>
        <div class="ai-typing-dot"></div>
      </div>
    </div>
  `;
  aiChatMessages.appendChild(typingDiv);
  aiSidebarBodyScrollToBottom();

  const boardState = getBoardContext();
  const fullPrompt = `當前留言板狀態:\n${boardState}\n\n使用者提問: ${messageText}`;

  try {
    const aiResponse = await callGemini(fullPrompt);
    typingDiv.remove();
    appendChatMessage("assistant", aiResponse);
  } catch (err) {
    typingDiv.remove();
    if (err.message === "QUOTA_EXCEEDED") {
      appendChatMessage("assistant", "⚠️ **AI 每日使用額度已達上限**\n\n今日的 Gemini API 免費配額（20 次）已用完，小鴻暫時無法回應。\n\n**解決方式：**\n- 明天額度自動重置後即可繼續使用。\n- 或請管理員至 [Google AI Studio](https://aistudio.google.com/) 開啟付費方案，即可無限制使用。");
      showToast("⚠️ AI 每日使用額度已達上限，請明天再試或開啟付費方案", "danger");
    } else {
      appendChatMessage("assistant", `❌ 發生錯誤: ${err.message}\n請點擊上方設定齒輪檢查 API 金鑰。`);
    }
  }
}

// AI Content Polish (Form optimization helper)
async function handleAiPolish() {
  const title = cardTitleInput.value.trim();
  const content = cardContentInput.value.trim();
  
  if (!content) {
    showToast("請先輸入卡片內容再進行潤飾", "danger");
    return;
  }

  const polishBtn = document.getElementById("aiPolishBtn");
  const origHtml = polishBtn.innerHTML;
  
  polishBtn.disabled = true;
  polishBtn.innerHTML = `<i data-lucide="loader" class="animate-spin" style="width: 12px; height: 12px;"></i> 潤飾中...`;
  lucide.createIcons();

  const polishPrompt = `你是一個專業的化工廠資材與品質工程師。請幫我將以下通報草稿，潤飾並重新整理成結構清晰、用詞專業的通報文件。
請保留原本草稿中的所有重要數據（如數值、人名、線別、批號）。
請以下列結構重寫：
- 【異常現象與描述】:
- 【暫定影響範疇】:
- 【建議處置與即時圍堵措施】:

原本的標題為：${title || "未命名"}
原本的卡片內容為：\n${content}`;

  try {
    const polishedResult = await callGemini(polishPrompt, "你是一個專門寫資材、品質與工作交接通報的專家，擅長使用項目符號與清晰段落。");
    cardContentInput.value = polishedResult;
    showToast("卡片內容已完成 AI 潤飾！");
  } catch (err) {
    console.error("AI Polish error:", err);
    if (err.message === "QUOTA_EXCEEDED") {
      showToast("⚠️ AI 每日使用額度已達上限，請明天再試或請管理員開啟付費方案", "danger");
    } else {
      showToast(`潤飾失敗: ${err.message}`, "danger");
    }
  } finally {
    polishBtn.disabled = false;
    polishBtn.innerHTML = origHtml;
    lucide.createIcons();
  }
}

// AI Diagnosis posted as comments
async function runCardDiagnosis(colId, cardId) {
  const col = state.columns.find(c => c.id === colId);
  if (!col) return;
  const card = col.cards.find(c => c.id === cardId);
  if (!card) return;

  const cardEl = document.querySelector(`.board-card[data-card-id="${cardId}"]`);
  const diagnoseBtn = cardEl?.querySelector(".btn-card-diagnose");
  const origBtnContent = diagnoseBtn ? diagnoseBtn.innerHTML : "";
  
  if (diagnoseBtn) {
    diagnoseBtn.disabled = true;
    diagnoseBtn.innerHTML = `<i data-lucide="loader" class="animate-spin" style="width: 11px; height: 11px;"></i> 診斷中...`;
    lucide.createIcons();
  }

  showToast("AI 診斷分析啟動中...");

  const diagnosePrompt = `你是一個品質分析與客訴處理（CAR）專家，熟悉 5-Why 根因分析。
請針對以下這張留言板上的品質事件卡片（包含標題與內文描述），進行專業診斷。
請提供：
1. 簡要的【5-Why 分析推導】（大膽猜測可能的原因，並標記需現場查證事項）
2. 【長期防呆與糾正措施建議（Corrective Action）】

卡片欄位: ${col.title}
卡片標題: ${card.title}
卡片內文: ${card.content || "無詳細內文"}`;

  try {
    const diagnosisResult = await callGemini(diagnosePrompt, "你是一個專業的化學資材與品質分析專家。請產出精簡、專業、可以直接寫進工作報告的 5-Why 分析。");
    
    if (!card.comments) card.comments = [];
    
    card.comments.push({
      author: "🤖 小鴻",
      body: diagnosisResult,
      timestamp: Date.now()
    });
    
    card.commentsOpen = true;

    saveState("AI 5-Why 診斷", card.title, "小鴻已生成診斷並新增為卡片留言");
    renderBoard();
    showToast("AI 診斷已完成，已新增為卡片留言！");
  } catch (err) {
    console.error("AI Diagnosis error:", err);
    if (err.message === "QUOTA_EXCEEDED") {
      showToast("⚠️ AI 每日使用額度已達上限，請明天再試或請管理員開啟付費方案", "danger");
    } else {
      showToast(`AI 診斷失敗: ${err.message}`, "danger");
    }
    if (diagnoseBtn) {
      diagnoseBtn.disabled = false;
      diagnoseBtn.innerHTML = origBtnContent;
      lucide.createIcons();
    }
  }
}

// Run Startup
document.addEventListener("DOMContentLoaded", init);
