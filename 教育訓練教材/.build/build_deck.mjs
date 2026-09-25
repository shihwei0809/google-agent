import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const { SKILL_DIR, TMP_DIR, WORKSPACE_DIR, FINAL_PPTX } = process.env;
const { resolvePresentationFont, finalizePresentation } = await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
await fs.mkdir(TMP_DIR,{recursive:true});
const font=resolvePresentationFont({fontFamily:'Microsoft JhengHei'});
const C={navy:'#12304A',teal:'#167D8D',gold:'#E9A23B',ink:'#263648',muted:'#617383',paper:'#F5F8FA',white:'#FFFFFF',line:'#D5E0E6',red:'#A9473D',green:'#39725B'};
const ppt=Presentation.create({slideSize:{width:1280,height:720}});
function box(slide,x,y,w,h,text,size=24,color=C.ink,bold=false,opts={}){
  const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:opts.fill??'none',line:{fill:'none',width:0}});
  s.text=text;
  s.text.style={typeface:font,fontSize:size,color,bold,verticalAlignment:'middle',wrap:true,autoFit:'shrinkText',...opts.style};
  return s;
}
function base(kicker,title,sub=''){
  const s=ppt.slides.add(); s.background.fill=C.paper;
  box(s,64,35,1130,24,kicker.toUpperCase(),15,C.teal,true);
  box(s,64,70,1140,64,title,39,C.navy,true);
  if(sub) box(s,66,139,1140,42,sub,19,C.muted,false);
  box(s,64,677,1110,20,'AI 教育訓練平台｜導入前後比較',13,C.muted,false);
  return s;
}
function txt(slide,x,y,w,h,text,size=22,color=C.ink,bold=false,opts={}){return box(slide,x,y,w,h,text,size,color,bold,opts)}

// 1 Cover
{
 const s=ppt.slides.add(); s.background.fill=C.navy;
 box(s,84,100,1050,32,'教育訓練平台導入評估',18,'#78D1D0',true);
 box(s,84,170,1080,145,'導入 AI 教育訓練平台\n前後差異與管理重點',54,C.white,true);
 box(s,88,365,970,62,'以教材閱覽、AI 助教與教材管理功能為基礎',25,'#D8E5EB',false);
 box(s,88,592,990,45,'系統現況分析｜未包含量化成效數據',18,'#B9C9D2',false);
}
// 2 Before
{
 const s=base('01｜導入前','導入前：訓練內容分散於教材與人工說明','以下描述為依既有教材情境所作的流程推估，實際作法依各單位而異。');
 txt(s,78,220,510,50,'學習者常見流程',27,C.navy,true);
 txt(s,100,285,490,240,'• 找到正確教材與版本\n• 自行閱讀檔案或簡報\n• 遇到疑問時詢問講師或同事\n• 依既有方式記錄學習與追蹤',23,C.ink,false);
 txt(s,680,220,510,50,'可能的管理負擔',27,C.navy,true);
 txt(s,700,285,480,250,'教材入口與版本較分散\n重複問題仰賴人員逐一回覆\n教材更新後需同步通知與維護\n學習紀錄仍由既有流程管理',22,C.ink,false);
 txt(s,78,570,1110,48,'優勢：原有教材與管理流程熟悉，可沿用既定制度。',21,C.green,true);
}
// 3 After
{
 const s=base('02｜導入後','導入後：同一介面串起教材閱讀與即時提問','目前程式可確認的功能：教材列表、閱讀、AI 對話、管理者教材維護。');
 txt(s,82,220,495,48,'學習者使用流程',27,C.navy,true);
 txt(s,105,280,500,235,'選取教材並在線閱讀\n針對內容輸入問題\n查看 AI 回答並回到原教材核對',23,C.ink,false);
 txt(s,680,220,495,48,'管理者維護流程',27,C.navy,true);
 txt(s,700,280,490,235,'登入管理模式\n上傳或編修教材並儲存\n抽查轉換結果與圖片顯示',23,C.ink,false);
 txt(s,82,565,1110,60,'預期價值：降低找教材與重複解說的摩擦；效果需透過實際使用數據驗證。',21,C.teal,true);
}
// 4 Compare table
{
 const s=base('03｜差異比較','前後差異聚焦在教材取得與答疑方式');
 const y=210, left=82, colW=355, mid=445, right=840;
 txt(s,left,y,colW,45,'面向',20,C.white,true,{fill:C.navy});
 txt(s,mid,y,350,45,'使用平台前',20,C.white,true,{fill:C.navy});
 txt(s,right,y,355,45,'使用平台後',20,C.white,true,{fill:C.teal});
 const rows=[
  ['教材入口','依原有檔案或流程尋找','教材集中列於平台清單'],
  ['內容閱讀','依檔案格式開啟閱讀','可於介面直接閱讀教材'],
  ['即時答疑','詢問講師、同事或查文件','可在教材旁向 AI 助教提問'],
  ['教材更新','依原有管理方式通知與更版','管理者可上傳、編修與儲存'],
  ['訓練紀錄','依正式制度與工具保存','平台未見簽到、時數或資格管理']
 ];
 rows.forEach((r,i)=>{let yy=260+i*68;let fill=i%2?'#EAF0F3':C.white;txt(s,left,yy,colW,56,r[0],19,C.navy,true,{fill});txt(s,mid,yy,350,56,r[1],17,C.ink,false,{fill});txt(s,right,yy,355,56,r[2],17,C.ink,false,{fill});});
}
// 5 Pros / cons
{
 const s=base('04｜優勢與限制','便利性提升，治理責任仍由組織承接');
 txt(s,95,210,495,45,'可期待的優勢',27,C.green,true);
 txt(s,105,274,505,300,'教材集中瀏覽，減少切換檔案\n問答可在學習當下進行\n常見教材可由管理者集中更新\nPDF、Office 文件及影片可進入解析流程',21,C.ink,false);
 txt(s,680,210,510,45,'導入後仍須管理的風險',27,C.red,true);
 txt(s,690,274,500,305,'AI 回答可能不完整，需回核正式教材\n需維護 API 金鑰、網路與本機服務\n固定預設管理密碼需評估存取控制\n平台未取代簽到、測驗、時數與資格紀錄',21,C.ink,false);
}
// 6 Operating workflow
{
 const s=base('05｜操作概覽','兩種角色，共用同一套教材內容');
 txt(s,90,215,1080,45,'學習者',26,C.navy,true);
 txt(s,100,278,1080,85,'開啟平台      選取教材      閱讀內容      提出問題      核對答案',23,C.ink,false,{fill:C.white});
 txt(s,90,420,1080,45,'教材管理者',26,C.navy,true);
 txt(s,100,483,1080,90,'登入管理模式      上傳或編修      儲存教材      抽查內容與圖片',23,C.ink,false,{fill:C.white});
 txt(s,93,602,1100,40,'管理員模式目前使用程式內固定密碼；正式部署前宜完成權限控管評估。',18,C.red,true);
}
// 7 Manual highlights
{
 const s=base('06｜操作重點','上線前先完成環境設定，再建立可用教材');
 txt(s,88,212,535,42,'啟動條件',25,C.navy,true);
 txt(s,100,268,520,150,'Windows 啟動腳本\n後端與前端服務\n有效的 Gemini API 金鑰與網路',21,C.ink,false);
 txt(s,670,212,535,42,'教材管理要點',25,C.navy,true);
 txt(s,680,268,520,180,'上傳後抽查轉換內容\n編修後確認儲存成功\n刪除前核對檔名並依規範備份',21,C.ink,false);
 txt(s,90,520,1090,70,'支援格式包含 MD、TXT、PDF、DOCX、XLSX、PPTX 與 MP4/MOV/AVI/WEBM。舊版 DOC 需先轉為 DOCX。',19,C.teal,true);
}
// 8 Measurement / close
{
 const s=base('07｜成效驗證','先建立基準，再用資料判斷改善幅度');
 txt(s,92,218,1065,54,'目前沒有可核實的導入前後量測結果。建議試行期間追蹤：',25,C.navy,true);
 txt(s,112,300,1020,200,'教材查找與答疑所需時間\n教材使用次數與常見問題\nAI 回答需修正的比例\n學習者回饋與教材更新週期',23,C.ink,false);
 txt(s,95,560,1080,54,'判讀原則：比較同一課程、相近人員與相同期間，避免把推估效益當成實績。',19,C.teal,true);
}

const workspaceDir=WORKSPACE_DIR;
const stagingDir=path.join(workspaceDir,'.codex-finalizer');
await fs.mkdir(stagingDir,{recursive:true});
await fs.mkdir(path.dirname(FINAL_PPTX),{recursive:true});
const candidatePath=path.join(stagingDir,'candidate-training-comparison.pptx');
await (await PresentationFile.exportPptx(ppt)).save(candidatePath);
const report=await finalizePresentation({
  explicitTotalSlideCount:8,
  workspaceDir,candidatePath,finalPath:FINAL_PPTX,
  pythonExecutable:process.env.RUNTIME_PYTHON,
  integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000'],
  requiredNativeTableOwnerSlides:[],
  fontPolicy:{basis:'design',families:[font],scriptFonts:{ea:'Microsoft JhengHei'}},
  verifyArtifactToolImport:true,
  receiptPath:path.join(stagingDir,'training-comparison.validation.json')
});
console.log(JSON.stringify(report,null,2));
