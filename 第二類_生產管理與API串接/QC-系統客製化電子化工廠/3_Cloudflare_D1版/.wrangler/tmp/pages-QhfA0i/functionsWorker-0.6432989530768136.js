var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// api/index.js
async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  if (request.method === "OPTIONS") return new Response(null, { headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type" } });
  const h = { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" };
  try {
    let action = url.searchParams.get("action");
    let payload = null;
    if (request.method === "POST") {
      try {
        payload = await request.json();
        action = payload.action || action;
      } catch (e) {
      }
    }
    if (action === "verifyLogin" && request.method === "POST") {
      const row = await env.DB.prepare("SELECT username, role FROM Accounts WHERE username = ? AND password_hash = ?").bind(payload.username, payload.password).first();
      if (row) return new Response(JSON.stringify({ success: true, username: row.username, role: row.role }), { headers: h });
      else return new Response(JSON.stringify({ error: "Invalid credentials" }), { headers: h, status: 401 });
    }
    if (action === "getConfig") {
      const { results } = await env.DB.prepare("SELECT * FROM System_Config").all();
      let configMap = {};
      results.forEach((r) => {
        configMap[r.config_key] = r.config_value;
      });
      return new Response(JSON.stringify(configMap), { headers: h });
    }
    if (action === "fixDatabase") {
      await env.DB.prepare("DELETE FROM System_Config").run();
      const stmt = env.DB.prepare("INSERT INTO System_Config (config_key, config_value) VALUES (?, ?)");
      const defaults = [
        ["QC_PIN", "8888"],
        ["TEAMS_MANAGER_WEBHOOK", ""],
        ["TEAMS_WEBHOOK_\u8CC7\u6750\u8AB2", ""],
        ["TEAMS_WEBHOOK_\u4E8C\u90E8\u4E00\u8AB2", ""],
        ["TEAMS_WEBHOOK_\u4E8C\u90E8\u4E8C\u8AB2", ""],
        ["TEAMS_WEBHOOK_\u4E00\u90E8\u4E00\u8AB2", ""],
        ["TEAMS_WEBHOOK_\u4E00\u90E8\u4E8C\u8AB2", ""],
        ["PWA_URL", "https://google-agent.pages.dev/qc-system"],
        ["OPTIONS_FLOW_TYPES", "\u51FA\u8CA8, \u9032\u6599, \u88DC\u6599, \u59D4\u8A17"],
        ["OPTIONS_GRADES", "\u5DE5\u696D\u7D1A, \u96FB\u5B50\u7D1A, IF"],
        ["OPTIONS_DEPTS", "\u8CC7\u6750\u8AB2, \u4E8C\u90E8\u4E00\u8AB2, \u4E8C\u90E8\u4E8C\u8AB2, \u4E00\u90E8\u4E00\u8AB2, \u4E00\u90E8\u4E8C\u8AB2"],
        ["OPTIONS_PRODUCTS", "IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR"],
        ["OPTIONS_JUDGE_RESULTS", "PASS:\u5408\u683C\u653E\u884C, FAIL:\u4E0D\u5408\u683C\u9000\u56DE, \u9700\u7279\u63A1:\u4E0D\u7B26\u5408\u5167\u63A7\u9700\u7279\u63A1"],
        ["OPTIONS_PRODUCT_GRADES_MAP", "EBR-P1R:\u96FB\u5B50\u7D1A, IPAUPS:UPS"]
      ];
      await env.DB.batch(defaults.map((d) => stmt.bind(d[0], d[1])));
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "updateConfig" && request.method === "POST") {
      const configs = payload.configs || {};
      for (const key of Object.keys(configs)) await env.DB.prepare("INSERT INTO System_Config (config_key, config_value) VALUES (?, ?) ON CONFLICT(config_key) DO UPDATE SET config_value=excluded.config_value").bind(key, configs[key]).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "getAccounts") {
      const { results } = await env.DB.prepare("SELECT id, username, role, created_at FROM Accounts").all();
      return new Response(JSON.stringify({ success: true, count: results.length, data: results }), { headers: h });
    }
    if (action === "createAccount" && request.method === "POST") {
      await env.DB.prepare("INSERT INTO Accounts (username, password_hash, role) VALUES (?, ?, ?)").bind(payload.username, payload.password, payload.role || "user").run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "changePassword" && request.method === "POST") {
      await env.DB.prepare("UPDATE Accounts SET password_hash = ? WHERE id = ?").bind(payload.newPassword, payload.id).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "deleteAccount" && request.method === "POST") {
      await env.DB.prepare("DELETE FROM Accounts WHERE id = ?").bind(payload.id).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "getSamples") {
      const { results } = await env.DB.prepare("SELECT * FROM QC_Samples ORDER BY createdAt DESC LIMIT 100").all();
      return new Response(JSON.stringify(results), { headers: h });
    }
    if ((action === "submitSample" || action === "createSample") && request.method === "POST") {
      const data = payload.payload || payload;
      const { id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, remark } = data;
      await env.DB.prepare("ALTER TABLE QC_Samples ADD COLUMN remark TEXT").run().catch((e) => {
      });
      const s_status = data.status || "pending";
      const s_result = data.qcResult || null;
      const s_note = data.qcNote || null;
      const s_approver = data.qcApprover || null;
      const s_compAt = s_status === "completed" ? data.completedAt || (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").substring(0, 19) : null;
      await env.DB.prepare("INSERT INTO QC_Samples (id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, remark, status, qcResult, qcNote, qcApprover, completedAt, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+8 hours'))").bind(id || null, barcode || null, productName || null, tankNo || null, customer || null, quantity || null, flowType || null, dept || null, requester || null, grade || null, remark || null, s_status, s_result, s_note, s_approver, s_compAt).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "completeSample" && request.method === "POST") {
      const { id, result, note, pin, approver } = payload;
      const { results: cfgResults } = await env.DB.prepare("SELECT * FROM System_Config").all();
      let configMap = {};
      cfgResults.forEach((r) => {
        configMap[r.config_key] = r.config_value;
      });
      const sample = await env.DB.prepare("SELECT * FROM QC_Samples WHERE id = ?").bind(id).first();
      if (!sample) {
        return new Response(JSON.stringify({ success: false, error: "\u627E\u4E0D\u5230\u8A72\u6A23\u54C1" }), { headers: h });
      }
      let status = "completed";
      if (result === "FAIL" || result === "\u9700\u7279\u63A1") status = "failed";
      let finalNote = note;
      if (result === "\u7279\u63A1" && sample.qcResult === "\u9700\u7279\u63A1") {
        finalNote = `[\u521D\u9A57:${sample.qcApprover}] ${sample.qcNote || ""}
[\u7279\u63A1:${approver}] ${note}`;
      }
      let completedAt = sample.completedAt || new Date((/* @__PURE__ */ new Date()).getTime() + 8 * 60 * 60 * 1e3).toISOString().replace("T", " ").substring(0, 19);
      await env.DB.prepare("UPDATE QC_Samples SET status = ?, qcResult = ?, qcNote = ?, qcApprover = ?, completedAt = ? WHERE id = ?").bind(status, result, finalNote, approver || "QC", completedAt, id).run();
      if (result === "FAIL") {
        const newId = crypto.randomUUID();
        const parentId = sample.parentId || sample.id;
        const round = parseInt(sample.round || 1) + 1;
        await env.DB.prepare(`
          INSERT INTO QC_Samples (id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, parentId, round, status, isAlerted)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0)
        `).bind(newId, sample.barcode, sample.productName, sample.tankNo, sample.customer, sample.quantity, sample.flowType, sample.dept, sample.requester, sample.grade, parentId, round).run();
      }
      const deptWebhook = configMap["TEAMS_WEBHOOK_" + sample.dept];
      const managerWebhook = configMap["TEAMS_MANAGER_WEBHOOK"];
      const isPass = status === "completed" || result === "PASS" || result === "\u7279\u63A1";
      let resultTitle = result;
      if (result === "FAIL") resultTitle = "\u26D4 FAIL (\u5DF2\u81EA\u52D5\u7522\u751F\u4E0B\u4E00\u6B21\u91CD\u9001\u6392\u7A0B)";
      else if (result === "\u9700\u7279\u63A1") resultTitle = "\u26A0\uFE0F \u4E0D\u7B26\u5408\u5167\u63A7 (\u7B49\u5F85\u4E3B\u7BA1\u5BE9\u6838\u7279\u63A1)";
      else if (result === "\u7279\u63A1") resultTitle = "\u{1F6A8} \u7D93\u4E3B\u7BA1\u7279\u63A1\u653E\u884C";
      const title = isPass ? `\u2705\u3010\u6AA2\u9A57\u5B8C\u6210\u3011${sample.productName}` : `\u274C\u3010\u6AA2\u9A57\u672A\u901A\u904E\u3011${sample.productName}`;
      const color = isPass ? "28a745" : "dc3545";
      const actualApprover = approver || "QC";
      const facts = [
        { name: "\u6AA2\u9A57\u7D50\u679C", value: `**${resultTitle}**` },
        { name: "\u5BE9\u6838\u4EBA\u54E1", value: actualApprover },
        { name: "\u55AE\u865F", value: sample.barcode || "-" },
        { name: "\u69FD\u865F/\u8ECA\u724C", value: `${sample.tankNo || "-"} / ${sample.customer || "-"}` },
        { name: "\u6AA2\u9A57\u5099\u8A3B", value: finalNote || "\u7121" }
      ];
      const msg = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": title,
        "sections": [{ "activityTitle": title, "activitySubtitle": "QC \u54C1\u7BA1\u7CFB\u7D71", "facts": facts }]
      };
      const sendWebhook = /* @__PURE__ */ __name(async (url2) => {
        if (!url2) return;
        try {
          await fetch(url2, { method: "POST", body: JSON.stringify(msg) });
        } catch (e) {
        }
      }, "sendWebhook");
      await Promise.all([sendWebhook(deptWebhook), sendWebhook(managerWebhook)]);
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "updateSample" && request.method === "POST") {
      const { id, result, note, approver } = payload;
      let status = "completed";
      if (result === "\u9000\u4EF6" || result === "\u91CD\u53D6\u6A23") status = "failed";
      await env.DB.prepare("UPDATE QC_Samples SET status = ?, qcResult = ?, qcNote = ?, qcApprover = ?, completedAt = datetime('now', '+8 hours') WHERE id = ?").bind(status || null, result || null, note || null, approver || null, id || null).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "updatePhotoUrl" && request.method === "POST") {
      await env.DB.prepare("UPDATE QC_Samples SET photoUrl = ? WHERE id = ?").bind(payload.url, payload.id).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "deleteSample" && request.method === "POST") {
      await env.DB.prepare("DELETE FROM QC_Samples WHERE id = ?").bind(payload.id).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "saveOrders" && request.method === "POST") {
      await env.DB.prepare("CREATE TABLE IF NOT EXISTS T100_Orders (id INTEGER PRIMARY KEY AUTOINCREMENT, doc_no TEXT, flowType TEXT, productName TEXT, tankNo TEXT, container TEXT, quantity TEXT, customer TEXT, grade TEXT, targetDate TEXT, date TEXT, time TEXT, note TEXT, createdAt DATETIME DEFAULT CURRENT_TIMESTAMP)").run();
      await env.DB.prepare("ALTER TABLE T100_Orders ADD COLUMN date TEXT").run().catch((e) => {
      });
      await env.DB.prepare("ALTER TABLE T100_Orders ADD COLUMN time TEXT").run().catch((e) => {
      });
      await env.DB.prepare("ALTER TABLE T100_Orders ADD COLUMN note TEXT").run().catch((e) => {
      });
      await env.DB.prepare("DELETE FROM T100_Orders").run();
      const orders = payload.orders || [];
      if (orders.length > 0) {
        const stmt = env.DB.prepare("INSERT INTO T100_Orders (doc_no, flowType, productName, tankNo, container, quantity, customer, grade, targetDate, date, time, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
        const batchStmts = orders.map((o) => stmt.bind(o.doc_no || "", o.flowType || "", o.productName || "", o.tankNo || "", o.container || "", o.quantity || "", o.customer || "", o.grade || "", o.targetDate || "", o.date || "", o.time || "", o.note || ""));
        await env.DB.batch(batchStmts);
      }
      return new Response(JSON.stringify({ success: true, count: orders.length, importedAt: (/* @__PURE__ */ new Date()).toISOString() }), { headers: h });
    }
    if (action === "getOrders") {
      await env.DB.prepare("CREATE TABLE IF NOT EXISTS T100_Orders (id INTEGER PRIMARY KEY AUTOINCREMENT, doc_no TEXT, flowType TEXT, productName TEXT, tankNo TEXT, container TEXT, quantity TEXT, customer TEXT, grade TEXT, targetDate TEXT, date TEXT, time TEXT, note TEXT, createdAt DATETIME DEFAULT CURRENT_TIMESTAMP)").run();
      const { results } = await env.DB.prepare("SELECT * FROM T100_Orders ORDER BY targetDate DESC, createdAt DESC LIMIT 200").all();
      return new Response(JSON.stringify({ success: true, count: results.length, orders: results }), { headers: h });
    }
    if (action === "checkOverdue") {
      const { results: cfgResults } = await env.DB.prepare("SELECT * FROM System_Config").all();
      let configMap = {};
      cfgResults.forEach((r) => {
        configMap[r.config_key] = r.config_value;
      });
      const managerWebhook = configMap["TEAMS_MANAGER_WEBHOOK"];
      const { results: samples } = await env.DB.prepare(`
        SELECT *, (julianday('now', '+8 hours') - julianday(createdAt)) * 24 as diffHours
        FROM QC_Samples 
        WHERE status = 'pending'
      `).all();
      let alertedCount = 0;
      let logs = [];
      for (const s of samples) {
        let alertLevel = 0;
        let alertTitle = "";
        if (s.diffHours >= 4 && (s.isAlerted || 0) < 2) {
          alertLevel = 2;
          alertTitle = `\u{1F534}\u3010QC \u56B4\u91CD\u8D85\u6642\u8B66\u544A\u3011\u7B49\u5F85\u6AA2\u9A57\u5DF2\u9054 ${s.diffHours.toFixed(1)} \u5C0F\u6642 (\u8D85\u904E4\u5C0F\u6642)`;
        } else if (s.diffHours >= 2 && s.diffHours < 4 && (s.isAlerted || 0) < 1) {
          alertLevel = 1;
          alertTitle = `\u26A0\uFE0F\u3010QC \u6AA2\u9A57\u8D85\u6642\u8B66\u544A\u3011\u7B49\u5F85\u6AA2\u9A57\u5DF2\u9054 ${s.diffHours.toFixed(1)} \u5C0F\u6642 (\u8D85\u904E2\u5C0F\u6642)`;
        }
        if (alertLevel > 0) {
          const cardPayload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": alertLevel === 2 ? "990000" : "D9381E",
            "summary": alertTitle,
            "sections": [{
              "activityTitle": alertTitle,
              "activitySubtitle": `\u6A23\u54C1\u5F85\u6AA2\u9A57\u5DF2\u8D85\u904E ${alertLevel === 2 ? "4" : "2"} \u5C0F\u6642\u672A\u5224\u5B9A\uFF0C\u8ACB\u76E1\u901F\u8655\u7406\uFF01`,
              "facts": [
                { "name": "\u{1F3E2} \u6A23\u54C1\u55AE\u4F4D", "value": `${s.dept} (\u9001\u6A23\u4EBA: ${s.requester || "\u7121"})` },
                { "name": "\u{1F9EA} \u6AA2\u9A57\u54C1\u540D", "value": s.productName },
                { "name": "\u{1F69A} \u69FD\u865F / \u8ECA\u724C", "value": `${s.tankNo || "-"} / ${s.customer || "-"}` },
                { "name": "\u{1F3F7}\uFE0F \u689D\u78BC\u8CC7\u8A0A", "value": s.barcode || "-" },
                { "name": "\u23F0 \u9001\u6A23\u6642\u9593", "value": s.createdAt }
              ],
              "markdown": true
            }]
          };
          const urls = [];
          if (managerWebhook) urls.push(managerWebhook);
          if (s.dept && configMap["TEAMS_WEBHOOK_" + s.dept]) urls.push(configMap["TEAMS_WEBHOOK_" + s.dept]);
          for (const url2 of urls) {
            if (!url2) continue;
            try {
              await fetch(url2, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(cardPayload)
              });
            } catch (e) {
              logs.push(`Failed to send to ${s.dept}: ${e.message}`);
            }
          }
          await env.DB.prepare("UPDATE QC_Samples SET isAlerted = ? WHERE id = ?").bind(alertLevel, s.id).run();
          alertedCount++;
          logs.push(`Alerted level ${alertLevel} for ${s.barcode}`);
        }
      }
      return new Response(JSON.stringify({ success: true, alertedCount, logs }), { headers: h });
    }
    if (action === "returnForResample" && request.method === "POST") {
      const { id, note, pin } = payload;
      const pinCfg = await env.DB.prepare("SELECT config_value FROM System_Config WHERE config_key = 'QC_PIN'").first();
      const sysPin = pinCfg ? pinCfg.config_value : "8888";
      if (pin !== sysPin) {
        return new Response(JSON.stringify({ success: false, error: "\u7CFB\u7D71\u9810\u8A2D\u5BC6\u78BC\u932F\u8AA4\uFF0C\u8ACB\u91CD\u65B0\u8F38\u5165" }), { headers: h });
      }
      const sample = await env.DB.prepare("SELECT * FROM QC_Samples WHERE id = ?").bind(id).first();
      if (!sample) {
        return new Response(JSON.stringify({ success: false, error: "\u627E\u4E0D\u5230\u8A72\u7B46\u6A23\u54C1\u7D00\u9304" }), { headers: h });
      }
      const nowStr = new Date((/* @__PURE__ */ new Date()).getTime() + 8 * 60 * 60 * 1e3).toISOString().replace("T", " ").substring(0, 19);
      await env.DB.prepare(`
        UPDATE QC_Samples 
        SET status = 'failed', qcResult = 'FAIL', qcNote = ?, completedAt = ? 
        WHERE id = ?
      `).bind(note || "\u6AA2\u9A57\u5224\u5B9A\u4E0D\u5408\u683C\uFF0C\u9000\u56DE\u91CD\u65B0\u9001\u6A23", nowStr, id).run();
      const newId = crypto.randomUUID();
      const parentId = sample.parentId || sample.id;
      const round = parseInt(sample.round || 1) + 1;
      await env.DB.prepare(`
        INSERT INTO QC_Samples (id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, parentId, round, status, isAlerted, createdAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, datetime('now', '+8 hours'))
      `).bind(newId, sample.barcode, sample.productName, sample.tankNo, sample.customer, sample.quantity, sample.flowType, sample.dept, sample.requester, sample.grade, parentId, round).run();
      return new Response(JSON.stringify({ success: true, round, newId }), { headers: h });
    }
    if (action === "getEmployees") {
      const { results } = await env.DB.prepare("SELECT * FROM Employees").all();
      return new Response(JSON.stringify({ success: true, data: results }), { headers: h });
    }
    return new Response(JSON.stringify({ error: "Unknown action" }), { headers: h, status: 400 });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), { headers: h, status: 500 });
  }
}
__name(onRequest, "onRequest");

// ../.wrangler/tmp/pages-QhfA0i/functionsRoutes-0.33900307295490917.mjs
var routes = [
  {
    routePath: "/api",
    mountPath: "/api",
    method: "",
    middlewares: [],
    modules: [onRequest]
  }
];

// ../../../../../Users/C606/AppData/Roaming/npm/node_modules/wrangler/node_modules/path-to-regexp/dist.es2015/index.js
function lexer(str) {
  var tokens = [];
  var i = 0;
  while (i < str.length) {
    var char = str[i];
    if (char === "*" || char === "+" || char === "?") {
      tokens.push({ type: "MODIFIER", index: i, value: str[i++] });
      continue;
    }
    if (char === "\\") {
      tokens.push({ type: "ESCAPED_CHAR", index: i++, value: str[i++] });
      continue;
    }
    if (char === "{") {
      tokens.push({ type: "OPEN", index: i, value: str[i++] });
      continue;
    }
    if (char === "}") {
      tokens.push({ type: "CLOSE", index: i, value: str[i++] });
      continue;
    }
    if (char === ":") {
      var name = "";
      var j = i + 1;
      while (j < str.length) {
        var code = str.charCodeAt(j);
        if (
          // `0-9`
          code >= 48 && code <= 57 || // `A-Z`
          code >= 65 && code <= 90 || // `a-z`
          code >= 97 && code <= 122 || // `_`
          code === 95
        ) {
          name += str[j++];
          continue;
        }
        break;
      }
      if (!name)
        throw new TypeError("Missing parameter name at ".concat(i));
      tokens.push({ type: "NAME", index: i, value: name });
      i = j;
      continue;
    }
    if (char === "(") {
      var count = 1;
      var pattern = "";
      var j = i + 1;
      if (str[j] === "?") {
        throw new TypeError('Pattern cannot start with "?" at '.concat(j));
      }
      while (j < str.length) {
        if (str[j] === "\\") {
          pattern += str[j++] + str[j++];
          continue;
        }
        if (str[j] === ")") {
          count--;
          if (count === 0) {
            j++;
            break;
          }
        } else if (str[j] === "(") {
          count++;
          if (str[j + 1] !== "?") {
            throw new TypeError("Capturing groups are not allowed at ".concat(j));
          }
        }
        pattern += str[j++];
      }
      if (count)
        throw new TypeError("Unbalanced pattern at ".concat(i));
      if (!pattern)
        throw new TypeError("Missing pattern at ".concat(i));
      tokens.push({ type: "PATTERN", index: i, value: pattern });
      i = j;
      continue;
    }
    tokens.push({ type: "CHAR", index: i, value: str[i++] });
  }
  tokens.push({ type: "END", index: i, value: "" });
  return tokens;
}
__name(lexer, "lexer");
function parse(str, options) {
  if (options === void 0) {
    options = {};
  }
  var tokens = lexer(str);
  var _a = options.prefixes, prefixes = _a === void 0 ? "./" : _a, _b = options.delimiter, delimiter = _b === void 0 ? "/#?" : _b;
  var result = [];
  var key = 0;
  var i = 0;
  var path = "";
  var tryConsume = /* @__PURE__ */ __name(function(type) {
    if (i < tokens.length && tokens[i].type === type)
      return tokens[i++].value;
  }, "tryConsume");
  var mustConsume = /* @__PURE__ */ __name(function(type) {
    var value2 = tryConsume(type);
    if (value2 !== void 0)
      return value2;
    var _a2 = tokens[i], nextType = _a2.type, index = _a2.index;
    throw new TypeError("Unexpected ".concat(nextType, " at ").concat(index, ", expected ").concat(type));
  }, "mustConsume");
  var consumeText = /* @__PURE__ */ __name(function() {
    var result2 = "";
    var value2;
    while (value2 = tryConsume("CHAR") || tryConsume("ESCAPED_CHAR")) {
      result2 += value2;
    }
    return result2;
  }, "consumeText");
  var isSafe = /* @__PURE__ */ __name(function(value2) {
    for (var _i = 0, delimiter_1 = delimiter; _i < delimiter_1.length; _i++) {
      var char2 = delimiter_1[_i];
      if (value2.indexOf(char2) > -1)
        return true;
    }
    return false;
  }, "isSafe");
  var safePattern = /* @__PURE__ */ __name(function(prefix2) {
    var prev = result[result.length - 1];
    var prevText = prefix2 || (prev && typeof prev === "string" ? prev : "");
    if (prev && !prevText) {
      throw new TypeError('Must have text between two parameters, missing text after "'.concat(prev.name, '"'));
    }
    if (!prevText || isSafe(prevText))
      return "[^".concat(escapeString(delimiter), "]+?");
    return "(?:(?!".concat(escapeString(prevText), ")[^").concat(escapeString(delimiter), "])+?");
  }, "safePattern");
  while (i < tokens.length) {
    var char = tryConsume("CHAR");
    var name = tryConsume("NAME");
    var pattern = tryConsume("PATTERN");
    if (name || pattern) {
      var prefix = char || "";
      if (prefixes.indexOf(prefix) === -1) {
        path += prefix;
        prefix = "";
      }
      if (path) {
        result.push(path);
        path = "";
      }
      result.push({
        name: name || key++,
        prefix,
        suffix: "",
        pattern: pattern || safePattern(prefix),
        modifier: tryConsume("MODIFIER") || ""
      });
      continue;
    }
    var value = char || tryConsume("ESCAPED_CHAR");
    if (value) {
      path += value;
      continue;
    }
    if (path) {
      result.push(path);
      path = "";
    }
    var open = tryConsume("OPEN");
    if (open) {
      var prefix = consumeText();
      var name_1 = tryConsume("NAME") || "";
      var pattern_1 = tryConsume("PATTERN") || "";
      var suffix = consumeText();
      mustConsume("CLOSE");
      result.push({
        name: name_1 || (pattern_1 ? key++ : ""),
        pattern: name_1 && !pattern_1 ? safePattern(prefix) : pattern_1,
        prefix,
        suffix,
        modifier: tryConsume("MODIFIER") || ""
      });
      continue;
    }
    mustConsume("END");
  }
  return result;
}
__name(parse, "parse");
function match(str, options) {
  var keys = [];
  var re = pathToRegexp(str, keys, options);
  return regexpToFunction(re, keys, options);
}
__name(match, "match");
function regexpToFunction(re, keys, options) {
  if (options === void 0) {
    options = {};
  }
  var _a = options.decode, decode = _a === void 0 ? function(x) {
    return x;
  } : _a;
  return function(pathname) {
    var m = re.exec(pathname);
    if (!m)
      return false;
    var path = m[0], index = m.index;
    var params = /* @__PURE__ */ Object.create(null);
    var _loop_1 = /* @__PURE__ */ __name(function(i2) {
      if (m[i2] === void 0)
        return "continue";
      var key = keys[i2 - 1];
      if (key.modifier === "*" || key.modifier === "+") {
        params[key.name] = m[i2].split(key.prefix + key.suffix).map(function(value) {
          return decode(value, key);
        });
      } else {
        params[key.name] = decode(m[i2], key);
      }
    }, "_loop_1");
    for (var i = 1; i < m.length; i++) {
      _loop_1(i);
    }
    return { path, index, params };
  };
}
__name(regexpToFunction, "regexpToFunction");
function escapeString(str) {
  return str.replace(/([.+*?=^!:${}()[\]|/\\])/g, "\\$1");
}
__name(escapeString, "escapeString");
function flags(options) {
  return options && options.sensitive ? "" : "i";
}
__name(flags, "flags");
function regexpToRegexp(path, keys) {
  if (!keys)
    return path;
  var groupsRegex = /\((?:\?<(.*?)>)?(?!\?)/g;
  var index = 0;
  var execResult = groupsRegex.exec(path.source);
  while (execResult) {
    keys.push({
      // Use parenthesized substring match if available, index otherwise
      name: execResult[1] || index++,
      prefix: "",
      suffix: "",
      modifier: "",
      pattern: ""
    });
    execResult = groupsRegex.exec(path.source);
  }
  return path;
}
__name(regexpToRegexp, "regexpToRegexp");
function arrayToRegexp(paths, keys, options) {
  var parts = paths.map(function(path) {
    return pathToRegexp(path, keys, options).source;
  });
  return new RegExp("(?:".concat(parts.join("|"), ")"), flags(options));
}
__name(arrayToRegexp, "arrayToRegexp");
function stringToRegexp(path, keys, options) {
  return tokensToRegexp(parse(path, options), keys, options);
}
__name(stringToRegexp, "stringToRegexp");
function tokensToRegexp(tokens, keys, options) {
  if (options === void 0) {
    options = {};
  }
  var _a = options.strict, strict = _a === void 0 ? false : _a, _b = options.start, start = _b === void 0 ? true : _b, _c = options.end, end = _c === void 0 ? true : _c, _d = options.encode, encode = _d === void 0 ? function(x) {
    return x;
  } : _d, _e = options.delimiter, delimiter = _e === void 0 ? "/#?" : _e, _f = options.endsWith, endsWith = _f === void 0 ? "" : _f;
  var endsWithRe = "[".concat(escapeString(endsWith), "]|$");
  var delimiterRe = "[".concat(escapeString(delimiter), "]");
  var route = start ? "^" : "";
  for (var _i = 0, tokens_1 = tokens; _i < tokens_1.length; _i++) {
    var token = tokens_1[_i];
    if (typeof token === "string") {
      route += escapeString(encode(token));
    } else {
      var prefix = escapeString(encode(token.prefix));
      var suffix = escapeString(encode(token.suffix));
      if (token.pattern) {
        if (keys)
          keys.push(token);
        if (prefix || suffix) {
          if (token.modifier === "+" || token.modifier === "*") {
            var mod = token.modifier === "*" ? "?" : "";
            route += "(?:".concat(prefix, "((?:").concat(token.pattern, ")(?:").concat(suffix).concat(prefix, "(?:").concat(token.pattern, "))*)").concat(suffix, ")").concat(mod);
          } else {
            route += "(?:".concat(prefix, "(").concat(token.pattern, ")").concat(suffix, ")").concat(token.modifier);
          }
        } else {
          if (token.modifier === "+" || token.modifier === "*") {
            throw new TypeError('Can not repeat "'.concat(token.name, '" without a prefix and suffix'));
          }
          route += "(".concat(token.pattern, ")").concat(token.modifier);
        }
      } else {
        route += "(?:".concat(prefix).concat(suffix, ")").concat(token.modifier);
      }
    }
  }
  if (end) {
    if (!strict)
      route += "".concat(delimiterRe, "?");
    route += !options.endsWith ? "$" : "(?=".concat(endsWithRe, ")");
  } else {
    var endToken = tokens[tokens.length - 1];
    var isEndDelimited = typeof endToken === "string" ? delimiterRe.indexOf(endToken[endToken.length - 1]) > -1 : endToken === void 0;
    if (!strict) {
      route += "(?:".concat(delimiterRe, "(?=").concat(endsWithRe, "))?");
    }
    if (!isEndDelimited) {
      route += "(?=".concat(delimiterRe, "|").concat(endsWithRe, ")");
    }
  }
  return new RegExp(route, flags(options));
}
__name(tokensToRegexp, "tokensToRegexp");
function pathToRegexp(path, keys, options) {
  if (path instanceof RegExp)
    return regexpToRegexp(path, keys);
  if (Array.isArray(path))
    return arrayToRegexp(path, keys, options);
  return stringToRegexp(path, keys, options);
}
__name(pathToRegexp, "pathToRegexp");

// ../../../../../Users/C606/AppData/Roaming/npm/node_modules/wrangler/templates/pages-template-worker.ts
var escapeRegex = /[.+?^${}()|[\]\\]/g;
function* executeRequest(request) {
  const requestPath = new URL(request.url).pathname;
  for (const route of [...routes].reverse()) {
    if (route.method && route.method !== request.method) {
      continue;
    }
    const routeMatcher = match(route.routePath.replace(escapeRegex, "\\$&"), {
      end: false
    });
    const mountMatcher = match(route.mountPath.replace(escapeRegex, "\\$&"), {
      end: false
    });
    const matchResult = routeMatcher(requestPath);
    const mountMatchResult = mountMatcher(requestPath);
    if (matchResult && mountMatchResult) {
      for (const handler of route.middlewares.flat()) {
        yield {
          handler,
          params: matchResult.params,
          path: mountMatchResult.path
        };
      }
    }
  }
  for (const route of routes) {
    if (route.method && route.method !== request.method) {
      continue;
    }
    const routeMatcher = match(route.routePath.replace(escapeRegex, "\\$&"), {
      end: true
    });
    const mountMatcher = match(route.mountPath.replace(escapeRegex, "\\$&"), {
      end: false
    });
    const matchResult = routeMatcher(requestPath);
    const mountMatchResult = mountMatcher(requestPath);
    if (matchResult && mountMatchResult && route.modules.length) {
      for (const handler of route.modules.flat()) {
        yield {
          handler,
          params: matchResult.params,
          path: matchResult.path
        };
      }
      break;
    }
  }
}
__name(executeRequest, "executeRequest");
var pages_template_worker_default = {
  async fetch(originalRequest, env, workerContext) {
    let request = originalRequest;
    const handlerIterator = executeRequest(request);
    let data = {};
    let isFailOpen = false;
    const next = /* @__PURE__ */ __name(async (input, init) => {
      if (input !== void 0) {
        let url = input;
        if (typeof input === "string") {
          url = new URL(input, request.url).toString();
        }
        request = new Request(url, init);
      }
      const result = handlerIterator.next();
      if (result.done === false) {
        const { handler, params, path } = result.value;
        const context = {
          request: new Request(request.clone()),
          functionPath: path,
          next,
          params,
          get data() {
            return data;
          },
          set data(value) {
            if (typeof value !== "object" || value === null) {
              throw new Error("context.data must be an object");
            }
            data = value;
          },
          env,
          waitUntil: workerContext.waitUntil.bind(workerContext),
          passThroughOnException: /* @__PURE__ */ __name(() => {
            isFailOpen = true;
          }, "passThroughOnException")
        };
        const response = await handler(context);
        if (!(response instanceof Response)) {
          throw new Error("Your Pages function should return a Response");
        }
        return cloneResponse(response);
      } else if ("ASSETS") {
        const response = await env["ASSETS"].fetch(request);
        return cloneResponse(response);
      } else {
        const response = await fetch(request);
        return cloneResponse(response);
      }
    }, "next");
    try {
      return await next();
    } catch (error) {
      if (isFailOpen) {
        const response = await env["ASSETS"].fetch(request);
        return cloneResponse(response);
      }
      throw error;
    }
  }
};
var cloneResponse = /* @__PURE__ */ __name((response) => (
  // https://fetch.spec.whatwg.org/#null-body-status
  new Response(
    [101, 204, 205, 304].includes(response.status) ? null : response.body,
    response
  )
), "cloneResponse");
export {
  pages_template_worker_default as default
};
