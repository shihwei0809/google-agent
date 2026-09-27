$emps = @"
C0606	陳世偉
C0663	陳彥志
C0704	黃俊翰
C0768	黃宏吉
C0770	張立杰
C0588	郭育綾
C0664	黃玟寧
C0723	趙令融
C0926	王莠婷
C0589	辛俊宏
C0605	莊世民
C0614	洪源松
C0676	鄭健利
C0683	蔡孟賢
C0718	楊溢銜
C0731	許原暢
C0735	梁聖國
C0736	林佳隆
C0761	涂敬宗
C0765	吳皓楷
C0769	陳志修
C0800	黃俊源
C0810	林東和
C0818	黃崇恩
C0854	江承河
C0861	林家宏
C0865	陳志弘
C0885	蘇明宏
C0895	鄧博文
C0896	邱建霖
C0905	黃振榮
C0909	張韋勝
C0615	辛俊杉
C0670	盧銘傑
C0590	黃坦意
C0637	紀睿展
C0644	詹鎧鍵
C0672	黃信銘
C0779	莊峯弦
C0834	林小平
C0850	黃嘉慶
C0851	陳培瑋
C0877	林峻民
C0880	許文豪
C0884	董烱輝
C0892	周奕承
C0899	林冠霆
C0902	黃弘名
C0918	劉嘉憲
C0924	楊濬陽
C0699	林佳宏
C0623	黃衍順
C0632	楊騰方
C0642	楊淑玲
C0650	吳青山
C0693	陳志雄
C0696	莊勝淵
C0712	林雨霖
C0726	粘淳淼
C0752	陳盈守
C0760	林建豪
C0763	黃柏程
C0781	林裕峰
C0784	邱振皓
C0795	陳正育
C0796	張宥騰
C0801	林東昇
C0807	廖啓貿
C0812	蕭耀琳
C0822	洪宗寶
C0838	謝承洧
C0901	鍾宏達
C0906	邱信凱
"@
$lines = $emps.Trim() -split "`n"
$sql = "INSERT OR IGNORE INTO Employees (emp_id, name) VALUES " + "`n"
$values = @()
foreach ($line in $lines) {
    $parts = $line.Trim() -split "\t"
    if ($parts.Length -ge 2) {
        $id = $parts[0]
        $name = $parts[1]
        $values += "('$id', '$name')"
    }
}
$sql += ($values -join ",`n") + ";"
Set-Content "emps_insert.sql" $sql -Encoding UTF8
