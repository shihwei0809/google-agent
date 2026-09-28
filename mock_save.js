const products = ['IPA', 'IPAUPS', 'IPAHQ'];
const grades = ['工業級', '', ''];
const ignores = [false, false, true];

const productsList = [];
const gradesMap = [];
const ignoresList = [];

for (let i = 0; i < products.length; i++) {
  const p = products[i];
  const g = grades[i];
  const ignore = ignores[i];
  
  if (p) {
    productsList.push(p);
    if (g) gradesMap.push(`${p}:${g}`);
    if (ignore) ignoresList.push(p);
  }
}

console.log('OPTIONS_PRODUCTS:', productsList.join(','));
console.log('OPTIONS_PRODUCT_GRADES_MAP:', gradesMap.join(','));
console.log('T100_IGNORE_PRODUCTS:', ignoresList.join(','));
