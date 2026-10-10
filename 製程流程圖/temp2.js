
    // --- 應用程式狀態 ---
    const state = {
      nodes: [],
      wires: [],
      selectedNodeId: null,
      selectedWireId: null,
      zoom: 1,
      pan: { x: 0, y: 0 },
      isPanning: false,
      panStart: { x: 0, y: 0 },
      draggingNodeId: null,
      dragOffset: { x: 0, y: 0 },
      connectingStart: null,
      globalAnim: true,
      animSpeed: 1,
      history: []
    };

    const SVG_NS = "http://www.w3.org/2000/svg";
    const canvasContainer = document.getElementById('canvas-container');
    const svgCanvas = document.getElementById('svg-canvas');
    const viewportGroup = document.getElementById('viewport-group');
    const nodesLayer = document.getElementById('nodes-layer');
    const wiresLayer = document.getElementById('wires-layer');
    const portsLayer = document.getElementById('ports-layer');
    const tempWire = document.getElementById('temp-wire');
    const connHint = document.getElementById('conn-hint');

    // --- 設備與元件模板定義 ---
        const NODE_TEMPLATES = {
      custom_block: {
        width: 100, height: 100,
        title: '自訂設備',
        tag: 'EQ-001',
        bgColor: '#ffffff',
        ports: [
          { x: 50, y: 0, name: 'Top' },
          { x: 100, y: 50, name: 'Right' },
          { x: 50, y: 100, name: 'Bottom' },
          { x: 0, y: 50, name: 'Left' },
          { x: 25, y: 0, name: 'Top-L' },
          { x: 75, y: 0, name: 'Top-R' },
          { x: 100, y: 25, name: 'Right-T' },
          { x: 100, y: 75, name: 'Right-B' },
          { x: 0, y: 25, name: 'Left-T' },
          { x: 0, y: 75, name: 'Left-B' },
          { x: 25, y: 100, name: 'Bottom-L' },
          { x: 75, y: 100, name: 'Bottom-R' }
        ],
        render: (n) => {
          const bg = n.bgColor || '#ffffff';
          const img = n.imageUrl ? `<image href="${n.imageUrl}" x="5" y="5" width="90" height="90" preserveAspectRatio="xMidYMid meet" />` : '';
          const textY = n.imageUrl ? 115 : 55;
          return `<g>
            <rect x="0" y="0" width="100" height="100" rx="8" fill="${bg}" stroke="#1e293b" stroke-width="2.5" />
            ${img}
            <text x="50" y="${textY}" font-size="12" font-weight="bold" fill="#1e293b" text-anchor="middle">${n.title}</text>
            <text x="50" y="${textY + 16}" font-size="10" fill="#64748b" text-anchor="middle">${n.tag || ''}</text>
          </g>`;
        }
      },
      distillation_tower: {
        width: 70, height: 210,
        title: 'Distillation Tower',
        tag: 'T-101',
        ports: [
          { x: 35, y: 0, name: 'Top Vapor' },
          { x: 70, y: 45, name: 'Reflux In' },
          { x: 0, y: 105, name: 'Feed In' },
          { x: 0, y: 170, name: 'Reboiler Return' },
          { x: 35, y: 210, name: 'Bottom Liquid' },
          { x: 70, y: 155, name: 'Side Draw' }
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
      reboiler: {
        width: 80, height: 60,
        title: 'Reboiler',
        tag: 'E-101',
        ports: [
          { x: 15, y: 0, name: 'Liquid In' },
          { x: 15, y: 60, name: 'Vapor Out' },
          { x: 0, y: 30, name: 'Steam In' },
          { x: 80, y: 30, name: 'Condensate' }
        ],
        render: (n) => `
          <g>
            <rect x="0" y="8" width="80" height="44" rx="3" fill="#ffffff" stroke="#1e293b" stroke-width="2.2" />
            <line x1="16" y1="2" x2="16" y2="58" stroke="#1e293b" stroke-width="2.5" />
            <line x1="64" y1="2" x2="64" y2="58" stroke="#1e293b" stroke-width="2.5" />
            <text x="40" y="34" font-size="11" font-weight="bold" fill="#1e293b" text-anchor="middle">${n.title}</text>
          </g>
        `
      },
      condenser: {
        width: 60, height: 50,
        title: 'Condenser',
        tag: 'E-102',
        ports: [
          { x: 0, y: 25, name: 'Vapor In' },
          { x: 60, y: 25, name: 'Liquid Out' },
          { x: 30, y: 0, name: 'CW In' },
          { x: 30, y: 50, name: 'CW Out' }
        ],
        render: (n) => `
          <g>
            <circle cx="30" cy="25" r="20" fill="#ffffff" stroke="#1e293b" stroke-width="2.2" />
            <line x1="12" y1="41" x2="48" y2="9" stroke="#1e293b" stroke-width="2" />
            <text x="30" y="58" font-size="10" font-weight="bold" fill="#1e293b" text-anchor="middle">${n.title}</text>
          </g>
        `
      },
      decanter: {
        width: 90, height: 40,
        title: 'Decanter',
        tag: 'V-101',
        ports: [
          { x: 0, y: 20, name: 'Mix In' },
          { x: 45, y: 40, name: 'Heavy Out' },
          { x: 90, y: 20, name: 'Light Out' },
          { x: 45, y: 0, name: 'Vent' }
        ],
        render: (n) => `
          <g>
            <rect x="0" y="0" width="90" height="40" rx="6" fill="#ffffff" stroke="#1e293b" stroke-width="2" />
            <line x1="5" y1="20" x2="85" y2="20" stroke="#0284c7" stroke-width="1.2" stroke-dasharray="3,3" />
            <text x="45" y="16" font-size="11" font-weight="bold" fill="#1e293b" text-anchor="middle">${n.title}</text>
          </g>
        `
      },
      pump: {
        width: 44, height: 40,
        title: 'Pump',
        tag: 'P-101',
        ports: [
          { x: 0, y: 20, name: 'In' },
          { x: 44, y: 20, name: 'Out' },
          { x: 20, y: 0, name: 'Top' }
        ],
        render: (n) => `
          <g>
            <circle cx="20" cy="20" r="14" fill="#ffffff" stroke="#1e293b" stroke-width="2.2" />
            <polygon points="20,6 40,20 20,34" fill="#f1f5f9" stroke="#1e293b" stroke-width="2" />
            <text x="20" y="38" font-size="9" fill="#64748b" text-anchor="middle">${n.tag || ''}</text>
          </g>
        `
      },
      boiler: {
        width: 80, height: 56,
        title: 'Boiler',
        tag: 'B-101',
        ports: [
          { x: 80, y: 28, name: 'Steam Out' },
          { x: 0, y: 28, name: 'Water In' }
        ],
        render: (n) => `
          <g>
            <rect x="0" y="0" width="80" height="56" rx="6" fill="#fff1f2" stroke="#e11d48" stroke-width="2.5" />
            <path d="M 20 40 Q 30 20 40 40 T 60 40" stroke="#e11d48" stroke-width="2" fill="none" />
            <text x="40" y="24" font-size="12" font-weight="bold" fill="#e11d48" text-anchor="middle">${n.title}</text>
          </g>
        `
      },
      cooling_tower: {
        width: 74, height: 60,
        title: 'Cooling Tower',
        tag: 'CT-101',
        ports: [
          { x: 37, y: 60, name: 'CW Supply' },
          { x: 37, y: 0, name: 'CW Return' }
        ],
        render: (n) => `
          <g>
            <rect x="0" y="0" width="74" height="60" rx="4" fill="#f0f9ff" stroke="#0284c7" stroke-width="2.2" />
            <text x="37" y="26" font-size="11" font-weight="bold" fill="#0369a1" text-anchor="middle">Cooling</text>
            <text x="37" y="42" font-size="11" font-weight="bold" fill="#0369a1" text-anchor="middle">Tower</text>
          </g>
        `
      },
      valve: {
        width: 36, height: 24,
        title: 'Valve',
        ports: [
          { x: 0, y: 12, name: 'In' },
          { x: 36, y: 12, name: 'Out' }
        ],
        render: (n) => `
          <g>
            <polygon points="4,4 18,12 4,20" fill="#f1f5f9" stroke="#1e293b" stroke-width="1.8" />
            <polygon points="32,4 18,12 32,20" fill="#f1f5f9" stroke="#1e293b" stroke-width="1.8" />
          </g>
        `
      },
      instrument_tt: {
        width: 32, height: 32,
        title: 'TT',
        tag: 'TT-101',
        ports: [
          { x: 16, y: 32, name: 'Lead' },
          { x: 0, y: 16, name: 'Left' },
          { x: 32, y: 16, name: 'Right' }
        ],
        render: (n) => `
          <g>
            <circle cx="16" cy="16" r="14" fill="#fef3c7" stroke="#d97706" stroke-width="2" />
            <text x="16" y="20" font-size="11" font-weight="900" fill="#92400e" text-anchor="middle">TT</text>
          </g>
        `
      },
      stream_tag: {
        width: 90, height: 26,
        title: 'Feed →',
        ports: [
          { x: 90, y: 13, name: 'Out' },
          { x: 0, y: 13, name: 'In' }
        ],
        render: (n) => `
          <g>
            <text x="45" y="18" font-size="13" font-weight="bold" fill="#0f172a" text-anchor="middle">${n.title}</text>
          </g>
        `
      },
      highlight_ring: {
        width: 44, height: 44,
        title: 'Focus',
        ports: [],
        render: (n) => `
          <g>
            <ellipse cx="22" cy="22" rx="20" ry="16" fill="rgba(239, 68, 68, 0.05)" stroke="#ef4444" stroke-width="2.5" />
          </g>
        `
      },
      // 具備自訂顏色、背景、邊框的標註卡片
      annotation_card: {
        width: 130, height: 50,
        title: '工藝參數備註說明',
        bgColor: '#fffbeb',
        textColor: '#b45309',
        borderColor: '#fcd34d',
        fontSize: '12',
        ports: [
          { x: 65, y: 50, name: 'Bottom Leader' },
          { x: 0, y: 25, name: 'Left' },
          { x: 130, y: 25, name: 'Right' }
        ],
        render: (n) => {
          const bg = n.bgColor || '#fffbeb';
          const txt = n.textColor || '#b45309';
          const bdr = n.borderColor || '#fcd34d';
          const fsize = n.fontSize || '12';
          return `
            <g>
              <rect x="0" y="0" width="130" height="50" rx="6" fill="${bg}" stroke="${bdr}" stroke-width="1.8" filter="drop-shadow(0 1px 2px rgba(0,0,0,0.06))" />
              <text x="10" y="28" font-size="${fsize}" font-weight="600" fill="${txt}">${n.title}</text>
            </g>
          `;
        }
      }
    };

    function loadSampleProcess() {
      saveHistory();
      state.nodes = [
        // 鍋爐與冷卻塔公用系統
        { id: 'boiler1', type: 'boiler', x: 60, y: 480, title: 'Boiler', tag: 'B-101' },
        { id: 'ct1', type: 'cooling_tower', x: 120, y: 120, title: 'Cooling Tower', tag: 'CT-1' },

        // 進料泵
        { id: 'tag_feed', type: 'stream_tag', x: 110, y: 320, title: 'Feed →' },
        { id: 'p_feed', type: 'pump', x: 190, y: 310, title: 'Feed Pump', tag: 'P-101' },

        // 第 1 蒸餾塔 (T-101) 及再沸器
        { id: 'tower1', type: 'distillation_tower', x: 270, y: 220, title: 'Distillation\nTower', tag: 'T-101' },
        { id: 'reb1', type: 'reboiler', x: 190, y: 440, title: 'Reboiler', tag: 'E-101' },
        { id: 'p_reb1', type: 'pump', x: 330, y: 470, title: 'Btm Pump', tag: 'P-102' },
        
        // 儀表 TT 測點
        { id: 'tt_t1_top', type: 'instrument_tt', x: 235, y: 230, title: 'TT' },
        { id: 'tt_t1_mid', type: 'instrument_tt', x: 360, y: 290, title: 'TT' },
        { id: 'tt_t1_btm', type: 'instrument_tt', x: 225, y: 390, title: 'TT' },

        // 第 1 塔頂冷凝與分層
        { id: 'cond1', type: 'condenser', x: 400, y: 140, title: 'Condenser', tag: 'E-102' },
        { id: 'dec1', type: 'decanter', x: 410, y: 215, title: 'Decanter', tag: 'V-101' },
        { id: 'p_dec1', type: 'pump', x: 440, y: 285, title: 'Reflux Pump', tag: 'P-103' },
        { id: 'tag_light', type: 'stream_tag', x: 540, y: 295, title: '→ Light End' },

        // 第 2 蒸餾塔 (T-102) 及再沸器
        { id: 'tower2', type: 'distillation_tower', x: 620, y: 200, title: 'Distillation\nTower', tag: 'T-102' },
        { id: 'reb2', type: 'reboiler', x: 530, y: 440, title: 'Reboiler', tag: 'E-103' },
        { id: 'p_reb2', type: 'pump', x: 680, y: 460, title: 'Heavy Pump', tag: 'P-104' },

        // 第 2 塔儀表
        { id: 'tt_t2_top', type: 'instrument_tt', x: 580, y: 210, title: 'TT' },
        { id: 'tt_t2_mid', type: 'instrument_tt', x: 710, y: 270, title: 'TT' },
        { id: 'tt_t2_reb', type: 'instrument_tt', x: 575, y: 390, title: 'TT' },

        // 第 2 塔頂冷凝與產品
        { id: 'cond2', type: 'condenser', x: 760, y: 120, title: 'Condenser', tag: 'E-104' },
        { id: 'dec2', type: 'decanter', x: 770, y: 195, title: 'Decanter', tag: 'V-102' },
        { id: 'p_dec2', type: 'pump', x: 790, y: 265, title: 'Prod Pump', tag: 'P-105' },
        { id: 'tag_prod', type: 'stream_tag', x: 900, y: 275, title: '→ Product' },
        { id: 'tag_heavy', type: 'stream_tag', x: 840, y: 470, title: '→ Heavy End' },

        // 自訂顏色的一般標線備註卡片 (展示自由顏色自訂)
        { 
          id: 'note_tower1_opt', 
          type: 'annotation_card', 
          x: 230, y: 550, 
          title: 'Tower 1 操作參數\n回流比: 2.5:1\n塔頂: 78.2°C', 
          bgColor: '#fffbeb', 
          textColor: '#b45309', 
          borderColor: '#f59e0b',
          fontSize: '11'
        },
        { 
          id: 'note_steam_spec', 
          type: 'annotation_card', 
          x: 480, y: 530, 
          title: '高壓飽和蒸汽管網\n壓力: 3.5 barG\n供熱能力充足', 
          bgColor: '#fff1f2', 
          textColor: '#be123c', 
          borderColor: '#fda4af',
          fontSize: '11'
        },

        // 簡報照片上的紅色重點圈
        { id: 'focus_reb1', type: 'highlight_ring', x: 205, y: 445, title: 'Reb Focus' },
        { id: 'focus_reb2', type: 'highlight_ring', x: 545, y: 445, title: 'Reb Focus' },
        { id: 'focus_cond1', type: 'highlight_ring', x: 410, y: 140, title: 'Cond Focus' },
        { id: 'focus_cond2', type: 'highlight_ring', x: 770, y: 120, title: 'Cond Focus' },
        { id: 'focus_boiler', type: 'highlight_ring', x: 70, y: 490, title: 'Boiler Focus' }
      ];

      // 管線列表：涵蓋製程液相（動態光斑）、氣相、蒸汽加熱、冷卻水
      state.wires = [
        // 進料液相 (Liquid)
        { id: 'w_feed1', from: { id: 'tag_feed', port: 0 }, to: { id: 'p_feed', port: 0 }, type: 'liquid', label: 'Feed' },
        { id: 'w_feed2', from: { id: 'p_feed', port: 1 }, to: { id: 'tower1', port: 2 }, type: 'liquid', label: '85°C' },

        // Tower 1 頂部氣相與液相回流
        { id: 'w_t1_top', from: { id: 'tower1', port: 0 }, to: { id: 'cond1', port: 0 }, type: 'vapor', label: 'Vapor Overhead' },
        { id: 'w_c1_out', from: { id: 'cond1', port: 1 }, to: { id: 'dec1', port: 0 }, type: 'liquid' },
        { id: 'w_d1_out', from: { id: 'dec1', port: 1 }, to: { id: 'p_dec1', port: 0 }, type: 'liquid' },
        { id: 'w_p1_reflux', from: { id: 'p_dec1', port: 1 }, to: { id: 'tower1', port: 1 }, type: 'liquid', label: 'Reflux' },
        { id: 'w_p1_light', from: { id: 'p_dec1', port: 1 }, to: { id: 'tag_light', port: 1 }, type: 'liquid', label: 'Light End' },

        // Tower 1 塔底再沸器液相與氣相回升
        { id: 'w_t1_btm', from: { id: 'tower1', port: 4 }, to: { id: 'reb1', port: 0 }, type: 'liquid' },
        { id: 'w_reb1_vap', from: { id: 'reb1', port: 1 }, to: { id: 'tower1', port: 3 }, type: 'vapor', label: 'Boilup' },
        { id: 'w_t1_pump', from: { id: 'tower1', port: 4 }, to: { id: 'p_reb1', port: 0 }, type: 'liquid' },

        // Tower 1 塔底液相泵送至 Tower 2
        { id: 'w_t1_to_t2', from: { id: 'p_reb1', port: 1 }, to: { id: 'tower2', port: 2 }, type: 'liquid', label: 'Tower 2 Feed' },

        // Tower 2 頂部氣相 -> 冷凝 -> 分層 -> 產品液相
        { id: 'w_t2_top', from: { id: 'tower2', port: 0 }, to: { id: 'cond2', port: 0 }, type: 'vapor' },
        { id: 'w_c2_out', from: { id: 'cond2', port: 1 }, to: { id: 'dec2', port: 0 }, type: 'liquid' },
        { id: 'w_d2_out', from: { id: 'dec2', port: 1 }, to: { id: 'p_dec2', port: 0 }, type: 'liquid' },
        { id: 'w_p2_prod', from: { id: 'p_dec2', port: 1 }, to: { id: 'tag_prod', port: 1 }, type: 'liquid', label: 'Pure Product' },
        { id: 'w_p2_reflux', from: { id: 'p_dec2', port: 1 }, to: { id: 'tower2', port: 1 }, type: 'liquid', label: 'Reflux' },

        // Tower 2 塔底液相至再沸器與重端出料
        { id: 'w_t2_btm', from: { id: 'tower2', port: 4 }, to: { id: 'reb2', port: 0 }, type: 'liquid' },
        { id: 'w_reb2_vap', from: { id: 'reb2', port: 1 }, to: { id: 'tower2', port: 3 }, type: 'vapor' },
        { id: 'w_t2_pump', from: { id: 'tower2', port: 4 }, to: { id: 'p_reb2', port: 0 }, type: 'liquid' },
        { id: 'w_heavy_end', from: { id: 'p_reb2', port: 1 }, to: { id: 'tag_heavy', port: 1 }, type: 'liquid', label: 'Heavy End' },

        // 蒸汽公用加熱線 (Steam - 紅色脈衝)
        { id: 'w_steam1', from: { id: 'boiler1', port: 0 }, to: { id: 'reb1', port: 2 }, type: 'steam', label: '140°C Steam' },
        { id: 'w_steam2', from: { id: 'boiler1', port: 0 }, to: { id: 'reb2', port: 2 }, type: 'steam', label: 'Steam Supply' },

        // 冷卻循環水線 (Cooling Water - 藍色脈衝)
        { id: 'w_cw1', from: { id: 'ct1', port: 0 }, to: { id: 'cond1', port: 2 }, type: 'cooling', label: '32°C CW' },
        { id: 'w_cw2', from: { id: 'ct1', port: 0 }, to: { id: 'cond2', port: 2 }, type: 'cooling', label: 'CW Supply' }
      ];

      state.zoom = 1.0;
      state.pan = { x: 30, y: 10 };
      updateTransform();
      renderAll();
    }

    function getNodePortPos(nodeId, portIndex) {
      const node = state.nodes.find(n => n.id === nodeId);
      if (!node) return { x: 0, y: 0 };
      const tpl = NODE_TEMPLATES[node.type];
      const scaleX = node.scaleX || node.scale || 1;
      const scaleY = node.scaleY || node.scale || 1;
      const port = (tpl.ports && tpl.ports[portIndex]) ? tpl.ports[portIndex] : { x: tpl.width / 2, y: tpl.height / 2 };
      return {
        x: node.x + port.x * scaleX,
        y: node.y + port.y * scaleY
      };
    }

    // 正交直角工程走線算法
    function generatePath(wire, p1, p2) {
      if (wire.waypoints && wire.waypoints.length > 0) {
        let path = `M ${p1.x} ${p1.y}`;
        wire.waypoints.forEach(wp => {
          path += ` L ${wp.x} ${wp.y}`;
        });
        path += ` L ${p2.x} ${p2.y}`;
        return path;
      }
      return generateOrthoPath(p1, p2);
    }
    
    function generateOrthoPath(p1, p2) {
      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      if (Math.abs(dx) > Math.abs(dy)) {
        const midX = p1.x + dx * 0.5;
        return `M ${p1.x} ${p1.y} L ${midX} ${p1.y} L ${midX} ${p2.y} L ${p2.x} ${p2.y}`;
      } else {
        const midY = p1.y + dy * 0.5;
        return `M ${p1.x} ${p1.y} L ${p1.x} ${midY} L ${p2.x} ${midY} L ${p2.x} ${p2.y}`;
      }
    }

    function renderAll() {
      renderWires();
      renderNodes();
      renderPorts();
    }

    function renderWires() {
      wiresLayer.innerHTML = '';
      state.wires.forEach(wire => {
        const p1 = getNodePortPos(wire.from.id, wire.from.port);
        const p2 = getNodePortPos(wire.to.id, wire.to.port);
        const pathData = generatePath(wire, p1, p2);

        // 預設樣式
        let strokeColor = '#0f172a';
        let marker = 'url(#arrow-process)';
        let flowClass = '';
        let strokeWidth = '2.5';
        let labelColor = '#0f172a';

        // 依據相別賦予動態流動
        if (wire.type === 'liquid') {
          // 製程液相：深黑底實管 + 動態流動脈衝
          strokeColor = wire.color || '#0f172a';
          labelColor = wire.labelColor || strokeColor;
          marker = 'url(#arrow-process)';
          if (state.globalAnim && wire.animated !== false) {
            flowClass = 'flow-liquid-pulse';
          }
        } else if (wire.type === 'vapor') {
          strokeColor = wire.color || '#d97706';
          labelColor = wire.labelColor || strokeColor;
          marker = 'url(#arrow-vapor)';
          if (state.globalAnim && wire.animated !== false) {
            flowClass = 'flow-vapor-pulse';
          }
        } else if (wire.type === 'steam') {
          strokeColor = wire.color || '#dc2626';
          labelColor = wire.labelColor || strokeColor;
          marker = 'url(#arrow-steam)';
          if (state.globalAnim && wire.animated !== false) {
            flowClass = 'flow-steam-pulse';
          }
        } else if (wire.type === 'cooling') {
          strokeColor = wire.color || '#0284c7';
          labelColor = wire.labelColor || strokeColor;
          marker = 'url(#arrow-cooling)';
          if (state.globalAnim && wire.animated !== false) {
            flowClass = 'flow-cooling-pulse';
          }
        } else if (wire.type === 'solid') {
          strokeColor = wire.color || '#64748b';
          labelColor = wire.labelColor || strokeColor;
          marker = '';
          flowClass = '';
          strokeWidth = '2';
        } else {
          // 自訂顏色
          strokeColor = wire.color || '#334155';
          labelColor = wire.labelColor || strokeColor;
          marker = 'url(#arrow-custom)';
          if (state.globalAnim && wire.animated !== false) {
            flowClass = 'flow-liquid-pulse';
          }
        }

        const isSelected = state.selectedWireId === wire.id;

        const g = document.createElementNS(SVG_NS, 'g');
        g.dataset.id = wire.id;
        g.className = 'cursor-pointer';

        // 點擊判定加粗透明層
        const hitPath = document.createElementNS(SVG_NS, 'path');
        hitPath.setAttribute('d', pathData);
        hitPath.setAttribute('fill', 'none');
        hitPath.setAttribute('stroke', 'transparent');
        hitPath.setAttribute('stroke-width', '16');

        // 管底底層（實體管壁）
        const basePath = document.createElementNS(SVG_NS, 'path');
        basePath.setAttribute('d', pathData);
        basePath.setAttribute('fill', 'none');
        basePath.setAttribute('stroke', isSelected ? '#3b82f6' : strokeColor);
        basePath.setAttribute('stroke-width', isSelected ? '4' : strokeWidth);
        basePath.setAttribute('stroke-linecap', 'round');
        basePath.setAttribute('marker-end', marker);

        g.appendChild(hitPath);
        g.appendChild(basePath);

        // 如果是液相或開啟流動，疊加一層動態脈衝層 (流動光斑效果)
        if (flowClass) {
          const flowOverlay = document.createElementNS(SVG_NS, 'path');
          flowOverlay.setAttribute('d', pathData);
          flowOverlay.setAttribute('fill', 'none');
          // 液相光斑使用亮青色/半透明白，呈現液體在管內流動
          flowOverlay.setAttribute('stroke', wire.type === 'liquid' ? '#38bdf8' : '#ffffff');
          flowOverlay.setAttribute('stroke-width', '1.8');
          flowOverlay.setAttribute('stroke-linecap', 'round');
          flowOverlay.setAttribute('class', flowClass);
          flowOverlay.setAttribute('style', `animation-duration: ${1.2 / state.animSpeed}s;`);
          g.appendChild(flowOverlay);
        }

        // 管線備註標籤 (支援自訂顏色)
        if (wire.label) {
          const midX = (p1.x + p2.x) / 2;
          const midY = (p1.y + p2.y) / 2;
          const offsetX = wire.labelOffsetX || 0;
          const offsetY = wire.labelOffsetY || 0;
          
          const text = document.createElementNS(SVG_NS, 'text');
          text.setAttribute('x', midX + offsetX);
          text.setAttribute('y', midY - 6 + offsetY);
          text.setAttribute('fill', labelColor);
          text.setAttribute('font-size', '10');
          text.setAttribute('font-weight', 'bold');
          text.setAttribute('text-anchor', 'middle');
          text.setAttribute('class', 'select-none cursor-move');
          text.textContent = wire.label;
          
          // 讓文字可以被拖曳
          text.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            startDragWireLabel(wire.id, e);
          });
          
          g.appendChild(text);
        }

        g.addEventListener('mousedown', (e) => {
          // 支援直接按住管線拖曳新增折點
          e.stopPropagation();
          if (state.selectedWireId !== wire.id) {
            selectWire(wire.id);
          } else {
            // 已選取狀態下，直接按住線段拖曳產生新折點
            const mouse = getCanvasMousePos(e);
            if (!wire.waypoints) wire.waypoints = [];
            
            const p1Pos = getNodePortPos(wire.from.id, wire.from.port);
            const p2Pos = getNodePortPos(wire.to.id, wire.to.port);
            const pts = [p1Pos, ...wire.waypoints, p2Pos];
            let minIndex = 0;
            let minDist = Infinity;
            const dist2 = (p, v, w) => {
              let l2 = (v.x - w.x)**2 + (v.y - w.y)**2;
              if (l2 === 0) return (p.x - v.x)**2 + (p.y - v.y)**2;
              let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
              t = Math.max(0, Math.min(1, t));
              return (p.x - (v.x + t * (w.x - v.x)))**2 + (p.y - (v.y + t * (w.y - v.y)))**2;
            };
            for(let i=0; i<pts.length-1; i++) {
              let d = dist2(mouse, pts[i], pts[i+1]);
              if (d < minDist) { minDist = d; minIndex = i; }
            }
            
            wire.waypoints.splice(minIndex, 0, { x: mouse.x, y: mouse.y });
            startDragWaypoint(wire, minIndex, e);
          }
        });

        wiresLayer.appendChild(g);
        
        // 如果被選取，繪製重新連接與折點控制點
        if (isSelected) {
          // 起點重新連接控制點
          const p1Handle = createWireHandle(p1.x, p1.y, '#eab308');
          p1Handle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            startReconnectWire(wire, 'from', e);
          });
          wiresLayer.appendChild(p1Handle);
          
          // 終點重新連接控制點
          const p2Handle = createWireHandle(p2.x, p2.y, '#eab308');
          p2Handle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            startReconnectWire(wire, 'to', e);
          });
          wiresLayer.appendChild(p2Handle);
          
          // 折點控制點
          if (wire.waypoints) {
            wire.waypoints.forEach((wp, idx) => {
              const wpHandle = createWireHandle(wp.x, wp.y, '#0ea5e9');
              wpHandle.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                startDragWaypoint(wire, idx, e);
              });
              wpHandle.addEventListener('dblclick', (e) => {
                e.stopPropagation();
                wire.waypoints.splice(idx, 1);
                saveHistory();
                renderAll();
              });
              wiresLayer.appendChild(wpHandle);
            });
          }
          
          // 中點虛擬控制點 (輔助提示，點擊拖曳即可新增)
          const pts = [p1, ...(wire.waypoints || []), p2];
          for(let i=0; i<pts.length-1; i++) {
             const midX = (pts[i].x + pts[i+1].x) / 2;
             const midY = (pts[i].y + pts[i+1].y) / 2;
             const midHandle = createWireHandle(midX, midY, '#bae6fd');
             midHandle.setAttribute('r', '4');
             midHandle.style.opacity = '0.8';
             midHandle.style.cursor = 'crosshair';
             midHandle.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                if (!wire.waypoints) wire.waypoints = [];
                wire.waypoints.splice(i, 0, { x: midX, y: midY });
                startDragWaypoint(wire, i, e);
             });
             wiresLayer.appendChild(midHandle);
          }
        }
      });
    }
    
    function createWireHandle(x, y, color) {
      const circle = document.createElementNS(SVG_NS, 'circle');
      circle.setAttribute('cx', x);
      circle.setAttribute('cy', y);
      circle.setAttribute('r', '6');
      circle.setAttribute('fill', color);
      circle.setAttribute('stroke', '#ffffff');
      circle.setAttribute('stroke-width', '2');
      circle.setAttribute('class', 'cursor-move');
      return circle;
    }
    
    function startDragWaypoint(wire, idx, e) {
      const startX = e.clientX;
      const startY = e.clientY;
      const wp = wire.waypoints[idx];
      const startWpX = wp.x;
      const startWpY = wp.y;
      let hasMoved = false;
      
      const onMouseMove = (moveEvent) => {
        hasMoved = true;
        wp.x = startWpX + (moveEvent.clientX - startX) / state.zoom;
        wp.y = startWpY + (moveEvent.clientY - startY) / state.zoom;
        renderWires();
      };
      
      const onMouseUp = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        // 如果沒有移動，代表只是誤點，把剛新增的節點刪除
        if (!hasMoved && wire.waypoints.length > 0) {
           // wire.waypoints.splice(idx, 1);
           // 不要隨便刪除，這可能讓使用者原本的點消失。我們在這裡不做任何事，維持雙擊刪除的邏輯即可。
        }
        saveHistory();
        renderAll();
      };
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }
    
    // 用於記錄目前正在重新連接的線段資訊
    let reconnectingData = null;

    function startReconnectWire(wire, endType, e) {
      reconnectingData = { wireId: wire.id, endType: endType };
      
      // 模擬進入連線狀態，讓其他設備的 Port 顯示出來
      state.connectingStart = { 
        nodeId: wire[endType === 'from' ? 'to' : 'from'].id, // 防止連向自己
        portIndex: wire[endType === 'from' ? 'to' : 'from'].port 
      };
      
      const pos = getNodePortPos(wire[endType].id, wire[endType].port);
      tempWire.setAttribute('x1', pos.x);
      tempWire.setAttribute('y1', pos.y);
      tempWire.setAttribute('x2', pos.x);
      tempWire.setAttribute('y2', pos.y);
      tempWire.classList.remove('hidden');
      connHint.classList.remove('hidden');
      
      renderPorts(); // 顯示所有可連接的目標點
      
      const onMouseMove = (moveEvent) => {
        const mouse = getCanvasMousePos(moveEvent);
        tempWire.setAttribute('x2', mouse.x);
        tempWire.setAttribute('y2', mouse.y);
      };
      
      const onMouseUp = (upEvent) => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        
        // 如果沒有在 port 上觸發 finishReconnect (mouseup)，則取消
        // finishReconnect 會在 port 的 mouseup 處理
        setTimeout(() => {
          if (reconnectingData) {
            cancelConnect();
            reconnectingData = null;
          }
        }, 50);
      };
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }


    function renderNodes() {
      nodesLayer.innerHTML = '';
      state.nodes.forEach(node => {
        const tpl = NODE_TEMPLATES[node.type];
        if (!tpl) return;

        const isSelected = state.selectedNodeId === node.id;
        const g = document.createElementNS(SVG_NS, 'g');
        g.dataset.id = node.id;
        const scaleX = node.scaleX || node.scale || 1;
        const scaleY = node.scaleY || node.scale || 1;
        g.setAttribute('transform', `translate(${node.x}, ${node.y}) scale(${scaleX}, ${scaleY})`);
        g.className = 'cursor-move';

        // 渲染設備/標註卡片本體
        g.innerHTML = tpl.render(node);

        // 選取高亮外框
        if (isSelected) {
          const selBox = document.createElementNS(SVG_NS, 'rect');
          selBox.setAttribute('x', -4);
          selBox.setAttribute('y', -4);
          selBox.setAttribute('width', tpl.width + 8);
          selBox.setAttribute('height', tpl.height + 8);
          selBox.setAttribute('rx', 6);
          selBox.setAttribute('fill', 'none');
          selBox.setAttribute('stroke', '#0284c7');
          selBox.setAttribute('stroke-width', '2');
          selBox.setAttribute('stroke-dasharray', '4,4');
          g.insertBefore(selBox, g.firstChild);

          // 新增右下角縮放控制點 (Drag to resize)
          const resizeHandle = document.createElementNS(SVG_NS, 'circle');
          resizeHandle.setAttribute('cx', tpl.width + 4);
          resizeHandle.setAttribute('cy', tpl.height + 4);
          resizeHandle.setAttribute('r', '6');
          resizeHandle.setAttribute('fill', '#ffffff');
          resizeHandle.setAttribute('stroke', '#0284c7');
          resizeHandle.setAttribute('stroke-width', '2');
          resizeHandle.setAttribute('class', 'cursor-se-resize');
          
          resizeHandle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            startResizeNode(node.id, e);
          });
          g.appendChild(resizeHandle);
        }

        g.addEventListener('mousedown', (e) => {
          if (e.button !== 0) return;
          e.stopPropagation();
          startDragNode(node.id, e);
          selectNode(node.id);
        });

        nodesLayer.appendChild(g);
      });
    }

    function renderPorts() {
      portsLayer.innerHTML = '';
      state.nodes.forEach(node => {
        const tpl = NODE_TEMPLATES[node.type];
        if (!tpl || !tpl.ports) return;

        // 只有在該節點被選取，或正在進行管線拖曳時，才顯示綠色連接點
        if (state.selectedNodeId !== node.id && !state.connectingStart) {
          return;
        }

        tpl.ports.forEach((port, idx) => {
          const pos = getNodePortPos(node.id, idx);
          const circle = document.createElementNS(SVG_NS, 'circle');
          circle.setAttribute('cx', pos.x);
          circle.setAttribute('cy', pos.y);
          circle.setAttribute('r', '4.5');
          circle.setAttribute('fill', '#10b981');
          circle.setAttribute('stroke', '#ffffff');
          circle.setAttribute('stroke-width', '1.5');
          circle.setAttribute('class', 'port-node cursor-crosshair transition-all');
          circle.dataset.nodeId = node.id;
          circle.dataset.portIdx = idx;

          circle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            startConnect(node.id, idx, pos);
          });

          circle.addEventListener('mouseup', (e) => {
            e.stopPropagation();
            if (reconnectingData) {
              finishReconnect(node.id, idx);
            } else {
              finishConnect(node.id, idx);
            }
          });

          portsLayer.appendChild(circle);
        });
      });
    }

    function startConnect(nodeId, portIdx, pos) {
      state.connectingStart = { nodeId, portIndex: portIdx, x: pos.x, y: pos.y };
      tempWire.setAttribute('x1', pos.x);
      tempWire.setAttribute('y1', pos.y);
      tempWire.setAttribute('x2', pos.x);
      tempWire.setAttribute('y2', pos.y);
      tempWire.classList.remove('hidden');
      connHint.classList.remove('hidden');
      renderPorts(); // 顯示所有可連接的目標點
    }

    function finishReconnect(targetNodeId, targetPortIdx) {
      if (!reconnectingData) return;
      
      const wire = state.wires.find(w => w.id === reconnectingData.wireId);
      if (wire) {
        saveHistory();
        wire[reconnectingData.endType] = { id: targetNodeId, port: targetPortIdx };
      }
      
      reconnectingData = null;
      cancelConnect();
      renderAll();
    }

    function finishConnect(targetNodeId, targetPortIdx) {
      if (!state.connectingStart) return;
      if (state.connectingStart.nodeId === targetNodeId) {
        cancelConnect();
        return;
      }

      saveHistory();
      const newWire = {
        id: 'wire_' + Date.now(),
        from: { id: state.connectingStart.nodeId, port: state.connectingStart.portIndex },
        to: { id: targetNodeId, port: targetPortIdx },
        type: 'liquid',
        label: 'Stream',
        animated: true
      };

      state.wires.push(newWire);
      cancelConnect();
      renderAll();
      selectWire(newWire.id);
    }

    function cancelConnect() {
      state.connectingStart = null;
      tempWire.classList.add('hidden');
      connHint.classList.add('hidden');
      renderPorts(); // 隱藏非選取的連接點
    }

    function selectNode(id) {
      state.selectedNodeId = id;
      state.selectedWireId = null;
      renderAll();

      const node = state.nodes.find(n => n.id === id);
      if (!node) return;

      document.getElementById('prop-empty').classList.add('hidden');
      document.getElementById('prop-wire-form').classList.add('hidden');
      document.getElementById('btn-delete-selected').classList.remove('hidden');

      if (node.type === 'annotation_card') {
        // 顯示備註卡片專屬調色屬性面板
        document.getElementById('prop-node-form').classList.add('hidden');
        document.getElementById('prop-annotation-form').classList.remove('hidden');

        document.getElementById('note-prop-text').value = node.title || '';
        document.getElementById('note-prop-bgcolor').value = node.bgColor || '#fffbeb';
        document.getElementById('note-prop-textcolor').value = node.textColor || '#b45309';
        document.getElementById('note-prop-bordercolor').value = node.borderColor || '#fcd34d';
        document.getElementById('note-prop-fontsize').value = node.fontSize || '12';
      } else {
        // 一般設備面板
        document.getElementById('prop-annotation-form').classList.add('hidden');
        document.getElementById('prop-node-form').classList.remove('hidden');

        document.getElementById('node-prop-title').value = node.title || '';
        document.getElementById('node-prop-tag').value = node.tag || '';
        document.getElementById('node-prop-temp').value = node.temp || '';
        document.getElementById('node-prop-press').value = node.press || '';
        document.getElementById('node-prop-scale').value = node.scaleX || node.scale || 1;
        document.getElementById('node-scale-val').textContent = (node.scaleX || node.scale || 1) + 'x';
        
        const customFields = document.getElementById('prop-custom-block-fields');
        if (customFields) {
          if (node.type === 'custom_block') {
            customFields.classList.remove('hidden');
            document.getElementById('node-prop-bgcolor').value = node.bgColor || '#ffffff';
          } else {
            customFields.classList.add('hidden');
          }
        }
      }
    }

    function selectWire(id) {
      state.selectedWireId = id;
      state.selectedNodeId = null;
      renderNodes();
      renderWires();

      const wire = state.wires.find(w => w.id === id);
      if (!wire) return;

      document.getElementById('prop-empty').classList.add('hidden');
      document.getElementById('prop-node-form').classList.add('hidden');
      document.getElementById('prop-annotation-form').classList.add('hidden');
      document.getElementById('prop-wire-form').classList.remove('hidden');
      document.getElementById('btn-delete-selected').classList.remove('hidden');

      document.getElementById('wire-prop-type').value = wire.type || 'liquid';
      document.getElementById('wire-prop-label').value = wire.label || '';
      document.getElementById('wire-prop-color').value = wire.color || (wire.type === 'steam' ? '#dc2626' : wire.type === 'cooling' ? '#0284c7' : wire.type === 'vapor' ? '#d97706' : '#0f172a');
      document.getElementById('wire-prop-label-color').value = wire.labelColor || document.getElementById('wire-prop-color').value;
      document.getElementById('wire-prop-flow').value = wire.flow || '';
      document.getElementById('wire-prop-diameter').value = wire.diameter || '';
      document.getElementById('wire-prop-animated').checked = wire.animated !== false;
    }

    function clearSelection() {
      state.selectedNodeId = null;
      state.selectedWireId = null;
      renderAll();
      document.getElementById('prop-empty').classList.remove('hidden');
      document.getElementById('prop-node-form').classList.add('hidden');
      document.getElementById('prop-annotation-form').classList.add('hidden');
      document.getElementById('prop-wire-form').classList.add('hidden');
      document.getElementById('btn-delete-selected').classList.add('hidden');
    }

    // 設備表單監聽
    document.getElementById('node-prop-title').addEventListener('input', (e) => {
      const node = state.nodes.find(n => n.id === state.selectedNodeId);
      if (node) { node.title = e.target.value; renderNodes(); }
    });
    document.getElementById('node-prop-tag').addEventListener('input', (e) => {
      const node = state.nodes.find(n => n.id === state.selectedNodeId);
      if (node) { node.tag = e.target.value; renderNodes(); }
    });
    document.getElementById('node-prop-scale').addEventListener('input', (e) => {
      const node = state.nodes.find(n => n.id === state.selectedNodeId);
      if (node) {
        const val = parseFloat(e.target.value);
        node.scale = val;
        node.scaleX = val;
        node.scaleY = val;
        document.getElementById('node-scale-val').textContent = val + 'x';
        renderAll();
      }
    });

    const customImgInput = document.getElementById('node-prop-image');
    if (customImgInput) {
      customImgInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
          const node = state.nodes.find(n => n.id === state.selectedNodeId);
          if (node && node.type === 'custom_block') {
            node.imageUrl = event.target.result;
            renderNodes();
            saveHistory();
          }
        };
        reader.readAsDataURL(file);
      });
    }

    const customBgInput = document.getElementById('node-prop-bgcolor');
    if (customBgInput) {
      customBgInput.addEventListener('input', (e) => {
        const node = state.nodes.find(n => n.id === state.selectedNodeId);
        if (node && node.type === 'custom_block') {
          node.bgColor = e.target.value;
          renderNodes();
        }
      });
      customBgInput.addEventListener('change', saveHistory);
    }

    // 標註卡片自訂顏色監聽
    document.getElementById('note-prop-text').addEventListener('input', (e) => {
      const node = state.nodes.find(n => n.id === state.selectedNodeId);
      if (node) { node.title = e.target.value; renderNodes(); }
    });
    document.getElementById('note-prop-bgcolor').addEventListener('input', (e) => {
      const node = state.nodes.find(n => n.id === state.selectedNodeId);
      if (node) { node.bgColor = e.target.value; renderNodes(); }
    });
    document.getElementById('note-prop-textcolor').addEventListener('input', (e) => {
      const node = state.nodes.find(n => n.id === state.selectedNodeId);
      if (node) { node.textColor = e.target.value; renderNodes(); }
    });
    document.getElementById('note-prop-bordercolor').addEventListener('input', (e) => {
      const node = state.nodes.find(n => n.id === state.selectedNodeId);
      if (node) { node.borderColor = e.target.value; renderNodes(); }
    });
    document.getElementById('note-prop-fontsize').addEventListener('change', (e) => {
      const node = state.nodes.find(n => n.id === state.selectedNodeId);
      if (node) { node.fontSize = e.target.value; renderNodes(); }
    });

    // 顏色預設集快捷點擊
    document.querySelectorAll('.color-preset-bg').forEach(btn => {
      btn.addEventListener('click', () => {
        const color = btn.dataset.color;
        document.getElementById('note-prop-bgcolor').value = color;
        const node = state.nodes.find(n => n.id === state.selectedNodeId);
        if (node) { node.bgColor = color; renderNodes(); }
      });
    });
    document.querySelectorAll('.color-preset-text').forEach(btn => {
      btn.addEventListener('click', () => {
        const color = btn.dataset.color;
        document.getElementById('note-prop-textcolor').value = color;
        const node = state.nodes.find(n => n.id === state.selectedNodeId);
        if (node) { node.textColor = color; renderNodes(); }
      });
    });

    // 管線自訂顏色與屬性監聽
    document.getElementById('wire-prop-type').addEventListener('change', (e) => {
      const wire = state.wires.find(w => w.id === state.selectedWireId);
      if (wire) {
        wire.type = e.target.value;
        renderWires();
      }
    });
    document.getElementById('wire-prop-label').addEventListener('input', (e) => {
      const wire = state.wires.find(w => w.id === state.selectedWireId);
      if (wire) { wire.label = e.target.value; renderWires(); }
    });
    document.getElementById('wire-prop-color').addEventListener('input', (e) => {
      const wire = state.wires.find(w => w.id === state.selectedWireId);
      if (wire) { wire.color = e.target.value; renderWires(); }
    });
    document.getElementById('wire-prop-label-color').addEventListener('input', (e) => {
      const wire = state.wires.find(w => w.id === state.selectedWireId);
      if (wire) { wire.labelColor = e.target.value; renderWires(); }
    });
    document.getElementById('wire-prop-animated').addEventListener('change', (e) => {
      const wire = state.wires.find(w => w.id === state.selectedWireId);
      if (wire) { wire.animated = e.target.checked; renderWires(); }
    });

    function startDragWireLabel(wireId, e) {
      const wire = state.wires.find(w => w.id === wireId);
      if (!wire) return;
      
      selectWire(wireId); // 選取該線段
      
      const startX = e.clientX;
      const startY = e.clientY;
      const initialOffsetX = wire.labelOffsetX || 0;
      const initialOffsetY = wire.labelOffsetY || 0;
      
      const onMouseMove = (moveEvent) => {
        const dx = (moveEvent.clientX - startX) / state.zoom;
        const dy = (moveEvent.clientY - startY) / state.zoom;
        wire.labelOffsetX = initialOffsetX + dx;
        wire.labelOffsetY = initialOffsetY + dy;
        renderWires();
      };
      
      const onMouseUp = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        saveHistory();
      };
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }

    function startDragNodeText(nodeId, e) {
      const node = state.nodes.find(n => n.id === nodeId);
      if (!node) return;
      
      selectNode(nodeId);
      
      const startX = e.clientX;
      const startY = e.clientY;
      // 注意：文字是在節點內部被 scale 的，所以位移需反向除以 scale
      const scaleX = node.scaleX || node.scale || 1;
      const scaleY = node.scaleY || node.scale || 1;
      
      const initialOffsetX = node.textOffsetX || 0;
      const initialOffsetY = node.textOffsetY || 0;
      
      const onMouseMove = (moveEvent) => {
        const dx = (moveEvent.clientX - startX) / state.zoom / scaleX;
        const dy = (moveEvent.clientY - startY) / state.zoom / scaleY;
        node.textOffsetX = initialOffsetX + dx;
        node.textOffsetY = initialOffsetY + dy;
        renderNodes();
      };
      
      const onMouseUp = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        saveHistory();
      };
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }

    function startResizeNode(nodeId, e) {
      const node = state.nodes.find(n => n.id === nodeId);
      if (!node) return;
      const tpl = NODE_TEMPLATES[node.type];
      
      const startX = e.clientX;
      const startY = e.clientY;
      const startScaleX = node.scaleX || node.scale || 1;
      const startScaleY = node.scaleY || node.scale || 1;
      
      const onMouseMove = (moveEvent) => {
        const dx = (moveEvent.clientX - startX) / state.zoom;
        const dy = (moveEvent.clientY - startY) / state.zoom;
        
        let newScaleX = startScaleX + dx / (tpl.width || 100);
        let newScaleY = startScaleY + dy / (tpl.height || 100);
        
        node.scaleX = Math.max(0.2, Math.min(newScaleX, 5.0));
        node.scaleY = Math.max(0.2, Math.min(newScaleY, 5.0));
        
        renderAll();
        
        // 更新右側面板
        if (state.selectedNodeId === node.id) {
          const scaleInput = document.getElementById('node-prop-scale');
          if (scaleInput) {
            // 取平均值或 X 軸作為滑桿顯示
            scaleInput.value = (node.scaleX).toFixed(1);
          }
        }
      };
      
      const onMouseUp = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        saveHistory();
      };
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }

    function startDragNode(nodeId, e) {
      state.draggingNodeId = nodeId;
      const node = state.nodes.find(n => n.id === nodeId);
      const mouse = getCanvasMousePos(e);
      state.dragOffset = {
        x: mouse.x - node.x,
        y: mouse.y - node.y
      };
    }

    function getCanvasMousePos(e) {
      const rect = svgCanvas.getBoundingClientRect();
      const screenX = e.clientX - rect.left;
      const screenY = e.clientY - rect.top;
      return {
        x: (screenX - state.pan.x) / state.zoom,
        y: (screenY - state.pan.y) / state.zoom
      };
    }

    function updateTransform() {
      viewportGroup.setAttribute('transform', `translate(${state.pan.x}, ${state.pan.y}) scale(${state.zoom})`);
      document.getElementById('zoom-level').textContent = Math.round(state.zoom * 100) + '%';
    }

    document.getElementById('zoom-in').addEventListener('click', () => {
      state.zoom = Math.min(state.zoom * 1.15, 3);
      updateTransform();
    });
    document.getElementById('zoom-out').addEventListener('click', () => {
      state.zoom = Math.max(state.zoom / 1.15, 0.4);
      updateTransform();
    });
    document.getElementById('zoom-reset').addEventListener('click', () => {
      state.zoom = 1;
      state.pan = { x: 0, y: 0 };
      updateTransform();
    });

    canvasContainer.addEventListener('mousedown', (e) => {
      if (e.target === svgCanvas || e.target.id === 'canvas-container') {
        clearSelection();
        state.isPanning = true;
        state.panStart = { x: e.clientX - state.pan.x, y: e.clientY - state.pan.y };
      }
    });

    window.addEventListener('mousemove', (e) => {
      if (state.isPanning) {
        state.pan.x = e.clientX - state.panStart.x;
        state.pan.y = e.clientY - state.panStart.y;
        updateTransform();
        return;
      }

      if (state.draggingNodeId) {
        const mouse = getCanvasMousePos(e);
        const node = state.nodes.find(n => n.id === state.draggingNodeId);
        if (node) {
          node.x = Math.round((mouse.x - state.dragOffset.x) / 10) * 10;
          node.y = Math.round((mouse.y - state.dragOffset.y) / 10) * 10;
          renderAll();
        }
        return;
      }

      if (state.connectingStart) {
        const mouse = getCanvasMousePos(e);
        tempWire.setAttribute('x2', mouse.x);
        tempWire.setAttribute('y2', mouse.y);
      }
    });

    window.addEventListener('mouseup', () => {
      if (state.draggingNodeId) {
        saveHistory();
        state.draggingNodeId = null;
      }
      state.isPanning = false;
    });

    canvasContainer.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
      const newZoom = Math.min(Math.max(state.zoom * zoomFactor, 0.4), 3);
      const rect = svgCanvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      state.pan.x = mouseX - (mouseX - state.pan.x) * (newZoom / state.zoom);
      state.pan.y = mouseY - (mouseY - state.pan.y) * (newZoom / state.zoom);
      state.zoom = newZoom;
      updateTransform();
    }, { passive: false });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        cancelConnect();
      } else if (e.key === 'Delete' || e.key === 'Backspace') {
        if (!['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
          deleteSelected();
        }
      }
    });

    document.querySelectorAll('.add-node-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        saveHistory();
        const type = btn.dataset.type;
        const tpl = NODE_TEMPLATES[type];
        // 改為放置在畫面左下方，避免與正中央的設備重疊
        // 加入些微隨機偏移量(±20px)，防止連續新增時完全重疊
        const offset = (Math.random() * 40 - 20);
        const centerPos = {
          x: (-state.pan.x + 80 + offset) / state.zoom,
          y: (-state.pan.y + canvasContainer.clientHeight - 80 + offset) / state.zoom - tpl.height
        };

        const newNode = {
          id: 'node_' + Date.now(),
          type: type,
          x: Math.round(centerPos.x / 10) * 10,
          y: Math.round(centerPos.y / 10) * 10,
          title: tpl.title,
          tag: tpl.tag || '',
          bgColor: tpl.bgColor || '#fffbeb',
          textColor: tpl.textColor || '#b45309',
          borderColor: tpl.borderColor || '#fcd34d'
        };

        state.nodes.push(newNode);
        renderAll();
        selectNode(newNode.id);
      });
    });

    function deleteSelected() {
      saveHistory();
      if (state.selectedNodeId) {
        state.nodes = state.nodes.filter(n => n.id !== state.selectedNodeId);
        state.wires = state.wires.filter(w => w.from.id !== state.selectedNodeId && w.to.id !== state.selectedNodeId);
        clearSelection();
        renderAll();
      } else if (state.selectedWireId) {
        state.wires = state.wires.filter(w => w.id !== state.selectedWireId);
        clearSelection();
        renderAll();
      }
    }
    document.getElementById('btn-delete-selected').addEventListener('click', deleteSelected);

    function saveHistory() {
      if (state.history.length > 25) state.history.shift();
      state.history.push({
        nodes: JSON.parse(JSON.stringify(state.nodes)),
        wires: JSON.parse(JSON.stringify(state.wires))
      });
    }

    document.getElementById('btn-undo').addEventListener('click', () => {
      if (state.history.length > 0) {
        const last = state.history.pop();
        state.nodes = last.nodes;
        state.wires = last.wires;
        clearSelection();
        renderAll();
      }
    });

    // 動畫全域開關
    document.getElementById('btn-toggle-anim').addEventListener('click', () => {
      state.globalAnim = !state.globalAnim;
      document.getElementById('anim-text').textContent = state.globalAnim ? '流動動畫：啟動中' : '流動動畫：已暫停';
      renderWires();
    });

    // 流速調節
    const speedButtons = {
      'speed-slow': 0.5,
      'speed-normal': 1,
      'speed-fast': 2
    };
    Object.keys(speedButtons).forEach(id => {
      document.getElementById(id).addEventListener('click', () => {
        state.animSpeed = speedButtons[id];
        ['speed-slow', 'speed-normal', 'speed-fast'].forEach(i => {
          document.getElementById(i).className = (i === id)
            ? 'px-1.5 py-0.5 rounded text-[11px] bg-sky-600 text-white font-bold'
            : 'px-1.5 py-0.5 rounded text-[11px] hover:bg-slate-200';
        });
        renderWires();
      });
    });

    // 清空與重載範例
    document.getElementById('btn-clear').addEventListener('click', () => {
      saveHistory();
      state.nodes = [];
      state.wires = [];
      clearSelection();
      renderAll();
    });

    document.getElementById('btn-reload-demo').addEventListener('click', () => {
      loadSampleProcess();
    });

    document.getElementById('btn-export-json').addEventListener('click', () => {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify({
        nodes: state.nodes,
        wires: state.wires
      }, null, 2));
      const a = document.createElement('a');
      a.setAttribute("href", dataStr);
      a.setAttribute("download", `chemflow_project_${Date.now()}.json`);
      document.body.appendChild(a);
      a.click();
      a.remove();
    });

    document.getElementById('file-input').addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const data = JSON.parse(event.target.result);
          if (data.nodes && data.wires) {
            saveHistory();
            state.nodes = data.nodes;
            state.wires = data.wires;
            clearSelection();
            renderAll();
          }
        } catch (err) {
          // ignore corrupted json
        }
      };
      reader.readAsText(file);
    });

    document.getElementById('btn-export-png').addEventListener('click', () => {
      const svgClone = svgCanvas.cloneNode(true);
      svgClone.setAttribute('width', 1920);
      svgClone.setAttribute('height', 1080);
      const svgString = new XMLSerializer().serializeToString(svgClone);
      const img = new Image();
      const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);

      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = 1920;
        canvas.height = 1080;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);

        const a = document.createElement('a');
        a.download = `distillation_pfd_${Date.now()}.png`;
        a.href = canvas.toDataURL('image/png');
        a.click();
        URL.revokeObjectURL(url);
      };
      img.src = url;
    });

    // 啟動加載鴻勝精餾雙塔完整流程
    loadSampleProcess();
  