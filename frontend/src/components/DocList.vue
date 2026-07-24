<script setup>
defineProps({
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
</script>

<template>
  <ul class="doc-list">
    <li v-if="documents.length === 0" class="doc-list__empty">문서가 없습니다.</li>
    <li
      v-for="doc in documents"
      :key="doc.directory"
      class="doc-list__item"
      :class="{ 'doc-list__item--active': doc.directory === activeDirectory }"
      @click="$emit('select', doc.directory)"
    >
      <span class="doc-list__directory">{{ doc.directory }}</span>
      <span class="doc-list__updated-at">{{ doc.updated_at }}</span>
    </li>
  </ul>
</template>

<style scoped>
.doc-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.doc-list__empty {
  color: #888;
  padding: 0.5rem 0;
}

.doc-list__item {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
}

.doc-list__item:hover {
  background: rgba(125, 125, 125, 0.12);
}

.doc-list__item--active {
  background: rgba(66, 184, 131, 0.18);
  font-weight: 600;
}

.doc-list__directory {
  font-family: monospace;
}

.doc-list__updated-at {
  color: #888;
  font-size: 0.8rem;
  white-space: nowrap;
}
</style>
