"""
山獅霸同款 Google Colab CLI 全自動遙控器 — 100% Apache-2.0 企業商用版 (Wan 2.2 I2V)
全程本機一行指令完成：自動開 G4/A100/L4 → 自動打包上傳首幀與分鏡 → 雲端批次生 24fps 720p 商用短片
→ 雙重 NT$50 預算煞車（VM 端＋本機端）→ 自動拉回本機資料夾 → finally 保證自動 colab stop 停費！

100% 商用合規（Apache-2.0、無美歐機房限制）：
  - Wan-AI/Wan2.2-I2V-A14B-Diffusers (14B MoE，G4 96GB 滿血首推)
  - Wan-AI/Wan2.2-TI2V-5B-Diffusers  (5B 輕量 L4 省點版)

前置條件（只需做一次，待帳號有 Colab 運算單元時）：
  1. uv tool install google-colab-cli
  2. python C:\\GOOGLE ANGET\\GoogleColab影片\\cloud\\colab_cli_windows_patch.py   (Windows 必做)
  3. colab usage   (登入有 Google AI Pro 或隨用隨付單元的 Google 帳號)

常用指令：
  python colab_wan22_cli.py check
  python colab_wan22_cli.py run --frames-dir tank_inbound_sop/flow_frames --out-dir tank_inbound_sop/flow_clips --budget 50 --gpu G4
  python colab_wan22_cli.py run --jobs video_jobs.json --frames-dir ./frames --out-dir ./clips --budget 50
  python colab_wan22_cli.py status
  python colab_wan22_cli.py stop
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RETRY = (
    "Connection was lost",
    "Timeout waiting for reply",
    "Read timed out",
    "ConnectionError",
    "RemoteDisconnected",
)

GPU_CU_RATES = {
    "G4": 8.90,
    "H100": 11.90,
    "A100": 5.30,
    "L4": 1.54,
    "T4": 1.07,
}

DEFAULT_NEG_PROMPT = (
    "blurry, distorted face, extra fingers, missing helmet, changing clothes, "
    "text, watermark, subtitle, logo, low quality, jitter, flicker, cartoon, anime"
)

VM_WORKER_SCRIPT = r'''import gc, json, os, shutil, subprocess, sys, time, zipfile
from pathlib import Path

cfg = json.loads(Path("/content/wan22_cfg.json").read_text(encoding="utf-8"))
SESSION_START = float(cfg["vm_start_ts"])
MAX_BUDGET_NTD = float(cfg["budget_ntd"])
NTD_PER_CU = float(cfg["ntd_per_cu"])
CU_PER_HR = float(cfg["cu_per_hr"])
NTD_PER_HR = CU_PER_HR * NTD_PER_CU
MODEL_ID = cfg["model_id"]
MAX_AREA = (720 * 1280) if cfg["res"] == "720p" else (480 * 832)
NUM_FRAMES = 81 if cfg["sec"] >= 5 else (65 if cfg["sec"] == 4 else 49)
STEPS = int(cfg["steps"])
GUIDANCE = float(cfg["guidance"])

WORK = Path("/content/wan22_work")
UP = WORK / "uploads"
OUT = WORK / "clips"
OUT.mkdir(parents=True, exist_ok=True)
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

def log(msg):
    print(f"[wan22] {msg}", flush=True)

def budget_ok(est_next_sec=0.0):
    el = time.time() - SESSION_START
    spent_ntd = (el / 3600.0) * NTD_PER_HR
    proj_ntd = ((el + est_next_sec) / 3600.0) * NTD_PER_HR
    rem_ntd = max(0.0, MAX_BUDGET_NTD - spent_ntd)
    ok = (spent_ntd < MAX_BUDGET_NTD) and (proj_ntd <= MAX_BUDGET_NTD * 1.02)
    return ok, el, spent_ntd, rem_ntd

def main():
    log(f"START model={MODEL_ID} res={cfg['res']} frames={NUM_FRAMES} budget=NT${MAX_BUDGET_NTD:.1f} rate=NT${NTD_PER_HR:.1f}/hr")
    # 1. 安裝依賴
    pkgs = ["diffusers>=0.34.0", "transformers>=4.49.0", "accelerate>=1.2.0", "ftfy", "sentencepiece", "imageio[ffmpeg]", "hf_transfer"]
    log("Installing diffusers & Wan 2.2 dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", *pkgs], check=True)
    if shutil.which("ffmpeg") is None:
        subprocess.run("apt-get -qq update && apt-get -qq install -y ffmpeg", shell=True, check=True)

    import numpy as np
    import torch
    from diffusers import WanImageToVideoPipeline
    from diffusers.utils import export_to_video, load_image

    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    gpu_name = torch.cuda.get_device_name(0)
    log(f"GPU ready: {gpu_name} ({vram_gb:.1f} GB VRAM)")

    ok, el, spent, rem = budget_ok()
    cost_log = []
    budget_stopped = False

    if not ok:
        budget_stopped = True
        log(f"BUDGET_BRAKE before model load: spent=NT${spent:.2f}")
    else:
        log(f"Loading Apache-2.0 model {MODEL_ID}...")
        t_load = time.time()
        pipe = WanImageToVideoPipeline.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16)
        if vram_gb >= 75:
            pipe.to("cuda")
            log(f"Loaded full bf16 on GPU ({time.time() - t_load:.1f}s)")
        else:
            pipe.enable_model_cpu_offload()
            log(f"Loaded with CPU offload ({time.time() - t_load:.1f}s)")

        jobs = json.loads((UP / "video_jobs.json").read_text(encoding="utf-8-sig"))
        avg_sec = 55.0 if vram_gb >= 75 else 170.0

        for idx, j in enumerate(jobs, start=1):
            ok, el, spent, rem = budget_ok(est_next_sec=avg_sec * 0.85)
            if not ok:
                budget_stopped = True
                log(f"BUDGET_BRAKE before shot {idx}/{len(jobs)} ({j['name']}): spent=NT${spent:.2f} / cap=NT${MAX_BUDGET_NTD:.1f}")
                break

            img_path = UP / j["image"]
            if not img_path.exists():
                log(f"SKIP missing image: {j['image']}")
                continue

            out_raw = OUT / f"{j['name']}_16fps.mp4"
            out_final = OUT / f"{j['name']}.mp4"
            image = load_image(str(img_path))
            ar = image.height / image.width
            mod = pipe.vae_scale_factor_spatial * pipe.transformer.config.patch_size[1]
            h = max(mod, round(np.sqrt(MAX_AREA * ar)) // mod * mod)
            w = max(mod, round(np.sqrt(MAX_AREA / ar)) // mod * mod)
            image = image.resize((w, h))

            seed = int(j.get("seed", 100 + idx))
            gen = torch.Generator(device="cuda").manual_seed(seed)
            log(f"SHOT {idx}/{len(jobs)} {j['name']} ({w}x{h}, {NUM_FRAMES}f, seed={seed}) rem=NT${rem:.2f}")
            t0 = time.time()
            frames = pipe(
                image=image,
                prompt=j["prompt"],
                negative_prompt=j.get("negative_prompt", ""),
                height=h,
                width=w,
                num_frames=NUM_FRAMES,
                guidance_scale=float(j.get("guidance_scale", GUIDANCE)),
                num_inference_steps=int(j.get("steps", STEPS)),
                generator=gen,
            ).frames[0]
            export_to_video(frames, str(out_raw), fps=16)
            subprocess.run([
                "ffmpeg", "-y", "-i", str(out_raw),
                "-vf", "fps=24", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                str(out_final),
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            out_raw.unlink(missing_ok=True)

            sec = time.time() - t0
            avg_sec = sec if idx == 1 else (avg_sec * 0.5 + sec * 0.5)
            _, el_now, spent_now, rem_now = budget_ok()
            clip_ntd = (sec / 3600.0) * NTD_PER_HR
            cost_log.append({
                "name": j["name"], "file": out_final.name, "size": f"{w}x{h}",
                "seed": seed, "sec": round(sec, 1), "est_clip_ntd": round(clip_ntd, 2),
                "cum_ntd": round(spent_now, 2),
            })
            log(f"DONE {out_final.name} {sec:.1f}s (clip~NT${clip_ntd:.2f} | cum~NT${spent_now:.2f})")

        del pipe
        gc.collect()
        torch.cuda.empty_cache()

    _, el_tot, spent_tot, _ = budget_ok()
    clips = sorted(OUT.glob("*.mp4"))
    summary = {
        "gpu": gpu_name,
        "vram_gb": round(vram_gb, 1),
        "model_id": MODEL_ID,
        "budget_cap_ntd": MAX_BUDGET_NTD,
        "budget_brake_triggered": budget_stopped,
        "elapsed_min": round(el_tot / 60.0, 2),
        "est_total_ntd": round(spent_tot, 2),
        "clips_completed": len(clips),
        "details": cost_log,
    }
    (WORK / "cost_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    zip_path = Path("/content/wan22_out.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(WORK / "cost_report.json", "cost_report.json")
        for mp4 in clips:
            zf.write(mp4, f"clips/{mp4.name}")
    log(f"PACKED {zip_path} clips={len(clips)} est_total=NT${spent_tot:.2f}")
    print("WAN22_ALL_DONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(f"WAN22_FAILED: {exc}", flush=True)
        sys.exit(1)
'''


def colab_bin() -> str:
    b = shutil.which("colab")
    if b:
        return b
    candidates = [
        Path.home() / "AppData" / "Roaming" / "Python" / f"Python{sys.version_info.major}{sys.version_info.minor}" / "Scripts" / "colab.exe",
        Path.home() / ".local" / "bin" / "colab.exe",
        Path(sys.prefix) / "Scripts" / "colab.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    sys.exit("找不到 colab 指令：請先執行  uv tool install google-colab-cli  （Windows 再執行 python GoogleColab影片/cloud/colab_cli_windows_patch.py）")


def cx(args, inp=None, timeout=900, tries=4, check=True) -> str:
    out = ""
    for k in range(tries):
        try:
            r = subprocess.run(
                [colab_bin()] + [str(a) for a in args],
                input=inp,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            out = (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            out = "Timeout waiting for reply (local timeout)"
        if "termios" in out:
            sys.exit("Colab CLI 在 Windows 需修補 termios：請執行  python GoogleColab影片/cloud/colab_cli_windows_patch.py")
        if not any(m in out for m in RETRY):
            break
        time.sleep(5 * (k + 1))
    if check and "Session not found" in out:
        sys.exit("Colab VM 已被收回（閒置過久）。請重新執行。")
    return out


def vm(name: str, code: str, timeout: int = 300) -> str:
    return cx(["exec", "-s", name], inp=code, timeout=timeout)


def alive(name: str) -> bool:
    return f"[{name}]" in cx(["sessions"], check=False)


def balance() -> float | None:
    m = re.search(r"Current balance:\s*([\d.]+)", cx(["usage"], check=False))
    return float(m.group(1)) if m else None


def stop_vm(name: str):
    if alive(name):
        print(f"\n🔌 [finally 安全關機] 正在釋放 Colab VM [{name}] 停止計費...", flush=True)
        out = cx(["stop", "-s", name], check=False)
        print("  ", out.strip()[-200:], flush=True)
    bal = balance()
    if bal is not None:
        print(f"💰 目前帳號剩餘運算單元：{bal:.2f} CU", flush=True)


def cmd_check(a):
    print(cx(["version"], check=False).strip())
    out = cx(["usage"], check=False).strip()
    print(out[-500:])
    bal = balance()
    if bal is None:
        print("→ 尚未登入：請在終端機執行 `colab usage`，用瀏覽器登入有運算單元的 Google 帳號。")
    elif bal <= 0.1:
        print("→ 目前運算單元為 0：CLI 全自動模式需有 Colab 隨用隨付或 Google AI Pro 附贈單元。")
        print("  （0 單元時請先使用免費 Web T4 語音版或 Google Flow。）")
    else:
        print(f"✅ 餘額 {bal:.2f} CU（約 NT${bal * a.ntd_per_cu:.0f}），可直接使用全自動 CLI 跑 Wan 2.2！")


def cmd_status(a):
    print(cx(["sessions"], check=False).strip())
    print(cx(["usage"], check=False).strip())


def cmd_stop(a):
    stop_vm(a.name)


def build_upload_bundle(frames_dir: Path, jobs_path: Path | None) -> tuple[Path, int]:
    tmp = Path(tempfile.mkdtemp())
    bundle = tmp / "wan22_in.zip"
    img_exts = {".png", ".jpg", ".jpeg", ".webp"}

    if jobs_path and jobs_path.exists():
        jobs = json.loads(jobs_path.read_text(encoding="utf-8-sig"))
    else:
        imgs = sorted([p for p in frames_dir.iterdir() if p.is_file() and p.suffix.lower() in img_exts])
        if not imgs:
            sys.exit(f"在 {frames_dir} 找不到任何首幀圖片 (.png/.jpg/.webp)")
        jobs = [
            {
                "name": img.stem,
                "image": img.name,
                "prompt": (
                    "Realistic industrial safety training film footage, smooth slow cinematic camera push-in, "
                    "technician wearing full PPE helmet and safety goggles performs careful inspection at chemical tank farm, "
                    "natural daylight, sharp focus, 24fps film look."
                ),
                "negative_prompt": DEFAULT_NEG_PROMPT,
                "seed": 100 + idx,
            }
            for idx, img in enumerate(imgs, start=1)
        ]

    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("video_jobs.json", json.dumps(jobs, ensure_ascii=False, indent=2))
        added = set()
        for j in jobs:
            img_name = j["image"]
            if img_name in added:
                continue
            p = Path(img_name)
            if not p.is_absolute():
                p = frames_dir / img_name
            if not p.exists():
                sys.exit(f"找不到分鏡指定的首幀圖片：{p}")
            zf.write(p, Path(img_name).name)
            added.add(img_name)
    return bundle, len(jobs)


def cmd_run(a):
    frames_dir = Path(a.frames_dir).resolve()
    out_dir = Path(a.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs_path = Path(a.jobs).resolve() if a.jobs else None

    bal_before = balance()
    if bal_before is None:
        sys.exit("尚未登入 Colab CLI：請先在終端機執行 `colab usage` 完成帳號授權。")
    if bal_before <= 0.1:
        sys.exit(f"目前 Colab 運算單元為 {bal_before:.2f} CU，無法開啟 {a.gpu}。待有隨用隨付或 AI Pro 單元後即可一行開跑。")

    bundle, n_jobs = build_upload_bundle(frames_dir, jobs_path)
    cu_rate = GPU_CU_RATES.get(a.gpu.upper(), 5.30)
    ntd_per_hr = cu_rate * a.ntd_per_cu
    model_id = "Wan-AI/Wan2.2-I2V-A14B-Diffusers" if a.model == "14b" else "Wan-AI/Wan2.2-TI2V-5B-Diffusers"

    print("=" * 68)
    print(f"🎬 Wan 2.2 全自動商用短片 CLI（Apache-2.0｜零瀏覽器全自動）")
    print(f"   GPU: {a.gpu} ({cu_rate} CU/hr ≈ NT${ntd_per_hr:.1f}/hr) | 模型: {model_id}")
    print(f"   鏡頭數: {n_jobs} 鏡 | 解析度: {a.res} {a.sec}s | 🛡️ 預算上限: NT${a.budget:.1f}")
    print(f"   帳號餘額: {bal_before:.2f} CU | 結束自動關機: {not a.keep_vm}")
    print("=" * 68, flush=True)

    local_t0 = time.time()
    created_here = False
    try:
        if not alive(a.name):
            print(f"🚀 開啟 Colab {a.gpu} VM [{a.name}]...", flush=True)
            out = cx(["new", "-s", a.name, "--gpu", a.gpu], timeout=600)
            if "rejected" in out.lower() or "Session READY" not in out:
                sys.exit(f"開機失敗（帳號可能無權限開 {a.gpu}）：\n{out[-600:]}")
            created_here = True
            print(f"✅ VM [{a.name}] 就緒！", flush=True)

        # 上傳分鏡包 + 寫入 VM Worker 與設定檔
        print(f"📤 上傳首幀與分鏡包 ({bundle.stat().st_size / 1e6:.2f} MB)...", flush=True)
        up_out = cx(["upload", "-s", a.name, str(bundle), "/content/wan22_in.zip"], timeout=1800)
        if "Uploaded" not in up_out:
            sys.exit(f"上傳失敗：\n{up_out[-500:]}")

        vm_cfg = {
            "vm_start_ts": time.time(),
            "budget_ntd": a.budget,
            "ntd_per_cu": a.ntd_per_cu,
            "cu_per_hr": cu_rate,
            "model_id": model_id,
            "res": a.res,
            "sec": a.sec,
            "steps": a.steps,
            "guidance": a.guidance,
        }
        setup_py = (
            "import json, zipfile\n"
            "from pathlib import Path\n"
            "up = Path('/content/wan22_work/uploads')\n"
            "up.mkdir(parents=True, exist_ok=True)\n"
            "zipfile.ZipFile('/content/wan22_in.zip').extractall(up)\n"
            f"Path('/content/wan22_cfg.json').write_text({json.dumps(vm_cfg)!r}, encoding='utf-8')\n"
            f"Path('/content/run_wan22.py').write_text({VM_WORKER_SCRIPT!r}, encoding='utf-8')\n"
            "print('VM_STAGED_OK')\n"
        )
        print(vm(a.name, setup_py).strip(), flush=True)

        # 背景啟動推論（避免單次 exec timeout）
        vm(a.name, "import subprocess; subprocess.Popen('nohup python -u /content/run_wan22.py > /content/wan22.log 2>&1 &', shell=True); print('LAUNCHED')")

        # 本機端輪詢進度 + 雙重超額保險（若超過預算 1.15 倍強制中止）
        seen = 0
        hard_limit_sec = (a.budget / ntd_per_hr) * 3600.0 * 1.15 + 120.0
        while True:
            txt = vm(a.name, "import os; print(open('/content/wan22.log', errors='replace').read() if os.path.exists('/content/wan22.log') else '')")
            lines = txt.splitlines()
            for l in lines[seen:]:
                if l.strip():
                    print("  ", l[:260], flush=True)
            seen = len(lines)
            if "WAN22_ALL_DONE" in txt:
                break
            if "WAN22_FAILED:" in txt:
                sys.exit("雲端生片發生錯誤，詳見上方 log。")
            if (time.time() - local_t0) > hard_limit_sec:
                print("🛑 [本機端強制超時煞車] 超過預算安全時限，準備直接結束並關機！", flush=True)
                break
            time.sleep(25)

        # 下載成品並自動解壓到 out_dir
        lz = Path(tempfile.mkdtemp()) / "wan22_out.zip"
        dl_out = cx(["download", "-s", a.name, "/content/wan22_out.zip", str(lz)], timeout=3600)
        if "Downloaded" in dl_out and lz.exists():
            with zipfile.ZipFile(lz) as zf:
                for m in zf.namelist():
                    if m.startswith("clips/") and m.endswith(".mp4"):
                        target = out_dir / Path(m).name
                        target.write_bytes(zf.read(m))
                        print(f"📥 已同步本機：{target}", flush=True)
                    elif m == "cost_report.json":
                        (out_dir / "wan22_cost_report.json").write_bytes(zf.read(m))
            rep = out_dir / "wan22_cost_report.json"
            if rep.exists():
                s = json.loads(rep.read_text(encoding="utf-8"))
                print(f"\n🏆 完成 {s['clips_completed']} 鏡 | 總耗時 {s['elapsed_min']} 分 | 預估花費 NT${s['est_total_ntd']:.2f} / 上限 NT${a.budget:.1f}")
        else:
            print(f"⚠️ 找不到可下載的成品包：\n{dl_out[-400:]}")
    finally:
        if not a.keep_vm and (created_here or alive(a.name)):
            stop_vm(a.name)
        elif a.keep_vm:
            print(f"ℹ️ --keep-vm 已啟用，VM [{a.name}] 保持開啟（請記得手動執行 `colab_wan22_cli.py stop`）。")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="wan22", help="Colab session 名稱（預設 wan22）")
    ap.add_argument("--ntd-per-cu", type=float, default=3.4, help="每運算單元台幣單價（預設 3.4）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="檢查 Colab CLI 與目前運算單元餘額")
    sub.add_parser("status", help="查看執行中 VM 與餘額")
    sub.add_parser("stop", help="立即關閉 Colab VM 停止計費")

    pr = sub.add_parser("run", help="一行指令全自動：開機 → 上傳 → 生片 → NT$50煞車 → 下載 → 自動關機")
    pr.add_argument("--frames-dir", required=True, help="本機首幀圖片資料夾")
    pr.add_argument("--out-dir", required=True, help="本機輸出 .mp4 資料夾")
    pr.add_argument("--jobs", default=None, help="選填 video_jobs.json 路徑（未填則自動為所有圖片生成 SOP 運鏡）")
    pr.add_argument("--gpu", default="G4", choices=["G4", "A100", "L4", "T4"], help="雲端 GPU（預設 G4 最快最省）")
    pr.add_argument("--model", default="14b", choices=["14b", "5b"], help="14b=Wan2.2-I2V-A14B | 5b=Wan2.2-TI2V-5B")
    pr.add_argument("--res", default="720p", choices=["720p", "480p"], help="解析度（預設 720p）")
    pr.add_argument("--sec", type=int, default=5, choices=[3, 4, 5], help="每鏡秒數（預設 5 秒）")
    pr.add_argument("--steps", type=int, default=28, help="推論步數（預設 28）")
    pr.add_argument("--guidance", type=float, default=3.5, help="CFG 引導強度（預設 3.5）")
    pr.add_argument("--budget", type=float, default=50.0, help="硬體預算上限新台幣（預設 NT$50.0，達標自動停機）")
    pr.add_argument("--keep-vm", action="store_true", help="跑完不自動關機（預設會自動關機停費）")

    a = ap.parse_args()
    {"check": cmd_check, "status": cmd_status, "stop": cmd_stop, "run": cmd_run}[a.cmd](a)


if __name__ == "__main__":
    main()
