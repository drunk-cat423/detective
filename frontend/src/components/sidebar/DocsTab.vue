<template>
  <div class="panel-content">
    <div
      class="upload-area"
      @dragover.prevent
      @drop.prevent="$emit('drop', $event)"
      @click="$emit('trigger')"
    >
      <input
        type="file"
        :ref="setFileInputRef"
        accept=".txt"
        style="display: none"
        @change="$emit('file-select', $event)"
      />
      <p>📂 拖拽或点击上传</p>
      <p style="font-size:12px;color:#999;">支持utf-8编码</p>
    </div>

    <div v-if="uploading" class="upload-progress">上传中...</div>

    <div v-if="docList.length > 0" class="doc-list">
      <h4>已上传文档</h4>
      <ul>
        <li v-for="doc in docList" :key="doc.id">
          {{ doc.filename }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  uploading: boolean
  docList: any[]
}>()

defineEmits<{
  'trigger': []
  'file-select': [event: Event]
  'drop': [event: DragEvent]
}>()

const fileInputRef = defineModel<HTMLInputElement | null>('fileInputRef', { default: null })

function setFileInputRef(el: Element | any | null) {
  fileInputRef.value = el as HTMLInputElement | null
}
</script>

<style scoped>
.upload-area {
  border: 3px dashed var(--gold);
  border-radius: 16px;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 20px;
  background: linear-gradient(135deg, rgba(255, 248, 220, 0.5), rgba(255, 250, 205, 0.3));
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.upload-area::before {
  content: '✦';
  position: absolute;
  top: 8px;
  right: 12px;
  font-size: 24px;
  color: var(--gold);
  opacity: 0.3;
}

.upload-area:hover {
  background: linear-gradient(135deg, rgba(255, 248, 220, 0.8), rgba(255, 250, 205, 0.5));
  border-color: var(--gold-deep);
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.upload-area p:first-child {
  font-size: 16px;
  font-weight: 600;
  color: var(--gold-deep);
  margin-bottom: 8px;
}

.upload-area p:last-child {
  font-size: 12px;
  color: var(--text-secondary);
}

.doc-list {
  background: var(--white);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border);
}

.doc-list h4 {
  font-size: 14px;
  font-weight: 700;
  color: var(--gold-deep);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.doc-list h4::before {
  content: '📄';
}

.doc-list li {
  padding: 8px 12px;
  background: var(--gold-pale);
  border-radius: 8px;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text);
  border-left: 3px solid var(--gold);
}

.upload-progress {
  color: var(--gold-deep);
  font-size: 12px;
  margin-bottom: 8px;
  text-align: center;
  font-weight: 500;
}
</style>
