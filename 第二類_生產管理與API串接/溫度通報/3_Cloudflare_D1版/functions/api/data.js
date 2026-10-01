export async function onRequest(context) {
    const { env } = context;

    const { results: logs } = await env.DB.prepare(
        "SELECT * FROM temperature_logs ORDER BY id DESC LIMIT 144" // 24 hours of 10-minute intervals
    ).all();

    const { results: alerts } = await env.DB.prepare(
        "SELECT * FROM alert_logs ORDER BY id DESC LIMIT 50"
    ).all();

    const { results: configRows } = await env.DB.prepare("SELECT key, value FROM config").all();
    const config = {};
    configRows.forEach(row => { config[row.key] = row.value; });

    return new Response(JSON.stringify({
        logs,
        alerts,
        config
    }), {
        headers: { "content-type": "application/json" }
    });
}
