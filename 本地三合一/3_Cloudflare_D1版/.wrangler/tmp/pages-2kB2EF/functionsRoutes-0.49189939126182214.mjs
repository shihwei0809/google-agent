import { onRequestPost as __api_save_js_onRequestPost } from "C:\\GOOGLE ANGET\\本地三合一\\3_Cloudflare_D1版\\functions\\api\\save.js"

export const routes = [
    {
      routePath: "/api/save",
      mountPath: "/api",
      method: "POST",
      middlewares: [],
      modules: [__api_save_js_onRequestPost],
    },
  ]