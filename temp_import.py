2201:                                 elif key == "DeliverDate": date_val = val
2202:                         fname = os.path.basename(filepath)
2203:                         m = re.search(r'\s([A-Za-z0-9]+)_\d+\.csv$', fname, re.IGNORECASE)
2204:                         if m:
2205:                             loc_val = m.group(1)
2206:                         else:
2207:                             parts = fname.split('_')
2208:                             if len(parts) >= 2:
2209:                                 loc_val = parts[-2].split(' ')[-1]
2210:                         po_val = ""
2211:                         if batch_val:
2212:                             norm_d = normalize_date_str(date_val)
2213:                             records.append({
2214:                                 "sheet": "CSV",
2215:                                 "batch": batch_val,
2216:                                 "loc": clean_location_str(loc_val, self.mapping_dict),
2217:                                 "date": norm_d,
2218:                                 "time": "",
2219:                                 "mod_time": "",
2220:                                 "tank": get_tank_from_batch(batch_val)
2221:                             })
2222:                     else:
2223:                         # Standard horizontal CSV
2224:                         batch_col, loc_col, date_col, tank_col, time_col, mod_time_col, po_col = -1, -1, -1, -1, -1, -1, -1
2225:                         start_row = 0
2226:                         for r_idx in range(min(15, len(rows))):
2227:                             row = rows[r_idx]
2228:                             if not row: continue
2229:                             for c_idx, val in enumerate(row):
2230:                                 v = str(val or "").strip().upper()
2231:                                 if batch_col == -1 and any(k in v for k in ["批號", "BATCH", "LOT"]): batch_col = c_idx
2232:                                 if loc_col == -1 and any(k in v for k in ["地點", "指送", "交貨", "到貨地", "送達", "廠區", "LOCATION", "DEST"]): loc_col = c_idx
2233:                                 if date_col == -1 and any(k in v for k in ["到貨日", "出貨日", "出車日", "日期", "DATE"]) and "地" not in v and "點" not in v: date_col = c_idx
2234:                                 if tank_col == -1 and any(k in v for k in ["槽號", "槽車", "TANK"]) and not any(k in v for k in ["日", "期", "時間", "TIME", "DATE", "到廠", "出車", "出貨"]): tank_col = c_idx
2235:                                 if time_col == -1 and any(k in v for k in ["到貨時間", "預計", "時間", "TIME"]) and "修正" not in v: time_col = c_idx
2236:                                 if mod_time_col == -1 and "修正" in v and ("時間" in v or "TIME" in v): mod_time_col = c_idx
2237:                                 if po_col == -1 and any(k in v for k in ["採購單", "PO"]): po_col = c_idx
2238:                                 if po_col == -1 and any(k in v for k in ["採購單", "PO"]): po_col = c_idx
2239:                             if batch_col != -1 and (loc_col != -1 or date_col != -1):
2240:                                 start_row = r_idx + 1
2241:                                 break
2242:                         if batch_col == -1 or loc_col == -1:
2243:                             batch_col, date_col, tank_col, loc_col = 2, 1, 3, 4
2244:                             start_row = 2
2245:                         for r_idx in range(start_row, len(rows)):
2246:                             row = rows[r_idx]
2247:                             if not row: continue
2248:                             def get_c(c): return row[c] if c != -1 and c < len(row) else None
2249:                             b_val = str(get_c(batch_col) or "").strip().upper()
2250:                             l_val = str(get_c(loc_col) or "").strip().upper()
2251:                             d_val = get_c(date_col)
2252:                             t_val = str(get_c(tank_col) or "").strip()
2253:                             origin_val = ""
2254:                             for cell in row:
2255:                                 cs = str(cell or "").strip().upper()
2256:                                 if not origin_val and any(k in cs for k in ["崙尾", "彰濱", "L1", "L2"]):
2257:                                     origin_val = cs
2258:                                     break
2259:                             tm_val = normalize_time_str(get_c(time_col))
2260:                             mt_val = normalize_time_str(get_c(mod_time_col))
2261:                             po_val = str(get_c(po_col) or "").strip()
2262:                             if len(b_val) != 10 or not re.search(r'[0-9]', b_val):
2263:                                 for cell in row:
2264:                                     cs = str(cell or "").strip().upper()
2265:                                     if len(cs) == 10 and re.search(r'[0-9]', cs) and re.search(r'[A-Z]', cs) and "/" not in cs and "-" not in cs:
2266:                                         b_val = cs
2267:                                         break
2268:                             if len(b_val) == 10 and re.search(r'[0-9]', b_val):
2269:                                 is_valid_tank = (
2270:                                     t_val and 
2271:                                     len(t_val) <= 6 and 
2272:                                     not any(c in t_val for c in ["-", "/", ":", " "]) and
2273:                                     not (len(t_val) > 4 and t_val.isdigit())
2274:                                 )
2275:                                 tank_final = t_val if is_valid_tank else get_tank_from_batch(b_val)
2276:                                 clean_l = clean_location_str(l_val, self.mapping_dict)
2277:                                 records.append({
2278:                                     "sheet": "CSV",
2279:                                     "batch": b_val,
2280:                                     "tank": tank_final,
2281:                                     "loc": clean_l,
2282:                                     "long_code": self.mapping_dict.get(clean_l, ""),
2283:                                     "date": normalize_date_str(d_val),
2284:                                     "time": tm_val,
2285:                                     "mod_time": mt_val,
2286:                                 "po": po_val,
2287:                                 "origin": origin_val
2288:                             })
2289:                 else:
2290:                     # 遍歷 Excel 所有分頁 (跨分頁抓取所有有效排程)
2291:                     wb = openpyxl.load_workbook(filepath, data_only=True)
2292:                     sheet_count = len(wb.worksheets)
2293: 
2294:                     for ws in wb.worksheets:
2295:                         sheet_name = ws.title
2296:                         rows = list(ws.iter_rows(values_only=True))
2297:                         if not rows or len(rows) == 0:
2298:                             continue
2299: 
2300:                         # 檢查分頁全域文字是否標記為台積電
2301:                         sheet_has_tsmc = False
2302:                         for r_idx in range(min(5, len(rows))):
2303:                             row_str = " ".join(str(cell or "") for cell in rows[r_idx]).upper()
2304:                             if "TSMC" in row_str or "台積" in row_str:
2305:                                 sheet_has_tsmc = True
2306:                                 break
2307: 
2308:                         # 動態掃描前 15 列尋找標題欄位
2309:                         batch_col = -1
2310:                         loc_col = -1
2311:                         date_col = -1
2312:                         tank_col = -1
2313:                         time_col = -1
2314:                         mod_time_col = -1
2315:                         cust_col = -1
2316:                         po_col = -1
2317:                         start_row = 0
2318: 
2319:                         for r_idx in range(min(15, len(rows))):
2320:                             row = rows[r_idx]
