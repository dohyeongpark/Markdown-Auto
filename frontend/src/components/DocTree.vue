<script setup>
import { computed } from 'vue'
import { buildDocTree } from '../docTree'
import DocTreeNode from './DocTreeNode.vue'

const props = defineProps({
  documents: {
    type: Array,
    required: true,
  },
  activeDirectory: {
    type: String,
    default: null,
  },
})

defineEmits(['select'])

const tree = computed(() => buildDocTree(props.documents))
</script>

<template>
  <div class="doc-tree">
    <p v-if="documents.length === 0" class="text-muted small mb-0">문서가 없습니다.</p>
    <template v-else>
      <div
        v-if="tree.doc"
        class="doc-tree-node__row doc-tree__root-row"
        :class="{ 'doc-tree-node__row--active': tree.doc.directory === activeDirectory }"
        @click="$emit('select', tree.doc.directory)"
      >
        <span class="doc-tree-node__caret doc-tree-node__caret--leaf"></span>
        <span class="doc-tree-node__icon">📄</span>
        <span class="doc-tree-node__name font-monospace">(root)</span>
      </div>
      <DocTreeNode
        v-for="child in tree.children"
        :key="child.path"
        :node="child"
        :depth="0"
        :active-directory="activeDirectory"
        @select="$emit('select', $event)"
      />
    </template>
  </div>
</template>

<style scoped>
.doc-tree {
  max-height: calc(100vh - 12rem);
  overflow-y: auto;
  overflow-x: hidden;
}

.doc-tree-node__row {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.25rem 0.4rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.doc-tree-node__row:hover {
  background: rgba(125, 125, 125, 0.12);
}

.doc-tree-node__row--active {
  background: rgba(13, 110, 253, 0.15);
  font-weight: 600;
}

.doc-tree-node__caret {
  width: 1rem;
  flex-shrink: 0;
}

.doc-tree-node__icon {
  flex-shrink: 0;
}

.doc-tree-node__name {
  min-width: 0;
  overflow-wrap: anywhere;
}
</style>
