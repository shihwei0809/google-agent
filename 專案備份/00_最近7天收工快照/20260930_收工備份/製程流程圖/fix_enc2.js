const fs = require('fs');
let html = fs.readFileSync('public/index.html', 'utf8');

const regex = /<button class="add-node-btn p-2 rounded-lg border border-slate-200 hover:border-sky-500 hover:bg-sky-50\/50 flex flex-col items-center gap-1 text-center transition col-span-2" data-type="custom_block">[\s\S]*?<\/button>\s*<\/div>\s*<\/div>/;

const replacement = `<button class="add-node-btn p-2 rounded-lg border border-slate-200 hover:border-sky-500 hover:bg-sky-50/50 flex flex-col items-center gap-1 text-center transition col-span-2" data-type="custom_block">
                <div class="px-2 py-1 bg-purple-50 border border-purple-300 rounded text-[11px] font-bold text-purple-900"><i class="fa-solid fa-image mr-1"></i>通用圖片設備</div>
                <span class="font-medium text-slate-700">自訂設備 (支援圖片上傳)</span>
              </button>
            </div>
          </div>`;

if(html.match(regex)) {
  html = html.replace(regex, replacement);
  fs.writeFileSync('public/index.html', html, 'utf8');
  console.log('Fixed encoding issue using data-type!');
} else {
  console.log('Not found!');
}
