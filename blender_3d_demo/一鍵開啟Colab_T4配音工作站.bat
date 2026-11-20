@echo off
cd /d "%~dp0"
title Colab Free T4 Voice Cloning Studio (BreezyVoice / VoxCPM2)
echo ============================================================================
echo   Colab Free T4 Voice Cloning Studio (BreezyVoice / VoxCPM2)
echo ============================================================================
echo.
echo [1/3] Exporting normalized voice jobs JSON (bpm_sop\bpm_voice_jobs.json)...
python build_bpm_sop_video.py --export-voice-jobs
if errorlevel 1 (
    echo [WARN] Failed to export bpm_voice_jobs.json, continuing anyway...
)
echo.
echo [2/3] Opening bpm_sop folder so you can drag bpm_voice_jobs.json & ref.wav...
start "" explorer "%cd%\bpm_sop"
echo.
echo [3/3] Opening Google Colab T4 Voice Cloning Notebook in your browser...
start "" "https://colab.research.google.com/github/shihwei0809/google-agent/blob/main/.agents/skills/sop-cinema-video/templates/colab_t4_voice_clone.ipynb"
echo.
echo ----------------------------------------------------------------------------
echo   Steps in Google Colab:
echo   1. Runtime -^> Change runtime type -^> Select [T4 GPU] (Free!).
echo   2. Choose [BreezyVoice] (Taiwan Mandarin) or [VoxCPM2] (48kHz) in Cell 1.
echo   3. Click Runtime -^> Run all (Ctrl+F9).
echo   4. Upload your 6-10s ref.wav + bpm_sop\bpm_voice_jobs.json at Cell 3.
echo   5. Extract final_audio\*.mp3 from downloaded ZIP into bpm_sop\audio\,
echo      then run:  python build_bpm_sop_video.py --cinema --speed 1.2
echo ----------------------------------------------------------------------------
pause
