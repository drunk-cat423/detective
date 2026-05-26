<template>
  <div class="home">
    <h1>案件管理</h1>

    <!-- 新建区域 -->
    <div class="create-form">
      <input
        v-model="newCaseName"
        placeholder="输入案件名称"
        @keyup.enter="handleCreate"
      />
      <button @click="handleCreate" :disabled="!newCaseName.trim()">
        新建案件
      </button>
    </div>

    <!-- 案件列表 -->
    <div v-if="cases.length" class="case-list">
      <div
        v-for="c in cases"
        :key="c.id"
        class="case-card"
        @click="$router.push(`/case/${c.id}`)"
      >
        <h3>{{ c.name }}</h3>
        <p v-if="c.description">{{ c.description }}</p>
        <span class="time">{{ new Date(c.created_at).toLocaleString() }}</span>
      </div>
    </div>
    <p v-else>暂无案件，请创建一个吧</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getCases, createCase } from '@/api/index'

const cases = ref<any[]>([])        // 案件列表
const newCaseName = ref('')         // 输入框内容

const fetchCases = async () => {
  try {
    const res = await getCases()
    cases.value = res.data
  } catch (err) {
    console.error('获取案件列表失败', err)
  }
}

const handleCreate = async () => {
  if (!newCaseName.value.trim()) return
  try {
    await createCase(newCaseName.value.trim())
    newCaseName.value = ''
    await fetchCases()
  } catch (err) {
    console.error('创建案件失败', err)
  }
}

onMounted(fetchCases)
</script>

<style scoped>
.home {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}
.create-form {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.create-form input {
  flex: 1;
  padding: 8px;
  font-size: 16px;
}
.create-form button {
  padding: 8px 20px;
  cursor: pointer;
}
.case-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.case-card {
  border: 1px solid #ccc;
  padding: 15px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.2s;
}
.case-card:hover {
  background: #f5f5f5;
}
.time {
  color: #999;
  font-size: 12px;
}
</style>