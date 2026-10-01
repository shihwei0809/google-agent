export async function onRequest(context) {
    const { request, env } = context;
    
    // 取得設定值
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

    // 抓取 CWA 氣象資料
    const apiUrl = `https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=${config.cwa_api_key}&StationId=${config.cwa_station_id}`;
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
    const obsTime = obsTimeRaw.replace("T", " ").substring(0, 19);
    const temp = parseFloat(s.WeatherElement?.AirTemperature || -99);
    const threshold = parseFloat(config.threshold || "29.0");

    let statusText = "正常 (未超標)";
    let alertStateText = "正常";

    if (temp >= threshold) {
        statusText = "高溫警報發送";
        alertStateText = "高溫持續中";
        
        // 發送 LINE 通知
        if (config.line_notify_token) {
            const tokens = config.line_notify_token.split(",");
            const msg = `\n【高溫警報】環境溫度已達 ${temp}°C，超過設定閾值 ${threshold}°C！\n觀測時間：${obsTime}`;
            
            for (let token of tokens) {
                token = token.trim();
                if (token) {
                    await fetch("https://notify-api.line.me/api/notify", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Authorization": `Bearer ${token}`
                        },
                        body: new URLSearchParams({ message: msg })
                    });
                }
            }
        }
    }

    // 寫入 24 小時紀錄
    await env.DB.prepare(
        "INSERT INTO temperature_logs (temperature, obs_time, status) VALUES (?, ?, ?)"
    ).bind(temp, obsTime, "即時觀測更新 (Cloudflare)").run();

    if (temp >= threshold) {
        // 寫入警報紀錄
        await env.DB.prepare(
            "INSERT INTO alert_logs (threshold, temperature, obs_time, alert_state, status_text) VALUES (?, ?, ?, ?, ?)"
        ).bind(threshold, temp, obsTime, alertStateText, statusText).run();
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
