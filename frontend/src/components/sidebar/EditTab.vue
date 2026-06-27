<template>
  <div class="panel-content">
    <div v-if="node">
      <div v-if="node.data.type === 'suspect'" class="edit-field">
        <label>嫌疑人名字</label>
        <input
          :value="node.data.name === '未知' ? '' : node.data.name"
          @input="updateNodeData('name', ($event.target as HTMLInputElement).value)"
          placeholder="请输入名字"
          class="suspect-name-input"
        />
      </div>
      <div class="edit-field">
        <label>编辑便签</label>
        <textarea
          :value="isDefaultContent ? '' : node.data.content"
          @input="updateNodeData('content', ($event.target as HTMLTextAreaElement).value)"
          :placeholder="defaultPlaceholder"
          rows="4"
        ></textarea>
      </div>

      <div class="color-picker">
        <div
          v-for="c in presetColors"
          :key="c"
          class="color-swatch"
          :style="{ background: c }"
          :class="{ active: node.data.color === c }"
          @click="updateNodeData('color', c)"
        ></div>
      </div>
      <button class="edit-btn save-btn" @click="$emit('save')">保存</button>
      <button class="edit-btn delete-btn" @click="$emit('delete')">删除</button>
    </div>
    <p v-else class="empty-hint">点击便签进行编辑</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  node: any
  presetColors: string[]
}>()

const emit = defineEmits<{
  'save': []
  'delete': []
  'update-node-data': [field: string, value: any]
}>()

const isDefaultContent = computed(() => {
  const defaultContents = ['新线索', '新嫌疑人']
  return defaultContents.includes(props.node?.data?.content)
})

const defaultPlaceholder = computed(() => {
  if (!props.node) return ''
  if (props.node.data.type === 'suspect') return '请输入嫌疑人信息...'
  return '请输入线索内容...'
})

function updateNodeData(field: string, value: any) {
  emit('update-node-data', field, value)
}
</script>

<style scoped>
.empty-hint {
  text-align: center;
  color: var(--text-secondary);
  padding: 60px 20px;
  font-size: 14px;
}

.edit-field {
  padding: 0 16px;
}

.edit-field label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: var(--text);
  font-size: 14px;
}

textarea {
  resize: none;
  width: 100%;
  min-height: 80px;
  padding: 10px 14px;
  border: 2px solid #ffe79e;
  border-radius: 12px;
  font-size: 14px;
  background: var(--white);
  transition: all 0.3s;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
}

textarea:focus {
  box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.35);
}

.color-picker {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 0;
  padding: 0 16px;
}

.color-swatch {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 3px solid transparent;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.color-swatch:hover {
  transform: scale(1.2);
}

.color-swatch.active {
  border-color: var(--gold-deep);
  box-shadow: 0 0 0 3px rgba(212, 168, 67, 0.2);
}

.suspect-name-input {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #ffe79e;
  border-radius: 12px;
  font-size: 14px;
  background: var(--white);
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
  transition: all 0.3s;
}

.suspect-name-input:focus {
  box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.35);
}

.edit-btn {
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
  border: 1.5px solid;
  margin-left: 16px;
}

.save-btn {
  background: #D4A843;
  border-color: #B8922E;
  color: #fff;
  margin-right: 10px;
}

.save-btn:hover {
  background: #B8922E;
  border-color: #9A7A28;
  transform: translateY(-1px);
}

.delete-btn {
  background: #fff;
  border-color: #e75765;
  color: #c62828;
}

.delete-btn:hover {
  background: #ffebee;
  border-color: #c62828;
  transform: translateY(-1px);
}
</style>
