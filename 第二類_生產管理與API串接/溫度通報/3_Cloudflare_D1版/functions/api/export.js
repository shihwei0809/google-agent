export async function onRequest(context) {
    const { env } = context;
    const { results: logs } = await env.DB.prepare(
        "SELECT * FROM temperature_logs ORDER BY id ASC"
    ).all();
    return new Response(JSON.stringify(logs), {
        headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
    });
}
