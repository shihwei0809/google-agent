// C50110-INV-02-01 (版別 3.1) 全部 5 張檢點表模板定義
// 支援 3 種通用版型引擎：single_stage (6.1) / dual_compare (6.2, 6.5) / before_after (6.3, 6.4)
window.WI_DEFAULT_TEMPLATES = [
  {
    id: 'tpl-c50110-05',
    groupKey: '6.1',
    shortCode: '6.1',
    category: '進貨入槽',
    layoutType: 'single_stage',
    company: '鴻勝化學科技股份有限公司',
    title: '槽車泵料入儲槽檢查表',
    formCode: 'C50110-INV-02-01(05)',
    wiVersion: 'WI 版別 3.1',
    plants: ['彰濱1廠(線西)', '彰濱2廠(崙尾)'],
    plantDisplayMode: 'checkbox', // 'checkbox' | 'text'
    signers: [
      { key: 'inspector', label: '檢查員', role: 'operator' },
      { key: 'leader', label: '組長', role: 'leader' },
      { key: 'manager', label: '課(副)長', role: 'manager' }
    ],
    footerNote: '檢查結果：正常打"是"，異常打"否"，不適用"＼"劃掉',
    isLatest: true,
    items: [
      { id: 'p1', section: '入料前檢查', name: '車輛鑰匙是否掛放至指定位置', mode: 'yn', normalChoice: '是' },
      { id: 'p2', section: '入料前檢查', name: '槽車之接地線是否接妥(10歐姆以下)', mode: 'yn_num', unit: '歐姆', maxOk: 10, normalChoice: '是' },
      { id: 'p3', section: '入料前檢查', name: '輪檔是否確實放置定位', mode: 'yn', normalChoice: '是' },
      { id: 'p4', section: '入料前檢查', name: '放置三角錐於槽車前後及是否備妥手提滅火器', mode: 'yn', normalChoice: '是' },
      { id: 'p5', section: '入料前檢查', name: '卸貨區2公尺內是否有影響作業安全之事物', mode: 'yn', normalChoice: '否' },
      { id: 'p6', section: '入料前檢查', name: '消防系統是否待命中', mode: 'yn', normalChoice: '是' },
      { id: 'p7', section: '入料前檢查', name: '確認槽車入料品名是否與進貨通知單符合', mode: 'yn', normalChoice: '是' },
      { id: 'p8', section: '入料前檢查', name: '入料泵浦是否清潔', mode: 'yn', normalChoice: '是', pumpRelated: true },
      { id: 'p9', section: '入料前檢查', name: '入料管線是否確認清潔及無破損', mode: 'yn', normalChoice: '是' },
      { id: 'p10', section: '入料前檢查', name: '對刷確認入料軟管是否與儲槽相符並銜接妥', mode: 'yn', normalChoice: '是' },
      { id: 'p11', section: '入料前檢查', name: '入料軟管是否與儲槽相符並銜接妥', mode: 'yn', normalChoice: '是' },
      { id: 'p12', section: '入料前檢查', name: '該儲槽作業之相關阻閥、管線是否確認在正常位置', mode: 'yn', normalChoice: '是' },
      { id: 'd1', section: '入料中檢查', name: '該儲槽之液位計作動是否正常', mode: 'yn', normalChoice: '是' },
      { id: 'd2', section: '入料中檢查', name: '洩壓裝置是否已開啟', mode: 'yn', normalChoice: '是' },
      { id: 'd3', section: '入料中檢查', name: '該PUMP作業壓力是否在範圍內', mode: 'yn_num', unit: 'Kg/cm²', maxOk: 5, normalChoice: '是', pumpRelated: true },
      { id: 'd4', section: '入料中檢查', name: '袋式過濾器壓力（超過2 Kg/cm² 須更換過濾袋）：紀錄', mode: 'num_only', unit: 'Kg/cm²', maxOk: 2, normalChoice: '是' },
      { id: 'a1', section: '入料後檢查', name: '管線閥件是否關妥，無殘液', mode: 'yn', normalChoice: '是' },
      { id: 'a2', section: '入料後檢查', name: '管線已拔離槽體，軟管塞頭已蓋妥且掛耳已扣緊', mode: 'yn', normalChoice: '是' },
      { id: 'a3', section: '入料後檢查', name: '槽車接地線已拔除並收回納箱', mode: 'yn', normalChoice: '是' },
      { id: 'a4', section: '入料後檢查', name: '輪檔已移除並放回定位', mode: 'yn', normalChoice: '是' },
      { id: 'a5', section: '入料後檢查', name: '氮氣管線及轉接頭是否關閉並拔除收回', mode: 'yn', normalChoice: '是' }
    ]
  },
  {
    id: 'tpl-c50110-03',
    groupKey: '6.2',
    shortCode: '6.2',
    category: '槽車出貨安檢',
    layoutType: 'dual_compare',
    company: '鴻勝化學科技股份有限公司',
    title: '運輸油槽車安檢、清潔度檢核表',
    formCode: 'C50110-INV-02-01(03)',
    wiVersion: 'WI 版別 3.1',
    plants: ['彰濱1廠(線西)', '彰濱2廠(崙尾)'],
    plantDisplayMode: 'text',
    colLeftLabel: '運輸公司檢點',
    colRightLabel: '現場人員確認',
    extraHeaderFields: [
      { key: 'carrier', label: '運輸公司名稱', placeholder: '例：大榮化學運輸' },
      { key: 'plateNo', label: '貨車車牌號碼', placeholder: '例：KLA-8899' },
      { key: 'material', label: '料品名稱', placeholder: '例：異丙醇 (IPA)' },
      { key: 'shipNotice', label: '出貨通知單號', placeholder: '例：DN-20261126-01' }
    ],
    signers: [
      { key: 'driver', label: '駕駛員簽名', role: 'operator' },
      { key: 'operator', label: '現場人員', role: 'operator' },
      { key: 'qc', label: '品管人員', role: 'qc' },
      { key: 'leader', label: '組長', role: 'leader' },
      { key: 'manager', label: '課(副)長', role: 'manager' }
    ],
    isLatest: true,
    items: [
      { id: 's1', section: '裝貨前檢查', name: '1.車輛鑰匙是否掛放至指定位置', mode: 'yn', normalChoice: '是' },
      { id: 's2', section: '裝貨前檢查', name: '2.接地線是否接妥(10歐姆以下)', mode: 'yn_num', unit: '歐姆', maxOk: 10, normalChoice: '是' },
      { id: 's3', section: '裝貨前檢查', name: '3.輪檔是否確實使用定位', mode: 'yn', normalChoice: '是' },
      { id: 's4', section: '裝貨前檢查', name: '4.運輸物質標示牌及SDS是否已備妥', mode: 'yn', normalChoice: '是' },
      { id: 's5', section: '裝貨前檢查', name: '5.安全防護具是否合格', mode: 'yn', normalChoice: '是' },
      { id: 's6', section: '裝貨前檢查', name: '6.槽車出口管線配件、及快連接頭封蓋是否確實封閉', mode: 'yn', normalChoice: '是' },
      { id: 's7', section: '裝貨前檢查', name: '7.VOC回收管已固定、無鬆動', mode: 'yn_na', normalChoice: '是' },
      { id: 's8', section: '裝貨前檢查', name: '8.槽車已安裝安全閥', mode: 'yn', normalChoice: '是' },
      { id: 's9', section: '裝貨前檢查', name: '9.放置三角錐於槽車前後及滅火器於兩旁', mode: 'yn', normalChoice: '是' },
      { id: 's10', section: '裝貨前檢查', name: '10.槽車液位管開關閥件是否正常', mode: 'yn', normalChoice: '是' },
      { id: 's11', section: '裝貨前檢查', name: '11.出貨管件銜接是否與儲槽相符', mode: 'yn', normalChoice: '是' },
      { id: 'c1', section: '清潔度檢核項目', name: '1.槽車出口Valve共幾個', mode: 'num_only', unit: '個' },
      { id: 'c2', section: '清潔度檢核項目', name: '2.槽車為單槽設計&雙槽設計', mode: 'single_double' },
      { id: 'c3', section: '清潔度檢核項目', name: '3.油槽車內部是否清潔無殘液', mode: 'yn', normalChoice: '是' },
      { id: 'c4', section: '清潔度檢核項目', name: '4.油槽車出口Valve是否清潔無殘液', mode: 'yn', normalChoice: '是' },
      { id: 'c5', section: '清潔度檢核項目', name: '5.槽車外部是否清潔無油漬', mode: 'yn', normalChoice: '是' },
      { id: 'm1', section: '裝貨中', name: '1.裝貨中槽車是否有洩漏情形', mode: 'yn', normalChoice: '否', leftDisabled: true },
      { id: 'm2', section: '裝貨中', name: '2.該PUMP作業壓力是否在範圍內？', mode: 'yn_num', unit: 'Kg/cm²', maxOk: 5, normalChoice: '是', leftDisabled: true },
      { id: 'e1', section: '裝貨完成檢查', name: '1.出貨管線Valve是否關妥，無殘液', mode: 'yn', normalChoice: '是' },
      { id: 'e2', section: '裝貨完成檢查', name: '2.出貨管線已拔離槽體，軟管塞頭已蓋妥且掛耳已扣緊', mode: 'yn', normalChoice: '是' },
      { id: 'e3', section: '裝貨完成檢查', name: '3.VOC管線已拔離槽體，管線Valve已關妥', mode: 'yn', normalChoice: '是' },
      { id: 'e4', section: '裝貨完成檢查', name: '4.槽車接地線已拔離並復原', mode: 'yn', normalChoice: '是' },
      { id: 'e5', section: '裝貨完成檢查', name: '5.輪檔已移除並歸位', mode: 'yn', normalChoice: '是' }
    ]
  },
  {
    id: 'tpl-c50110-04',
    groupKey: '6.3',
    shortCode: '6.3',
    category: 'ISO TANK 出貨',
    layoutType: 'before_after',
    company: '鴻勝化學科技股份有限公司',
    title: 'ISO TANK 作業檢點表',
    formCode: 'C50110-INV-02-01(04)',
    wiVersion: 'WI 版別 3.1',
    plants: ['彰濱1廠(線西)', '彰濱2廠(崙尾)'],
    plantDisplayMode: 'text',
    extraHeaderFields: [
      { key: 'tankNo', label: '槽別', placeholder: '例：T-201' },
      { key: 'material', label: '品名', placeholder: '例：電子級醋酸' },
      { key: 'isoNo', label: 'ISO TANK 號碼', placeholder: '例：HSTC-202608' }
    ],
    signers: [
      { key: 'opBefore', label: '實施者(接合前)', role: 'operator' },
      { key: 'qc', label: '品管人員簽章(內部判定合格)', role: 'qc' },
      { key: 'opAfter', label: '實施者(拆卸後)', role: 'operator' },
      { key: 'leader', label: '組長確認', role: 'leader' },
      { key: 'manager', label: '課(副)長', role: 'manager' }
    ],
    footnotes: [
      '1.檢查說明：V代表正常；X代表異常(異常狀況需於備註欄說明)。',
      '2.ISO TANK內部檢查須入料500L後壓出取樣，由品管人員判定合格並簽核後才始充填。',
      '3.如有異常時，維護人員應立即提出改善措施或維修，並於異常處理完畢時，敘述過程於本表內。',
      '4.接地完成需檢測是否接地電阻在10歐姆以下。'
    ],
    isLatest: true,
    items: [
      { id: 't1', name: '1.放輪檔', stateLabel: '檢查', mode: 'vx' },
      { id: 't2', name: '2.接地線(10歐姆以下)', stateLabel: '紀錄', mode: 'num', unit: 'Ω', maxOk: 10 },
      { id: 't3', name: '3.放置三角錐於槽車前後及是否備妥手提滅火器?', stateLabel: '檢查', mode: 'vx' },
      { id: 't4', name: '4.氮氣加壓開關', stateLabel: '關閉', mode: 'vx' },
      { id: 't5', name: '5.化學品出口閥', stateLabel: '關閉', mode: 'vx' },
      { id: 't6', name: '6.氮氣軟管(NSB)之管帽', stateLabel: '蓋上', mode: 'vx' },
      { id: 't7', name: '7.化學品軟管(NSB)之管帽', stateLabel: '蓋上', mode: 'vx' },
      { id: 't8', name: '8.氮氣軟管(NSB)有無洩漏折損', stateLabel: '檢查', mode: 'vx' },
      { id: 't9', name: '9.化學品軟管(NSB)有無洩漏折損', stateLabel: '檢查', mode: 'vx' },
      { id: 't10', name: '10.槽車蓋(槽頂箱內無化學品)', stateLabel: '蓋上', mode: 'vx' },
      { id: 't11', name: '11.槽體壓力 0.5~1Kg/cm²', stateLabel: '紀錄', mode: 'num', unit: 'Kg/cm²', beforeDisabled: true, minOk: 0.5, maxOk: 1.0 },
      { id: 't12', name: '12.安全閥是否破裂', stateLabel: '檢查', mode: 'vx' },
      { id: 't13', name: '13.本體外觀有無損傷、異常', stateLabel: '檢查', mode: 'vx' },
      { id: 't14', name: '14.該PUMP作業壓力是否在範圍內', stateLabel: '紀錄', mode: 'num', unit: 'Kg/cm²', beforeDisabled: true, maxOk: 5 },
      { id: 't15', name: '15.袋式過濾器壓力：(超過2 Kg/cm² 須更換濾袋)', stateLabel: '紀錄', mode: 'num', unit: 'Kg/cm²', beforeDisabled: true, maxOk: 2 },
      { id: 't16', name: '16.確認殘液紀錄量', stateLabel: '紀錄', mode: 'text' },
      { id: 't17', name: '17.客戶需求充填量(KG)/設定流量(L)/完成充填量(KG)', stateLabel: '紀錄', mode: 'text' }
    ]
  },
  {
    id: 'tpl-c50110-02',
    groupKey: '6.4',
    shortCode: '6.4',
    category: 'ISO TANK 取樣',
    layoutType: 'before_after',
    company: '鴻勝化學科技股份有限公司',
    title: 'ISO TANK 取樣作業檢點表',
    formCode: 'C50110-INV-02-01(02)',
    wiVersion: 'WI 版別 3.1',
    plants: ['彰濱1廠(線西)', '彰濱2廠(崙尾)'],
    plantDisplayMode: 'text',
    extraHeaderFields: [
      { key: 'material', label: '品名', placeholder: '例：電子級醋酸' },
      { key: 'isoNo', label: 'ISO TANK 號碼', placeholder: '例：HSTC-202609' }
    ],
    signers: [
      { key: 'opBefore', label: '實施者(接合前)', role: 'operator' },
      { key: 'qc', label: '品管人員簽章(內部判定合格)', role: 'qc' },
      { key: 'opAfter', label: '實施者(拆卸後)', role: 'operator' },
      { key: 'leader', label: '組長確認', role: 'leader' },
      { key: 'manager', label: '課(副)長', role: 'manager' }
    ],
    footnotes: [
      '1.檢查說明：V代表正常；X代表異常(異常狀況需於備註欄說明)。',
      '2.ISO TANK內部檢查須壓出40Liter後請品管取樣，由品管人員判定合格並簽核後始可收管。',
      '3.如有異常時，維護人員應立即提出改善措施或維修，並於異常處理完畢時，敘述過程於本表內。',
      '4.接地完成需檢測是否接地電阻在10歐姆以下。'
    ],
    isLatest: true,
    items: [
      { id: 'q1', name: '1.放輪檔', stateLabel: '檢查', mode: 'vx' },
      { id: 'q2', name: '2.接地線(10歐姆以下)', stateLabel: '紀錄', mode: 'num', unit: 'Ω', maxOk: 10 },
      { id: 'q3', name: '3.放置三角錐於槽車前後及是否備妥手提滅火器?', stateLabel: '檢查', mode: 'vx' },
      { id: 'q4', name: '4.氮氣加壓開關', stateLabel: '關閉', mode: 'vx' },
      { id: 'q5', name: '5.化學品出口閥', stateLabel: '關閉', mode: 'vx' },
      { id: 'q6', name: '6.氮氣軟管(NSB)之管帽或防護蓋', stateLabel: '蓋上', mode: 'vx' },
      { id: 'q7', name: '7.化學品軟管(NSB)之管帽或防護蓋', stateLabel: '蓋上', mode: 'vx' },
      { id: 'q8', name: '8.氮氣軟管(NSB)之接頭有無異常', stateLabel: '檢查', mode: 'vx' },
      { id: 'q9', name: '9.化學品軟管(NSB)之接頭有無異常', stateLabel: '檢查', mode: 'vx' },
      { id: 'q10', name: '10.氮氣軟管(NSB)有無洩漏折損', stateLabel: '檢查', mode: 'vx' },
      { id: 'q11', name: '11.化學品軟管(NSB)有無洩漏折損', stateLabel: '檢查', mode: 'vx' },
      { id: 'q12', name: '12.槽車蓋(槽頂箱內無化學品)', stateLabel: '蓋上', mode: 'vx' },
      { id: 'q13', name: '13.槽體壓力 0.5~1Kg/cm²', stateLabel: '紀錄', mode: 'num', unit: 'Kg/cm²', minOk: 0.5, maxOk: 1.0 },
      { id: 'q14', name: '14.安全閥是否破裂', stateLabel: '檢查', mode: 'vx' },
      { id: 'q15', name: '15.本體外觀有無損傷、異常', stateLabel: '檢查', mode: 'vx' }
    ]
  },
  {
    id: 'tpl-c50110-01',
    groupKey: '6.5',
    shortCode: '6.5',
    category: '油罐車放櫃',
    layoutType: 'dual_compare',
    company: '鴻勝化學科技股份有限公司',
    title: '油罐車放櫃作業前檢點表',
    formCode: 'C50110-INV-02-01(01)',
    wiVersion: 'WI 版別 3.1',
    plants: ['彰濱1廠(線西)', '彰濱2廠(崙尾)'],
    plantDisplayMode: 'text',
    opTypeOptions: ['充填作業', '卸料作業'],
    colLeftLabel: '運輸公司檢點',
    colRightLabel: '現場人員確認',
    extraHeaderFields: [
      { key: 'carrier', label: '運輸公司名稱', placeholder: '例：大榮化學運輸' },
      { key: 'plateNo', label: '尾車車牌號碼', placeholder: '例：TR-5566' },
      { key: 'material', label: '料品名稱', placeholder: '例：丙酮' }
    ],
    signers: [
      { key: 'driver', label: '駕駛員簽名', role: 'operator' },
      { key: 'operator', label: '現場人員', role: 'operator' },
      { key: 'manager', label: '主管', role: 'manager' }
    ],
    isLatest: true,
    items: [
      { id: 'f1', section: '充填/洩料前檢查', name: '1.接地線是否接妥(10歐姆以下)', mode: 'yn_num', unit: '歐姆', maxOk: 10, normalChoice: '是' },
      { id: 'f2', section: '充填/洩料前檢查', name: '2.輪檔是否確實使用定位', mode: 'yn', normalChoice: '是' },
      { id: 'f3', section: '充填/洩料前檢查', name: '3.放置三角錐於槽車前後及滅火器於槽車旁', mode: 'yn', normalChoice: '是' },
      { id: 'f4', section: '充填/洩料前檢查', name: '4.槽車排氣閥/呼吸閥是否已開啟', mode: 'yn', normalChoice: '是' },
      { id: 'f5', section: '充填/洩料前檢查', name: '5.運輸物質標示牌是否正確', mode: 'yn', normalChoice: '是' },
      { id: 'f6', section: '充填/洩料前檢查', name: '6.槽車出口管線配件、及快速接頭封蓋是否確實封閉', mode: 'yn', normalChoice: '是' },
      { id: 'f7', section: '充填/洩料前檢查', name: '7.槽車是否安裝安全閥', mode: 'yn', normalChoice: '是' },
      { id: 'f8', section: '充填/洩料前檢查', name: '8.槽車液位管開關閥件是否正常', mode: 'yn', normalChoice: '是' },
      { id: 'fc1', section: '充填清潔度檢核項目', name: '1.槽車出口Valve共幾個', mode: 'num_only', unit: '個' },
      { id: 'fc2', section: '充填清潔度檢核項目', name: '2.槽車為單槽設計&雙槽設計', mode: 'single_double' },
      { id: 'fc3', section: '充填清潔度檢核項目', name: '3.油槽車內部是否清潔無殘液', mode: 'yn', normalChoice: '是' },
      { id: 'fc4', section: '充填清潔度檢核項目', name: '4.油槽車出口Valve是否清潔無殘液', mode: 'yn', normalChoice: '是' },
      { id: 'fc5', section: '充填清潔度檢核項目', name: '5.槽車外部是否清潔無油漬', mode: 'yn', normalChoice: '是' }
    ]
  }
];
