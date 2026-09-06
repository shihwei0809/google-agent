import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { MessageCircle, Send, BookOpen, ChevronRight, Upload, FileText, Trash2 } from 'lucide-react';
import axios from 'axios';
import mermaid from 'mermaid';

const API_BASE = `http://${window.location.hostname}:8000`;

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
});

function App() {
  const [materials, setMaterials] = useState([]);
  const [currentMaterialName, setCurrentMaterialName] = useState('');
  const [currentContent, setCurrentContent] = useState('# 請從左側選擇教材');
  const [isAdmin, setIsAdmin] = useState(false);
  
  // 新增編輯模式的狀態
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '您好！我是您的專屬 AI 助教。請問您對目前的教材有什麼疑問嗎？' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

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

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_BASE}/materials`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await fetchMaterials();
      selectMaterial(res.data.filename || file.name);
    } catch (err) {
      alert('上傳失敗');
      console.error(err);
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
    <div className="flex h-screen bg-gray-50">
      {/* 左側欄：章節或檔案列表 */}
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
                  img: ({ node, ...props }) => {
                    const src = props.src?.startsWith('http') ? props.src : `${API_BASE}/materials_static/${props.src}`;
                    return <img {...props} src={src} className="max-w-full h-auto rounded shadow-sm" alt={props.alt || ''} />;
                  },
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
                          const src = props.src?.startsWith('http') ? props.src : `${API_BASE}/materials_static/${props.src}`;
                          return <img {...props} src={src} className="max-w-full h-auto rounded shadow-sm" alt={props.alt || ''} />;
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
    </div>
  );
}

export default App;
