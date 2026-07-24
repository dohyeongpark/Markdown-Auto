<script setup>
import { ref, watch } from 'vue'
import { listDocs, getDoc } from './api'
import DocList from './components/DocList.vue'
import DocViewer from './components/DocViewer.vue'

const owner = ref('')
const repo = ref('')
const branch = ref('main')

const documents = ref([])
const activeDirectory = ref(null)
const activeDocument = ref(null)
const loading = ref(false)
const error = ref(null)

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
  <div class="layout">
    <header class="layout__header">
      <h1>Markdown Auto</h1>
      <form class="repo-form" @submit.prevent="loadDocs">
        <input v-model.trim="owner" placeholder="owner" required />
        <span>/</span>
        <input v-model.trim="repo" placeholder="repo" required />
        <span>@</span>
        <input v-model.trim="branch" placeholder="branch" required />
        <button type="submit">불러오기</button>
      </form>
    </header>

    <p v-if="error" class="layout__error">{{ error }}</p>
    <p v-else-if="loading" class="layout__loading">불러오는 중...</p>

    <main class="layout__body">
      <aside class="layout__sidebar">
        <DocList :documents="documents" :active-directory="activeDirectory" @select="selectDirectory" />
      </aside>
      <section class="layout__content">
        <DocViewer :document="activeDocument" />
      </section>
    </main>
  </div>
</template>

<style scoped>
.layout {
  max-width: 960px;
  margin: 0 auto;
  padding: 1.5rem;
}

.layout__header {
  margin-bottom: 1.5rem;
}

.repo-form {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.75rem;
}

.repo-form input {
  padding: 0.4rem 0.6rem;
  font-family: monospace;
}

.layout__error {
  color: #e5484d;
}

.layout__loading {
  color: #888;
}

.layout__body {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 1.5rem;
  align-items: start;
}

.layout__sidebar {
  border-right: 1px solid rgba(125, 125, 125, 0.25);
  padding-right: 1rem;
}
</style>
