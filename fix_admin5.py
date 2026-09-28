path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Extract the tab-grades div
m = re.search(r'      <!-- 品名等級設定分頁 -->\s*<div id="tab-grades".*?</table>\s*</div>', text, re.DOTALL)
if m:
    grades_div = m.group(0)
    # Remove it from its current location
    text = text.replace(grades_div, '')
    
    # Insert it before `  </div>\n\n  <script>`
    target = '    </div>\n\n  </div>\n\n  <script>'
    if '    </div>\n\n  </div>\n\n  <script>' in text:
        text = text.replace('    </div>\n\n  </div>\n\n  <script>', '    </div>\n\n' + grades_div + '\n\n  </div>\n\n  <script>')
    else:
        # try another pattern
        target2 = '    </div>\n\n  <script>'
        text = text.replace('    </div>\n\n  <script>', '    </div>\n\n' + grades_div + '\n\n  </div>\n\n  <script>')
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed location!")
else:
    print("Not found")
