# 固定 AI 演員班底庫 (`actor_library`)

跨 MV 與企業 SOP 微電影共用的 **6 位固定台灣男女主角定裝庫**（25 / 35 / 45 歲各一男一女），每位皆採 **16:9 正面＋微側臉雙角度棚拍萬用定裝照**，搭配鎖臉英文錨點（`anchor_en`），大幅降低 Google Flow / Veo / Nano Banana 2.1 生成時的跑臉與長鬍子問題。

## 規格與班底一覽

- **女性共通規格**：身高 172cm、長髮清秀、自然台灣氣質
- **男性共通規格**：身高 178cm、短髮幹練（25 / 35 歲完全無鬍子；45 歲極淡成熟短鬚）

| 代號 | 姓名 | 年齡 | 身高 | 定位 / 適用題材 | 定裝照 |
|---|---|---|---|---|---|
| `f25` | 林若晴 (Ruo-Qing) | 25 | 172cm | 青春都會 MV、R&B 情歌、新進員工 SOP | `refs/f25_ref.jpg` |
| `m25` | 許承恩 (Cheng-En) | 25 | 178cm | 青春都會 MV、流行男主、年輕工程師 SOP | `refs/m25_ref.jpg` |
| `f35` | 蘇品妍 (Pin-Yan) | 35 | 172cm | 輕熟抒情 MV、職場主管、品管/行政 SOP | `refs/f35_ref.jpg` |
| `m35` | 林致遠 (Zhi-Yuan) | 35 | 178cm | 輕熟都會 MV、課長/資深工程師 SOP | `refs/m35_ref.jpg` |
| `f45` | 陳雅慧 (Ya-Hui) | 45 | 172cm | 親情/人生故事 MV、高階女主管、企業形象 | `refs/f45_ref.jpg` |
| `m45` | 張維誠 (Wei-Cheng) | 45 | 178cm | 人生故事 MV、資深廠長/職人、工安管理 SOP | `refs/m45_ref.jpg` |

## 檔案結構

```text
actor_library/
├── actors.json                  # 程式可讀演員清單（含 ID、路徑、鎖臉 anchor_en）
├── build_roster.py              # 一鍵拼出 3x2 視覺總覽圖
├── upload_to_flow_characters.py # 一鍵批次上傳 6 位固定演員至 Google Flow「角色」庫
├── 固定演員班底總覽圖.png        # 6 位演員一覽表（可在 IDE 直接開啟挑角）
├── refs/
│   ├── f25_ref.jpg              # 25 歲女（林若晴，右眼下小淚痣）
│   ├── m25_ref.jpg              # 25 歲男（許承恩，無鬍子）
│   ├── f35_ref.jpg              # 35 歲女（蘇品妍，右眼下小淚痣）
│   ├── m35_ref.jpg              # 35 歲男（林致遠，無鬍子）
│   ├── f45_ref.jpg              # 45 歲女（陳雅慧，右眼下小淚痣）
│   └── m45_ref.jpg              # 45 歲男（張維誠，極淡成熟短鬚）
├── README.md                    # 本說明書
├── SKILL.md                     # AI 助理自動調用規範
└── setup_env.ps1                # 一鍵環境初始化腳本
```

## 快速使用

```powershell
# 查看固定演員清單
python ..\mv_flow_runner.py --list-actors

# 執行 MV 生成時直接指定固定演員班底（自動掛定裝照＋注入鎖臉 anchor_en）
python ..\mv_flow_runner.py --project my_new_mv --actors f35 m35

# 將 6 位固定演員批次上傳至任意 Google Flow 專案的「角色」分頁
python upload_to_flow_characters.py --project-url https://flow.google.com/project/<你的專案ID>

# 若更換某位定裝照，重新產生總覽圖
python build_roster.py
```

在 `storyboard.json` 頂層加上 `"actors": ["f35", "m35"]`（或在分鏡 `"chars": ["f35", "m35"]`）即可直接套用固定班底。
