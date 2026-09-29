// app.js - 核心業務邏輯與渲染引擎
const NODE_TEMPLATES = {
  distillation_tower: {
    width: 70, height: 210, title: 'Distillation Tower', tag: 'T-101',
    ports: [
      { x: 35, y: 0, name: 'Top Vapor' }, { x: 70, y: 45, name: 'Reflux In' },
      { x: 0, y: 105, name: 'Feed In' }, { x: 0, y: 170, name: 'Reboiler Return' },
      { x: 35, y: 210, name: 'Bottom Liquid' }, { x: 70, y: 155, name: 'Side Draw' }
    ],
    render: (n) => `
      <g>
        <rect x="0" y="0" width="70" height="210" rx="20" fill="#ffffff" stroke="#1e293b" stroke-width="2.5" />
        <line x1="8" y1="50" x2="62" y2="50" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3,3" />
        <line x1="8" y1="80" x2="62" y2="80" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3,3" />
        <line x1="8" y1="110" x2="62" y2="110" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3,3" />
        <line x1="8" y1="140" x2="62" y2="140" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3,3" />
        <line x1="8" y1="170" x2="62" y2="170" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3,3" />
        <path d="M 35 155 L 35 75" stroke="#f59e0b" stroke-width="2.5" marker-end="url(#arrow-vapor)" />
        <text x="35" y="170" font-size="11" font-weight="bold" fill="#d97706" text-anchor="middle">Vapor</text>
        <text x="35" y="100" font-size="11" font-weight="bold" fill="#1e293b" text-anchor="middle">${n.title}</text>
        <text x="35" y="116" font-size="10" fill="#64748b" text-anchor="middle">${n.tag || ''}</text>
      </g>
    `
  },
  // Add other templates as needed...
};

function initLibrary() {
    const libContainer = document.getElementById('library-container');
    libContainer.innerHTML = `<p class="text-xs text-slate-500">此處為動態載入的組件庫。您可以點擊以新增至畫布。</p>`;
    // Dynamically generating buttons for NODE_TEMPLATES would go here in a full implementation.
}

window.addEventListener('DOMContentLoaded', () => {
    initLibrary();
});
