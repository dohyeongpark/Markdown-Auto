<script setup>
import { ref } from 'vue'

defineOptions({ name: 'DocTreeNode' })

const props = defineProps({
  node: { type: Object, required: true },
  depth: { type: Number, default: 0 },
  activeDirectory: { type: String, default: null },
})

const emit = defineEmits(['select'])

const expanded = ref(true)
const hasChildren = props.node.children.length > 0

function onRowClick() {
  if (props.node.doc) {
    emit('select', props.node.doc.directory)
  } else if (hasChildren) {
    expanded.value = !expanded.value
  }
}

function onCaretClick(event) {
  event.stopPropagation()
  expanded.value = !expanded.value
}
</script>

<template>
  <div class="doc-tree-node">
    <div
      class="doc-tree-node__row"
      :class="{ 'doc-tree-node__row--active': node.doc && node.doc.directory === activeDirectory }"
      :style="{ paddingLeft: `${depth * 0.9 + 0.4}rem` }"
      @click="onRowClick"
    >
      <span v-if="hasChildren" class="doc-tree-node__caret" @click="onCaretClick">{{
        expanded ? '▾' : '▸'
      }}</span>
      <span v-else class="doc-tree-node__caret doc-tree-node__caret--leaf"></span>
      <span class="doc-tree-node__icon">{{ hasChildren ? '📁' : '📄' }}</span>
      <span class="doc-tree-node__name font-monospace" :class="{ 'doc-tree-node__name--empty': !node.doc }">
        {{ node.name }}
      </span>
    </div>
    <div v-if="hasChildren && expanded" class="doc-tree-node__children">
      <DocTreeNode
        v-for="child in node.children"
        :key="child.path"
        :node="child"
        :depth="depth + 1"
        :active-directory="activeDirectory"
        @select="$emit('select', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
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
  text-align: center;
  color: #888;
}

.doc-tree-node__caret--leaf {
  visibility: hidden;
}

.doc-tree-node__icon {
  flex-shrink: 0;
}

.doc-tree-node__name {
  min-width: 0;
  overflow-wrap: anywhere;
}

.doc-tree-node__name--empty {
  color: #888;
}
</style>
