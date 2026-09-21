<template>
  <div class="home">
    <aside class="archive-rail">
      <div class="brand">Detective<i>●</i></div>
      <p>把散落的信息钉在一起，直到事实浮出墙面。</p>
      <span class="rail-label">ARCHIVE</span>
      <nav>
        <button class="active"><span>⌁</span>全部案件 <b>{{ cases.length }}</b></button>
        <button><span>◌</span>最近查看</button>
      </nav>
      <blockquote>每条线索都在等待一个正确的位置。</blockquote>
    </aside>

    <main class="archive-main">
      <header class="header">
        <div>
          <span class="eyebrow">PRIVATE INVESTIGATION ARCHIVE</span>
          <h1>案件档案室</h1>
          <p>建立案件，整理线索、人物关系与时间线。</p>
        </div>
        <button v-if="showLogout" class="logout-btn" @click="handleLogout">退出登录</button>
      </header>

      <section class="create-form" aria-label="新建案件">
        <div class="create-mark">＋</div>
        <label>
          <span>OPEN A NEW FILE / 新案件</span>
          <input v-model="newCaseName" placeholder="输入案件名称" @keyup.enter="handleCreate" />
        </label>
        <button @click="handleCreate" :disabled="!newCaseName.trim()">建立档案</button>
      </section>

      <div class="section-heading">
        <span>ACTIVE CASES</span><i></i><b>{{ cases.length }} 件</b>
      </div>

      <section v-if="cases.length" class="case-list">
        <article v-for="(c, index) in cases" :key="c.id" class="case-card" @click="$router.push(`/case/${c.id}`)">
          <div class="folder-tab">CASE {{ String(index + 1).padStart(2, '0') }}</div>
          <div class="case-seal">{{ c.name.slice(0, 1).toUpperCase() }}</div>
          <div class="case-copy">
            <span class="case-id">FILE NO. {{ c.id }}</span>
            <h2>{{ c.name }}</h2>
            <p>{{ c.description || '尚未填写案件摘要。进入档案后开始整理调查材料。' }}</p>
            <time>{{ new Date(c.created_at).toLocaleString() }}</time>
          </div>
          <span class="open-case">打开档案 <b>→</b></span>
          <button class="delete-case-btn" @click.stop="handleDelete(c.id)" aria-label="删除案件">删除</button>
        </article>
      </section>
      <section v-else class="empty-archive">
        <span>＋</span><h2>档案柜还是空的</h2><p>在上方为第一起案件建立档案。</p>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getCases, createCase, deleteCaseApi } from '@/api/index'

const cases = ref<any[]>([])
const newCaseName = ref('')
const showLogout = localStorage.getItem('auth_enabled') === 'true'

const handleLogout = () => {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('auth_enabled')
  window.location.href = '/login'
}

const fetchCases = async () => {
  try { cases.value = (await getCases()).data }
  catch (err) { console.error('获取案件列表失败', err) }
}

const handleCreate = async () => {
  if (!newCaseName.value.trim()) return
  try {
    await createCase(newCaseName.value.trim())
    newCaseName.value = ''
    await fetchCases()
  } catch (err) { console.error('创建案件失败', err) }
}

async function handleDelete(id: number) {
  if (!confirm('确定要删除该案件吗？所有便签、连线、时间线、对话历史将被永久删除。')) return
  try { await deleteCaseApi(id); await fetchCases() }
  catch (err) { console.error('删除案件失败', err) }
}

onMounted(fetchCases)
</script>

<style scoped>
.home { min-height: calc(100vh - 36px); display: grid; grid-template-columns: 220px minmax(0, 1fr); background: radial-gradient(circle at 88% 12%, rgba(255,255,255,.48), transparent 24%), var(--paper); }
.archive-rail { min-height: inherit; display: flex; flex-direction: column; padding: 34px 22px 28px; border-right: 1px solid var(--line); background: rgba(235,227,213,.62); }
.brand { font-family: var(--serif); font-size: 27px; font-weight: 700; letter-spacing: -.02em; }
.brand i { margin-left: 3px; color: var(--rust); font-size: 10px; font-style: normal; vertical-align: top; }
.archive-rail > p { margin: 9px 0 28px; color: var(--ink-soft); font-size: 12px; line-height: 1.65; }
.rail-label, .eyebrow, .section-heading span, .create-form label > span, .case-id { color: var(--ink-faint); font: 9px var(--mono); letter-spacing: .16em; }
.archive-rail nav { display: grid; gap: 5px; margin-top: 8px; }
.archive-rail nav button { width: 100%; display: flex; align-items: center; gap: 9px; padding: 10px; border: 0; border-radius: 10px; color: var(--ink-soft); background: transparent; text-align: left; cursor: default; font-size: 12px; }
.archive-rail nav button.active { color: var(--ink); background: rgba(255,255,255,.58); box-shadow: 0 2px 9px rgba(63,49,31,.06); }
.archive-rail nav b { margin-left: auto; color: var(--rust); font: 10px var(--mono); }
.archive-rail blockquote { margin: auto 0 0; padding: 0 2px 0 13px; border-left: 2px solid var(--rust); color: var(--ink-soft); font-family: var(--serif); font-size: 13px; font-style: italic; line-height: 1.55; }
.archive-main { width: min(1080px, 100%); margin: 0 auto; padding: 46px clamp(28px, 5vw, 74px) 70px; }
.header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 34px; }
.header h1 { margin: 8px 0 5px; color: var(--ink); font-family: var(--serif); font-size: clamp(34px, 5vw, 56px); font-weight: 600; line-height: 1; letter-spacing: -.05em; }
.header p { margin: 0; color: var(--ink-soft); font-size: 13px; }
.logout-btn { background: transparent; border: 1px solid var(--line); color: var(--ink-soft); padding: 8px 13px; border-radius: 999px; cursor: pointer; font-size: 12px; transition: .2s; }
.logout-btn:hover { background: var(--white); color: var(--rust-dark); border-color: var(--rust); }
.create-form { display: flex; align-items: center; gap: 16px; margin-bottom: 34px; padding: 18px 20px; border: 1px solid rgba(255,255,255,.74); border-radius: 18px; background: rgba(255,253,248,.78); box-shadow: 0 14px 36px rgba(59,45,29,.09); }
.create-mark { width: 43px; height: 43px; display: grid; place-items: center; flex: none; border-radius: 50%; color: #6e3a25; background: radial-gradient(circle at 35% 30%, #f1c6a4, #cf8053); box-shadow: 0 5px 13px rgba(106,59,32,.24); font-size: 23px; }
.create-form label { flex: 1; display: grid; gap: 5px; }
.create-form label > span { color: var(--rust-dark); }
.create-form input { width: 100%; padding: 4px 0; border: 0; border-bottom: 1px solid var(--line); outline: 0; color: var(--ink); background: transparent; font-family: var(--serif); font-size: 18px; }
.create-form > button { padding: 11px 18px; border: 0; border-radius: 999px; color: #f9f2e8; background: var(--ink); cursor: pointer; font-size: 12px; font-weight: 600; }
.create-form > button:disabled { opacity: .34; cursor: not-allowed; }
.section-heading { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.section-heading i { flex: 1; height: 1px; background: var(--line); }
.section-heading b { color: var(--ink-faint); font: 10px var(--mono); }
.case-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 30px 18px; }
.case-card { min-height: 210px; display: grid; grid-template-columns: 52px 1fr; gap: 16px; padding: 28px 24px 22px; border: 1px solid rgba(91,70,44,.13); cursor: pointer; border-radius: 4px 15px 10px 5px; color: var(--ink); background: linear-gradient(115deg, rgba(255,255,255,.28), transparent 45%), #e9dfc9; box-shadow: 0 8px 22px rgba(58,43,27,.12); transition: transform .28s cubic-bezier(.22,1,.36,1), box-shadow .28s ease; position: relative; }
.case-card:hover { transform: translateY(-6px) rotate(-.35deg); box-shadow: 0 20px 42px rgba(58,43,27,.18); }
.folder-tab { position: absolute; top: -18px; left: 16px; padding: 6px 17px 5px; border-radius: 8px 8px 0 0; color: var(--ink-soft); background: #ddd0b6; font: 8px var(--mono); letter-spacing: .13em; }
.case-seal { width: 48px; height: 48px; display: grid; place-items: center; border: 1px solid rgba(126,54,38,.42); border-radius: 50%; color: var(--rust-dark); font: 22px var(--serif); transform: rotate(-7deg); box-shadow: inset 0 0 0 4px rgba(182,95,62,.07); }
.case-copy { min-width: 0; }
.case-card h2 { margin: 7px 0; font-family: var(--serif); font-size: 23px; font-weight: 600; line-height: 1.15; }
.case-card p { margin: 0; color: var(--ink-soft); font-size: 12px; line-height: 1.6; }
.case-card time { display: block; margin-top: 16px; color: var(--ink-faint); font: 9px var(--mono); }
.open-case { position: absolute; left: 24px; bottom: 18px; color: var(--rust-dark); font-size: 11px; font-weight: 600; }
.open-case b { margin-left: 5px; }
.empty-archive { padding: 70px 20px; border: 1px dashed rgba(82,64,44,.25); border-radius: 16px; text-align: center; color: var(--ink-soft); }
.empty-archive > span { color: var(--rust); font-size: 28px; }
.empty-archive h2 { margin: 8px 0; font: 24px var(--serif); color: var(--ink); }
.empty-archive p { margin: 0; font-size: 12px; }
.delete-case-btn { opacity: 0; position: absolute; top: 14px; right: 14px; padding: 5px 9px; border: 1px solid rgba(159,62,53,.28); border-radius: 999px; color: var(--evidence-red); background: rgba(255,253,248,.65); cursor: pointer; font-size: 10px; transition: opacity .2s ease, background .2s ease; }
.case-card:hover .delete-case-btn, .delete-case-btn:focus-visible { opacity: 1; }
.delete-case-btn:hover { background: #f4ddd7; }
@media (max-width: 850px) { .home { grid-template-columns: 1fr; } .archive-rail { display: none; } .case-list { grid-template-columns: 1fr; } .archive-main { padding: 34px 20px 60px; } }
@media (max-width: 520px) { .create-form { align-items: stretch; flex-wrap: wrap; } .create-form label { min-width: calc(100% - 62px); } .create-form > button { width: 100%; } .header h1 { font-size: 38px; } }
</style>
