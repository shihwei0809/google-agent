import os
import re
import datetime
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')


# Target paths
workspace_dir = r"c:\GOOGLE ANGET\aigc-music-video-hub"
kb_dir = os.path.join(workspace_dir, "知識庫")
proj_cards_dir = os.path.join(kb_dir, "專案卡")
index_path = os.path.join(kb_dir, "Index.md")

# Source paths
root_dir = r"c:\GOOGLE ANGET"
html_dashboard_path = os.path.join(root_dir, "專案總覽.html")

# Folders to exclude from project scanning
EXCLUDE_FOLDERS = {
    "aigc-music-video-hub", "venv", "images", ".git", ".firebase", ".netlify", 
    "skills", "trip_photos", "test", "subtitles", "Clipping", "知識庫", "創作庫"
}

# Mapping extensions to technology names
TECH_MAPPING = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".php": "PHP",
    ".html": "HTML",
    ".css": "CSS",
    ".sh": "Shell Script",
    ".ps1": "PowerShell",
    ".doc": "Word Document",
    ".docx": "Word Document",
    ".pptx": "PowerPoint",
    ".pdf": "PDF",
    "package.json": "Node.js",
    "firebase.json": "Firebase",
    "composer.json": "Composer/PHP"
}

def get_project_metadata(folder_path):
    detected_techs = set()
    last_mod_time = 0
    readme_title = ""
    readme_desc = ""
    
    # Walk through the folder
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules' and d != 'venv']

        for file in files:
            file_path = os.path.join(root, file)
            try:
                mod_time = os.path.getmtime(file_path)
                if mod_time > last_mod_time:
                    last_mod_time = mod_time
            except:
                pass
                
            _, ext = os.path.splitext(file)
            if ext in TECH_MAPPING:
                detected_techs.add(TECH_MAPPING[ext])
            if file in TECH_MAPPING:
                detected_techs.add(TECH_MAPPING[file])
                
            if file.lower() == "readme.md" and not readme_title:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = [f.readline() for _ in range(15)]
                        for line in lines:
                            line = line.strip()
                            if line.startswith("# ") and not readme_title:
                                readme_title = line[2:].strip()
                            elif line and not line.startswith("#") and not readme_desc:
                                readme_desc = line[:200] + "..." if len(line) > 200 else line
                except:
                    pass
                    
    if last_mod_time > 0:
        mod_date = datetime.datetime.fromtimestamp(last_mod_time).strftime('%Y-%m-%d %H:%M:%S')
    else:
        mod_date = "未知"
        
    return {
        "techs": sorted(list(detected_techs)),
        "last_modified": mod_date,
        "readme_title": readme_title,
        "readme_desc": readme_desc
    }

# HTML Dashboard Template Generator
def generate_html(projects):
    projects_json = json.dumps(projects, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>鴻勝化學 / GOOGLE AGENT 專案總覽駕駛艙</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Marked.js for parsing markdown in modal -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <!-- Google Fonts Outfit & Inter -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', 'Outfit', system-ui, -apple-system, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
        }}
        .glass-card {{
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .glass-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(99, 102, 241, 0.4);
            box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.15);
        }}
        /* Markdown rendering overrides */
        .markdown-body h1 {{ font-size: 1.8rem; font-weight: 700; margin-bottom: 1rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
        .markdown-body h2 {{ font-size: 1.4rem; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.75rem; color: #818cf8; }}
        .markdown-body ul {{ list-style-type: disc; padding-left: 1.5rem; margin-bottom: 1rem; }}
        .markdown-body li {{ margin-bottom: 0.25rem; }}
        .markdown-body code {{ background-color: #334155; padding: 0.125rem 0.25rem; border-radius: 0.25rem; font-size: 0.9em; }}
        .markdown-body a {{ color: #6366f1; text-decoration: underline; }}
    </style>
</head>
<body class="min-h-screen pb-12">
    <!-- Navigation Bar -->
    <nav class="sticky top-0 z-40 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-6 py-4">
        <div class="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
            <div class="flex items-center gap-3">
                <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
                    GA
                </div>
                <div>
                    <h1 class="text-xl font-bold tracking-tight bg-gradient-to-r from-indigo-200 via-slate-200 to-indigo-100 bg-clip-text text-transparent">GOOGLE AGENT 專案總覽駕駛艙</h1>
                    <p class="text-xs text-slate-400">本機專案自動同步化系統</p>
                </div>
            </div>
            <div class="text-right">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    ● 本機服務運作中
                </span>
                <p class="text-[10px] text-slate-500 mt-1">最後更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-6 mt-8">
        <!-- Search and Filter Bar -->
        <div class="flex flex-col md:flex-row gap-4 mb-8">
            <div class="flex-1 relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                </div>
                <input type="text" id="searchInput" placeholder="搜尋專案名稱、描述或開發技術..." class="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:outline-none focus:border-indigo-500 text-slate-200 placeholder-slate-400 transition">
            </div>
            <div class="flex flex-wrap gap-2 items-center" id="techTagsContainer">
                <span class="text-xs text-slate-400 mr-2">快速篩選:</span>
                <button onclick="filterByTech('')" class="tech-tag-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white transition">全部</button>
            </div>
        </div>

        <!-- Project Grid -->
        <div id="projectGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- Cards will be injected dynamically -->
        </div>

        <!-- Empty State -->
        <div id="emptyState" class="hidden text-center py-16">
            <svg class="mx-auto h-12 w-12 text-slate-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <p class="text-slate-400 text-lg">沒有找到符合條件的專案</p>
        </div>
    </main>

    <!-- Modal Backdrop -->
    <div id="cardModal" class="fixed inset-0 z-50 hidden flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm transition-opacity">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            <!-- Modal Header -->
            <div class="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50 rounded-t-2xl">
                <div>
                    <h2 id="modalTitle" class="text-xl font-bold text-slate-100">專案卡片詳細資訊</h2>
                    <p id="modalMeta" class="text-xs text-slate-400 mt-1">目錄資訊</p>
                </div>
                <button onclick="closeModal()" class="text-slate-400 hover:text-white p-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
            <!-- Modal Body -->
            <div class="p-6 overflow-y-auto flex-1 markdown-body" id="modalBody">
                <!-- Markdown parsed content goes here -->
            </div>
            <!-- Modal Footer -->
            <div class="px-6 py-4 border-t border-slate-800 flex justify-end gap-3 bg-slate-900/50 rounded-b-2xl">
                <a id="modalFolderLink" href="#" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition flex items-center gap-2">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z"></path></svg>
                    開啟本機資料夾
                </a>
                <button onclick="closeModal()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition">
                    關閉
                </button>
            </div>
        </div>
    </div>

    <!-- JavaScript logic -->
    <script>
        const rawProjects = {projects_json};
        let activeFilterTech = '';

        // Dynamically build tech tags for selection
        function buildTechTags() {{
            const techSet = new Set();
            rawProjects.forEach(p => {{
                if (p.techs && p.techs !== '未知') {{
                    p.techs.split(', ').forEach(t => techSet.add(t));
                }}
            }});
            
            const container = document.getElementById('techTagsContainer');
            Array.from(techSet).sort().forEach(tech => {{
                const btn = document.createElement('button');
                btn.className = 'tech-tag-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-850 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 text-slate-300 transition';
                btn.textContent = tech;
                btn.onclick = () => filterByTech(tech);
                container.appendChild(btn);
            }});
        }}

        // Filter projects by search input and tech tags
        function renderCards() {{
            const query = document.getElementById('searchInput').value.toLowerCase();
            const grid = document.getElementById('projectGrid');
            grid.innerHTML = '';
            
            let matchCount = 0;
            
            rawProjects.forEach(p => {{
                const matchSearch = p.friendly_name.toLowerCase().includes(query) || 
                                    p.description.toLowerCase().includes(query) || 
                                    p.techs.toLowerCase().includes(query);
                
                const matchTag = !activeFilterTech || p.techs.includes(activeFilterTech);
                
                if (matchSearch && matchTag) {{
                    matchCount++;
                    
                    // Generate badge HTML for technologies
                    let badgeHtml = '';
                    if (p.techs && p.techs !== '未知') {{
                        p.techs.split(', ').forEach(tech => {{
                            badgeHtml += `<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mr-1.5">${{tech}}</span>`;
                        }});
                    }} else {{
                        badgeHtml = `<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">無偵測技術</span>`;
                    }}
                    
                    const card = document.createElement('div');
                    card.className = 'glass-card rounded-2xl p-6 cursor-pointer flex flex-col justify-between';
                    card.onclick = () => openModal(p);
                    
                    card.innerHTML = `
                        <div>
                            <div class="flex justify-between items-start mb-3">
                                <span class="text-[10px] text-slate-400 font-medium tracking-wider uppercase">最後變更: ${{p.last_modified.split(' ')[0]}}</span>
                                <span class="h-2 w-2 rounded-full bg-indigo-500"></span>
                            </div>
                            <h3 class="text-lg font-bold text-slate-100 mb-2 hover:text-indigo-400 transition line-clamp-1">${{p.friendly_name}}</h3>
                            <p class="text-sm text-slate-400 mb-4 line-clamp-3 leading-relaxed">${{p.description}}</p>
                        </div>
                        <div class="mt-4 pt-4 border-t border-slate-800 flex flex-wrap gap-y-1.5">
                            ${{badgeHtml}}
                        </div>
                    `;
                    
                    grid.appendChild(card);
                }}
            }});
            
            // Toggle empty state
            const emptyState = document.getElementById('emptyState');
            if (matchCount === 0) {{
                emptyState.classList.remove('hidden');
            }} else {{
                emptyState.classList.add('hidden');
            }}
        }}

        // Filter action
        function filterByTech(tech) {{
            activeFilterTech = tech;
            
            // Update button styles
            const buttons = document.querySelectorAll('.tech-tag-btn');
            buttons.forEach(btn => {{
                if (btn.textContent === tech || (tech === '' && btn.textContent === '全部')) {{
                    btn.className = 'tech-tag-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white transition';
                }} else {{
                    btn.className = 'tech-tag-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-300 transition';
                }}
            }});
            
            renderCards();
        }}

        // Modal operations
        function openModal(project) {{
            const modal = document.getElementById('cardModal');
            const title = document.getElementById('modalTitle');
            const meta = document.getElementById('modalMeta');
            const body = document.getElementById('modalBody');
            const folderLink = document.getElementById('modalFolderLink');
            
            title.textContent = project.friendly_name;
            meta.textContent = `本機目錄: c:\\GOOGLE ANGET\\${{project.folder_name}} | 最後更新: ${{project.last_modified}}`;
            folderLink.href = `file:///c:/GOOGLE%20ANGET/${{encodeURIComponent(project.folder_name)}}`;
            
            // Synthesize Markdown body details
            const mdText = `
## 🛠️ 偵測技術棧
\\`${{project.techs}}\\`

## 📝 專案用途與詳細描述
${{project.description}}

## 📁 資料夾路徑
- **本機目錄實體路徑**：\\`c:\\\\GOOGLE ANGET\\\\${{project.folder_name}}\\`
- 點擊下方按鈕或複製此路徑，即可快速打開檔案總管。
            `;
            
            body.innerHTML = marked.parse(mdText);
            
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }}

        function closeModal() {{
            const modal = document.getElementById('cardModal');
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }}

        // Initialize
        window.onload = () => {{
            buildTechTags();
            renderCards();
            
            // Search Input listener
            document.getElementById('searchInput').addEventListener('input', renderCards);
            
            // Close modal when clicking backdrop
            document.getElementById('cardModal').addEventListener('click', (e) => {{
                if (e.target.id === 'cardModal') closeModal();
            }});
        }};
    </script>
</body>
</html>
"""
    return html_content

def main():
    print("開始掃描本機專案目錄...")
    
    projects = []
    for entry in os.scandir(root_dir):
        if entry.is_dir() and entry.name not in EXCLUDE_FOLDERS and not entry.name.startswith('.'):
            folder_path = entry.path
            print(f"偵測到專案資料夾: {entry.name}")
            meta = get_project_metadata(folder_path)
            
            friendly_name = meta["readme_title"] if meta["readme_title"] else entry.name.replace("-", " ").replace("_", " ").title()
            
            projects.append({
                "folder_name": entry.name,
                "friendly_name": friendly_name,
                "techs": ", ".join(meta["techs"]) if meta["techs"] else "未知",
                "last_modified": meta["last_modified"],
                "description": meta["readme_desc"] if meta["readme_desc"] else "尚無描述，可在專案內新增 README.md 進行描述。"
            })
            
    projects.sort(key=lambda x: x["friendly_name"])
    
    # Update/Write Project Cards
    os.makedirs(proj_cards_dir, exist_ok=True)
    
    for p in projects:
        card_filename = f"{p['friendly_name'].replace(' ', '_').replace('/', '_')}.md"
        card_path = os.path.join(proj_cards_dir, card_filename)
        
        existing_desc = ""
        if os.path.exists(card_path):
            try:
                with open(card_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"## 📝 專案用途\n(.*?)\n\n(?:##|🔗)", content, re.DOTALL)
                    if match:
                        existing_desc = match.group(1).strip()
            except:
                pass
                
        desc_to_write = existing_desc if existing_desc else p["description"]
        
        card_content = f"# 📌 {p['friendly_name']}\n\n"
        card_content += f"- **專案類型**: 自動偵測專案\n"
        card_content += f"- **本機目錄**: `c:\\GOOGLE ANGET\\{p['folder_name']}`\n"
        card_content += f"- **偵測技術**: `{p['techs']}`\n"
        card_content += f"- **最後更新**: {p['last_modified']}\n\n"
        card_content += "## 📝 專案用途\n"
        card_content += f"{desc_to_write}\n\n"
        card_content += "## 🔗 相關資源與連結\n"
        card_content += f"- [本機專案資料夾](file:///c:/GOOGLE%20ANGET/{p['folder_name'].replace(' ', '%20')})\n"
        card_content += f"- [返回專案總覽索引]([[Index]])\n"
        
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(card_content)
            
    # Generate Index.md
    index_content = "# 🗂️ 專案總覽索引 (Project Hub)\n\n"
    index_content += f"*最後掃描時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    index_content += "此索引由系統自動掃描生成，用來導覽本機的所有開發專案。點擊下方連結可進入各專案的知識卡片：\n\n"
    index_content += "| 專案名稱 | 偵測技術 | 最後變更時間 | 專案卡片 |\n"
    index_content += "| --- | --- | --- | --- |\n"
    
    for p in projects:
        card_link = f"[[專案卡/{p['friendly_name'].replace(' ', '_').replace('/', '_')}\\|查看卡片]]"
        index_content += f"| {p['friendly_name']} | {p['techs']} | {p['last_modified']} | {card_link} |\n"
        
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)
        
    # Generate HTML Dashboard
    html_content = generate_html(projects)
    with open(html_dashboard_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"同步完成！共偵測到 {len(projects)} 個專案，已更新 Index.md、專案卡片與網頁駕駛艙。")

if __name__ == "__main__":
    main()
