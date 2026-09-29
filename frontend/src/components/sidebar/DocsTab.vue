<template>
  <div class="panel-content attachments">
    <div v-if="previewEnabled" class="preview-notice">示例文档 · 未上传<button @click="previewEnabled = false">退出预览</button></div>
    <input type="file" :ref="setFileInputRef" accept=".txt" hidden @change="$emit('file-select', $event)" />
    <button class="attachment-pocket" :class="{ dragging: dragDepth > 0 }" :disabled="uploading" title="选择或拖入 UTF-8 编码的 TXT 文件"
      @dragenter.prevent="dragDepth++" @dragleave.prevent="dragDepth = Math.max(0, dragDepth - 1)"
      @dragover.prevent @drop.prevent="onDrop" @click="$emit('trigger')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="m8 13 7-7a3 3 0 0 1 4 4l-9 9a5 5 0 0 1-7-7l9-9" stroke-linecap="round" stroke-linejoin="round" /></svg>
      <span class="pocket-title">{{ uploading ? '正在收录…' : dragDepth ? '松开放入档案' : '添加文档' }}</span>
    </button>
    <ol v-if="visibleDocuments.length" class="attachment-register">
      <li v-for="doc in visibleDocuments" :key="doc.filename">
        <div class="record-file"><span class="record-name" :title="doc.filename">{{ doc.filename }}</span></div>
        <button class="remove-attachment" @click="removeVisibleDocument(doc)" :aria-label="'删除文档 ' + doc.filename" title="删除文档">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v5m4-5v5" stroke-linecap="round" stroke-linejoin="round" /></svg>
        </button>
      </li>
    </ol>
    <span v-if="uploading" class="upload-status" role="status">正在上传材料，请稍候。</span>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
const props = defineProps<{ uploading: boolean; docList: any[] }>()
const emit = defineEmits<{ 'trigger': []; 'file-select': [event: Event]; 'drop': [event: DragEvent]; 'remove': [filename: string] }>()
const dragDepth = ref(0)
const previewEnabled = ref(import.meta.env.DEV && new URLSearchParams(window.location.search).get('mockDocs') === '1')
const previewDocuments = ref([
  { filename: '东区码头 · 现场勘查记录.txt', preview: true },
  { filename: '目击者陈述.txt', preview: true },
  { filename: '11月14日监控录像时间整理与补充说明.txt', preview: true },
  { filename: '失踪前的最后一通电话.txt', preview: true },
])
const visibleDocuments = computed(() => previewEnabled.value ? [...props.docList, ...previewDocuments.value] : props.docList)
function removeVisibleDocument(doc: { filename: string; preview?: boolean }) {
  if (doc.preview) previewDocuments.value = previewDocuments.value.filter(item => item !== doc)
  else emit('remove', doc.filename)
}
const fileInputRef = defineModel<HTMLInputElement | null>('fileInputRef', { default: null })
function setFileInputRef(el: Element | any | null) { fileInputRef.value = el as HTMLInputElement | null }
function onDrop(event: DragEvent) { dragDepth.value = 0; if (!props.uploading) emit('drop', event) }
</script>

<style scoped>
.attachments { padding: 12px 20px 8px 3px; color: #40392f; font-family: var(--serif); }
.preview-notice { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 15px; color: #807662; font-size: 11px; }
.preview-notice button { border: 0; padding: 0; background: none; color: #805047; font: inherit; cursor: pointer; }
.attachment-pocket { display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; min-height: 48px; margin: 0 0 24px; border: 0; border-radius: 2px; background: #d7d9bf; color: #4e624e; cursor: pointer; box-shadow: 0 2px 3px rgba(73,54,27,.08); transition: background-color 160ms ease; }
.attachment-pocket > svg { width: 20px; height: 20px; color: inherit; }
.pocket-title { font: 16px var(--serif); letter-spacing: .06em; }
.attachment-pocket:hover:not(:disabled), .attachment-pocket.dragging { background-color: #c8ceb0; }
.attachment-pocket:disabled { cursor: wait; opacity: .6; }
.attachment-register { display: flex; flex-direction: column; gap: 16px; list-style: none; padding: 0 3px 8px; margin: 0; }
.attachment-register li { position: relative; display: flex; align-items: center; gap: 8px; padding: 16px 11px 12px 15px; background: #fbf4df; box-shadow: 1px 3px 6px rgba(73,54,27,.12); transform: rotate(-.7deg); }
.attachment-register li:nth-child(even) { transform: rotate(.7deg); background: #f4efdf; }
.attachment-register li::before { content: ''; position: absolute; left: 16px; top: -5px; width: 36px; height: 10px; background: rgba(158,170,121,.48); transform: rotate(-3deg); pointer-events: none; }
.attachment-register li:nth-child(even)::before { left: auto; right: 22px; transform: rotate(3deg); }
.record-file { flex: 1; min-width: 0; }
.record-name { display: block; overflow-wrap: anywhere; font-size: 14px; line-height: 1.6; }
.remove-attachment { display: grid; place-items: center; width: 30px; height: 32px; flex: none; border: 0; background: transparent; color: #938675; cursor: pointer; }
.remove-attachment svg { width: 17px; height: 17px; }
.remove-attachment:hover { color: #98534a; background: rgba(149,72,63,.07); }
button:focus-visible { outline: 2px solid #98534a; outline-offset: 3px; }
.upload-status { display: block; margin-top: 12px; color: #98534a; font-size: 12px; }
@media (max-width: 600px) { .attachments { padding-right: 10px; } }
@media (prefers-reduced-motion: reduce) { .attachment-pocket { transition: none; } }
</style>
