@echo off
cd /d "%~dp0"
title Tank Inbound Part 1 - Colab Free T4 Taiwan Voice Studio
echo ============================================================================
echo   Tank Inbound Part 1 - Colab Free T4 Taiwan Voice Studio
echo ============================================================================
echo.
echo [1/3] Exporting normalized voice jobs (tank_inbound_sop\inbound_voice_jobs.json)...
python ..\build_tank_inbound_video.py --export-voice-jobs
echo.
echo [2/3] Opening tank_inbound_sop folder so you can drag inbound_voice_jobs.json...
start "" explorer "%cd%"
echo.
echo [3/3] Opening Google Colab Free T4 Voice Cloning Notebook...
start "" "https://colab.research.google.com/github/shihwei0809/google-agent/blob/main/.agents/skills/sop-cinema-video/templates/colab_t4_voice_clone.ipynb"
echo.
echo ----------------------------------------------------------------------------
echo   Steps in Google Colab (Free T4 GPU):
echo   1. Runtime -^> Change runtime type -^> Select [T4 GPU].
echo   2. Cell 1 Engine:
echo      - [VoxCPM2]     : 48kHz, NO ref.wav needed (uses Taiwan voice_design!)
echo      - [BreezyVoice] : Most authentic Taiwan Mandarin (upload 6-10s ref.wav)
echo   3. Click Runtime -^> Run all (Ctrl+F9).
echo   4. Upload tank_inbound_sop\inbound_voice_jobs.json at Cell 3.
echo   5. Extract final_audio\shot01..08.mp3 from downloaded ZIP into:
echo        tank_inbound_sop\audio\
echo      Then run:
echo        python build_tank_inbound_video.py --cinema
echo ----------------------------------------------------------------------------
pause
