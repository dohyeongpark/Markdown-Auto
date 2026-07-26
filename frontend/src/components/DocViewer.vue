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
import plaintext from 'highlight.js/lib/languages/plaintext'
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
hljs.registerLanguage('plaintext', plaintext)
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
//
// marked.parse()가 예기치 않게 실패하면(예: 등록되지 않은 코드 펜스 언어) 뷰어
// 전체가 아무것도 안 보이는 상태로 조용히 깨지므로, 실패 시 최소한 원본 텍스트라도
// 보여준다.
const renderedHtml = computed(() => {
  if (!props.document) return ''

  try {
    return DOMPurify.sanitize(marked.parse(props.document.content))
  } catch (e) {
    console.error('마크다운 렌더링 실패:', e)
    // content를 텍스트 노드로만 넣어 <, > 등이 태그로 오인되지 않게 한다.
    const pre = window.document.createElement('pre')
    pre.textContent = props.document.content
    return DOMPurify.sanitize(pre.outerHTML)
  }
})

function downloadDoc() {
  if (!props.document) return

  const safeName = props.document.directory === '.' ? 'root' : props.document.directory.replace(/\//g, '-')
  const blob = new Blob([props.document.content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)

  const link = window.document.createElement('a')
  link.href = url
  link.download = `${safeName}.md`
  link.click()

  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="doc-viewer">
    <p v-if="!document" class="doc-viewer__placeholder text-muted">왼쪽 목록에서 문서를 선택하세요.</p>
    <template v-else>
      <div class="doc-viewer__meta d-flex align-items-center gap-3 text-muted small font-monospace mb-3">
        <span>{{ document.directory }}</span>
        <span class="badge text-bg-secondary">{{ document.source_sha.slice(0, 7) }}</span>
        <span>{{ document.updated_at }}</span>
        <button type="button" class="btn btn-sm btn-outline-secondary ms-auto" @click="downloadDoc">
          다운로드
        </button>
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
