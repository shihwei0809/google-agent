export async function onRequest(context) {
    const { request, env } = context;
    
    // 取得設定檔
    const { results } = await env.DB.prepare("SELECT key, value FROM config").all();
    const config = {};
    results.forEach(row => { config[row.key] = row.value; });

    const currentHour = new Date(new Date().toLocaleString("en-US", {timeZone: "Asia/Taipei"})).getHours();
    const startHour = parseInt(config.start_hour || "0");
    const endHour = parseInt(config.end_hour || "24");

    if (currentHour < startHour || currentHour >= endHour) {
        return new Response(JSON.stringify({status: "skipped", reason: "outside working hours"}), {
            headers: { "content-type": "application/json" }
        });
    }

    // 呼叫 CWA 氣象資料
    const apiUrl = https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization= + config.cwa_api_key + &StationId= + config.cwa_station_id;
    const cwaResponse = await fetch(apiUrl);
    
    if (!cwaResponse.ok) {
        return new Response(JSON.stringify({error: "CWA API failed"}), {status: 500});
    }

    const cwaData = await cwaResponse.json();
    const stations = cwaData?.records?.Station;
    if (!stations || stations.length === 0) {
        return new Response(JSON.stringify({error: "No station data"}), {status: 500});
    }

    const s = stations[0];
    const obsTimeRaw = s.ObsTime?.DateTime || "";
    
    // Generate Taiwan timestamp
    const twNow = new Date(new Date().toLocaleString("en-US", {timeZone: "Asia/Taipei"}));
    const pad = n => n.toString().padStart(2, '0');
    const twTimestamp = ` + twNow.getFullYear() + - + pad(twNow.getMonth()+1) + - + pad(twNow.getDate()) +   + pad(twNow.getHours()) + : + pad(twNow.getMinutes()) + : + pad(twNow.getSeconds());
    
    const obsTime = obsTimeRaw.replace("T", " ").substring(0, 19);
    const temp = parseFloat(s.WeatherElement?.AirTemperature || -99);
    const threshold = parseFloat(config.threshold || "28.0");

    let statusText = "正常 (未超標)";
    let alertStateText = "正常";

    if (temp >= threshold) {
        statusText = "高溫超標警報";
        alertStateText = "高溫警報中";
        
        // 觸發 LINE 推播
        if (config.line_notify_token) {
            const tokens = config.line_notify_token.split(",");
            const msg = \n【高溫警報】現場環境溫度已達  + temp + °C，已超設定閾值  + threshold + °C！\n觀測時間： + obsTime;
            
            for (let token of tokens) {
                token = token.trim();
                if (token) {
                    await fetch("https://notify-api.line.me/api/notify", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Authorization": "Bearer " + token
                        },
                        body: new URLSearchParams({ message: msg })
                    });
                }
            }
        }
    }

    // 防止重複觸發 (防呆機制)
    const existing = await env.DB.prepare("SELECT id FROM temperature_logs WHERE obs_time = ?").bind(obsTime).first();
    if (existing) {
        return new Response(JSON.stringify({status: "skipped", reason: "Data for this obs_time already exists"}), {
            headers: { "content-type": "application/json" }
        });
    }

    // 寫入 24 小時紀錄
    await env.DB.prepare(
        "INSERT INTO temperature_logs (timestamp, temperature, obs_time, status) VALUES (?, ?, ?, ?)"
    ).bind(twTimestamp, temp, obsTime, "即時觀測更新 (Cloudflare)").run();

    if (temp >= threshold) {
        // 寫入警報紀錄
        await env.DB.prepare(
            "INSERT INTO alert_logs (timestamp, threshold, temperature, obs_time, alert_state, status_text) VALUES (?, ?, ?, ?, ?, ?)"
        ).bind(twTimestamp, threshold, temp, obsTime, alertStateText, statusText).run();
    }

    return new Response(JSON.stringify({
        status: "success",
        temperature: temp,
        obs_time: obsTime,
        alert_state: alertStateText
    }), {
        headers: { "content-type": "application/json" }
    });
}
