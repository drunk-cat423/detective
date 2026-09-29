<template>
  <div ref="registerElement" class="panel-content facts-register" @keydown.esc="selectedId = null">
    <div class="fact-entry">
      <textarea class="fact-paper-input" id="new-case-fact" :value="newInfoContent" aria-label="新的已知事实" placeholder="记下一条已知事实…" rows="1"
        @input="$emit('update:newInfoContent', ($event.target as HTMLTextAreaElement).value)"></textarea>
      <div class="entry-footer"><button class="record-fact" @click="$emit('add')" :disabled="!newInfoContent.trim()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="m5 12 4 4L19 6" stroke-linecap="round" stroke-linejoin="round" /></svg>记下
      </button></div>
    </div>
    <ol v-if="knownInfos.length" class="fact-records">
      <li v-for="(info, index) in knownInfos" :key="info.id" :class="{ 'is-editing': editingId === info.id }">
        <div class="fact-body">
          <textarea class="fact-paper-input" v-if="editingId === info.id" :value="editInfoContent" rows="3" aria-label="编辑已知事实"
            @input="$emit('update:editInfoContent', ($event.target as HTMLTextAreaElement).value)"
            @blur="$emit('save-edit', info)" @keydown.enter="saveOnEnter($event, info)"
            :ref="(el: any) => { if (el) editTextareaRefs[info.id] = el }"></textarea>
          <button v-else class="fact-text" :aria-expanded="selectedId === info.id" title="点击显示操作，双击编辑" @click="selectedId = selectedId === info.id ? null : info.id" @dblclick.prevent="$emit('start-edit', info)">{{ info.content }}</button>
          <div v-if="selectedId === info.id || editingId === info.id" class="fact-tools">
            <button v-if="editingId !== info.id" @click="$emit('start-edit', info)" :aria-label="'编辑事实 ' + (index + 1)" title="编辑事实"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m15 5 4 4M4 20l5-1L20 8a2.8 2.8 0 0 0-4-4L5 15z" stroke-linejoin="round" /></svg></button>
            <button @click="$emit('delete', info.id)" :aria-label="'删除事实 ' + (index + 1)" title="删除事实"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v5m4-5v5" stroke-linecap="round" stroke-linejoin="round" /></svg></button>
          </div>
        </div>
      </li>
    </ol>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
const selectedId = ref<number | null>(null)
const registerElement = ref<HTMLElement | null>(null)
function dismissActions(event: PointerEvent) {
  if (event.target instanceof Element && !registerElement.value?.contains(event.target)) selectedId.value = null
}
onMounted(() => document.addEventListener('pointerdown', dismissActions))
onBeforeUnmount(() => document.removeEventListener('pointerdown', dismissActions))
defineProps<{ knownInfos: any[]; newInfoContent: string; editingId: number | null; editInfoContent: string; editTextareaRefs: Record<number, HTMLTextAreaElement> }>()
const emit = defineEmits<{ 'add': []; 'start-edit': [info: any]; 'save-edit': [info: any]; 'delete': [infoId: number]; 'update:newInfoContent': [value: string]; 'update:editInfoContent': [value: string] }>()
function saveOnEnter(event: KeyboardEvent, info: any) { if (event.isComposing || event.shiftKey) return; event.preventDefault(); emit('save-edit', info) }
</script>

<style scoped>
.facts-register { padding: 12px 20px 8px 3px; font-family: var(--serif); color: #40392f; }
.fact-entry { display: flex; align-items: center; gap: 10px; padding: 8px 0; margin: 0 0 25px; border-bottom: 1px solid #bdb19a; }
.fact-entry textarea { flex: 1; min-width: 0; height: 34px; }
.facts-register textarea.fact-paper-input { border: 0; border-radius: 0; padding: 3px 1px; background: transparent; box-shadow: none; }
.facts-register textarea.fact-paper-input:focus { background: transparent; box-shadow: none; outline: 0; }
.fact-entry:focus-within { border-bottom-color: #98534a; }
.facts-register textarea { display: block; width: 100%; box-sizing: border-box; resize: none; border: 1px solid #c9bca2; border-radius: 2px; padding: 10px 12px; background: rgba(255,253,247,.4); color: #40392f; font: 14px/1.8 var(--serif); scrollbar-width: thin; scrollbar-color: #b7a98d transparent; }
.facts-register textarea::placeholder { color: #9b907e; }
.facts-register textarea:focus { outline: 1px solid #98534a; outline-offset: 1px; }
.entry-footer { display: flex; flex: none; }
.record-fact { display: inline-flex; align-items: center; gap: 4px; padding: 5px 2px; border: 0; background: transparent; color: #98534a; font: 13px var(--serif); white-space: nowrap; cursor: pointer; }
.record-fact svg { width: 17px; height: 17px; }
.record-fact:hover:not(:disabled) { color: #71382f; }
.record-fact:disabled { color: #a59a85; cursor: default; }
.fact-records { list-style: none; padding: 0; margin: 0 0 0 5px; }
.fact-records li { position: relative; padding: 0 0 22px 19px; border-left: 1px solid #b98b7b; }
.fact-records li::before { content: ''; position: absolute; left: -4px; top: 10px; width: 7px; height: 7px; border-radius: 50%; background: #98534a; box-shadow: 0 0 0 3px #f1eadb; }
.fact-records li:last-child { padding-bottom: 9px; }
.fact-records li.is-editing .fact-body { border-bottom: 1px solid #98534a; }
.fact-body { flex: 1; min-width: 0; display: flex; align-items: flex-start; gap: 8px; }
.fact-text { flex: 1; min-width: 0; margin: 0; padding: 0; border: 0; background: transparent; color: inherit; text-align: left; font: 14px/1.85 var(--serif); white-space: pre-wrap; overflow-wrap: anywhere; cursor: pointer; }
.fact-text:hover, .fact-text[aria-expanded="true"] { color: #98534a; }
.fact-tools { display: flex; flex: none; gap: 0; }
.fact-tools button { display: grid; place-items: center; width: 28px; height: 28px; border: 0; background: transparent; color: #938675; cursor: pointer; }
.fact-tools button:hover { color: #98534a; background: rgba(149,72,63,.07); }
.fact-tools svg { width: 15px; height: 15px; }
button:focus-visible { outline: 2px solid #98534a; outline-offset: 2px; }
@media (max-width: 600px) { .facts-register { padding-right: 10px; } }
</style>
