import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { MessageCircle, Send, BookOpen, ChevronRight, Upload, FileText, Trash2, Camera, Square, Edit3, ZoomIn, X, ExternalLink, Maximize2 } from 'lucide-react';
import axios from 'axios';
import mermaid from 'mermaid';
import ImageAnnotatorModal from './ImageAnnotatorModal';

const API_BASE = `http://${window.location.hostname}:8000`;

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
});

// 動態解析圖片路徑：支援相對路徑、自動將寫死的 localhost:8000/127.0.0.1:8000 替換為當前伺服器主機 IP
export function resolveImageUrl(rawSrc) {
  if (!rawSrc) return '';
  let s = rawSrc.trim();

  // 若圖片路徑寫死了 localhost:8000 或 127.0.0.1:8000，自動替換為當前連線的主機 API_BASE
  s = s.replace(/^https?:\/\/(localhost|127\.0\.0\.1):8000\/materials_static\//i, `${API_BASE}/materials_static/`);
  s = s.replace(/^https?:\/\/(localhost|127\.0\.0\.1):8000/i, API_BASE);

  // 若為外部完整網址且非本地，直接返回
  if (s.startsWith('http://') || s.startsWith('https://')) {
    return s;
  }

  // 處理以 /materials_static/ 開頭的相對路徑
  if (s.startsWith('/materials_static/')) {
    return `${API_BASE}${s}`;
  }
  if (s.startsWith('materials_static/')) {
    return `${API_BASE}/${s}`;
  }

  // 純檔名（安全編碼路徑，確保中文檔名與特殊字元均能正常請求）
  let safeSrc = s;
  try {
    safeSrc = encodeURI(decodeURI(s));
  } catch (e) {
    safeSrc = s;
  }
  return `${API_BASE}/materials_static/${safeSrc}`;
}

function MarkdownImage({ src, alt, onOpenAnnotator, onUploadAndAnnotate, onPreviewImage, isAdmin, ...props }) {
  const isRealImage = /\.(png|jpe?g|gif|webp|svg)$/i.test(src || '');
  const [hasError, setHasError] = useState(false);

  // 如果不是標準圖片檔案名稱，或者後端載入失敗，優雅渲染為精美 SOP 提示卡片
  if (!isRealImage || hasError) {
    let hintText = (!isRealImage ? src : null) || alt || "請於系統中截取對應操作畫面";
    try {
      hintText = decodeURIComponent(hintText);
    } catch (e) {}
    return (
      <div className="my-5 p-4 border border-blue-200 bg-gradient-to-r from-blue-50/80 to-indigo-50/50 rounded-xl flex items-start gap-3 shadow-xs">
        <div className="p-2 bg-blue-500 text-white rounded-lg shrink-0 mt-0.5 shadow-sm">
          <Camera className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="text-xs font-bold text-blue-700 uppercase tracking-wide mb-1 flex items-center gap-1.5">
            <span>📸 建議操作截圖</span>
            <span className="text-[10px] px-1.5 py-0.5 bg-blue-200/70 text-blue-800 rounded font-normal">SOP重點</span>
          </div>
          <div className="text-sm font-medium text-gray-800 leading-relaxed">
            {hintText}
          </div>
          {isAdmin ? (
            <div className="text-xs text-gray-500 mt-2.5 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-1">
                <span>💡 提示：點擊右上方「編輯教材」，按</span>
                <kbd className="px-1.5 py-0.5 bg-white border border-gray-300 rounded shadow-2xs text-[11px] font-mono text-gray-700">Ctrl+V</kbd>
                <span>即可貼上截圖，或直接：</span>
              </div>
              <button
                type="button"
                onClick={() => onUploadAndAnnotate && onUploadAndAnnotate(src)}
                className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold flex items-center gap-1 shadow-xs transition-colors cursor-pointer"
              >
                <Square className="w-3.5 h-3.5" />
                <span>選圖加框標註</span>
              </button>
            </div>
          ) : (
            <div className="text-xs text-gray-400 mt-2 flex items-center gap-1">
              <span>💡 請參閱此步驟對應之系統操作畫面</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  let cleanOriginalName = src;
  try {
    cleanOriginalName = decodeURIComponent(src);
  } catch (e) {}

  const fullSrc = resolveImageUrl(src);
  return (
    <div className="relative group my-4 inline-block max-w-full">
      {/* 圖片點擊可放大容器 */}
      <div 
        className="relative overflow-hidden rounded-lg cursor-zoom-in border border-gray-100 shadow-md hover:shadow-xl transition-all"
        onClick={() => onPreviewImage && onPreviewImage({ src: fullSrc, alt: alt || cleanOriginalName, originalFilename: cleanOriginalName })}
        title="點擊放大檢視圖片"
      >
        <img 
          {...props}
          src={fullSrc} 
          className="max-w-full h-auto block transition-transform duration-300 group-hover:scale-[1.01]" 
          alt={alt || ''} 
          onError={() => setHasError(true)}
        />
        
        {/* 懸浮放大提示徽章（左下角） */}
        <div className="absolute bottom-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-gray-900/80 backdrop-blur-xs text-white text-[11px] px-2.5 py-1 rounded-md flex items-center gap-1.5 shadow pointer-events-none">
          <ZoomIn className="w-3.5 h-3.5 text-blue-400" />
          <span>點擊放大檢視</span>
        </div>
      </div>

      {/* 管理員專屬：圖片懸浮標註按鈕（右上角，僅登入管理員可見） */}
      {isAdmin && (
        <div className="absolute top-2.5 right-2.5 opacity-0 group-hover:opacity-100 transition-all duration-200 flex items-center gap-1 bg-gray-900/85 backdrop-blur-xs p-1 rounded-xl shadow-lg z-10">
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onOpenAnnotator && onOpenAnnotator({
                src: fullSrc,
                originalFilename: cleanOriginalName,
                fromEditor: false
              });
            }}
            className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-xs transition-all cursor-pointer"
            title="在圖片上加框、標記代號(①②③)或說明文字"
          >
            <Square className="w-3.5 h-3.5" />
            <span>加框/代號標註</span>
          </button>
        </div>
      )}
    </div>
  );
}

function App() {
  const [materials, setMaterials] = useState([]);
  const [currentMaterialName, setCurrentMaterialName] = useState('');
  const [currentContent, setCurrentContent] = useState('# 請從左側選擇教材');
  const [isAdmin, setIsAdmin] = useState(false);
  
  // 新增編輯模式的狀態
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '您好！我是您的專屬 AI 助教。請問您對目前的教材有什麼疑問嗎？' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const annotateFileInputRef = useRef(null);
  const targetReplacePlaceholderRef = useRef(null);

  // 圖片標註彈窗狀態
  const [annotatingImage, setAnnotatingImage] = useState(null); // { src, originalFilename, fromEditor }

  // 圖片放大預覽燈箱狀態
  const [previewImage, setPreviewImage] = useState(null); // { src, alt, originalFilename }

  // 監聽鍵盤 ESC 關閉預覽
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (previewImage) setPreviewImage(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [previewImage]);

  // 開啟圖片標註編輯器
  const handleOpenAnnotator = ({ src, originalFilename, fromEditor = false }) => {
    setAnnotatingImage({
      src,
      originalFilename,
      fromEditor
    });
  };

  // 從本機選擇圖片進行標註
  const handleUploadAndAnnotate = (targetPlaceholder = null) => {
    targetReplacePlaceholderRef.current = targetPlaceholder;
    annotateFileInputRef.current?.click();
  };

  const handleAnnotateFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result;
      setAnnotatingImage({
        src: dataUrl,
        originalFilename: targetReplacePlaceholderRef.current,
        fromEditor: isEditing
      });
      targetReplacePlaceholderRef.current = null;
    };
    reader.readAsDataURL(file);
    e.target.value = ''; // 重置 input 供下次重複選擇相同檔案
  };

  // 儲存標註後的圖片並自動更新教材
  const handleSaveAnnotatedImage = async (newFilename) => {
    if (!annotatingImage) return;
    const oldName = annotatingImage.originalFilename;

    if (oldName && currentMaterialName) {
      let decodedOldName = oldName;
      try {
        decodedOldName = decodeURIComponent(oldName);
      } catch (e) {}

      // 提取純檔名（去除任何 URL 前綴如 http://... 或 materials_static/）
      const cleanOldName = decodedOldName.split('/').pop().split('\\').pop();

      // 所有可能出現在 Markdown 中的舊檔名樣式
      const targetsToReplace = Array.from(new Set([
        oldName,
        decodedOldName,
        cleanOldName,
        encodeURI(cleanOldName),
        encodeURIComponent(cleanOldName)
      ])).filter(t => t && t.length > 1);

      let updatedContent = currentContent;
      let updatedEditContent = editContent;
      let replaced = false;

      // 1. 正規表達式精準替換 markdown 圖片語法: ![alt](target) -> ![alt](newFilename)
      for (const target of targetsToReplace) {
        const escaped = target.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const imgRegex = new RegExp(`(!\\[[^\\]]*\\]\\()([^)]*?${escaped})(\\))`, 'g');
        if (imgRegex.test(updatedContent)) {
          updatedContent = updatedContent.replace(imgRegex, `$1${newFilename}$3`);
          updatedEditContent = updatedEditContent.replace(imgRegex, `$1${newFilename}$3`);
          replaced = true;
        }
      }

      // 2. 若不是標準 markdown 圖片（例如純文字佔位符），直接全局替換
      if (!replaced) {
        for (const target of targetsToReplace) {
          if (updatedContent.includes(target)) {
            updatedContent = updatedContent.replaceAll(target, `![操作標註圖](${newFilename})`);
            updatedEditContent = updatedEditContent.replaceAll(target, `![操作標註圖](${newFilename})`);
            replaced = true;
          }
        }
      }

      setCurrentContent(updatedContent);
      setEditContent(updatedEditContent);

      try {
        await fetch(`${API_BASE}/materials/${currentMaterialName}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: updatedContent })
        });
        alert('🎉 圖片已成功更新！畫面已自動套用最新圖片。');
      } catch (e) {
        console.error(e);
        alert('新圖片已上傳，但自動同步至教材時發生錯誤，請點擊「儲存修改」。');
      }
    } else if (isEditing || annotatingImage.fromEditor) {
      const imgMarkdown = `\n\n![操作標註圖](${newFilename})\n\n`;
      setEditContent(prev => prev + imgMarkdown);
      alert('🎉 標註圖片已成功插入至編輯區最下方！');
    }

    setAnnotatingImage(null);
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 處理管理員登入
  const handleAdminLogin = () => {
    if (isAdmin) {
      setIsAdmin(false);
    } else {
      const pwd = window.prompt('請輸入管理員密碼：');
      if (pwd === 'admin123') { // 預設密碼
        setIsAdmin(true);
        alert('已切換為管理員模式！現在可以上傳與刪除教材。');
      } else if (pwd !== null) {
        alert('密碼錯誤！');
      }
    }
  };

  // 載入教材列表
  const fetchMaterials = async () => {
    try {
      const res = await axios.get(`${API_BASE}/materials`);
      setMaterials(res.data.materials);
      if (res.data.materials.length > 0 && !currentMaterialName) {
        selectMaterial(res.data.materials[0]);
      } else if (res.data.materials.length === 0) {
        setCurrentMaterialName('');
        setCurrentContent('# 尚無教材');
      }
    } catch (err) {
      console.error("無法取得教材列表", err);
    }
  };

  useEffect(() => {
    fetchMaterials();
  }, []);

  // 選擇並讀取教材
  const selectMaterial = async (filename) => {
    setIsEditing(false);
    try {
      const res = await axios.get(`${API_BASE}/materials/${filename}`);
      setCurrentContent(res.data.content || '# 教材為空');
      setCurrentMaterialName(filename);
    } catch (err) {
      console.error("無法讀取教材", err);
    }
  };

  // 處理上傳
  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const isVideo = /\.(mp4|mov|avi|webm)$/i.test(file.name);
    setUploadMessage(isVideo 
      ? `正在上傳並由 Gemini 深度觀看影片「${file.name}」，提煉操作 SOP 與生成流程圖，通常需要 30~60 秒，請稍候...` 
      : `正在上傳並解析文件「${file.name}」...`
    );
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_BASE}/materials`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (res.data?.error) {
        throw new Error(res.data.error);
      }

      await fetchMaterials();
      const targetName = res.data?.filename || (file.name.replace(/\.[^/.]+$/, "") + ".md");
      await selectMaterial(targetName);
      alert(`✅ 檔案「${file.name}」已由 AI 成功轉化為教學手冊！`);
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.response?.data?.error || err.message;
      alert(`❌ 上傳解析失敗：\n${errorDetail}`);
      console.error("上傳失敗", err);
    } finally {
      setIsUploading(false);
      setUploadMessage('');
    }
    
    // 清空 input 讓下次同檔名也能觸發 onChange
    e.target.value = null;
  };

  // 處理刪除
  const handleDelete = async (e, filename) => {
    e.stopPropagation();
    if (!window.confirm(`確定要刪除教材 ${filename} 嗎？`)) return;
    try {
      await fetch(`${API_BASE}/materials/${filename}`, { method: 'DELETE' });
      if (currentMaterialName === filename) {
        setCurrentMaterialName('');
        setCurrentContent('# 請從左側選擇教材');
        setIsEditing(false);
      }
      await fetchMaterials();
    } catch (err) {
      alert('刪除失敗');
      console.error(err);
    }
  };

  const handleSaveMaterial = async () => {
    try {
      const response = await fetch(`${API_BASE}/materials/${currentMaterialName}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: editContent })
      });
      if (response.ok) {
        setCurrentContent(editContent);
        setIsEditing(false);
        alert('儲存成功！');
      } else {
        alert('儲存失敗！');
      }
    } catch (err) {
      alert('儲存失敗');
      console.error(err);
    }
  };

  const handleGenerateImage = async () => {
    const prompt = window.prompt("請輸入您想要 AI 畫出的畫面 (例如：工廠堆高機搬運鐵桶的示意圖)：");
    if (!prompt) return;
    
    setIsGeneratingImage(true);
    try {
      const res = await fetch(`${API_BASE}/generate_image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      const data = await res.json();
      if (data.filename) {
        const imgMarkdown = `\n\n![AI示意圖](${data.filename})\n\n`;
        // 將圖片插入到目前編輯文字的游標處或是最下方
        setEditContent(prev => prev + imgMarkdown);
        alert('✨ 圖片已成功生成並插入至草稿最下方！');
      } else {
        alert('生成失敗: ' + data.error);
      }
    } catch (err) {
      alert('圖片生成發生錯誤');
      console.error(err);
    } finally {
      setIsGeneratingImage(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !currentContent || isLoading) return;
    
    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setIsLoading(true);

    // 先在畫面上加入一個空的 AI 回覆泡泡
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          context: currentContent,
          material_name: currentMaterialName
        })
      });

      if (!response.ok) {
        throw new Error("伺服器錯誤");
      }

      // 如果回傳是 JSON 格式的錯誤訊息 (例如 API 失敗)
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
         const data = await response.json();
         setMessages(prev => {
           const newMessages = [...prev];
           newMessages[newMessages.length - 1].content = data.response;
           return newMessages;
         });
         setIsLoading(false);
         return;
      }

      // 讀取串流 (打字機效果)
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        setMessages(prev => {
          const newMessages = [...prev];
          const lastIndex = newMessages.length - 1;
          // [重要修復] 必須拷貝物件，不能直接修改舊物件的屬性，否則 React 嚴格模式會導致文字重複疊加兩次
          newMessages[lastIndex] = {
            ...newMessages[lastIndex],
            content: newMessages[lastIndex].content + chunk
          };
          return newMessages;
        });
      }

    } catch (error) {
      console.error(error);
      setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1].content = '發生錯誤，請確認後端是否啟動，或是 API 金鑰是否正確。';
          return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 relative">
      {/* 上傳等待遮罩 */}
      {isUploading && (
        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-black/75 text-white backdrop-blur-sm p-6 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-400 mb-4"></div>
          <h2 className="text-2xl font-bold mb-2">AI 智能解析進行中...</h2>
          <p className="text-gray-200 text-base max-w-lg leading-relaxed">
            {uploadMessage || "正在萃取文件並使用 AI 提煉教學重點，請稍候..."}
          </p>
        </div>
      )}
      
      {/* 側邊欄：教材清單與操作 */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-bold flex items-center text-gray-800">
            <BookOpen className="w-5 h-5 mr-2" />
            教材列表
          </h2>
          <div className="flex gap-2">
            {isAdmin && (
              <button 
                onClick={() => fileInputRef.current?.click()}
                className="p-1.5 bg-blue-100 text-blue-600 rounded hover:bg-blue-200 transition-colors"
                title="上傳新教材"
              >
                <Upload className="w-4 h-4" />
              </button>
            )}
            <button 
              onClick={handleAdminLogin}
              className={`p-1.5 rounded transition-colors text-xs font-bold ${isAdmin ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
              title={isAdmin ? "登出管理員" : "管理員登入"}
            >
              {isAdmin ? "Admin" : "登入"}
            </button>
          </div>
          <input 
            type="file" 
            ref={fileInputRef}
            onChange={handleUpload}
            accept=".md,.txt,.pdf,.docx,.xlsx,.pptx,.mp4,.mov,.avi,.webm"
            className="hidden" 
          />
        </div>
        <div className="flex-1 overflow-y-auto">
          {materials.length === 0 ? (
            <div className="p-4 text-sm text-gray-400">尚無教材。</div>
          ) : (
            materials.map((mat) => (
              <div 
                key={mat}
                onClick={() => selectMaterial(mat)}
                className={`p-3 font-medium flex items-center justify-between cursor-pointer transition-colors ${
                  currentMaterialName === mat 
                    ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-500' 
                    : 'text-gray-600 hover:bg-gray-100 border-l-4 border-transparent'
                }`}
              >
                <div className="flex items-center overflow-hidden">
                  {currentMaterialName === mat ? (
                    <ChevronRight className="w-4 h-4 mr-1 shrink-0" />
                  ) : (
                    <FileText className="w-4 h-4 mr-1 shrink-0 text-gray-400" />
                  )}
                  <span className="truncate" title={mat}>{mat}</span>
                </div>
                {isAdmin && (
                  <button 
                    onClick={(e) => handleDelete(e, mat)}
                    className="text-gray-400 hover:text-red-500 p-1"
                    title="刪除"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* 中間：教材內容顯示區塊 */}
      <div className="flex-1 overflow-y-auto p-8 relative">
        {currentMaterialName && isAdmin && (
          <div className="absolute top-4 right-8 flex gap-2">
            {!isEditing ? (
              <button
                onClick={() => {
                  setEditContent(currentContent);
                  setIsEditing(true);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700 text-sm font-medium"
              >
                編輯教材
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => handleUploadAndAnnotate(null)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded shadow hover:bg-indigo-700 text-sm font-medium flex items-center gap-1.5"
                  title="選擇本機圖片加框、標記代號(①②③)或文字後插入教材"
                >
                  <Square className="w-4 h-4" />
                  <span>圖片加框標註</span>
                </button>
                <button
                  onClick={handleGenerateImage}
                  disabled={isGeneratingImage}
                  className="px-4 py-2 bg-purple-600 text-white rounded shadow hover:bg-purple-700 text-sm font-medium disabled:opacity-50"
                >
                  {isGeneratingImage ? "✨ 畫圖中..." : "✨ AI 生成圖片"}
                </button>
                <button
                  onClick={handleSaveMaterial}
                  className="px-4 py-2 bg-green-600 text-white rounded shadow hover:bg-green-700 text-sm font-medium"
                >
                  儲存修改
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 bg-gray-500 text-white rounded shadow hover:bg-gray-600 text-sm font-medium"
                >
                  取消
                </button>
              </>
            )}
          </div>
        )}
        <div className="max-w-3xl mx-auto bg-white p-10 shadow-sm rounded-lg border border-gray-100 min-h-full">
          {isEditing ? (
            <textarea
              className="w-full h-full min-h-[600px] p-4 border border-blue-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              onPaste={async (e) => {
                const items = e.clipboardData?.items;
                if (!items) return;
                for (let i = 0; i < items.length; i++) {
                  if (items[i].type.indexOf('image') !== -1) {
                    e.preventDefault(); // 阻止預設貼上文字行為
                    const file = items[i].getAsFile();
                    if (!file) continue;
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    try {
                      // 顯示上傳中提示
                      const start = e.target.selectionStart;
                      const end = e.target.selectionEnd;
                      const uploadingText = "\n![圖片上傳中...]()\n";
                      setEditContent(prev => prev.substring(0, start) + uploadingText + prev.substring(end));
                      
                      const res = await fetch(`${API_BASE}/upload_image`, {
                        method: 'POST',
                        body: formData
                      });
                      const data = await res.json();
                      if (data.url) {
                        const imgMd = `\n![系統截圖](${data.url})\n`;
                        // 替換掉上傳中文字
                        setEditContent(prev => prev.replace(uploadingText, imgMd));
                        
                        // 提示是否立即加框標註
                        setTimeout(() => {
                          if (window.confirm("📸 截圖已成功貼上！\n需要立即開啟「加框與代號標註工具」，在圖片上加紅框、步驟序號(①②③)或說明文字嗎？")) {
                            handleOpenAnnotator({
                              src: `${API_BASE}/materials_static/${data.url}`,
                              originalFilename: data.url,
                              fromEditor: true
                            });
                          }
                        }, 200);
                      } else {
                        setEditContent(prev => prev.replace(uploadingText, "\n(圖片上傳失敗)\n"));
                      }
                    } catch(err) {
                      console.error(err);
                    }
                    break;
                  }
                }
              }}
              placeholder="您可以在這裡修改教材，或是直接按 Ctrl+V 貼上您的螢幕截圖！"
            />
          ) : (
            <div className="prose prose-blue max-w-none">
              <ReactMarkdown
                components={{
                  img: (props) => (
                    <MarkdownImage 
                      {...props} 
                      isAdmin={isAdmin}
                      onOpenAnnotator={handleOpenAnnotator}
                      onUploadAndAnnotate={handleUploadAndAnnotate}
                      onPreviewImage={(imgData) => setPreviewImage(imgData)}
                    />
                  ),
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    if (!inline && match && match[1] === 'mermaid') {
                      useEffect(() => {
                        try {
                          mermaid.contentLoaded();
                        } catch (e) {}
                      }, []);
                      return (
                        <div className="mermaid flex justify-center my-8">
                          {String(children).replace(/\n$/, '')}
                        </div>
                      );
                    }
                    return (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  }
                }}
              >
                {currentContent}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>

      {/* 右側：AI 對話區 */}
      <div className="w-96 bg-white border-l border-gray-200 flex flex-col shadow-lg shrink-0">
        <div className="p-4 border-b border-gray-200 bg-blue-600 text-white flex justify-between items-center">
          <h2 className="text-lg font-bold flex items-center">
            <MessageCircle className="w-5 h-5 mr-2" />
            AI 助教
          </h2>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-lg p-3 ${msg.role === 'user' ? 'bg-blue-100 text-blue-900' : 'bg-gray-100 text-gray-800'}`}>
                <div className="text-sm">
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown
                      components={{
                        img: ({ node, ...props }) => {
                          const src = resolveImageUrl(props.src);
                          return (
                            <img 
                              {...props} 
                              src={src} 
                              className="max-w-full h-auto rounded shadow-sm cursor-zoom-in hover:opacity-95 transition-opacity" 
                              alt={props.alt || ''} 
                              onClick={() => setPreviewImage({ src, alt: props.alt || '', originalFilename: props.src })}
                              title="點擊放大檢視"
                            />
                          );
                        }
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-3 text-gray-500 text-sm animate-pulse">
                AI 思考中...
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center bg-white border border-gray-300 rounded-full px-4 py-2 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.nativeEvent.isComposing) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="請輸入您的問題，AI 將自動跨教材為您解答..."
              className="flex-1 bg-transparent outline-none text-sm text-gray-700 placeholder-gray-400"
            />
            <button 
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="ml-2 text-blue-600 hover:text-blue-800 disabled:text-gray-400 transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* 隱藏的標註圖片選擇器 */}
      <input
        type="file"
        ref={annotateFileInputRef}
        onChange={handleAnnotateFileSelect}
        accept="image/*"
        className="hidden"
      />

      {/* 圖片加框/代號/文字標註編輯器彈窗 */}
      {annotatingImage && (
        <ImageAnnotatorModal
          imageSrc={annotatingImage.src}
          apiBase={API_BASE}
          onClose={() => setAnnotatingImage(null)}
          onSave={handleSaveAnnotatedImage}
        />
      )}

      {/* 圖片點擊放大檢視燈箱 (Lightbox) */}
      {previewImage && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md p-4 animate-in fade-in duration-200 select-none"
          onClick={() => setPreviewImage(null)}
        >
          {/* 頂部操作列 */}
          <div 
            className="absolute top-0 left-0 right-0 px-6 py-4 flex items-center justify-between text-white bg-gradient-to-b from-black/80 via-black/40 to-transparent z-10"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-gray-100 truncate max-w-md">
                {previewImage.alt || previewImage.originalFilename || '圖片放大檢視'}
              </span>
              <span className="text-xs px-2 py-0.5 bg-white/15 rounded-full text-gray-300 font-mono hidden sm:inline-block">
                按 ESC 或點擊背景關閉
              </span>
            </div>

            <div className="flex items-center gap-2">
              {/* 如果是已登入管理員，支援直接從大圖開啟加框標註工具 */}
              {isAdmin && (
                <button
                  type="button"
                  onClick={() => {
                    const current = previewImage;
                    setPreviewImage(null);
                    handleOpenAnnotator({
                      src: current.src,
                      originalFilename: current.originalFilename || current.src,
                      fromEditor: false
                    });
                  }}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer shadow-md"
                  title="開啟加框與代號標註工具"
                >
                  <Square className="w-3.5 h-3.5" />
                  <span>加框/代號標註</span>
                </button>
              )}

              <a
                href={previewImage.src}
                target="_blank"
                rel="noopener noreferrer"
                download={previewImage.originalFilename || "image.png"}
                className="p-2 hover:bg-white/20 text-gray-200 hover:text-white rounded-lg transition-colors cursor-pointer"
                title="在新分頁開啟/下載原圖"
              >
                <ExternalLink className="w-5 h-5" />
              </a>

              <button
                type="button"
                onClick={() => setPreviewImage(null)}
                className="p-2 hover:bg-white/20 text-gray-200 hover:text-white rounded-lg transition-colors cursor-pointer ml-1"
                title="關閉放大檢視 (ESC)"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* 大圖本體 */}
          <div 
            className="max-w-[96vw] max-h-[88vh] flex items-center justify-center"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={previewImage.src}
              alt={previewImage.alt || ''}
              className="max-w-full max-h-[88vh] object-contain rounded-lg shadow-2xl transition-transform duration-200 cursor-zoom-out"
              onClick={() => setPreviewImage(null)}
              title="點擊圖片關閉"
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
