const grade = '工業級';
const CURRENT_GRADE_OPTIONS = ['工業級', 'UPS', 'IF', '電子級', '回收液'];
const gOpts = CURRENT_GRADE_OPTIONS.map(g => `<option value="${g}" ${g===grade?'selected':''}>${g}</option>`).join('');
console.log(gOpts);
