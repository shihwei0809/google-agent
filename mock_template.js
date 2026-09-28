const s = {
  productName: 'EBR-P1R',
  flowType: '進料',
  grade: '回收液',
  round: 1,
  barcode: 'ESPM411-20260927004, ESF',
  tankNo: 'TKC03',
  customer: 'KEK-0717(櫃:6108)',
  dept: '資材課',
  requester: 'C0704',
  createdAt: new Date().toISOString(),
  id: 'test'
};
const loggedInUser = null;

function getFlowTag(type) {
    if(!type) return '';
    const colorMap = { '出貨': '#3b82f6', '進料': '#10b981', '補料': '#f59e0b', '委託': '#8b5cf6' };
    const bg = colorMap[type] || '#64748b';
    return `<span style="font-size:0.75rem; color:white; background:${bg}; padding:2px 6px; border-radius:12px; font-weight:bold;">${type}</span>`;
}
function formatSimpleDate(dStr) { return dStr; }
function getWaitTimeBadge(dStr) { return dStr; }

const html = `<tr style="${(parseInt(s.round)||1) >= 2 ? 'background:#fff7ed;' : ''}">
        <td>
          <div style="display:flex; align-items:center; gap:4px; flex-wrap:wrap; margin-bottom:2px;">
            <b style="font-size:0.88rem; color:#0f172a;">${s.productName}</b>
            ${getFlowTag(s.flowType)}
            <span style="font-size:0.72rem; font-weight:bold; color:#1e40af; background:#eff6ff; padding:1px 4px; border-radius:3px;">${s.grade || '-'}</span>
            ${(parseInt(s.round)||1) >= 2 ? `<span style="font-size:0.72rem; font-weight:bold; color:#ea580c; background:#fed7aa; padding:1px 6px; border-radius:10px;">⚠️ 第${s.round}次送樣</span>` : ''}
          </div>
          <div style="font-size:0.75rem; color:#64748b; font-family:monospace; word-break:break-all;">單: <b>${s.barcode}</b></div>
        </td>
        <td>
          <div style="margin-bottom:2px;">
            <span style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:0.78rem;">${s.tankNo || '-'}</span>
          </div>
          <div style="font-size:0.76rem; color:#334155; word-break:break-all;">車: <b>${s.customer || '-'}</b></div>
        </td>
        <td>
          <div style="font-weight:600; color:#1e293b; font-size:0.8rem; margin-bottom:2px;">
            ${s.dept} ${s.requester ? `<span style="font-size:0.72rem; color:#64748b;">(${s.requester})</span>` : ''}
          </div>
          <div style="font-size:0.72rem; color:#64748b;">${formatSimpleDate(s.createdAt)}</div>
          <div style="margin-top:2px;">${getWaitTimeBadge(s.createdAt)}</div>
        </td>
        <td style="text-align:center;">
          <div style="display:flex; flex-direction:column; gap:4px; align-items:center;">
            <button class="btn-action btn-print" onclick="printLabelById('${s.id}')" style="width:100%; padding:4px 0; font-size:0.75rem; margin:0;">列印</button>
            ${loggedInUser ? `<button class="btn-action btn-judge" onclick="openJudge('${s.id}')" style="width:100%; padding:4px 0; font-size:0.75rem; margin:0;">判定</button>` : `<div style="text-align:center; color:#94a3b8; font-size:0.75rem; margin-top:8px; border: 1px dashed #cbd5e1; border-radius: 4px; padding: 2px;">登入後判定</div>`}
          </div>
        </td>
      </tr>`;
console.log("Success");
