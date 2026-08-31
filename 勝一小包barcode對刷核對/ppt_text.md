
--- Slide ---
RFID標籤定義

--- Slide ---
Labeling and packaging requirement – Drum (1/4)
Overview
Drum RFID Label
1
Pallet RFID Label
Packaging RFID Label
3
New
No Change
No Change
2

23930512
23930512
LAZ1/0001
2
--- Slide ---
Drum RFID label 

1
MAX: 53 characters
Identifier
(Fixed) 
PO vendor’s DUNS
1st layer PPN
MAX: 18 characters
Lot Number
MAX: 15 characters
Serial
Prefix
(Fixed) 
美國僑力 DUNS: 
102184893
料號
- 716: L1185100
- 1106: L140024
- A515: L2C9172
- C260: L2C9180
充填桶流水號
By material and packaging
(defined by supplier
Registered in TSMC system)
By drum of material and lot (named by supplier)
e.g. 00001 for the 1st drum of L12C007/LOT67890
00002 for the 2nd drum of L12C007/LOT67890
美國僑力
Vendor code:
10651601


料號
(TW/AZ相同)

充填桶流水號
批號
1+料號  效期(YYYYMMDD)+TS
2+批號    桶號serial(OPQRS)
3+美國僑力vendor code(10651601)
--- Slide ---
Pallet RFID Label


MAX: 35 characters
Identifier
(Fixed) 
PO vendor’s DUNS
Pallet no.
Prefix
(Fixed) 
By pallet
(named by supplier)
理論上要用
美國僑力 DUNS: 
102184893

與思康確認
可以沿用勝一DUNS:
656112406
RFID已印在塑膠板上
思康已印在塑膠板上
一張棧板2個RFID

--- Slide ---
Packaging RFID Label
1
2
MAX: 53 characters
Identifier
(Fixed) 
PO vendor’s DUNS
2nd layer PPN
MAX: 18 characters
Packaging serial number
MAX: 22 characters
Identifier
(Fixed) 
PO vendor’s DUNS
Packaging serial number
Prefix
(Fixed) 
Prefix
(Fixed) 
By material and packaging
(defined by supplier
Registered in TSMC system)
By every shipping packaging unit (named by supplier)
Not repeatable
* Filling in “Cylinder No.” field in ASN
(ASN由美國僑力開立給F21,我們不用填寫)

Vendor code

到達廠區
    PAL料號-002
- 716: L1185100-002
- 1106: L140024-002
- A515: L2C9172-002
- C260: L2C9180-002
美國僑力
Vendor code:
10651601
美國僑力 DUNS: 
102184893

台積電要求Co-batch,同一批號要在台灣&美國皆使用
N產品: 固定呈現Mixed
       (因N產品每批生產42桶,又要給台灣廠區pre-use,所以每櫃會有兩個以上批號)
2.   P產品: 填寫此櫃批號&有效期限
      (因每批可以沖填的桶數較多,所以不會有N產品的問題)
美國僑力 DUNS: 
102184893

    YMMDDWXYZ(共9碼)
- YMMDD: 生產日期
- W=1(勝一), W=2(鴻勝)
- X=暫定0
- YZ=棧板流水號(e.g. 01對應充填時1~4桶, 02對應充填時5~8桶)

此碼即是運輸上傳追蹤表的Packaging ID

e.g. 20230505生產,充填第393~396桶
Packaging serial number
UN10218489330505099
30505099

--- Slide ---
No specific labeling and packaging requirement
Labeling and packaging requirement – ISO tank
Overview