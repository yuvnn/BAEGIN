export function fmt(s) {
  return s.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
}

export function fmtMd(s) {
  return s
    .replace(/\*\*(.*?)\*\*/g, '<strong style="color:var(--t1)">$1</strong>')
    .replace(/•/g, '<span style="color:var(--teal)">•</span>')
    .replace(/\n/g, '<br>')
}
