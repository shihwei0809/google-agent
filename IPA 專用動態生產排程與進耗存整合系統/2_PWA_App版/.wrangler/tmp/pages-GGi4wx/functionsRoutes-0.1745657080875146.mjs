import { onRequestGet as __api_archive_js_onRequestGet } from "C:\\GOOGLE ANGET\\IPA 專用動態生產排程與進耗存整合系統\\2_PWA_App版\\functions\\api\\archive.js"
import { onRequestPost as __api_archive_js_onRequestPost } from "C:\\GOOGLE ANGET\\IPA 專用動態生產排程與進耗存整合系統\\2_PWA_App版\\functions\\api\\archive.js"
import { onRequestGet as __api_data_js_onRequestGet } from "C:\\GOOGLE ANGET\\IPA 專用動態生產排程與進耗存整合系統\\2_PWA_App版\\functions\\api\\data.js"
import { onRequestPost as __api_data_js_onRequestPost } from "C:\\GOOGLE ANGET\\IPA 專用動態生產排程與進耗存整合系統\\2_PWA_App版\\functions\\api\\data.js"

export const routes = [
    {
      routePath: "/api/archive",
      mountPath: "/api",
      method: "GET",
      middlewares: [],
      modules: [__api_archive_js_onRequestGet],
    },
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
      routePath: "/api/data",
      mountPath: "/api",
      method: "POST",
      middlewares: [],
      modules: [__api_data_js_onRequestPost],
    },
  ]