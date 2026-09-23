import { onRequestPost as __api_submit_js_onRequestPost } from "C:\\GOOGLE ANGET\\nitrogen-valve-training\\1_Web_網頁版\\functions\\api\\submit.js"

export const routes = [
    {
      routePath: "/api/submit",
      mountPath: "/api",
      method: "POST",
      middlewares: [],
      modules: [__api_submit_js_onRequestPost],
    },
  ]