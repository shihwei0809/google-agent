#!/usr/bin/env python3
"""
html-slide-builder Skill 安裝腳本
用法：python install.py
"""
import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

# ANSI 顏色
G = "\033[92m"   # 綠
Y = "\033[93m"   # 黃
R = "\033[91m"   # 紅
C = "\033[96m"   # 青
B = "\033[1m"    # 粗體
X = "\033[0m"    # 重置


def ok(msg):   print(f"  {G}✔{X}  {msg}")
def warn(msg): print(f"  {Y}⚠{X}  {msg}")
def err(msg):  print(f"  {R}✘{X}  {msg}")
def info(msg): print(f"  {C}→{X}  {msg}")
def head(msg): print(f"\n{B}{msg}{X}")


# ──────────────────────────────────────────────
# 1. 找 Claude skills 目錄
# ──────────────────────────────────────────────

def find_claude_skills_dir() -> Path | None:
    home = Path.home()
    candidates = [
        home / ".claude" / "skills",
        home / ".claude-skills",
    ]
    for p in candidates:
        if p.exists():
            return p
    # 試著建立預設位置
    default = home / ".claude" / "skills"
    default.mkdir(parents=True, exist_ok=True)
    return default


# ──────────────────────────────────────────────
# 2. 找 draw skill
# ──────────────────────────────────────────────

def find_draw_skill() -> Path | None:
    home = Path.home()
    candidates = [
        home / ".claude" / "skills" / "draw" / "draw.py",
        home / ".claude-skills" / "draw" / "draw.py",
        Path("C:/Users") / os.environ.get("USERNAME", "") / ".claude" / "skills" / "draw" / "draw.py",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


# ──────────────────────────────────────────────
# 3. 檢查必要元件
# ──────────────────────────────────────────────

def check_requirements() -> dict:
    head("【1】 檢查必要元件")
    results = {}

    # Python 版本
    vi = sys.version_info
    if vi >= (3, 8):
        ok(f"Python {vi.major}.{vi.minor}.{vi.micro}")
        results["python"] = True
    else:
        err(f"Python 版本過舊（{vi.major}.{vi.minor}），需要 3.8+")
        results["python"] = False

    # Pillow
    try:
        from PIL import Image
        import PIL
        ok(f"Pillow {PIL.__version__}（圖標去背）")
        results["pillow"] = True
    except ImportError:
        warn("Pillow 未安裝（圖標去背功能需要）")
        results["pillow"] = False

    # Draw Skill
    draw_path = find_draw_skill()
    if draw_path:
        ok(f"Draw Skill：{draw_path}")
        results["draw"] = str(draw_path)
    else:
        warn("找不到 Draw Skill（底圖 / 圖標生成需要）")
        info("請先安裝 Draw Skill，或從 Claude Code 技能庫取得")
        results["draw"] = None

    # OpenAI API Key（Draw Skill 用）
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        env_files = [
            Path.home() / ".openai.env",
            Path.cwd() / ".env",
        ]
        for ef in env_files:
            if ef.exists():
                content = ef.read_text(encoding="utf-8", errors="ignore")
                if "OPENAI_API_KEY" in content:
                    openai_key = "found_in_file"
                    break
    if openai_key:
        ok("OpenAI API Key 已設定（gpt-image-2 生圖）")
        results["openai"] = True
    else:
        warn("找不到 OPENAI_API_KEY")
        info("請設定環境變數，或在 ~/.openai.env 中加入 OPENAI_API_KEY=sk-...")
        results["openai"] = False

    # GitHub CLI
    gh = shutil.which("gh")
    if gh:
        ok(f"GitHub CLI (gh)：{gh}")
        results["gh"] = True
    else:
        warn("GitHub CLI (gh) 未安裝（自動部署到 GitHub Pages 需要）")
        info("安裝：https://cli.github.com/")
        results["gh"] = False

    # git
    git = shutil.which("git")
    if git:
        ok(f"git：{git}")
        results["git"] = True
    else:
        err("git 未安裝（版本控制必要）")
        results["git"] = False

    return results


# ──────────────────────────────────────────────
# 4. Firebase 設定
# ──────────────────────────────────────────────

DEMO_FIREBASE = {
    "apiKey":            "AIzaSyAYQhNavPSce17XtvDC5xnXyl9iUhW9KjA",
    "authDomain":        "teacherstudy-109ef.firebaseapp.com",
    "projectId":         "teacherstudy-109ef",
    "storageBucket":     "teacherstudy-109ef.firebasestorage.app",
    "messagingSenderId": "196599230156",
    "appId":             "1:196599230156:web:cfe55d364df3ae1b9d5c69",
}


def configure_firebase() -> dict:
    head("【2】 Firebase 設定（互動元件：文字雲、投票）")
    print(f"""
  此 Skill 的互動元件需要 Firebase Firestore 資料庫。
  你可以選擇：

    {C}A{X}  使用共用示範專案（teacherstudy-109ef）
       適合：快速試用、無需申請 Firebase 帳號
       注意：資料為公開共用，正式課程請使用自己的專案

    {C}B{X}  使用自己的 Firebase 專案（推薦正式使用）
       需要：在 console.firebase.google.com 建立專案並取得設定值
""")
    choice = input("  請選擇 [A/B]（直接 Enter = A）：").strip().upper() or "A"

    if choice == "B":
        print(f"\n  請至 Firebase Console → 專案設定 → 應用程式，複製 firebaseConfig 各欄位：\n")
        config = {}
        config["apiKey"]            = input("  apiKey：").strip()
        config["authDomain"]        = input("  authDomain：").strip()
        config["projectId"]         = input("  projectId：").strip()
        config["storageBucket"]     = input("  storageBucket：").strip()
        config["messagingSenderId"] = input("  messagingSenderId：").strip()
        config["appId"]             = input("  appId：").strip()
        ok("已儲存自訂 Firebase 設定")
        return config
    else:
        ok("使用共用示範 Firebase 專案（teacherstudy-109ef）")
        return DEMO_FIREBASE


def inject_firebase_config(firebase_config_path: Path, fb: dict):
    """將 Firebase 設定注入 firebase-config.md"""
    content = firebase_config_path.read_text(encoding="utf-8")
    replacements = {
        "AIzaSyAYQhNavPSce17XtvDC5xnXyl9iUhW9KjA": fb["apiKey"],
        "teacherstudy-109ef.firebaseapp.com":        fb["authDomain"],
        "teacherstudy-109ef":                        fb["projectId"],
        "teacherstudy-109ef.firebasestorage.app":    fb["storageBucket"],
        "196599230156":                              fb["messagingSenderId"],
        "1:196599230156:web:cfe55d364df3ae1b9d5c69": fb["appId"],
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    firebase_config_path.write_text(content, encoding="utf-8")


# ──────────────────────────────────────────────
# 5. 注入 draw.py 路徑到 SKILL.md
# ──────────────────────────────────────────────

def inject_draw_path(skill_md_path: Path, draw_path: str | None):
    if not draw_path:
        return
    content = skill_md_path.read_text(encoding="utf-8")
    content = content.replace(
        'python "C:/Users/user/.claude/skills/draw/draw.py"',
        f'python "{draw_path}"'
    )
    skill_md_path.write_text(content, encoding="utf-8")


# ──────────────────────────────────────────────
# 6. 安裝
# ──────────────────────────────────────────────

def install_skill(skills_dir: Path, fb: dict, draw_path: str | None):
    head("【3】 安裝 Skill")

    src = Path(__file__).parent / "skill"
    dst = skills_dir / "html-slide-builder"

    if dst.exists():
        print(f"\n  目標目錄已存在：{dst}")
        overwrite = input("  覆蓋安裝？[y/N]：").strip().lower()
        if overwrite != "y":
            warn("取消安裝")
            return False
        shutil.rmtree(dst)

    shutil.copytree(src, dst)
    ok(f"Skill 已安裝至：{dst}")

    # 注入 Firebase 設定
    fb_cfg = dst / "references" / "firebase-config.md"
    if fb_cfg.exists():
        inject_firebase_config(fb_cfg, fb)
        ok("Firebase 設定已注入")

    # 注入 draw.py 路徑
    skill_md = dst / "SKILL.md"
    inject_draw_path(skill_md, draw_path)
    if draw_path:
        ok("Draw Skill 路徑已更新")

    return True


# ──────────────────────────────────────────────
# 主程式
# ──────────────────────────────────────────────

def main():
    print(f"""
{B}{C}╔══════════════════════════════════════════════╗
║   html-slide-builder Skill 安裝程式          ║
║   教材 → AI 互動 HTML 簡報 + GitHub Pages   ║
╚══════════════════════════════════════════════╝{X}
""")

    # 1. 檢查元件
    results = check_requirements()

    # 2. 必要元件驗證
    if not results.get("python"):
        err("Python 版本不符，無法安裝。")
        sys.exit(1)
    if not results.get("git"):
        err("git 未安裝，無法繼續。請先安裝 git。")
        sys.exit(1)

    # 缺少 Pillow → 詢問自動安裝
    if not results.get("pillow"):
        install_pillow = input("\n  是否自動安裝 Pillow？[Y/n]：").strip().lower()
        if install_pillow != "n":
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
                ok("Pillow 安裝完成")
            except Exception as e:
                warn(f"Pillow 安裝失敗：{e}（圖標去背功能將無法使用）")

    # 3. Firebase 設定
    fb = configure_firebase()

    # 4. 找到 skills 目錄
    skills_dir = find_claude_skills_dir()
    info(f"Claude skills 目錄：{skills_dir}")

    # 5. 安裝
    draw_path = results.get("draw")
    success = install_skill(skills_dir, fb, draw_path)

    # 6. 結果報告
    head("【4】 安裝完成報告")
    if success:
        print(f"""
  {G}{B}✔ html-slide-builder Skill 已成功安裝！{X}

  安裝位置：{skills_dir / "html-slide-builder"}

  {B}使用方式：{X}
    在 Claude Code 對話中說：
    「幫我把這份教材做成 HTML 互動簡報」
    「把這個課程大綱轉成 Reveal.js 簡報」

  {B}元件狀態：{X}""")
        components = [
            ("底圖生成（Draw Skill）",     bool(results.get("draw"))),
            ("圖標去背（Pillow）",          results.get("pillow", False)),
            ("AI 生圖（OpenAI API Key）",  results.get("openai", False)),
            ("GitHub Pages 部署（gh CLI）", results.get("gh", False)),
        ]
        for name, status in components:
            symbol = f"{G}✔{X}" if status else f"{Y}⚠ 需手動設定{X}"
            print(f"    {symbol}  {name}")

        if not results.get("draw"):
            print(f"""
  {Y}提示：Draw Skill 未找到{X}
    請至 Claude Code 技能庫安裝 draw skill，
    或在 ~/.claude/skills/draw/draw.py 建立生圖腳本。
    安裝後重新執行此腳本以更新路徑設定。
""")
    else:
        warn("安裝未完成。")


if __name__ == "__main__":
    main()
