<template>
  <main class="spatial-home" :class="{instant,departing}">
    <header class="topline">
      <a href="/" class="identity" aria-label="Detective 首页"><svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="14" cy="14" r="9"/><circle cx="14" cy="14" r="3"/><path d="m21 21 7 7M14 1v4M1 14h4"/></svg><span>DETECTIVE<small>侦探推理助手</small></span></a>
      <button class="find-trigger" @click="openIndex"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="10" r="6"/><path d="m15 15 5 5"/></svg><span>查找案件</span><kbd aria-hidden="true">Ctrl K</kbd></button>
      <div class="top-actions"><button v-if="showLogout" class="logout" @click="logout">退出</button><button class="new-trigger" @click="openCreate"><span>新建案件</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg></button></div>
    </header>

    <p v-if="preview" class="sample-banner">多案件排版预览 · 示例不写入真实档案 <a href="/">返回真实案件</a></p>
    <section class="archive-hero" aria-labelledby="hero-title">
      <div class="hero-copy"><p class="hero-kicker">从疑点，到推理。</p><h1 id="hero-title">线索<span>之间<svg class="title-star" viewBox="0 0 60 60" aria-hidden="true"><path d="M30 2v56M2 30h56M10 10l40 40M10 50l40-40"/><circle cx="30" cy="30" r="12"/></svg></span></h1><p class="hero-description">把散落的信息放在一起。<br>与小识，找到下一条线索。</p><button class="all-files" @click="openIndex">案件档案 <span>{{ cases.length }}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16M4 12h16M4 19h16"/></svg></button></div>

      <div ref="stage" class="file-stage" :class="{dragging}" @pointerdown="startDrag" @pointermove="moveDrag" @pointerup="endDrag" @pointercancel="cancelDrag" @lostpointercapture="cancelDrag" @wheel="wheel" @keydown.left.prevent="step(-1,true)" @keydown.right.prevent="step(1,true)">
        <div class="stage-ground" aria-hidden="true"/>
        <p v-if="loading" class="stage-message" role="status">正在调阅档案…</p>
        <div v-else-if="loadError" class="stage-message" role="alert">{{ loadError }}<button @click="fetchCases">重新加载</button></div>
        <template v-else>
          <article v-for="entry in visibleEntries" :key="entry.file?.id ?? 'new'" class="case-object" :class="{current:entry.index===active,blank:!entry.file}" :style="fileStyle(entry.index,entry.file?.id)" :aria-hidden="Math.abs(entry.index-active)>2">
            <button class="folder-button" :tabindex="Math.abs(entry.index-active)>2?-1:0" :aria-label="entry.file ? `取阅案件：${entry.file.name}` : '建立新案件'" @click="choose(entry.index,$event)" @dblclick="activate(entry.index,$event)">
              <span class="folder-back" aria-hidden="true"/>
              <span class="folder-tab">{{ entry.file ? `NO. ${number(entry.file.id)}` : 'NEW CASE' }}</span>
              <span class="insert-paper"><span class="paper-caption">{{ entry.file ? '案件摘要' : '案件名称' }}</span><span class="paper-excerpt">{{ entry.file?.description || (entry.file ? '在调查墙上整理线索、人物和事件。' : '下一份档案，留给新的疑点。') }}</span><span class="paper-ruling" aria-hidden="true"/></span>
              <span class="folder-cover"><span class="cover-grain" aria-hidden="true"/><span class="folder-fold" aria-hidden="true"/><span class="cover-top"><span>{{ entry.file ? '调查档案' : '空白档案' }}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3h10l4 4v14H5zM15 3v5h4M9 12h6m-6 4h4"/></svg></span>
                <span v-if="entry.file" class="evidence-label"><span class="label-index">CASE {{ number(entry.file.id) }}<svg viewBox="0 0 60 12" aria-hidden="true"><path d="M2 0v12M6 0v12M10 0v12M13 0v12M19 0v12M22 0v12M25 0v12M31 0v12M35 0v12M39 0v12M42 0v12M48 0v12M52 0v12M56 0v12"/></svg></span><span class="folder-name">{{ entry.file.name }}</span><span class="label-date">建档 <time :datetime="entry.file.created_at">{{ date(entry.file.created_at) }}</time></span></span>
                <span v-else class="blank-label"><svg viewBox="0 0 40 40" aria-hidden="true"><path d="M20 7v26M7 20h26"/></svg><span>新建<br>案件</span></span>
                <svg v-if="entry.file" class="fingerprint" viewBox="0 0 180 180" aria-hidden="true"><path d="M30 107C6 17 166 4 158 103M20 78c4-93 157-65 147 28M42 119C13 34 150 17 146 101c-2 34-24 61-44 71M54 135C18 50 135 28 134 97c-1 34-19 62-33 65M63 140c-31-61 50-94 58-51 7 39-10 62-18 62M76 147c-30-42 32-101 33-47 1 20-3 37-10 44M86 136c-19-34 1-73 11-41 5 15-1 31-6 36M48 148l10 13M31 132l8 13M139 130l-8 14M160 119l-7 20"/></svg>
                <span v-if="entry.file" class="file-tie" aria-hidden="true"><i/><i/><svg viewBox="0 0 24 116"><path d="M12 8C-1 5 0 25 13 23S24 5 12 8C6 23 16 72 12 104S-1 110 10 93s19 11 3 12L12 8"/></svg></span>
                <span class="folder-bottom"><span>{{ entry.file ? 'DETECTIVE / CASE FILE' : 'DETECTIVE / NEW FILE' }}</span><span class="seal" aria-hidden="true">{{ entry.file ? number(entry.file.id) : '+' }}</span></span>
              </span>
            </button>
          </article>
        </template>
      </div>

    </section>

    <footer class="archive-navigation"><span class="browse-hint"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 8-4 4 4 4m10-8 4 4-4 4M4 12h16"/></svg>拖动翻阅 / 双击进入</span><div class="archive-position"><button class="nav-arrow" aria-label="上一份档案" :disabled="active===0||loading" @click="step(-1,$event.detail===0)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m14 6-6 6 6 6"/></svg></button><span><b>{{ String(active+1).padStart(2,'0') }}</b><i>/</i>{{ String(cases.length+1).padStart(2,'0') }}</span><button class="nav-arrow" aria-label="下一份档案" :disabled="active>=cases.length||loading" @click="step(1,$event.detail===0)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m10 6 6 6-6 6"/></svg></button></div><button v-if="selected" class="manage-file" @click="openManage">管理档案<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></svg></button><span v-else class="manage-placeholder"/></footer>

    <dialog ref="indexDialog" class="index-dialog" aria-labelledby="search-heading" @click="outsideIndex"><div class="index-sheet"><div class="index-sheet-top"><h2 id="search-heading">案件索引</h2><button class="close-icon" aria-label="关闭案件索引" @click="indexDialog?.close()"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg></button></div><div class="index-search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="10" r="6"/><path d="m15 15 5 5"/></svg><input ref="searchInput" v-model="query" aria-label="查找案件" type="search" placeholder="案件名称或摘要…"/><button v-if="query" class="close-icon" aria-label="清空搜索" @click="query=''">清空</button></div><p class="result-count">{{ results.length }} 份档案</p><ul class="search-results"><li v-for="file in results" :key="file.id"><button @click="fromIndex(file)"><span>{{ number(file.id) }}</span><span><b>{{ file.name }}</b><small>{{ date(file.created_at) }}</small></span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7"/></svg></button></li><li v-if="!results.length" class="no-result">{{ loading?'正在调阅档案…':loadError||'没有找到匹配的案件。' }}</li></ul></div></dialog>

    <dialog ref="editor" class="file-editor" aria-labelledby="edit-title" @cancel.prevent="closeEditor" @click="outsideEditor"><div class="editor-paper"><button class="close-icon editor-close" aria-label="关闭" :disabled="busy" @click="closeEditor"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg></button><p class="editor-kicker">{{ managing ? `CASE ${number(selected?.id||0)}` : 'NEW CASE' }}</p><h2 id="edit-title">{{ managing?'管理档案':'新的疑点，新的档案。' }}</h2><template v-if="managing"><p class="manage-name">{{ selected?.name }}</p><p class="warning">删除后，案件的线索、关系、时间线和对话记录将无法恢复。</p><p v-if="error" role="alert" class="editor-error">{{ error }}</p><div class="editor-actions"><button :disabled="busy" @click="closeEditor">保留档案</button><button class="destructive" :disabled="busy||preview" @click="remove">{{ busy?'删除中…':'删除案件' }}</button></div></template><form v-else @submit.prevent="create"><input ref="nameInput" v-model="newName" aria-label="案件名称" placeholder="给案件起个名字…" required maxlength="120" :disabled="busy"/><p v-if="error" role="alert" class="editor-error">{{ error }}</p><div class="editor-actions"><button type="button" :disabled="busy" @click="closeEditor">取消</button><button class="create-submit" :disabled="busy||preview||!newName.trim()">{{ busy?'建立中…':'建立档案' }}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></button></div></form></div></dialog>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { CSSProperties } from 'vue'
import { createCase, deleteCaseApi, getCases } from '@/api'
interface CaseFile {id:number;name:string;description?:string|null;created_at:string}
const router=useRouter(),cases=ref<CaseFile[]>([]),active=ref(0),loading=ref(true),loadError=ref(''),instant=ref(false),departing=ref(false)
const stage=ref<HTMLElement>(),indexDialog=ref<HTMLDialogElement>(),editor=ref<HTMLDialogElement>(),searchInput=ref<HTMLInputElement>(),nameInput=ref<HTMLInputElement>()
const query=ref(''),newName=ref(''),error=ref(''),busy=ref(false),managing=ref(false),dragging=ref(false)
// Fractional browsing position drives geometry; active identifies the nearest file.
const position=ref(0)
watch(active,value=>{if(!dragging.value)position.value=value},{flush:'sync'})
const preview=import.meta.env.DEV&&new URLSearchParams(location.search).get('archivePreview')==='1'
const showLogout=localStorage.getItem('auth_enabled')==='true'
const selected=computed(()=>cases.value[active.value]||null)
const results=computed(()=>cases.value.filter(c=>`${c.name} ${c.description||''}`.toLocaleLowerCase().includes(query.value.trim().toLocaleLowerCase())))
const visibleEntries=computed(()=>Array.from({length:cases.value.length+1},(_,index)=>({index,file:cases.value[index]||null})).filter(entry=>Math.abs(entry.index-active.value)<=3))
const number=(id:number)=>String(id).padStart(3,'0')
const date=(value:string)=>{const d=new Date(value);return Number.isNaN(d.getTime())?'':new Intl.DateTimeFormat('zh-CN',{year:'numeric',month:'2-digit',day:'2-digit'}).format(d)}
const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches
function fileStyle(index:number,id?:number):CSSProperties {
  const delta=index-position.value,dist=Math.abs(delta)
  const colors=['#57695f','#303e40','#9b6550','#8b805e']
  return {'--offset':delta,'--yaw':`${delta*8-13}deg`,'--lift':`${dist*24}px`,'--rotation':`${delta*10-9}deg`,'--scale':String(1-dist*.085),'--folder':id?colors[id%colors.length]:'#d6c4a1','--folder-ink':id?'#e3ddcd':'#5c6253',zIndex:10-Math.round(dist),opacity:Math.max(0,Math.min(1,3-dist)),pointerEvents:dist>2?'none':'auto'}
}
function step(direction:number,keyboard=false){instant.value=keyboard;active.value=Math.max(0,Math.min(cases.value.length,active.value+direction))}
function choose(index:number,event:MouseEvent){if(Date.now()<suppressClickUntil||departing.value)return;instant.value=event.detail===0;if(!cases.value[index]){void openCreate(event);return}active.value=index;if(event.detail===0)void enter(event)}
function activate(index:number,event:MouseEvent){if(Date.now()<suppressClickUntil||departing.value||!cases.value[index])return;active.value=index;void enter(event)}
async function enter(event:MouseEvent){if(!selected.value||preview||departing.value)return;const id=selected.value.id;if(event.detail!==0&&!reduced()){departing.value=true;const file=stage.value?.querySelector('.case-object.current');const motion=file?.animate([{transform:getComputedStyle(file).transform,opacity:1},{transform:'translate(-50%,-50%) translateY(-28px) rotate(-3deg) scale(1.05)',opacity:0}],{duration:190,easing:'cubic-bezier(.23,1,.32,1)'});try{await motion?.finished}catch{ /* Navigation can interrupt motion. */ }}await router.push(`/case/${id}`);departing.value=false}
async function fetchCases(){loading.value=true;loadError.value='';try{cases.value=(await getCases()).data;cases.value.sort((a,b)=>(Date.parse(b.created_at)||0)-(Date.parse(a.created_at)||0)||b.id-a.id);active.value=Math.min(active.value,cases.value.length)}catch{loadError.value='档案加载失败，请重试。'}finally{loading.value=false}}
async function openIndex(){query.value='';indexDialog.value?.showModal();await nextTick();searchInput.value?.focus()}
function fromIndex(file:CaseFile){instant.value=true;active.value=cases.value.findIndex(c=>c.id===file.id);indexDialog.value?.close()}
function outsideIndex(event:MouseEvent){if(event.target===indexDialog.value)indexDialog.value?.close()}
let editorAnimation:Animation|undefined
async function showEditor(event:MouseEvent){error.value='';await nextTick();editor.value?.showModal();if(event.detail!==0&&!reduced()){editorAnimation?.cancel();editorAnimation=editor.value?.querySelector('.editor-paper')?.animate([{transform:'translateY(18px) rotate(-2deg)',opacity:0},{transform:'translateY(0) rotate(-1deg)',opacity:1}],{duration:240,easing:'cubic-bezier(.23,1,.32,1)'})}}
async function openCreate(event:MouseEvent){managing.value=false;newName.value='';await showEditor(event);nameInput.value?.focus()}
async function openManage(event:MouseEvent){managing.value=true;await showEditor(event)}
function closeEditor(){if(!busy.value){editorAnimation?.cancel();editor.value?.close()}}
function outsideEditor(event:MouseEvent){if(event.target===editor.value)closeEditor()}
async function create(){if(busy.value||preview||!newName.value.trim())return;busy.value=true;error.value='';try{const response=await createCase(newName.value.trim());cases.value.unshift(response.data);active.value=0;instant.value=true;busy.value=false;closeEditor()}catch{error.value='建立失败，请重试。'}finally{busy.value=false}}
async function remove(){const id=selected.value?.id;if(!id||busy.value||preview||!confirm('确定永久删除此案件及其全部调查记录吗？'))return;busy.value=true;error.value='';try{await deleteCaseApi(id);cases.value=cases.value.filter(c=>c.id!==id);active.value=Math.min(active.value,cases.value.length);busy.value=false;closeEditor()}catch{error.value='删除失败，档案仍然保留。'}finally{busy.value=false}}
function logout(){localStorage.removeItem('auth_token');localStorage.removeItem('auth_enabled');location.href='/login'}
function shortcut(event:KeyboardEvent){const target=event.target as HTMLElement;if((event.key.toLowerCase()==='k'&&(event.ctrlKey||event.metaKey))||event.key==='/'&&!target.closest('input,textarea,select,[contenteditable="true"]')){if(editor.value?.open)return;event.preventDefault();void openIndex()}}
let startX=0,startY=0,pointer:number|null=null,dragOrigin=0,spacing=157,suppressClickUntil=0,wheelAt=0
function startDrag(event:PointerEvent){if(event.button!==0||pointer!==null)return;pointer=event.pointerId;startX=event.clientX;startY=event.clientY;dragOrigin=position.value;const file=stage.value?.querySelector('.case-object');spacing=file?parseFloat(getComputedStyle(file).getPropertyValue('--spacing'))||157:157}
function moveDrag(event:PointerEvent){
  if(pointer!==event.pointerId)return
  const dx=event.clientX-startX,dy=event.clientY-startY
  if(!dragging.value&&Math.abs(dx)>10&&Math.abs(dx)>Math.abs(dy)){dragging.value=true;stage.value?.setPointerCapture(event.pointerId)}
  if(!dragging.value)return
  instant.value=false
  const raw=dragOrigin-dx/spacing,bounded=Math.max(0,Math.min(cases.value.length,raw))
  const overshoot=raw-bounded
  position.value=bounded+.35*overshoot/(1+Math.abs(overshoot))
  active.value=Math.max(0,Math.min(cases.value.length,Math.round(bounded)))
}
function finishDrag(){
  if(dragging.value){suppressClickUntil=Date.now()+250;position.value=active.value}
  if(pointer!==null&&stage.value?.hasPointerCapture(pointer))stage.value.releasePointerCapture(pointer)
  pointer=null;dragging.value=false
}
function endDrag(event:PointerEvent){if(pointer!==event.pointerId)return;if(dragging.value)moveDrag(event);finishDrag()}
function cancelDrag(){finishDrag()}
function wheel(event:WheelEvent){if(event.ctrlKey||Math.abs(event.deltaX)<Math.abs(event.deltaY))return;event.preventDefault();if(Date.now()-wheelAt<220)return;wheelAt=Date.now();step(Math.sign(event.deltaX))}
onMounted(async()=>{document.addEventListener('keydown',shortcut);if(preview){cases.value=(await import('../dev/archiveFixtures')).archiveFixtures;loading.value=false}else await fetchCases()})
onBeforeUnmount(()=>{document.removeEventListener('keydown',shortcut);editorAnimation?.cancel();editor.value?.close();indexDialog.value?.close()})
</script>

<style scoped src="../styles/spatial-home.css"/>
