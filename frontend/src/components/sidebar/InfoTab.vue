<template>
  <div class="panel-content">
    <div class="known-info-form">
      <textarea
        :value="newInfoContent"
        placeholder="请输入信息"
        rows="3"
        @input="$emit('update:newInfoContent', ($event.target as HTMLTextAreaElement).value)"
      ></textarea>
    </div>
    <div>
      <button class="known-info-button" @click="$emit('add')" :disabled="!newInfoContent.trim()">
        添加
      </button>
    </div>

    <div class="info-hint">💡 提示：双击列表中的信息可直接编辑</div>

    <div v-if="knownInfos.length === 0" class="empty-info">
      暂无已知信息
    </div>

    <ul v-else class="known-info-list">
      <li v-for="info in knownInfos" :key="info.id">
        <span
          @dblclick.prevent="$emit('start-edit', info)"
          class="info-content"
          :class="{ editing: editingId === info.id }"
        >
          <template v-if="editingId === info.id">
            <textarea
              :value="editInfoContent"
              rows="2"
              @input="$emit('update:editInfoContent', ($event.target as HTMLTextAreaElement).value)"
              @blur="$emit('save-edit', info)"
              @keyup.enter="$emit('save-edit', info)"
              :ref="(el: any) => { if (el) editTextareaRefs[info.id] = el }"
            ></textarea>
          </template>
          <template v-else>
            {{ info.content }}
          </template>
        </span>
        <div class="info-actions">
          <button @click="$emit('delete', info.id)" class="delete-btn">🗑️</button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  knownInfos: any[]
  newInfoContent: string
  editingId: number | null
  editInfoContent: string
  editTextareaRefs: Record<number, HTMLTextAreaElement>
}>()

defineEmits<{
  'add': []
  'start-edit': [info: any]
  'save-edit': [info: any]
  'delete': [infoId: number]
  'update:newInfoContent': [value: string]
  'update:editInfoContent': [value: string]
}>()
</script>

<style scoped>
.known-info-form {
  margin-bottom: 12px;
  width: 100%;
  box-sizing: border-box;
  padding: 0 4px;
}

.known-info-form textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #ffe79e;
  border-radius: 12px;
  font-size: 14px;
  resize: none;
  box-sizing: border-box;
  margin: 0;
  background: var(--white);
  transition: all 0.3s;
  outline: none;
  font-family: inherit;
}

.known-info-form textarea:focus {
  box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.35);
}

.known-info-button {
  padding: 8px 24px;
  background: linear-gradient(135deg, var(--gold), var(--gold-deep));
  color: var(--white);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  margin: 10px 0 0 4px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(212, 168, 67, 0.25);
  transition: all 0.3s;
}

.known-info-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(212, 168, 67, 0.35);
}

.info-hint {
  font-size: 12px;
  color: var(--gold-deep);
  margin: 12px 4px;
  padding: 8px 12px;
  background: var(--gold-pale);
  border-radius: 8px;
  border-left: 3px solid var(--gold);
}

.known-info-list {
  list-style: none;
  padding: 0 4px;
  margin: 0;
  width: calc(100% - 8px);
  box-sizing: border-box;
}

.known-info-list li {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.3s;
  width: 100%;
  box-sizing: border-box;
}

.known-info-list li:hover {
  border-color: var(--gold);
  box-shadow: var(--shadow);
  transform: translateX(4px);
}

.info-content {
  flex: 1;
  cursor: pointer;
  word-break: break-word;
  min-width: 0;
  border: 1px solid #D4C9A8;
  border-radius: 6px;
  padding: 6px 8px;
  background: var(--white);
  transition: all 0.3s;
}

.info-content.editing {
  border-color: transparent;
  background: transparent;
  padding: 0;
}

.info-content textarea {
  width: 100%;
  padding: 4px;
  font-size: 12px;
  border: 1px solid #ffe79e;
  border-radius: 4px;
  resize: none;
  box-sizing: border-box;
  outline: none;
  font-family: inherit;
}

.info-content textarea:focus {
  box-shadow: 0 0 0 3px rgba(255, 215, 0, 0.35);
}

.info-actions button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 0 4px;
  opacity: 0.6;
}

.info-actions button:hover {
  opacity: 1;
}

.empty-info {
  color: var(--text-secondary);
  text-align: center;
  padding: 40px 20px;
  font-size: 14px;
}

.empty-info::before {
  content: '✦';
  display: block;
  font-size: 36px;
  color: var(--gold);
  margin-bottom: 12px;
  opacity: 0.5;
}
</style>
