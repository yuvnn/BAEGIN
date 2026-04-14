import { reactive } from 'vue'
import { PAPERS } from './data/papers.js'

export const store = reactive({
  currentPage: 'p1',
  curPaper: PAPERS[0],
  p4Paper: PAPERS[0],
  generatedReports: [],
  searchQuery: '',
  curCat: '전체',
  curSort: 'latest',
  p1ModalOpen: false,

  go(id) {
    this.currentPage = id
    document.body.classList.toggle('light-theme', id !== 'p1')
    if (id === 'p1') this.p1ModalOpen = false
  },

  openPaper(id) {
    const p = PAPERS.find(x => x.id === id)
    if (!p) return
    this.curPaper = p
    this.p4Paper = p
    this.go('p3')
  },

  generateReport(docName, paperId) {
    const p = PAPERS.find(x => x.id === paperId)
    if (!p) return
    this.generatedReports.unshift({
      docName,
      paperTitle: p.title,
      paperId,
      createdAt: new Date().toLocaleDateString('ko-KR')
    })
    this.p4Paper = p
    this.go('p4')
  },

  viewReport(idx) {
    const r = this.generatedReports[idx]
    const p = PAPERS.find(x => x.id === r.paperId)
    if (!p) return
    this.p4Paper = p
    this.go('p4')
  },

  doSearch(q) {
    this.searchQuery = q
    this.go('p2')
  }
})
