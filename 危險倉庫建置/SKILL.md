---
name: chemical-warehouse-planner
description: 協助進行化學品防爆倉儲系統的自動化規劃與報告生成
---

# 化學品防爆倉儲專案 (Chemical Warehouse Planner)

## 專案目的
本專案提供 1,000 m² 化學品防爆棧板穿梭車 (Pallet Shuttle) 倉儲的規劃報告及後續擴充框架。

## 依賴環境
- Python 3.9+ (若後續需擴充模擬分析工具)
- Markdown 閱讀器或靜態網頁產生工具

## 執行指令與安裝引導
當 AI 助理開啟本專案時，若使用者環境尚未安裝必要軟體，請主動詢問使用者是否要執行 `setup_env.ps1`：
```powershell
.\setup_env.ps1
```

## 自動維護規範
未來若新增了物流模擬腳本或後端 API，請同步更新本 `SKILL.md` 及 `setup_env.ps1`，確保安裝指令與說明書永久可用。
