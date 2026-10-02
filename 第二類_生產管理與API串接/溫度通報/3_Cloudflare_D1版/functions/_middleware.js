export const onRequest = async (context) => {
  return await context.next();
};

// Cron Trigger Handler
export const scheduled = async (event, env, ctx) => {
  console.log("Cron triggered!");
  // To avoid circular fetch limits or weird routing, we fetch the live domain directly.
  // The live domain is weather-monitor-pwa.pages.dev
  const url = "https://weather-monitor-pwa.pages.dev/api/check";
  const req = new Request(url, { headers: { "User-Agent": "Cloudflare-Cron" } });
  
  try {
    const res = await fetch(req);
    const text = await res.text();
    console.log("Cron trigger check result:", text);
  } catch (e) {
    console.error("Cron trigger failed:", e);
  }
};
