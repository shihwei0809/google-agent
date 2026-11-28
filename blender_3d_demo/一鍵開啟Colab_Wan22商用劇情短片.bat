@echo off
chcp 65001 >nul
echo ========================================================================
echo   企業 SOP 商用劇情短片工作站 (Colab G4/A100/L4 + Wan 2.2 Apache-2.0)
echo   內建 NT$50 硬體預算自動煞車 + 跑完自動釋放 GPU 停費
echo ========================================================================
echo.
echo [1] 即將開啟 Google Colab 一鍵連結...
echo [2] 請於右上角切換執行階段為 G4 (最推薦) 或 A100 / L4
echo [3] 第 1 格預設 MAX_BUDGET_NTD = 50.0，達上限會自動打包下載並關機！
echo.
start "" "https://colab.research.google.com/github/shihwei0809/google-agent/blob/main/.agents/skills/sop-cinema-video/templates/colab_wan22_sop_cinema.ipynb"
echo.
echo 本機備份檔案：C:\GOOGLE ANGET\.agents\skills\sop-cinema-video\templates\colab_wan22_sop_cinema.ipynb
pause
