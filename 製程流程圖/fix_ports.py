import re

file_path = r'd:\GOOGLE ANGET\製程流程圖\public\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update renderPorts()
render_ports_old = """    function renderPorts() {
      portsLayer.innerHTML = '';
      state.nodes.forEach(node => {
        const tpl = NODE_TEMPLATES[node.type];
        if (!tpl || !tpl.ports) return;

        tpl.ports.forEach((port, idx) => {"""

render_ports_new = """    function renderPorts() {
      portsLayer.innerHTML = '';
      state.nodes.forEach(node => {
        const tpl = NODE_TEMPLATES[node.type];
        if (!tpl || !tpl.ports) return;

        // 只有在該節點被選取，或正在進行管線拖曳時，才顯示綠色連接點
        if (state.selectedNodeId !== node.id && !state.connectingStart) {
          return;
        }

        tpl.ports.forEach((port, idx) => {"""

content = content.replace(render_ports_old, render_ports_new)

# 2. Update selectNode()
select_node_old = """    function selectNode(id) {
      state.selectedNodeId = id;
      state.selectedWireId = null;
      renderNodes();
      renderWires();"""
select_node_new = """    function selectNode(id) {
      state.selectedNodeId = id;
      state.selectedWireId = null;
      renderAll();"""
content = content.replace(select_node_old, select_node_new)

# 3. Update clearSelection()
clear_selection_old = """    function clearSelection() {
      state.selectedNodeId = null;
      state.selectedWireId = null;
      renderNodes();
      renderWires();"""
clear_selection_new = """    function clearSelection() {
      state.selectedNodeId = null;
      state.selectedWireId = null;
      renderAll();"""
content = content.replace(clear_selection_old, clear_selection_new)

# 4. Update startConnect()
start_connect_old = """    function startConnect(nodeId, portIdx, pos) {
      state.connectingStart = { nodeId, portIndex: portIdx, x: pos.x, y: pos.y };
      tempWire.setAttribute('x1', pos.x);
      tempWire.setAttribute('y1', pos.y);
      tempWire.setAttribute('x2', pos.x);
      tempWire.setAttribute('y2', pos.y);
      tempWire.classList.remove('hidden');
      connHint.classList.remove('hidden');
    }"""
start_connect_new = """    function startConnect(nodeId, portIdx, pos) {
      state.connectingStart = { nodeId, portIndex: portIdx, x: pos.x, y: pos.y };
      tempWire.setAttribute('x1', pos.x);
      tempWire.setAttribute('y1', pos.y);
      tempWire.setAttribute('x2', pos.x);
      tempWire.setAttribute('y2', pos.y);
      tempWire.classList.remove('hidden');
      connHint.classList.remove('hidden');
      renderPorts(); // 顯示所有可連接的目標點
    }"""
content = content.replace(start_connect_old, start_connect_new)

# 5. Update cancelConnect()
cancel_connect_old = """    function cancelConnect() {
      state.connectingStart = null;
      tempWire.classList.add('hidden');
      connHint.classList.add('hidden');
    }"""
cancel_connect_new = """    function cancelConnect() {
      state.connectingStart = null;
      tempWire.classList.add('hidden');
      connHint.classList.add('hidden');
      renderPorts(); // 隱藏非選取的連接點
    }"""
content = content.replace(cancel_connect_old, cancel_connect_new)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Modifications applied successfully.")
