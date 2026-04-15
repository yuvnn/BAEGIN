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
      <div class="form-section">
        <label class="form-label">문서 제목 *</label>
        <input class="form-input" v-model="form.title" placeholder="예: 2024 AI 기술 도입 검토서" />
      </div>

      <div class="form-section">
        <label class="form-label">등록 방식</label>
        <div class="mode-row">
          <button class="mode-btn" :class="{ on: form.mode === 'text' }" @click="form.mode = 'text'">텍스트 직접 입력</button>
          <button class="mode-btn" :class="{ on: form.mode === 'pdf' }" @click="form.mode = 'pdf'">PDF 파일 업로드</button>
        </div>
      </div>

      <div v-if="form.mode === 'text'" class="form-section">
        <label class="form-label">문서 내용 *</label>
        <textarea class="form-textarea" v-model="form.text" rows="12" placeholder="사내문서 내용을 입력하세요..."></textarea>
      </div>

      <div v-if="form.mode === 'pdf'" class="form-section">
        <label class="form-label">PDF 파일 *</label>
        <input type="file" accept=".pdf" @change="onFileChange" class="form-file" />
        <div v-if="form.file" class="file-info">{{ form.file.name }}</div>
      </div>

      <div v-if="submitError" class="form-error">{{ submitError }}</div>

      <button class="btn-submit" :disabled="submitting" @click="handleSubmit">
        {{ submitting ? '등록 중...' : '등록하기' }}
      </button>

      <div v-if="submitSuccess" class="form-success">
        ✓ 등록 완료 (청크 {{ submitSuccess.chunk_count }}개 저장)
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
.tab-btn { padding: 6px 16px; border-radius: 20px; border: 1px solid var(--bd); background: transparent; color: var(--t2); cursor: pointer; font-size: 16px; }
.tab-btn.on { background: var(--accent); color: #fff; border-color: var(--accent); }

.doc-list { padding: 0 24px; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; max-height: calc(100vh - 160px); }
.dcard { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; background: var(--card-bg); border: 1px solid var(--bd); border-radius: 10px; }
.dcard-title { font-size: 17px; font-weight: 600; color: var(--t1); margin-bottom: 4px; }
.dcard-meta { font-size: 15px; color: var(--t3); }
.dcard-id { font-size: 12px; color: var(--t3); margin-top: 2px; font-family: monospace; }
.btn-del { padding: 5px 12px; border-radius: 6px; border: 1px solid #e55; background: transparent; color: #e55; cursor: pointer; font-size: 15px; }

.add-form { padding: 0 24px; max-width: 680px; display: flex; flex-direction: column; gap: 20px; }
.form-section { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 16px; font-weight: 600; color: var(--t2); }
.form-input { padding: 8px 12px; border-radius: 8px; border: 1px solid var(--bd); background: var(--card-bg); color: var(--t1); font-size: 17px; }
.form-textarea { padding: 10px 12px; border-radius: 8px; border: 1px solid var(--bd); background: var(--card-bg); color: var(--t1); font-size: 16px; resize: vertical; }
.form-file { font-size: 16px; color: var(--t2); }
.file-info { font-size: 15px; color: var(--t3); }
.mode-row { display: flex; gap: 8px; }
.mode-btn { padding: 6px 14px; border-radius: 6px; border: 1px solid var(--bd); background: transparent; color: var(--t2); cursor: pointer; font-size: 16px; }
.mode-btn.on { background: var(--accent); color: #fff; border-color: var(--accent); }
.btn-submit { padding: 10px 28px; border-radius: 8px; border: none; background: var(--accent); color: #fff; font-size: 17px; cursor: pointer; font-weight: 600; align-self: flex-start; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.form-error { color: #e55; font-size: 16px; }
.form-success { color: #3c3; font-size: 16px; }
.empty-state { text-align: center; color: var(--t3); padding: 40px; font-size: 17px; }
</style>
