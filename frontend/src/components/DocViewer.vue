<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js/lib/core'
import bash from 'highlight.js/lib/languages/bash'
import css from 'highlight.js/lib/languages/css'
import dockerfile from 'highlight.js/lib/languages/dockerfile'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import python from 'highlight.js/lib/languages/python'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'
import yaml from 'highlight.js/lib/languages/yaml'
import 'github-markdown-css/github-markdown-light.css'
import 'highlight.js/styles/github.css'

hljs.registerLanguage('bash', bash)
hljs.registerLanguage('css', css)
hljs.registerLanguage('dockerfile', dockerfile)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('json', json)
hljs.registerLanguage('python', python)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('yaml', yaml)

// LLM이 생성한 코드 펜스 언어 태그는 자유 형식이라 등록되지 않은 언어일 수 있다.
marked.use(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang) {
      const language = hljs.getLanguage(lang) ? lang : 'plaintext'
      return hljs.highlight(code, { language }).value
    },
  }),
)

const props = defineProps({
  document: {
    type: Object,
    default: null,
  },
})

// LLM이 생성한 content에는 소스 코드에서 유입된 <script> 등이 섞일 수 있으므로
// v-html로 삽입하기 전에 반드시 sanitize한다. highlight.js가 넣는 span class는
// DOMPurify 기본 설정에서 그대로 유지된다.
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
      <div class="doc-viewer__content markdown-body" v-html="renderedHtml" />
    </template>
  </div>
</template>

<style scoped>
.doc-viewer__content {
  max-width: 860px;
  overflow-x: hidden;
  overflow-wrap: break-word;
  font-size: 1rem;
  line-height: 1.7;
  background: transparent;
}
</style>
