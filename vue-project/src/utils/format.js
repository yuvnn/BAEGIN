import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

export function fmt(s) {
  return s.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
}

export function fmtMd(s) {
  return marked.parse(s || '')
}
