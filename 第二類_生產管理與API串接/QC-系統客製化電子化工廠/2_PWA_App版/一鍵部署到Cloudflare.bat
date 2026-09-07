@echo off
chcp 65001 >nul
echo 正在部署至 Cloudflare Pages...
npx wrangler pages deploy . --project-name=eshine-qc-kanban
pause
