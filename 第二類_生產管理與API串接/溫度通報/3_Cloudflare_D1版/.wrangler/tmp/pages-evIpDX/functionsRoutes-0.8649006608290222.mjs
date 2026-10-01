import { onRequest as __api_check_js_onRequest } from "C:\\GOOGLE ANGET\\第二類_生產管理與API串接\\溫度通報\\3_Cloudflare_D1版\\functions\\api\\check.js"
import { onRequest as __api_data_js_onRequest } from "C:\\GOOGLE ANGET\\第二類_生產管理與API串接\\溫度通報\\3_Cloudflare_D1版\\functions\\api\\data.js"
import { onRequest as __api_export_js_onRequest } from "C:\\GOOGLE ANGET\\第二類_生產管理與API串接\\溫度通報\\3_Cloudflare_D1版\\functions\\api\\export.js"

export const routes = [
    {
      routePath: "/api/check",
      mountPath: "/api",
      method: "",
      middlewares: [],
      modules: [__api_check_js_onRequest],
    },
  {
      routePath: "/api/data",
      mountPath: "/api",
      method: "",
      middlewares: [],
      modules: [__api_data_js_onRequest],
    },
  {
      routePath: "/api/export",
      mountPath: "/api",
      method: "",
      middlewares: [],
      modules: [__api_export_js_onRequest],
    },
  ]