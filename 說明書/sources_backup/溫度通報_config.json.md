# Source Code Backup - 溫度通報 - config.json

> [!NOTE]
> *   **原始本機路徑**: [config.json](file:///D:/GOOGLE%20ANGET/溫度通報/config.json)
> *   **自動備份時間**: `2026-07-15 13:39:13`
> *   **語言類型**: `json`

``` json
{
  "frequency": 60,
  "tid": "1000704",
  "town_name": "彰化縣線西鄉",
  "cwa_api_key": "CWA-718BCC42-A79F-4138-99BC-81D9C317BE28",
  "cwa_station_id": "C2G870",
  "temperature_threshold": 28.0,
  "mode": "both",
  "google_sheet_csv_url": "",
  "spreadsheet_id": "1cE__uNZfCd3Zm0_RZT0YVmRhqyTXeT-nWbhw8N3s37s",
  "web_app_url": "https://script.google.com/macros/s/AKfycbygJPZBmI2CUj4VfRUwN0gx1phqkbbdrYO5E-10jRWxOjoDCLyHbs0crFtfdarhEnwA/exec",
  "line": {
    "enabled": true,
    "channel_access_token": "5GyVAKorqM7GsTi5+OdJNtEMJZuvGXU4OXEHWeSS+gnhkpkV0ZFCEb7M2KdTopUKPELADU+xIMadPUytJO0g1XDpq2pnYj/70KNDBcL0pBLutivXV9P6Ff76ylrHQ0dbILQsPd7pCGLFXMcCrmgcEQdB04t89/1O/w1cDnyilFU=",
    "to": [
      "U2027149eee2292abfe9dc3e2fb4b9ee9",
      "C10943136364033b036ffb3d607034462"
    ]
  },
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "shihwei0809@gmail.com",
    "smtp_password": "fekzixzcmzjjbhmg",
    "to_email": [
      "king@shinychem.com.tw",
      "Alex@shinychem.com.tw",
      "C0876@eshineac.com.tw",
      "trevor.wang@eshineac.com.tw",
      "ycchen@shinychem.com.tw",
      "shihwei@eshineac.com.tw",
      "milo@eshineac.com.tw"
    ],
    "from_email": "shihwei0809@gmail.com"
  },
  "teams": {
    "enabled": true,
    "webhook_url": "https://defaulta46d9e33ad01451aaec52ee61979c6.d0.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/18fc24e04a0c4a2b97c100af08b2bce1/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=e8AjOzwQItiNynIkjq7MK5gN7KbvP1MSzr2u-tP_-8w"
  }
}
```
