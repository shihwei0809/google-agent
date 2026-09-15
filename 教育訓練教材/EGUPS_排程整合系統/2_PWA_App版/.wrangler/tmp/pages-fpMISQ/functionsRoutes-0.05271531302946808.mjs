import { onRequestPost as __api_archive_js_onRequestPost } from "D:\\GOOGLE ANGET\\教育訓練教材\\EGUPS_排程整合系統\\2_PWA_App版\\functions\\api\\archive.js"
import { onRequestGet as __api_data_js_onRequestGet } from "D:\\GOOGLE ANGET\\教育訓練教材\\EGUPS_排程整合系統\\2_PWA_App版\\functions\\api\\data.js"
import { onRequestPost as __api_save_js_onRequestPost } from "D:\\GOOGLE ANGET\\教育訓練教材\\EGUPS_排程整合系統\\2_PWA_App版\\functions\\api\\save.js"

export const routes = [
    {
      routePath: "/api/archive",
      mountPath: "/api",
      method: "POST",
      middlewares: [],
      modules: [__api_archive_js_onRequestPost],
    },
  {
      routePath: "/api/data",
      mountPath: "/api",
      method: "GET",
      middlewares: [],
      modules: [__api_data_js_onRequestGet],
    },
  {
      routePath: "/api/save",
      mountPath: "/api",
      method: "POST",
      middlewares: [],
      modules: [__api_save_js_onRequestPost],
    },
  ]