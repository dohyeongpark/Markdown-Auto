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
    <p v-if="!document" class="doc-viewer__placeholder text-muted">왼쪽 목록에서 문서를 선택하세요.</p>
    <template v-else>
      <div class="doc-viewer__meta d-flex align-items-center gap-3 text-muted small font-monospace mb-3">
        <span>{{ document.directory }}</span>
        <span class="badge text-bg-secondary">{{ document.source_sha.slice(0, 7) }}</span>
        <span>{{ document.updated_at }}</span>
      </div>
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div class="doc-viewer__content" v-html="renderedHtml" />
    </template>
  </div>
</template>

<style scoped>
.doc-viewer__content {
  overflow-x: hidden;
  overflow-wrap: break-word;
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
