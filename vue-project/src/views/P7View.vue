<template>
  <div id="p7" class="page">
    <div class="p2-head">
      <div class="pg-title">사내문서 관리</div>
      <div class="tab-row">
        <button class="tab-btn" :class="{ on: tab === 'list' }" @click="tab = 'list'">문서 목록</button>
        <button class="tab-btn" :class="{ on: tab === 'add' }" @click="tab = 'add'">문서 등록</button>
      </div>
    </div>

    <!-- 문서 목록 탭 -->
    <div v-if="tab === 'list'" class="doc-list">
      <div class="empty-state" v-if="loading">불러오는 중...</div>
      <div class="empty-state" v-else-if="!docs.length">등록된 사내문서가 없습니다.</div>
      <div v-for="d in docs" :key="d.doc_id" class="dcard">
        <div class="dcard-info">
          <div class="dcard-title">{{ d.title }}</div>
          <div class="dcard-meta">
            {{ d.source_file || '직접 입력' }} · 청크 {{ d.chunk_count }}개 · {{ d.created_at?.slice(0, 10) }}
          </div>
          <div class="dcard-id">ID: {{ d.doc_id }}</div>
        </div>
        <button class="btn-del" @click="handleDelete(d.doc_id)">삭제</button>
      </div>
    </div>

    <!-- 문서 등록 탭 -->
    <div v-if="tab === 'add'" class="add-form">
      <div class="form-card">
        <div class="form-card-title">새 사내문서 등록</div>
        <div class="form-card-sub">등록된 문서는 논문과 자동으로 매핑되어 비교보고서 생성에 활용됩니다.</div>

        <div class="form-divider"></div>

        <div class="form-section">
          <label class="form-label">문서 제목 <span class="form-required">*</span></label>
          <input class="form-input" v-model="form.title" placeholder="예: 2024 AI 기술 도입 검토서" />
        </div>

        <div class="form-section">
          <label class="form-label">등록 방식</label>
          <div class="mode-row">
            <button class="mode-btn" :class="{ on: form.mode === 'text' }" @click="form.mode = 'text'">
              <span class="mode-icon">✏️</span> 텍스트 직접 입력
            </button>
            <button class="mode-btn" :class="{ on: form.mode === 'pdf' }" @click="form.mode = 'pdf'">
              <span class="mode-icon">📄</span> PDF 파일 업로드
            </button>
          </div>
        </div>

        <div v-if="form.mode === 'text'" class="form-section">
          <label class="form-label">문서 내용 <span class="form-required">*</span></label>
          <textarea class="form-textarea" v-model="form.text" rows="12" placeholder="사내문서 내용을 입력하세요..."></textarea>
        </div>

        <div v-if="form.mode === 'pdf'" class="form-section">
          <label class="form-label">PDF 파일 <span class="form-required">*</span></label>
          <label class="file-drop" :class="{ 'has-file': form.file }">
            <input type="file" accept=".pdf" @change="onFileChange" class="form-file-hidden" />
            <span v-if="!form.file" class="file-drop-hint">클릭하거나 파일을 드래그해서 업로드</span>
            <span v-else class="file-drop-name">📎 {{ form.file.name }}</span>
          </label>
        </div>

        <div v-if="submitError" class="form-error">{{ submitError }}</div>
        <div v-if="submitSuccess" class="form-success">✓ 등록 완료 (청크 {{ submitSuccess.chunk_count }}개 저장)</div>

        <div class="form-actions">
          <button class="btn-submit" :disabled="submitting" @click="handleSubmit">
            {{ submitting ? '등록 중...' : '등록하기' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { store } from '../store.js'
import {
  listInternalDocs,
  registerInternalDoc,
  uploadInternalDocFile,
  deleteInternalDoc,
  refreshPaperRelates,
} from '../api/reportService.js'

const tab = ref('list')
const docs = ref([])
const loading = ref(false)

const form = ref({ title: '', text: '', mode: 'text', file: null })
const submitting = ref(false)
const submitError = ref('')
const submitSuccess = ref(null)

async function loadDocs() {
  loading.value = true
  try { docs.value = await listInternalDocs() } catch {} finally { loading.value = false }
}

onMounted(loadDocs)

function onFileChange(e) {
  form.value.file = e.target.files[0] || null
}

async function handleSubmit() {
  submitError.value = ''
  submitSuccess.value = null
  if (!form.value.title.trim()) { submitError.value = '제목을 입력하세요.'; return }

  submitting.value = true
  try {
    let result
    if (form.value.mode === 'text') {
      if (!form.value.text.trim()) { submitError.value = '내용을 입력하세요.'; return }
      result = await registerInternalDoc({ title: form.value.title, text: form.value.text })
    } else {
      if (!form.value.file) { submitError.value = 'PDF 파일을 선택하세요.'; return }
      result = await uploadInternalDocFile(form.value.title, form.value.file)
    }
    submitSuccess.value = result
    form.value = { title: '', text: '', mode: 'text', file: null }
    await loadDocs()
    refreshPaperRelates().catch(() => {})
  } catch (e) {
    submitError.value = e?.response?.data?.detail || '등록에 실패했습니다.'
  } finally {
    submitting.value = false
  }
}

async function handleDelete(docId) {
  if (!confirm('삭제하시겠습니까?')) return
  try {
    await deleteInternalDoc(docId)
    await loadDocs()
  } catch {}
}
</script>

<style scoped>
.pg-title { font-size: 23px; font-weight: 700; padding: 20px 24px 8px; }
.tab-row { display: flex; gap: 8px; padding: 0 24px 16px; }
.tab-btn { padding: 6px 18px; border-radius: 20px; border: 1px solid var(--border); background: transparent; color: var(--t2); cursor: pointer; font-size: 15px; font-family: inherit; transition: all .16s; }
.tab-btn.on { background: var(--teal); color: #fff; border-color: var(--teal); }

/* 문서 목록 탭 */
.doc-list { padding: 16px 28px; display: flex; flex-direction: column; gap: 10px; overflow-y: auto; flex: 1; }
.doc-list::-webkit-scrollbar { width: 3px; }
.doc-list::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.dcard { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; background: var(--card); border: 1px solid var(--border); border-radius: 10px; gap: 14px; }
.dcard-title { font-size: 16px; font-weight: 600; color: var(--t1); margin-bottom: 4px; }
.dcard-meta { font-size: 14px; color: var(--t3); }
.dcard-id { font-size: 11px; color: var(--t3); margin-top: 2px; font-family: monospace; opacity: .75; }
.btn-del { padding: 5px 13px; border-radius: 6px; border: 1px solid #e55; background: transparent; color: #e55; cursor: pointer; font-size: 14px; font-family: inherit; flex-shrink: 0; }
.btn-del:hover { background: rgba(238,85,85,.08); }

/* 문서 등록 탭 */
.add-form { flex: 1; overflow-y: auto; padding: 32px 28px; display: flex; flex-direction: column; align-items: center; }
.add-form::-webkit-scrollbar { width: 3px; }
.add-form::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

.form-card { width: 100%; max-width: 700px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 40px 44px; display: flex; flex-direction: column; gap: 24px; box-shadow: 0 2px 20px rgba(13,27,46,.08); }
.form-card-title { font-size: 20px; font-weight: 700; color: var(--t1); }
.form-card-sub { font-size: 14px; color: var(--t3); line-height: 1.6; margin-top: -16px; }
.form-divider { height: 1px; background: var(--border); }

.form-section { display: flex; flex-direction: column; gap: 8px; }
.form-label { font-size: 14px; font-weight: 600; color: var(--t2); letter-spacing: .02em; }
.form-required { color: var(--teal); margin-left: 2px; }
.form-input { padding: 10px 14px; border-radius: 9px; border: 1px solid var(--border); background: var(--bg); color: var(--t1); font-size: 15px; font-family: inherit; outline: none; transition: border-color .16s; }
.form-input:focus { border-color: var(--teal); }
.form-input::placeholder { color: var(--t3); }
.form-textarea { padding: 12px 14px; border-radius: 9px; border: 1px solid var(--border); background: var(--bg); color: var(--t1); font-size: 15px; font-family: inherit; resize: vertical; outline: none; transition: border-color .16s; line-height: 1.7; }
.form-textarea:focus { border-color: var(--teal); }
.form-textarea::placeholder { color: var(--t3); }

.mode-row { display: flex; gap: 10px; }
.mode-btn { flex: 1; padding: 12px 16px; border-radius: 10px; border: 1.5px solid var(--border); background: var(--bg); color: var(--t2); cursor: pointer; font-size: 14px; font-family: inherit; font-weight: 500; transition: all .16s; display: flex; align-items: center; justify-content: center; gap: 6px; }
.mode-btn:hover { border-color: var(--border2); color: var(--t1); }
.mode-btn.on { border-color: var(--teal); background: rgba(0,212,170,.06); color: var(--teal); font-weight: 600; }
.mode-icon { font-size: 16px; }

.file-drop { display: flex; align-items: center; justify-content: center; border: 1.5px dashed var(--border); border-radius: 10px; padding: 32px 20px; cursor: pointer; transition: all .16s; background: var(--bg); position: relative; }
.file-drop:hover { border-color: var(--teal); background: rgba(0,212,170,.03); }
.file-drop.has-file { border-style: solid; border-color: var(--teal); background: rgba(0,212,170,.04); }
.file-drop-hint { font-size: 14px; color: var(--t3); }
.file-drop-name { font-size: 14px; color: var(--teal); font-weight: 500; }
.form-file-hidden { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }

.form-actions { display: flex; justify-content: flex-end; padding-top: 4px; }
.btn-submit { padding: 11px 32px; border-radius: 9px; border: none; background: var(--teal); color: #080e1a; font-size: 15px; cursor: pointer; font-weight: 700; font-family: inherit; transition: opacity .16s; }
.btn-submit:hover { opacity: .85; }
.btn-submit:disabled { opacity: 0.45; cursor: not-allowed; }
.form-error { color: #d94f4f; font-size: 14px; padding: 10px 14px; background: rgba(217,79,79,.06); border-radius: 8px; border: 1px solid rgba(217,79,79,.2); }
.form-success { color: #059669; font-size: 14px; padding: 10px 14px; background: rgba(5,150,105,.07); border-radius: 8px; border: 1px solid rgba(5,150,105,.2); }
.empty-state { text-align: center; color: var(--t3); padding: 60px 40px; font-size: 16px; }
</style>
