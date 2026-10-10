# setup_env.ps1
Write-Host "設定回收液入料記錄系統環境..."
cd 2_PWA_App版
pip install -r requirements.txt
Write-Host "環境設定完成！"
