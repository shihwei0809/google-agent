import { onRequestPost as __api_ai_chat_js_onRequestPost } from "C:\\GOOGLE ANGET\\製程流程圖\\functions\\api\\ai_chat.js"
import { onRequestPost as __api_ai_image_js_onRequestPost } from "C:\\GOOGLE ANGET\\製程流程圖\\functions\\api\\ai_image.js"
import { onRequestGet as __api_load_js_onRequestGet } from "C:\\GOOGLE ANGET\\製程流程圖\\functions\\api\\load.js"
import { onRequestPost as __api_save_js_onRequestPost } from "C:\\GOOGLE ANGET\\製程流程圖\\functions\\api\\save.js"

export const routes = [
    {
      routePath: "/api/ai_chat",
      mountPath: "/api",
      method: "POST",
      middlewares: [],
      modules: [__api_ai_chat_js_onRequestPost],
    },
  {
      routePath: "/api/ai_image",
      mountPath: "/api",
      method: "POST",
      middlewares: [],
      modules: [__api_ai_image_js_onRequestPost],
    },
  {
      routePath: "/api/load",
      mountPath: "/api",
      method: "GET",
      middlewares: [],
      modules: [__api_load_js_onRequestGet],
    },
  {
      routePath: "/api/save",
      mountPath: "/api",
      method: "POST",
      middlewares: [],
      modules: [__api_save_js_onRequestPost],
    },
  ]