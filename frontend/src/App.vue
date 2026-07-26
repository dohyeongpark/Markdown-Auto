<script setup>
import { ref, watch } from 'vue'
import { listDocs, getDoc } from './api'
import DocTree from './components/DocTree.vue'
import DocViewer from './components/DocViewer.vue'
import PromptSettingsModal from './components/PromptSettingsModal.vue'

const owner = ref('')
const repo = ref('')
const branch = ref('main')

const documents = ref([])
const activeDirectory = ref(null)
const activeDocument = ref(null)
const loading = ref(false)
const error = ref(null)
const showPromptSettings = ref(false)

async function loadDocs() {
  if (!owner.value || !repo.value || !branch.value) return

  loading.value = true
  error.value = null
  activeDirectory.value = null
  activeDocument.value = null

  try {
    documents.value = (await listDocs(owner.value, repo.value, branch.value)) ?? []
  } catch (e) {
    error.value = e.message
    documents.value = []
  } finally {
    loading.value = false
  }
}

async function selectDirectory(directory) {
  activeDirectory.value = directory
  error.value = null

  try {
    activeDocument.value = await getDoc(owner.value, repo.value, branch.value, directory)
  } catch (e) {
    error.value = e.message
    activeDocument.value = null
  }
}

watch(branch, () => {
  if (owner.value && repo.value) loadDocs()
})
</script>

<template>
  <div class="layout container-lg py-4">
    <header class="layout__header d-flex justify-content-between align-items-center flex-wrap gap-3 pb-3 border-bottom">
      <div>
        <h1 class="h3 mb-2">Markdown Auto</h1>
        <form class="d-flex align-items-center gap-2" @submit.prevent="loadDocs">
          <div class="input-group input-group-sm" style="width: auto">
            <input v-model.trim="owner" class="form-control font-monospace" placeholder="owner" required />
            <span class="input-group-text">/</span>
            <input v-model.trim="repo" class="form-control font-monospace" placeholder="repo" required />
            <span class="input-group-text">@</span>
            <input v-model.trim="branch" class="form-control font-monospace" placeholder="branch" required />
          </div>
          <button type="submit" class="btn btn-primary btn-sm">불러오기</button>
        </form>
      </div>
      <button
        type="button"
        class="btn btn-outline-secondary btn-sm"
        :disabled="!owner || !repo || !branch"
        @click="showPromptSettings = true"
      >
        프롬프트 설정
      </button>
    </header>

    <p v-if="error" class="text-danger mt-3 mb-0">{{ error }}</p>
    <p v-else-if="loading" class="text-muted mt-3 mb-0">불러오는 중...</p>

    <main class="layout__body">
      <aside class="layout__sidebar">
        <DocTree :documents="documents" :active-directory="activeDirectory" @select="selectDirectory" />
      </aside>
      <section class="layout__content">
        <DocViewer :document="activeDocument" />
      </section>
    </main>

    <PromptSettingsModal v-model:visible="showPromptSettings" :owner="owner" :repo="repo" :branch="branch" />
  </div>
</template>

<style scoped>
.layout__body {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 1.5rem;
  align-items: start;
  margin-top: 1.5rem;
}

.layout__sidebar {
  border-right: 1px solid rgba(125, 125, 125, 0.25);
  padding-right: 1rem;
}
</style>
