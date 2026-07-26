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
  <ul class="list-group doc-list">
    <li v-if="documents.length === 0" class="list-group-item text-muted">문서가 없습니다.</li>
    <li
      v-for="doc in documents"
      :key="doc.directory"
      class="list-group-item list-group-item-action doc-list__item"
      :class="{ active: doc.directory === activeDirectory }"
      @click="$emit('select', doc.directory)"
    >
      <span class="doc-list__directory font-monospace">{{ doc.directory }}</span>
      <span class="doc-list__updated-at text-muted">{{ doc.updated_at }}</span>
    </li>
  </ul>
</template>

<style scoped>
.doc-list {
  max-height: calc(100vh - 12rem);
  overflow-y: auto;
  overflow-x: hidden;
}

.doc-list__item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.15rem;
  cursor: pointer;
}

.doc-list__directory {
  width: 100%;
  min-width: 0;
  overflow-wrap: anywhere;
}

.doc-list__updated-at {
  font-size: 0.75rem;
}
</style>
