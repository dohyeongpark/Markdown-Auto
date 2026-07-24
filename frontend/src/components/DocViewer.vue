<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  document: {
    type: Object,
    default: null,
  },
})

// LLM이 생성한 content에는 소스 코드에서 유입된 <script> 등이 섞일 수 있으므로
// v-html로 삽입하기 전에 반드시 sanitize한다.
const renderedHtml = computed(() =>
  props.document ? DOMPurify.sanitize(marked.parse(props.document.content)) : '',
)
</script>

<template>
  <div class="doc-viewer">
    <p v-if="!document" class="doc-viewer__placeholder">왼쪽 목록에서 문서를 선택하세요.</p>
    <template v-else>
      <div class="doc-viewer__meta">
        <span class="doc-viewer__directory">{{ document.directory }}</span>
        <span class="doc-viewer__sha">source: {{ document.source_sha.slice(0, 7) }}</span>
        <span class="doc-viewer__updated-at">{{ document.updated_at }}</span>
      </div>
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div class="doc-viewer__content" v-html="renderedHtml" />
    </template>
  </div>
</template>

<style scoped>
.doc-viewer__placeholder {
  color: #888;
}

.doc-viewer__meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 1rem;
  font-family: monospace;
}

.doc-viewer__content :deep(pre) {
  background: rgba(125, 125, 125, 0.12);
  padding: 0.75rem;
  border-radius: 6px;
  overflow-x: auto;
}

.doc-viewer__content :deep(code) {
  font-family: monospace;
}
</style>
