<script setup>
import { onMounted, ref, watch } from 'vue'
import { getPromptConfig, listPromptPresets, savePromptConfig } from '../api'

const props = defineProps({
  owner: { type: String, required: true },
  repo: { type: String, required: true },
  branch: { type: String, required: true },
  visible: { type: Boolean, default: false },
})

const emit = defineEmits(['update:visible'])

const presets = ref([])
const presetId = ref('default')
const customInstructions = ref('')
const loading = ref(false)
const saving = ref(false)
const error = ref(null)
const savedAt = ref(null)

onMounted(async () => {
  try {
    presets.value = await listPromptPresets()
  } catch (e) {
    error.value = e.message
  }
})

watch(
  () => props.visible,
  async (visible) => {
    if (!visible) return

    loading.value = true
    error.value = null
    savedAt.value = null

    try {
      const config = await getPromptConfig(props.owner, props.repo, props.branch)
      presetId.value = config?.preset_id ?? 'default'
      customInstructions.value = config?.custom_instructions ?? ''
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  },
)

function close() {
  emit('update:visible', false)
}

async function save() {
  saving.value = true
  error.value = null

  try {
    const saved = await savePromptConfig(props.owner, props.repo, props.branch, {
      preset_id: presetId.value === 'default' ? null : presetId.value,
      custom_instructions: customInstructions.value.trim() || null,
    })
    savedAt.value = saved.updated_at
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div v-if="visible">
    <div class="modal d-block" tabindex="-1" @click.self="close">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">프롬프트 설정 — {{ owner }}/{{ repo }}@{{ branch }}</h5>
            <button type="button" class="btn-close" aria-label="Close" @click="close"></button>
          </div>
          <div class="modal-body">
            <p v-if="loading" class="text-muted mb-0">불러오는 중...</p>
            <template v-else>
              <p class="text-muted small">
                이 저장소/브랜치에서 문서를 생성할 때 기본 프롬프트에 덧붙일 스타일 지침을 설정합니다.
              </p>

              <div class="mb-3">
                <label class="form-label">프리셋</label>
                <select v-model="presetId" class="form-select">
                  <option v-for="preset in presets" :key="preset.id" :value="preset.id">
                    {{ preset.label }} — {{ preset.description }}
                  </option>
                </select>
              </div>

              <div class="mb-2">
                <label class="form-label">커스텀 지침 (선택)</label>
                <textarea
                  v-model="customInstructions"
                  class="form-control font-monospace"
                  rows="6"
                  placeholder="예: 각 함수마다 사용 예시를 하나씩 포함해줘"
                ></textarea>
              </div>
            </template>

            <p v-if="error" class="text-danger small mb-0">{{ error }}</p>
            <p v-else-if="savedAt" class="text-success small mb-0">저장됨 ({{ savedAt }})</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="close">닫기</button>
            <button type="button" class="btn btn-primary" :disabled="saving || loading" @click="save">
              {{ saving ? '저장 중...' : '저장' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop d-block"></div>
  </div>
</template>
