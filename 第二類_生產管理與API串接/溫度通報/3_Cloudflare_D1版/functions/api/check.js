export async function onRequest(context) {
    const { request, env } = context;
    
    // ??閮剖?瑼?
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

    // ?澆 CWA 瘞?情鞈?
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
    
    // Generate Taiwan timestamp
    const twNow = new Date(new Date().toLocaleString("en-US", {timeZone: "Asia/Taipei"}));
    const pad = n => n.toString().padStart(2, '0');
    const twTimestamp = `${twNow.getFullYear()}-${pad(twNow.getMonth()+1)}-${pad(twNow.getDate())} ${pad(twNow.getHours())}:${pad(twNow.getMinutes())}:${pad(twNow.getSeconds())}`;
    
    const obsTime = obsTimeRaw.replace("T", " ").substring(0, 19);
    const temp = parseFloat(s.WeatherElement?.AirTemperature || -99);
    const threshold = parseFloat(config.threshold || "28.0");

    let statusText = "甇?虜 (?芾?璅?";
    let alertStateText = "甇?虜";

    if (temp >= threshold) {
        statusText = "擃澈頞?霅血";
        alertStateText = "擃澈霅血銝?;
        
        // 閫貊 LINE ?
        if (config.line_notify_token) {
            const tokens = config.line_notify_token.split(",");
            const msg = `\n??皞怨郎?晞?渡憓澈摨血歇??${temp}簞C嚗歇頞身摰??${threshold}簞C嚗n閫皜祆???${obsTime}`;
            
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

    // 撖怠 24 撠?蝝??(?Ⅱ?? timestamp ?箏?????
    // 防止重複觸發 (防呆機制)
    const existing = await env.DB.prepare("SELECT id FROM temperature_logs WHERE obs_time = ?").bind(obsTime).first();
    if (existing) {
        return new Response(JSON.stringify({status: "skipped", reason: "Data for this obs_time already exists"}), {
            headers: { "content-type": "application/json" }
        });
    }

    await env.DB.prepare(
        "INSERT INTO temperature_logs (timestamp, temperature, obs_time, status) VALUES (?, ?, ?, ?)"
    ).bind(twTimestamp, temp, obsTime, "?單?閫皜祆??(Cloudflare)").run();

    if (temp >= threshold) {
        // 撖怠霅血蝝??
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

