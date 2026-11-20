"""
Google Colab T4 GPU Voice Cloning CLI Runner (`breezyvoice` | `voxcpm2`).
Adapted from GoogleColab影片/cloud/colab_h3.py for voice-only execution on Colab T4
(15GB VRAM / 12GB System RAM), stripping H3/ComfyUI (~150GB) completely.

If `colab` CLI is unavailable or the Google account lacks CLI compute units,
automatically prints the 1-click Free Web Colab Notebook URL and local .ipynb path.
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

SKILL_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_LOCAL = SKILL_ROOT / "templates" / "colab_t4_voice_clone.ipynb"
NOTEBOOK_WEB_URL = (
    "https://colab.research.google.com/github/shihwei0809/google-agent/blob/main/"
    ".agents/skills/sop-cinema-video/templates/colab_t4_voice_clone.ipynb"
)
RETRY = ("Connection was lost", "Timeout waiting for reply", "Read timed out", "ConnectionError", "RemoteDisconnected")


def print_web_colab_fallback(reason: str = ""):
    print("\n" + "=" * 72)
    if reason:
        print(f"[備援提示] {reason}")
    print("💡 若要直接用「完全免費 Google Colab Web 版 (T4 GPU)」跑語音克隆：")
    print(f"   1. 一鍵開啟網址：{NOTEBOOK_WEB_URL}")
    print(f"   2. 或手動上傳本機 Notebook：{NOTEBOOK_LOCAL}")
    print("   3. 選單列「執行階段 -> 變更執行階段類型 -> T4 GPU」後按「全部執行」即可！")
    print("=" * 72 + "\n")


def colab_bin() -> str | None:
    b = shutil.which("colab")
    if b:
        return b
    candidates = [
        Path.home()
        / "AppData"
        / "Roaming"
        / "Python"
        / f"Python{sys.version_info.major}{sys.version_info.minor}"
        / "Scripts"
        / "colab.exe",
        Path(sys.prefix) / "Scripts" / "colab.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def require_colab_bin() -> str:
    b = colab_bin()
    if not b:
        print_web_colab_fallback("本機未安裝 google-colab-cli（免費帳號可直接使用上方 Web Colab T4 連結，免安裝 CLI）。")
        sys.exit(2)
    return b


def cx(args, inp=None, timeout=900, tries=4, check=True) -> str:
    bin_path = require_colab_bin()
    out = ""
    for k in range(tries):
        try:
            r = subprocess.run(
                [bin_path] + [str(a) for a in args],
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
            sys.exit("Colab CLI 在 Windows 上需修補 termios：請執行  python GoogleColab影片/cloud/colab_cli_windows_patch.py")
        if not any(m in out for m in RETRY):
            break
        time.sleep(5 * (k + 1))
    if check and "Session not found" in out:
        sys.exit("Colab T4 機器已釋放（閒置約 20 分鐘會自動收回）。請重新執行 start。")
    return out


def vm(name: str, code: str, timeout: int = 300) -> str:
    return cx(["exec", "-s", name], inp=code, timeout=timeout)


def vm_sh(name: str, cmd: str, timeout: int = 600) -> str:
    return vm(
        name,
        f"import subprocess\nr = subprocess.run({cmd!r}, shell=True, capture_output=True, text=True)\n"
        "print(r.stdout[-6000:] + r.stderr[-3000:])",
        timeout=timeout,
    )


def alive(name: str) -> bool:
    return f"[{name}]" in cx(["sessions"], check=False)


def balance():
    m = re.search(r"Current balance:\s*([\d.]+)", cx(["usage"], check=False))
    return float(m.group(1)) if m else None


def new_t4_session(name: str) -> bool:
    if alive(name):
        return False
    print(f"[colab-t4] 正在啟動免費/雲端 T4 GPU (目前餘額：{balance()})...", flush=True)
    out = cx(["new", "-s", name, "--gpu", "T4"], timeout=600)
    if "rejected" in out.lower() or "Session READY" not in out:
        print_web_colab_fallback(f"Colab CLI 無法開啟 T4（免費帳號未配發 CLI 運算單元或額度不足）：\n{out[-500:]}")
        sys.exit(1)
    vm(name, "import os; os.makedirs('/content/work', exist_ok=True); print('READY')")
    return True


def _build_remote_setup_script(engine: str) -> str:
    return f"""import os, shutil, subprocess, sys
from pathlib import Path

ENGINE = {engine!r}

def sh(cmd, check=True):
    r = subprocess.run(cmd, shell=isinstance(cmd, str), text=True, capture_output=True)
    if r.returncode != 0:
        print(r.stdout[-1500:])
        print(r.stderr[-1500:])
        if check:
            raise RuntimeError(f"cmd failed: {{cmd}}")
    return r

if shutil.which("uv") is None:
    sh([sys.executable, "-m", "pip", "install", "-q", "uv"])
if shutil.which("ffmpeg") is None:
    sh("apt-get -qq update && apt-get -qq install -y ffmpeg")
sh([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub", "faster-whisper", "opencc-python-reimplemented", "soundfile", "librosa"])

def install_torch(py_exe, pinned=None):
    for cu in ("cu128", "cu126", "cu124"):
        pkgs = [f"torch=={{pinned}}", f"torchaudio=={{pinned}}"] if pinned else ["torch", "torchaudio"]
        r = sh(["uv", "pip", "install", "-q", "--python", str(py_exe), *pkgs, "--index-url", f"https://download.pytorch.org/whl/{{cu}}"], check=False)
        if r.returncode == 0:
            chk = sh([str(py_exe), "-c", "import torch; assert torch.cuda.is_available(); print(torch.__version__)"], check=False)
            if chk.returncode == 0:
                print("[setup] torch OK:", cu, chk.stdout.strip(), flush=True)
                return
    raise RuntimeError("CUDA PyTorch install failed")

if ENGINE == "breezyvoice":
    bv_code = Path("/content/BreezyVoice/code")
    bv_stub = Path("/content/BreezyVoice/winstub")
    bv_venv = Path("/content/BreezyVoice/venv")
    bv_py = bv_venv / "bin" / "python"
    bv_model = Path("/content/model_cache/BreezyVoice-300M")
    if not (bv_code / "single_inference.py").exists():
        sh(["git", "clone", "-q", "--recurse-submodules", "https://github.com/mtkresearch/BreezyVoice", str(bv_code)])
        sh(["git", "-C", str(bv_code), "checkout", "-q", "d592c9d3e8927a0f53f68616387060dcd32a05ea"])
        sh(["git", "-C", str(bv_code), "submodule", "update", "-q", "--init", "--recursive"])
    for rel, body in {{
        "tn/__init__.py": "",
        "tn/chinese/__init__.py": "",
        "tn/chinese/normalizer.py": "class Normalizer:\\n    def __init__(self, *a, **k): pass\\n    def normalize(self, text): return text\\n",
        "tn/english/__init__.py": "",
        "tn/english/normalizer.py": "class Normalizer:\\n    def __init__(self, *a, **k): pass\\n    def normalize(self, text): return text\\n",
    }}.items():
        p = bv_stub / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    if not bv_py.exists():
        sh(["uv", "venv", "-q", "-p", "3.10", str(bv_venv)])
        sh(["uv", "pip", "install", "-q", "--python", str(bv_py), "setuptools<70", "wheel"])
        install_torch(bv_py, pinned="2.7.1")
        req_txt = Path("/content/req_bv.txt")
        req_txt.write_text("\\n".join([
            "absl-py==2.5.0", "aiohttp", "antlr4-python3-runtime==4.9.3", "conformer==0.3.2",
            "diffusers==0.32.0", "einops==0.8.2", "fsspec==2024.12.0", "g2pw==0.1.1", "gdown==5.1.0",
            "huggingface-hub==0.36.2", "hydra-core==1.3.2", "hyperpyyaml==1.2.2", "inflect==7.3.1",
            "librosa==0.10.2", "lightning==2.2.4", "matplotlib==3.7.5", "networkx==3.1",
            "numpy==1.26.4", "omegaconf==2.3.0", "onnxruntime-gpu", "openai-whisper==20231117",
            "opencc-python-reimplemented==0.1.7", "packaging==24.2", "pandas", "pillow",
            "protobuf==4.25.0", "pydantic==2.7.0", "pydantic-core==2.18.1", "pydantic-settings==2.7.0",
            "pyyaml", "rich==13.7.1", "ruamel-yaml==0.17.40", "ruamel-yaml-clib==0.2.15",
            "safetensors", "scikit-learn", "scipy", "soundfile==0.12.1", "soxr", "tiktoken",
            "tokenizers==0.20.3", "torchmetrics", "tqdm", "transformers==4.45.2", "typeguard", "wget==3.2",
        ]), encoding="utf-8")
        sh(["uv", "pip", "install", "-q", "--python", str(bv_py), "--no-build-isolation", "--no-deps", "-r", str(req_txt), "--index-strategy", "unsafe-best-match"])
    if not (bv_model / "llm.pt").exists():
        from huggingface_hub import snapshot_download
        snapshot_download("MediaTek-Research/BreezyVoice-300M", revision="e33b502e0ac21c16b0ee0d00df66ac3fa737393d", local_dir=str(bv_model))
else:
    vx_venv = Path("/content/VoxCPM2/venv")
    vx_py = vx_venv / "bin" / "python"
    vx_model = Path("/content/model_cache/VoxCPM2")
    if not vx_py.exists():
        sh(["uv", "venv", "-q", "-p", "3.12", str(vx_venv)])
        install_torch(vx_py, pinned=None)
        sh(["uv", "pip", "install", "-q", "--python", str(vx_py), "voxcpm==2.0.3", "soundfile", "huggingface_hub", "opencc-python-reimplemented"])
    if not (vx_model / "model.safetensors").exists():
        from huggingface_hub import snapshot_download
        snapshot_download("openbmb/VoxCPM2", revision="32279effe8c19989596f05d353d1447f51d9e915", local_dir=str(vx_model))

Path(f"/content/t4_voice_{{ENGINE}}.ready").write_text("OK", encoding="utf-8")
print("T4_VOICE_SETUP_DONE", flush=True)
"""


def cmd_check(_args):
    if not colab_bin():
        print_web_colab_fallback("本機未安裝 google-colab-cli。")
        return
    print(cx(["version"], check=False).strip())
    out = cx(["usage"], check=False)
    print(out.strip()[-500:])
    if "balance" not in out.lower():
        print_web_colab_fallback("尚未登入 `colab usage` 或該帳號無 Colab CLI 額度；免費帳號請改用上方 Web Colab T4 連結。")
    else:
        m = re.search(r"Current balance:\s*([\d.]+)", out)
        if m and float(m.group(1)) <= 0.0:
            print_web_colab_fallback("目前 Colab CLI 運算單元餘額為 0.00；免費 T4 GPU 請直接使用上方 Web Colab 連結。")


def cmd_start(args):
    new_t4_session(args.name)
    marker = f"/content/t4_voice_{args.engine}.ready"
    has_ready = vm(args.name, f"import os; print('YES' if os.path.exists({marker!r}) else 'NO')")
    if "YES" in has_ready:
        print(f"[colab-t4] {args.engine} 環境已就緒（沿用現有 VM）。")
        return

    setup_py = _build_remote_setup_script(args.engine)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(setup_py)
        local_setup = tf.name
    try:
        out = cx(["upload", "-s", args.name, local_setup, "/content/setup_t4_voice.py"], timeout=300)
        if "Uploaded" not in out:
            sys.exit(f"上傳安裝腳本失敗：{out}")
    finally:
        Path(local_setup).unlink(missing_ok=True)

    print(f"[colab-t4] 正在 T4 VM 安裝 {args.engine} 環境與權重（約 1.5–3 分鐘）...", flush=True)
    vm_sh(args.name, "nohup python /content/setup_t4_voice.py > /content/setup_t4_voice.log 2>&1 &")
    t0 = time.time()
    seen = 0
    while time.time() - t0 < 1200:
        log = vm(args.name, "import os\nprint(open('/content/setup_t4_voice.log', errors='replace').read() if os.path.exists('/content/setup_t4_voice.log') else '')")
        lines = log.splitlines()
        for ln in lines[seen:]:
            print("  ", ln[:200], flush=True)
        seen = len(lines)
        if "T4_VOICE_SETUP_DONE" in log:
            print(f"[colab-t4] {args.engine} 安裝完成！（耗時 {time.time() - t0:.0f}s）")
            return
        if "Traceback" in log or "RuntimeError:" in log:
            sys.exit("T4 VM 安裝失敗，請查看上方 log。")
        time.sleep(15)
    sys.exit("T4 VM 安裝逾時（超過 20 分鐘）。")


def cmd_run(args):
    jobs_path = Path(args.jobs).resolve()
    if not jobs_path.exists():
        sys.exit(f"找不到 jobs JSON：{jobs_path}")

    ref_path = Path(args.ref).resolve() if args.ref else None
    if args.engine == "breezyvoice" and (not ref_path or not ref_path.exists()):
        sys.exit("BreezyVoice 必須提供 --ref <參考音檔.wav/mp3>（6–10 秒乾淨人聲）。若無參考音可改用 --engine voxcpm2。")

    cmd_start(args)

    # Package jobs.json (+ optional ref)
    tmp_dir = Path(tempfile.mkdtemp())
    in_zip = tmp_dir / "voice_bundle.zip"
    with zipfile.ZipFile(in_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(jobs_path, "jobs.json")
        if ref_path and ref_path.exists():
            zf.write(ref_path, f"ref{ref_path.suffix.lower()}")

    cx(["upload", "-s", args.name, str(in_zip), "/content/work/voice_bundle.zip"], timeout=600)

    ref_name = f"ref{ref_path.suffix.lower()}" if (ref_path and ref_path.exists()) else ""
    remote_runner = f"""import difflib, gc, json, os, re, subprocess, zipfile
from pathlib import Path

WORK = Path('/content/work')
with zipfile.ZipFile(WORK / 'voice_bundle.zip') as zf:
    zf.extractall(WORK)

ENGINE = {args.engine!r}
SEEDS = {int(args.seeds)!r}
REF_NAME = {ref_name!r}
REF_TEXT = {args.ref_text!r}.strip()
VOICE_DESIGN = {args.voice_design!r}.strip()

REF_WAV = WORK / 'ref_clean.wav'
if REF_WAV.exists():
    REF_WAV.unlink()
if REF_NAME and (WORK / REF_NAME).exists():
    subprocess.run([
        'ffmpeg', '-y', '-i', str(WORK / REF_NAME), '-ac', '1', '-ar', '24000', '-sample_fmt', 's16',
        '-af', 'silenceremove=start_periods=1:start_threshold=-45dB:detection=peak,areverse,silenceremove=start_periods=1:start_threshold=-45dB:detection=peak,areverse',
        str(REF_WAV)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if ENGINE == 'breezyvoice' and not REF_TEXT:
    import opencc
    from faster_whisper import WhisperModel
    wm = WhisperModel('small', device='cpu', compute_type='int8')
    segs, _ = wm.transcribe(str(REF_WAV), language='zh', beam_size=5)
    REF_TEXT = opencc.OpenCC('s2twp').convert(''.join(s.text for s in segs).strip())
    del wm
    gc.collect()
(WORK / 'resolved_ref_text.txt').write_text(REF_TEXT, encoding='utf-8')

CAND = WORK / 'candidates'
CAND.mkdir(parents=True, exist_ok=True)
WORKER = WORK / 'worker.py'

if ENGINE == 'breezyvoice':
    WORKER.write_text('''import json, os, re, sys, time
from pathlib import Path
BV_CODE = Path('/content/BreezyVoice/code')
BV_STUB = Path('/content/BreezyVoice/winstub')
os.chdir(BV_CODE)
for p in (BV_STUB, BV_CODE, BV_CODE / 'third_party' / 'Matcha-TTS'):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
import torch, torchaudio
from g2pw import G2PWConverter
from single_inference import CustomCosyVoice, get_bopomofo_rare
from cosyvoice.utils.file_utils import load_wav
TW_BOPO = {{'連假':'連假[:ㄐㄧㄚ4]','放假':'放假[:ㄐㄧㄚ4]','請假':'請假[:ㄐㄧㄚ4]','暑假':'暑假[:ㄐㄧㄚ4]','寒假':'寒假[:ㄐㄧㄚ4]','假期':'假[:ㄐㄧㄚ4]期','假日':'假[:ㄐㄧㄚ4]日'}}
DIG = '零一二三四五六七八九'
def int_zh(n):
    if n < 10: return DIG[n]
    if n < 100: t, o = divmod(n, 10); return ('' if t == 1 else DIG[t]) + '十' + (DIG[o] if o else '')
    if n < 1000: h, r = divmod(n, 100); return DIG[h] + '百' + ('' if r == 0 else ('零'+DIG[r] if r < 10 else ('一'+int_zh(r) if r < 20 else int_zh(r))))
    return ''.join(DIG[int(c)] for c in str(n))
def prep(t):
    t = re.sub(r'\\[:[^\\]]*\\]|\\d+', lambda m: m.group() if m.group().startswith('[') else int_zh(int(m.group())), t)
    for k, v in TW_BOPO.items():
        if v not in t: t = t.replace(k, v)
    return t.replace('……','，').replace('——','，').replace('～','！').strip()
cv = CustomCosyVoice('/content/model_cache/BreezyVoice-300M')
conv = G2PWConverter(); conv.num_workers = 0
spec = json.loads(Path('/content/work/jobs.json').read_text(encoding='utf-8-sig'))
ps = load_wav('/content/work/ref_clean.wav', 16000)
rt = Path('/content/work/resolved_ref_text.txt').read_text(encoding='utf-8').strip()
pt = get_bopomofo_rare(cv.frontend.text_normalize_new(rt, split=False), conv)
for j in spec['jobs']:
    txt = prep(j['text'])
    ct = get_bopomofo_rare(txt if '[' in txt else cv.frontend.text_normalize_new(txt, split=False), conv)
    for seed in range(1, int(j.get('seeds', int(sys.argv[1]))) + 1):
        dst = Path('/content/work/candidates') / f"{{j['name']}}_s{{seed}}.wav"
        torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
        out = cv.inference_zero_shot_no_normalize(ct, pt, ps)
        torchaudio.save(str(dst), out['tts_speech'], 22050)
        print('OK', dst.name, flush=True)
''', encoding='utf-8')
    subprocess.run(['/content/BreezyVoice/venv/bin/python', str(WORKER), str(SEEDS)], check=True)
else:
    WORKER.write_text('''import json, re, sys
from pathlib import Path
import soundfile as sf, torch
from voxcpm import VoxCPM
model = VoxCPM.from_pretrained('/content/model_cache/VoxCPM2', load_denoiser=False, optimize=False, device='cuda')
spec = json.loads(Path('/content/work/jobs.json').read_text(encoding='utf-8-sig'))
ref = Path('/content/work/ref_clean.wav'); has_ref = ref.exists()
design = (spec.get('voice_design') or sys.argv[2]).strip()
for j in spec['jobs']:
    clean = re.sub(r'\\[:[^\\]]*\\]', '', j['text']).strip()
    prompt = clean if has_ref else f"({{design}}){{clean}}"
    for seed in range(1, int(j.get('seeds', int(sys.argv[1]))) + 1):
        dst = Path('/content/work/candidates') / f"{{j['name']}}_s{{seed}}.wav"
        torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
        kw = dict(text=prompt, cfg_value=2.0, inference_timesteps=10, normalize=False, denoise=False)
        if has_ref: kw['reference_wav_path'] = str(ref)
        wav = model.generate(**kw)
        sf.write(str(dst), wav, model.tts_model.sample_rate, subtype='PCM_16')
        print('OK', dst.name, flush=True)
''', encoding='utf-8')
    subprocess.run(['/content/VoxCPM2/venv/bin/python', str(WORKER), str(SEEDS), VOICE_DESIGN], check=True)

# Pick best candidate via faster-whisper small + loudnorm
import librosa, opencc, soundfile as sf
from faster_whisper import WhisperModel
FINAL = WORK / 'final_audio'
FINAL.mkdir(parents=True, exist_ok=True)
asr = WhisperModel('small', device='cpu', compute_type='int8')
s2t = opencc.OpenCC('s2twp')
spec = json.loads((WORK / 'jobs.json').read_text(encoding='utf-8-sig'))
def cc(s): return re.sub(r'[^\\u4e00-\\u9fffA-Za-z0-9]', '', re.sub(r'\\[:[^\\]]*\\]', '', s)).upper()

report = {{}}
for j in spec['jobs']:
    name = j['name']
    tgt = cc(j['text'])
    cands = sorted(CAND.glob(f'{{name}}_s*.wav'), key=lambda p: int(p.stem.rsplit('_s', 1)[1]))
    scored = []
    for c in cands:
        x, sr = sf.read(str(c), dtype='float32'); mono = x.mean(axis=1) if x.ndim > 1 else x
        tr, _ = librosa.effects.trim(mono, top_db=38); dur = round(max(len(tr), 1)/sr, 2)
        segs, _ = asr.transcribe(str(c), language='zh', beam_size=5)
        heard = s2t.convert(''.join(s.text for s in segs)).strip()
        sim = round(difflib.SequenceMatcher(None, cc(heard), tgt).ratio(), 4)
        scored.append(dict(file=c.name, sim=sim, dur_s=dur, heard=heard))
    valid = [r for r in scored if r['dur_s'] >= 0.8] or scored
    best = max(valid, key=lambda r: (r['sim'], -abs(r['dur_s'] - len(tgt)*0.24)))
    x, sr = sf.read(str(CAND / best['file']), dtype='float32')
    mono = x.mean(axis=1) if x.ndim > 1 else x
    _, (a, b) = librosa.effects.trim(mono, top_db=40)
    a = max(0, a - int(0.08*sr)); b = min(len(x), b + int(0.15*sr))
    twav = WORK / f'{{name}}_trim.wav'
    sf.write(str(twav), x[a:b], sr, subtype='PCM_16')
    out_mp3 = FINAL / f'{{name}}.mp3'
    subprocess.run(['ffmpeg', '-y', '-i', str(twav), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '44100', '-ac', '2', '-b:a', '192k', str(out_mp3)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    twav.unlink(missing_ok=True)
    report[name] = dict(picked=best['file'], sim=best['sim'], dur_s=best['dur_s'], candidates=scored)
    print(f'PICK {{name}} -> {{best["file"]}} ({{best["sim"]*100:.1f}}%)', flush=True)

(WORK / 'pick_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
zout = Path('/content/cloned_audio_ready.zip')
with zipfile.ZipFile(zout, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write(WORK / 'pick_report.json', 'pick_report.json')
    for f in sorted(FINAL.iterdir()): zf.write(f, f'final_audio/{{f.name}}')
    for f in sorted(CAND.iterdir()): zf.write(f, f'candidates/{{f.name}}')
print('VOICE_RUN_DONE')
"""
    print(f"[colab-t4] 正在 T4 執行 {args.engine} 配音克隆＋Whisper 自動挑音...", flush=True)
    res_out = vm(args.name, remote_runner, timeout=1800)
    print(res_out[-2500:])
    if "VOICE_RUN_DONE" not in res_out:
        sys.exit("遠端配音執行未出現完成標記，請檢查上方輸出。")

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    local_zip = out_dir / "cloned_audio_ready.zip"
    dl = cx(["download", "-s", args.name, "/content/cloned_audio_ready.zip", str(local_zip)], timeout=600)
    if "Downloaded" not in dl:
        sys.exit(f"下載 cloned_audio_ready.zip 失敗：{dl}")

    with zipfile.ZipFile(local_zip) as zf:
        for member in zf.namelist():
            if member.startswith("final_audio/") and not member.endswith("/"):
                target = out_dir / Path(member).name
                target.write_bytes(zf.read(member))
            elif member == "pick_report.json":
                (out_dir / "pick_report.json").write_bytes(zf.read(member))

    print(f"[colab-t4] ✅ 完成！所有克隆配音已存至 {out_dir}（含 cloned_audio_ready.zip 備份與 pick_report.json）。")
    if args.stop_after:
        cmd_stop(args)


def cmd_stop(args):
    if not colab_bin():
        return
    print(cx(["stop", "-s", args.name], check=False).strip()[-200:])


def main():
    ap = argparse.ArgumentParser(description="Colab T4 語音克隆 CLI 工具 (BreezyVoice / VoxCPM2)")
    ap.add_argument("--name", default="t4voice", help="Colab session 名稱")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p_start = sub.add_parser("start")
    p_start.add_argument("--engine", choices=["breezyvoice", "voxcpm2"], default="breezyvoice")
    p_run = sub.add_parser("run")
    p_run.add_argument("--engine", choices=["breezyvoice", "voxcpm2"], default="breezyvoice")
    p_run.add_argument("--jobs", required=True, help="jobs JSON 檔案路徑 (如 bpm_voice_jobs.json)")
    p_run.add_argument("--ref", default="", help="6-10 秒參考聲音檔 (.wav/.mp3)")
    p_run.add_argument("--ref-text", default="", help="參考聲音逐字稿（留空則用 Whisper 自動辨識）")
    p_run.add_argument("--voice-design", default="一位親切專業的台灣職場講師，聲音自然清亮、吐字清晰、節奏明快")
    p_run.add_argument("--seeds", type=int, default=3)
    p_run.add_argument("--out-dir", required=True, help="配音輸出資料夾（如 blender_3d_demo/bpm_sop/audio）")
    p_run.add_argument("--stop-after", action="store_true")
    sub.add_parser("stop")
    args = ap.parse_args()
    {"check": cmd_check, "start": cmd_start, "run": cmd_run, "stop": cmd_stop}[args.cmd](args)


if __name__ == "__main__":
    main()
