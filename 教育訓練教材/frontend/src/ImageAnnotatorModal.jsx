import React, { useState, useRef, useEffect } from 'react';
import { 
  Square, 
  Type, 
  Hash, 
  ArrowUpRight, 
  Undo2, 
  Redo2, 
  Trash2, 
  Download, 
  Check, 
  X, 
  RotateCcw,
  Palette,
  FolderOpen,
  AlertCircle,
  AlertTriangle
} from 'lucide-react';

const COLORS = [
  { name: '紅色', value: '#ef4444' },
  { name: '藍色', value: '#3b82f6' },
  { name: '綠色', value: '#10b981' },
  { name: '橙色', value: '#f97316' },
  { name: '黃色', value: '#eab308' },
  { name: '紫色', value: '#8b5cf6' },
  { name: '純白', value: '#ffffff' },
  { name: '純黑', value: '#1f2937' },
];

const WARNING_PRESETS = [
  { label: '⚠️ 注意', bg: '#fef08a', border: '#eab308', text: '#854d0e' }, // 黃色警戒
  { label: '❗ 重要', bg: '#fee2e2', border: '#ef4444', text: '#991b1b' }, // 紅色重要
  { label: '★ 必看', bg: '#ffedd5', border: '#f97316', text: '#9a3412' }, // 橙色必看
  { label: '⛔ 禁止', bg: '#ffffff', border: '#ef4444', text: '#dc2626' }, // 白底紅字禁令
  { label: '💡 提示', bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' }, // 藍色提示
  { label: '✔️ 必填', bg: '#dcfce7', border: '#10b981', text: '#166534' }, // 綠色確認
];

export default function ImageAnnotatorModal({ 
  imageSrc, 
  onClose, 
  onSave, 
  apiBase = typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : 'http://localhost:8000'
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const fileInputRef = useRef(null);

  // 當前選擇工具: 'rect' (加框), 'badge' (加代號/序號), 'warning' (重點注意), 'text' (加文字), 'arrow' (加箭頭)
  const [activeTool, setActiveTool] = useState('rect');
  const [color, setColor] = useState('#ef4444'); // 預設亮紅最吸睛
  const [strokeWidth, setStrokeWidth] = useState(4);
  const [badgeType, setBadgeType] = useState('circle_num'); // 'circle_num' (①), 'num' (1), 'alpha' (A)
  const [badgeCounter, setBadgeCounter] = useState(1);
  const [customText, setCustomText] = useState('');
  
  // 重點注意工具專用設定
  const [warningPreset, setWarningPreset] = useState('⚠️ 注意');
  const [customWarningText, setCustomWarningText] = useState('');
  
  // 標記紀錄
  const [shapes, setShapes] = useState([]);
  const [redoStack, setRedoStack] = useState([]);
  
  // 繪製狀態
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [currentPos, setCurrentPos] = useState({ x: 0, y: 0 });
  
  const [currentSrc, setCurrentSrc] = useState(imageSrc);
  const [imgElement, setImgElement] = useState(null);
  const [imgDimensions, setImgDimensions] = useState({ width: 0, height: 0 });
  const [isLoadingImage, setIsLoadingImage] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  // 1. 強健的圖片載入邏輯 (徹底解決跨域與瀏覽器 CORS 快取問題)
  useEffect(() => {
    if (!currentSrc) {
      setIsLoadingImage(false);
      setLoadError('尚未指定圖片路徑');
      return;
    }

    let isMounted = true;
    let blobUrl = null;

    setIsLoadingImage(true);
    setLoadError(null);

    const initImage = (srcToLoad) => {
      const img = new Image();
      // 如果不是同源 data: 或 blob:，加入 crossOrigin 宣告
      if (!srcToLoad.startsWith('data:') && !srcToLoad.startsWith('blob:')) {
        img.crossOrigin = 'anonymous';
      }

      img.onload = () => {
        if (!isMounted) return;
        setImgElement(img);
        setImgDimensions({ width: img.naturalWidth, height: img.naturalHeight });
        setIsLoadingImage(false);
        setLoadError(null);
      };

      img.onerror = () => {
        if (!isMounted) return;
        // 如果帶 crossOrigin 失敗，嘗試最後降級不帶 crossOrigin 載入
        if (img.crossOrigin) {
          const directImg = new Image();
          directImg.onload = () => {
            if (!isMounted) return;
            setImgElement(directImg);
            setImgDimensions({ width: directImg.naturalWidth, height: directImg.naturalHeight });
            setIsLoadingImage(false);
          };
          directImg.onerror = () => {
            if (!isMounted) return;
            setIsLoadingImage(false);
            setLoadError('無法讀取圖片，請點擊上方「更換圖片」或按 Ctrl+V 貼上截圖。');
          };
          directImg.src = srcToLoad;
        } else {
          setIsLoadingImage(false);
          setLoadError('圖片解析失敗，請點擊「更換圖片」選擇本地圖片。');
        }
      };

      img.src = srcToLoad;
    };

    // 若為 http 遠端或靜態路徑，先透過 fetch 轉為純本機 Blob 物件 URL，保證 Canvas 標記輸出不受 CORS 阻擋
    let targetSrc = currentSrc;
    if (targetSrc.includes('localhost:8000') || targetSrc.includes('127.0.0.1:8000')) {
      targetSrc = targetSrc.replace(/https?:\/\/(localhost|127\.0\.0\.1):8000/g, apiBase);
    }

    if (targetSrc.startsWith('http')) {
      const cacheBustUrl = targetSrc + (targetSrc.includes('?') ? '&' : '?') + 't=' + Date.now();
      fetch(cacheBustUrl)
        .then(res => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          return res.blob();
        })
        .then(blob => {
          if (!isMounted) return;
          blobUrl = URL.createObjectURL(blob);
          initImage(blobUrl);
        })
        .catch(err => {
          console.warn('Fetch blob failed, fallback to direct img:', err);
          initImage(targetSrc);
        });
    } else {
      initImage(targetSrc);
    }

    return () => {
      isMounted = false;
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [currentSrc]);

  // 支援在彈窗內直接按 Ctrl+V 貼上任何新截圖
  useEffect(() => {
    const handlePaste = (e) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
          const file = items[i].getAsFile();
          if (file) {
            const reader = new FileReader();
            reader.onload = (evt) => {
              if (evt.target?.result) {
                setCurrentSrc(evt.target.result);
                setShapes([]); // 清空前一張標記
                setRedoStack([]);
                setBadgeCounter(1);
              }
            };
            reader.readAsDataURL(file);
            break;
          }
        }
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, []);

  // 本機更換圖片選擇
  const handleLocalFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      if (evt.target?.result) {
        setCurrentSrc(evt.target.result);
        setShapes([]);
        setRedoStack([]);
        setBadgeCounter(1);
      }
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  // 取得代號文字
  const getBadgeLabel = (count, type) => {
    if (type === 'circle_num') {
      const circled = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', 
                       '⑪', '⑫', '⑬', '⑭', '⑮', '⑯', '⑰', '⑱', '⑲', '⑳'];
      if (count >= 1 && count <= 20) return circled[count - 1];
      return `(${count})`;
    }
    if (type === 'alpha') {
      return String.fromCharCode(64 + ((count - 1) % 26) + 1);
    }
    return String(count);
  };

  // 2. 核心繪製畫布函數
  const drawCanvas = (previewShape = null) => {
    const canvas = canvasRef.current;
    if (!canvas || !imgElement) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 清空並畫上底圖
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(imgElement, 0, 0, canvas.width, canvas.height);

    // 繪製所有已確定的形狀
    const allShapes = previewShape ? [...shapes, previewShape] : shapes;

    allShapes.forEach(shape => {
      ctx.save();
      if (shape.type === 'rect') {
        ctx.strokeStyle = shape.color;
        ctx.lineWidth = shape.strokeWidth;
        ctx.strokeRect(shape.x, shape.y, shape.w, shape.h);
        
        // 淡淡的半透明遮罩襯托
        ctx.fillStyle = shape.color + '22';
        ctx.fillRect(shape.x, shape.y, shape.w, shape.h);
      } 
      else if (shape.type === 'badge') {
        const radius = Math.max(16, shape.size || 20);
        
        // 陰影
        ctx.shadowColor = 'rgba(0,0,0,0.4)';
        ctx.shadowBlur = 6;
        ctx.shadowOffsetX = 1;
        ctx.shadowOffsetY = 2;

        // 實心底圓
        ctx.beginPath();
        ctx.arc(shape.x, shape.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = shape.color;
        ctx.fill();

        // 圓圈白邊
        ctx.shadowColor = 'transparent';
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = '#ffffff';
        ctx.stroke();

        // 序號/文字
        ctx.fillStyle = '#ffffff';
        ctx.font = `bold ${Math.round(radius * 1.15)}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(shape.label, shape.x, shape.y + 1);
      } 
      else if (shape.type === 'text') {
        const fontSize = shape.fontSize || 20;
        ctx.font = `bold ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
        const textMetrics = ctx.measureText(shape.text);
        const textW = textMetrics.width;
        const padX = 10;
        const padY = 6;
        const boxW = textW + padX * 2;
        const boxH = fontSize + padY * 2;
        const boxX = shape.x;
        const boxY = shape.y - fontSize - padY;

        // 圓角背景氣泡
        ctx.shadowColor = 'rgba(0,0,0,0.3)';
        ctx.shadowBlur = 4;
        ctx.fillStyle = 'rgba(17, 24, 39, 0.88)'; // 深灰近黑高對比底色
        roundRect(ctx, boxX, boxY, boxW, boxH, 6);
        ctx.fill();

        // 外框線
        ctx.shadowColor = 'transparent';
        ctx.lineWidth = 2;
        ctx.strokeStyle = shape.color;
        roundRect(ctx, boxX, boxY, boxW, boxH, 6);
        ctx.stroke();

        // 文字
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'alphabetic';
        ctx.fillText(shape.text, boxX + padX, shape.y - 2);
      } 
      else if (shape.type === 'warning') {
        const fontSize = Math.max(16, Math.round(shape.size || 20));
        ctx.font = `bold ${fontSize}px "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif`;
        const textMetrics = ctx.measureText(shape.text);
        const padX = 12;
        const padY = 6;
        const boxW = textMetrics.width + padX * 2;
        const boxH = fontSize + padY * 2;
        const boxX = shape.x;
        const boxY = shape.y - fontSize - padY;

        // 立體陰影
        ctx.shadowColor = 'rgba(0,0,0,0.35)';
        ctx.shadowBlur = 6;
        ctx.shadowOffsetX = 1;
        ctx.shadowOffsetY = 2;

        // 圓角背景氣泡
        ctx.fillStyle = shape.bgColor || '#fef08a';
        roundRect(ctx, boxX, boxY, boxW, boxH, 8);
        ctx.fill();

        // 外框線
        ctx.shadowColor = 'transparent';
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = shape.borderColor || '#ca8a04';
        roundRect(ctx, boxX, boxY, boxW, boxH, 8);
        ctx.stroke();

        // 文字與符號
        ctx.fillStyle = shape.textColor || '#854d0e';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'alphabetic';
        ctx.fillText(shape.text, boxX + padX, shape.y - 2);
      }
      else if (shape.type === 'arrow') {
        ctx.strokeStyle = shape.color;
        ctx.fillStyle = shape.color;
        ctx.lineWidth = shape.strokeWidth;
        ctx.lineCap = 'round';

        // 繪製主直線
        ctx.beginPath();
        ctx.moveTo(shape.x1, shape.y1);
        ctx.lineTo(shape.x2, shape.y2);
        ctx.stroke();

        // 繪製箭頭頭部
        const angle = Math.atan2(shape.y2 - shape.y1, shape.x2 - shape.x1);
        const headLen = Math.max(14, shape.strokeWidth * 3.5);
        ctx.beginPath();
        ctx.moveTo(shape.x2, shape.y2);
        ctx.lineTo(
          shape.x2 - headLen * Math.cos(angle - Math.PI / 6),
          shape.y2 - headLen * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          shape.x2 - headLen * Math.cos(angle + Math.PI / 6),
          shape.y2 - headLen * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fill();
      }
      ctx.restore();
    });
  };

  // 繪製圓角矩形輔助函數
  const roundRect = (ctx, x, y, width, height, radius) => {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
  };

  // 當底圖或標記陣列改變時重繪
  useEffect(() => {
    if (imgElement) {
      const canvas = canvasRef.current;
      if (canvas) {
        canvas.width = imgDimensions.width;
        canvas.height = imgDimensions.height;
        drawCanvas();
      }
    }
  }, [imgElement, imgDimensions, shapes]);

  // 計算滑鼠在 Canvas 原圖解析度上的實際座標
  const getCanvasCoordinates = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: Math.round((e.clientX - rect.left) * scaleX),
      y: Math.round((e.clientY - rect.top) * scaleY)
    };
  };

  // 滑鼠按下
  const handleMouseDown = (e) => {
    if (!imgElement) return;
    const pos = getCanvasCoordinates(e);
    setStartPos(pos);
    setCurrentPos(pos);
    setIsDrawing(true);

    if (activeTool === 'badge') {
      // 點擊即放代號序號
      const label = getBadgeLabel(badgeCounter, badgeType);
      const newShape = {
        type: 'badge',
        x: pos.x,
        y: pos.y,
        label: label,
        color: color,
        size: Math.max(18, Math.round(strokeWidth * 4.5))
      };
      setShapes(prev => [...prev, newShape]);
      setBadgeCounter(prev => prev + 1);
      setRedoStack([]);
      setIsDrawing(false);
    } 
    else if (activeTool === 'warning') {
      // 點擊即放重點注意標記
      const preset = WARNING_PRESETS.find(p => p.label === warningPreset) || WARNING_PRESETS[0];
      const textToUse = customWarningText.trim() || preset.label;
      const newShape = {
        type: 'warning',
        x: pos.x,
        y: pos.y,
        text: textToUse,
        bgColor: preset.bg,
        borderColor: preset.border,
        textColor: preset.text,
        size: Math.max(18, Math.round(strokeWidth * 4.5))
      };
      setShapes(prev => [...prev, newShape]);
      setRedoStack([]);
      setIsDrawing(false);
    }
    else if (activeTool === 'text') {
      // 點擊彈出文字輸入
      const defaultTxt = customText.trim() || prompt("請輸入要加在圖片上的標註文字：", "請點擊此處");
      if (defaultTxt) {
        const newShape = {
          type: 'text',
          x: pos.x,
          y: pos.y,
          text: defaultTxt,
          color: color,
          fontSize: Math.max(18, Math.round(strokeWidth * 4.5))
        };
        setShapes(prev => [...prev, newShape]);
        setRedoStack([]);
      }
      setIsDrawing(false);
    }
  };

  // 滑鼠移動 (拖曳加框或箭頭)
  const handleMouseMove = (e) => {
    if (!isDrawing || !imgElement) return;
    const pos = getCanvasCoordinates(e);
    setCurrentPos(pos);

    if (activeTool === 'rect') {
      const previewRect = {
        type: 'rect',
        x: Math.min(startPos.x, pos.x),
        y: Math.min(startPos.y, pos.y),
        w: Math.abs(pos.x - startPos.x),
        h: Math.abs(pos.y - startPos.y),
        color: color,
        strokeWidth: strokeWidth
      };
      drawCanvas(previewRect);
    } 
    else if (activeTool === 'arrow') {
      const previewArrow = {
        type: 'arrow',
        x1: startPos.x,
        y1: startPos.y,
        x2: pos.x,
        y2: pos.y,
        color: color,
        strokeWidth: strokeWidth
      };
      drawCanvas(previewArrow);
    }
  };

  // 滑鼠放開 (確認形狀)
  const handleMouseUp = () => {
    if (!isDrawing || !imgElement) return;
    setIsDrawing(false);

    if (activeTool === 'rect') {
      const w = Math.abs(currentPos.x - startPos.x);
      const h = Math.abs(currentPos.y - startPos.y);
      if (w > 5 && h > 5) {
        const newShape = {
          type: 'rect',
          x: Math.min(startPos.x, currentPos.x),
          y: Math.min(startPos.y, currentPos.y),
          w: w,
          h: h,
          color: color,
          strokeWidth: strokeWidth
        };
        setShapes(prev => [...prev, newShape]);
        setRedoStack([]);
      }
    } 
    else if (activeTool === 'arrow') {
      const dist = Math.hypot(currentPos.x - startPos.x, currentPos.y - startPos.y);
      if (dist > 10) {
        const newShape = {
          type: 'arrow',
          x1: startPos.x,
          y1: startPos.y,
          x2: currentPos.x,
          y2: currentPos.y,
          color: color,
          strokeWidth: strokeWidth
        };
        setShapes(prev => [...prev, newShape]);
        setRedoStack([]);
      }
    }
    drawCanvas();
  };

  // 復原 (Undo)
  const handleUndo = () => {
    if (shapes.length === 0) return;
    const last = shapes[shapes.length - 1];
    setRedoStack(prev => [...prev, last]);
    setShapes(prev => prev.slice(0, -1));
    if (last.type === 'badge' && badgeCounter > 1) {
      setBadgeCounter(prev => prev - 1);
    }
  };

  // 重做 (Redo)
  const handleRedo = () => {
    if (redoStack.length === 0) return;
    const next = redoStack[redoStack.length - 1];
    setRedoStack(prev => prev.slice(0, -1));
    setShapes(prev => [...prev, next]);
    if (next.type === 'badge') {
      setBadgeCounter(prev => prev + 1);
    }
  };

  // 清除全部
  const handleClear = () => {
    if (shapes.length === 0) return;
    if (window.confirm("確定要清除目前圖片上的所有標記嗎？")) {
      setShapes([]);
      setRedoStack([]);
      setBadgeCounter(1);
    }
  };

  // 本機下載
  const handleDownload = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = `annotated_${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  // 儲存並上傳後端
  const handleSaveAndApply = async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    setIsSaving(true);

    try {
      // 轉為 Blob
      canvas.toBlob(async (blob) => {
        if (!blob) {
          alert("圖片轉換失敗");
          setIsSaving(false);
          return;
        }

        const formData = new FormData();
        const filename = `annotated_${Date.now()}.png`;
        formData.append('file', blob, filename);

        const res = await fetch(`${apiBase}/upload_image`, {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        
        if (data.url) {
          onSave(data.url);
        } else {
          alert('上傳標註圖片失敗');
        }
        setIsSaving(false);
      }, 'image/png');
    } catch (err) {
      console.error(err);
      alert('儲存發生錯誤: ' + err.message);
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-white w-full max-w-6xl h-[92vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-gray-200">
        
        {/* 隱藏的本地圖片上傳 input */}
        <input 
          type="file"
          ref={fileInputRef}
          onChange={handleLocalFileChange}
          accept="image/*"
          className="hidden"
        />

        {/* 頂部標題列 */}
        <div className="px-6 py-3.5 bg-gray-900 text-white flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 bg-blue-500 rounded-lg text-white">
              <Square className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base leading-tight">圖片加框與代號標註工具</h3>
              <p className="text-xs text-gray-400">
                支援加紅框、步驟代號(①②③)、說明文字與指向箭頭（可直接按 Ctrl+V 貼上截圖）
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 border border-gray-700 transition-colors"
              title="更換或重新選擇本機圖片"
            >
              <FolderOpen className="w-3.5 h-3.5 text-blue-400" />
              <span>更換圖片</span>
            </button>
            <button 
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 工具列 */}
        <div className="px-6 py-2.5 bg-gray-50 border-b border-gray-200 flex flex-wrap items-center justify-between gap-3 shrink-0">
          
          {/* 工具按鈕組 */}
          <div className="flex items-center gap-1 bg-white p-1 rounded-xl border border-gray-200 shadow-xs">
            <button
              onClick={() => setActiveTool('rect')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTool === 'rect' 
                  ? 'bg-blue-600 text-white shadow-xs' 
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              title="拖曳繪製加框"
            >
              <Square className="w-4 h-4" />
              <span>加框</span>
            </button>

            <button
              onClick={() => setActiveTool('badge')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTool === 'badge' 
                  ? 'bg-blue-600 text-white shadow-xs' 
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              title="點擊圖片放置步驟代號序號"
            >
              <Hash className="w-4 h-4" />
              <span>加代號/步驟 ({getBadgeLabel(badgeCounter, badgeType)})</span>
            </button>

            <button
              onClick={() => setActiveTool('warning')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTool === 'warning' 
                  ? 'bg-amber-500 text-white shadow-xs' 
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              title="點擊圖片放置重點注意標記 (⚠️ 注意、❗ 重要、★ 必看、⛔ 禁止)"
            >
              <AlertTriangle className="w-4 h-4 text-amber-300" />
              <span>重點注意 ({customWarningText ? customWarningText.slice(0, 4) + '..' : warningPreset})</span>
            </button>

            <button
              onClick={() => setActiveTool('text')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTool === 'text' 
                  ? 'bg-blue-600 text-white shadow-xs' 
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              title="點擊圖片放置說明文字標籤"
            >
              <Type className="w-4 h-4" />
              <span>加文字標註</span>
            </button>

            <button
              onClick={() => setActiveTool('arrow')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTool === 'arrow' 
                  ? 'bg-blue-600 text-white shadow-xs' 
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              title="拖曳繪製指示箭頭"
            >
              <ArrowUpRight className="w-4 h-4" />
              <span>加箭頭</span>
            </button>
          </div>

          {/* 序號樣式選擇 */}
          {activeTool === 'badge' && (
            <div className="flex items-center gap-1 bg-white px-2 py-1 rounded-xl border border-gray-200 text-xs">
              <span className="text-gray-500 font-medium">代號格式:</span>
              <button 
                onClick={() => setBadgeType('circle_num')}
                className={`px-2 py-0.5 rounded font-bold cursor-pointer ${badgeType === 'circle_num' ? 'bg-blue-100 text-blue-700' : 'text-gray-600'}`}
              >
                ① ② ③
              </button>
              <button 
                onClick={() => setBadgeType('num')}
                className={`px-2 py-0.5 rounded font-bold cursor-pointer ${badgeType === 'num' ? 'bg-blue-100 text-blue-700' : 'text-gray-600'}`}
              >
                1 2 3
              </button>
              <button 
                onClick={() => setBadgeType('alpha')}
                className={`px-2 py-0.5 rounded font-bold cursor-pointer ${badgeType === 'alpha' ? 'bg-blue-100 text-blue-700' : 'text-gray-600'}`}
              >
                A B C
              </button>
              <button 
                onClick={() => setBadgeCounter(1)}
                className="ml-1 p-1 text-gray-400 hover:text-blue-600 hover:bg-gray-100 rounded cursor-pointer"
                title="重新從 1 開始編號"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* 重點注意樣式選擇 */}
          {activeTool === 'warning' && (
            <div className="flex items-center gap-1 bg-white px-2 py-1 rounded-xl border border-gray-200 text-xs">
              <span className="text-gray-500 font-medium">注意標記:</span>
              {WARNING_PRESETS.map(p => (
                <button
                  key={p.label}
                  onClick={() => {
                    setWarningPreset(p.label);
                    setCustomWarningText('');
                  }}
                  className={`px-2 py-0.5 rounded font-bold cursor-pointer transition-all ${
                    warningPreset === p.label && !customWarningText
                      ? 'ring-2 ring-amber-400 font-extrabold shadow-2xs' 
                      : 'hover:opacity-80'
                  }`}
                  style={{ backgroundColor: p.bg, color: p.text, border: `1px solid ${p.border}` }}
                >
                  {p.label}
                </button>
              ))}
              <button
                onClick={() => {
                  const val = prompt("請輸入自訂重點注意文字 (例如：⚠️ 務必核對料號)：", customWarningText || "⚠️ 注意事項");
                  if (val !== null) {
                    setCustomWarningText(val.trim());
                  }
                }}
                className={`px-2 py-0.5 rounded font-bold cursor-pointer text-gray-700 bg-gray-100 hover:bg-gray-200 ${
                  customWarningText ? 'ring-2 ring-amber-400 bg-amber-100 text-amber-800' : ''
                }`}
                title="自訂重點文字"
              >
                {customWarningText ? `✏️ ${customWarningText}` : '✏️ 自訂'}
              </button>
            </div>
          )}

          {/* 顏色調色盤 */}
          <div className="flex items-center gap-1.5 bg-white px-3 py-1.5 rounded-xl border border-gray-200">
            <Palette className="w-3.5 h-3.5 text-gray-400 mr-0.5" />
            {COLORS.map(c => (
              <button
                key={c.value}
                onClick={() => setColor(c.value)}
                className={`w-5 h-5 rounded-full border transition-transform cursor-pointer ${
                  color === c.value ? 'scale-125 ring-2 ring-blue-500 ring-offset-1 z-10' : 'hover:scale-110 border-gray-300'
                }`}
                style={{ backgroundColor: c.value }}
                title={c.name}
              />
            ))}
          </div>

          {/* 線條粗細 */}
          <div className="flex items-center gap-1 bg-white px-2.5 py-1 rounded-xl border border-gray-200 text-xs">
            <span className="text-gray-500 font-medium">粗細:</span>
            {[2, 4, 6].map(w => (
              <button
                key={w}
                onClick={() => setStrokeWidth(w)}
                className={`px-2 py-1 rounded font-bold transition-colors cursor-pointer ${
                  strokeWidth === w ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {w === 2 ? '細' : w === 4 ? '中' : '粗'}
              </button>
            ))}
          </div>

          {/* 歷史操作 */}
          <div className="flex items-center gap-1 bg-white p-1 rounded-xl border border-gray-200">
            <button
              onClick={handleUndo}
              disabled={shapes.length === 0}
              className="p-1.5 rounded-lg text-gray-600 hover:bg-gray-100 disabled:opacity-30 disabled:hover:bg-transparent cursor-pointer"
              title="復原 (Undo)"
            >
              <Undo2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleRedo}
              disabled={redoStack.length === 0}
              className="p-1.5 rounded-lg text-gray-600 hover:bg-gray-100 disabled:opacity-30 disabled:hover:bg-transparent cursor-pointer"
              title="重做 (Redo)"
            >
              <Redo2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleClear}
              disabled={shapes.length === 0}
              className="p-1.5 rounded-lg text-red-500 hover:bg-red-50 disabled:opacity-30 disabled:hover:bg-transparent cursor-pointer"
              title="清除所有標記"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>

        </div>

        {/* 畫布工作區 */}
        <div 
          ref={containerRef}
          className="flex-1 bg-gray-800 overflow-auto p-4 flex items-center justify-center relative select-none"
          style={{
            backgroundImage: `radial-gradient(circle, #374151 1px, transparent 1px)`,
            backgroundSize: '20px 20px'
          }}
        >
          {isLoadingImage ? (
            <div className="text-gray-300 flex flex-col items-center gap-3 bg-gray-900/60 p-6 rounded-2xl backdrop-blur-xs border border-gray-700 shadow-xl">
              <div className="animate-spin rounded-full h-10 w-10 border-3 border-blue-500 border-t-transparent"></div>
              <span className="text-sm font-medium">正在解析載入圖片中...</span>
            </div>
          ) : loadError ? (
            <div className="text-gray-200 flex flex-col items-center gap-4 bg-gray-900/80 p-8 rounded-2xl max-w-md text-center border border-red-500/40 shadow-2xl">
              <div className="p-3 bg-red-500/20 text-red-400 rounded-full">
                <AlertCircle className="w-8 h-8" />
              </div>
              <div>
                <h4 className="font-bold text-base text-red-300 mb-1">載入圖片發生狀況</h4>
                <p className="text-xs text-gray-400 leading-relaxed">{loadError}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-md flex items-center gap-1.5 cursor-pointer"
                >
                  <FolderOpen className="w-4 h-4" />
                  <span>從電腦選擇這張圖片</span>
                </button>
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-xl text-xs font-medium transition-colors"
                >
                  關閉
                </button>
              </div>
            </div>
          ) : imgElement ? (
            <div className="relative inline-block shadow-2xl rounded-sm overflow-hidden bg-white">
              <canvas
                ref={canvasRef}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                className="max-w-full max-h-[64vh] object-contain block cursor-crosshair"
              />
            </div>
          ) : null}
        </div>

        {/* 底部功能列 */}
        <div className="px-6 py-3 bg-white border-t border-gray-200 flex items-center justify-between shrink-0">
          <div className="text-xs text-gray-500 flex items-center gap-3">
            <span>原圖尺寸：{imgDimensions.width} × {imgDimensions.height} px</span>
            <span>已加標記：{shapes.length} 個</span>
            <span className="text-blue-600 bg-blue-50 px-2 py-0.5 rounded font-medium">
              提示：{activeTool === 'rect' ? '按住滑鼠左鍵拖曳畫框' : activeTool === 'badge' ? '點擊圖片任一處即可放上步驟代號' : activeTool === 'warning' ? '點擊圖片任一處即可放上醒目的重點注意標記' : activeTool === 'arrow' ? '按住滑鼠拖曳拉出箭頭' : '點擊圖片任一處即可放上文字說明'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleDownload}
              disabled={!imgElement}
              className="flex items-center gap-1.5 px-4 py-2 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 text-sm font-medium transition-colors disabled:opacity-40 cursor-pointer"
            >
              <Download className="w-4 h-4" />
              <span>下載標註圖</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-xl text-sm font-medium transition-colors cursor-pointer"
            >
              取消
            </button>
            <button
              onClick={handleSaveAndApply}
              disabled={isSaving || !imgElement}
              className="flex items-center gap-1.5 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-md text-sm font-bold transition-all disabled:opacity-50 cursor-pointer"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  <span>儲存中...</span>
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  <span>完成並更新圖片</span>
                </>
              )}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
