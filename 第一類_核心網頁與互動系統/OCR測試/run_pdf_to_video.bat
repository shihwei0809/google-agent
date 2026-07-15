@echo off
title PDF to Narrated Video Converter
echo ===================================================
echo  PDF to Narrated Video Converter (edge-tts + moviepy)
echo ===================================================
echo.
echo [*] Step 1: Extracting images and text from PDF...
python pdf_to_video.py --prepare
echo.
echo [+][+][+][+][+][+][+][+][+][+][+][+][+][+][+][+][+][+]
echo [!] Step 1 Complete!
echo [!] Please open "video_workspace\narration.json" and review/edit the voice script.
echo     (You can customize exactly what the neural voice says for each slide page)
echo [!] Once you are done saving narration.json, press any key below to start generating the video.
echo [+][+][+][+][+][+][+][+][+][+][+][+][+][+][+][+][+][+]
echo.
pause
echo.
echo [*] Step 2: Generating neural speech and synthesizing MP4 video...
python pdf_to_video.py --generate
echo.
echo [+] Video generation complete! Look for "*_導覽影片.mp4" in the current folder.
pause
