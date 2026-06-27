import { ref, nextTick } from 'vue'
import {
  getKnownInfos,
  createKnownInfo,
  updateKnownInfo,
  deleteKnownInfo,
} from '@/api/index'

export function useKnownInfo(caseId: number) {
  const knownInfos = ref<any[]>([])
  const newInfoContent = ref('')
  const editingId = ref<number | null>(null)
  const editInfoContent = ref('')
  const editTextareaRefs = ref<Record<number, HTMLTextAreaElement>>({})

  async function loadKnownInfos() {
    try {
      const res = await getKnownInfos(caseId)
      knownInfos.value = res.data
    } catch (err) {
      console.error('加载已知信息失败', err)
    }
  }

  async function addKnownInfo() {
    const content = newInfoContent.value.trim()
    if (!content) return
    try {
      await createKnownInfo(caseId, content)
      newInfoContent.value = ''
      await loadKnownInfos()
    } catch (err) {
      console.error('添加失败', err)
    }
  }

  function startEditInfo(info: any) {
    editingId.value = info.id
    editInfoContent.value = info.content
    nextTick(() => {
      setTimeout(() => {
        const ta = editTextareaRefs.value[info.id]
        if (ta) {
          ta.focus()
          ta.selectionStart = ta.selectionEnd = ta.value.length
        }
      }, 0)
    })
  }

  async function saveEditInfo(info: any) {
    if (!editingId.value) return
    const newContent = editInfoContent.value.trim()
    if (newContent && newContent !== info.content) {
      try {
        await updateKnownInfo(caseId, info.id, newContent)
        await loadKnownInfos()
      } catch (err) {
        console.error('更新失败', err)
      }
    }
    editingId.value = null
    editInfoContent.value = ''
  }

  async function deleteKnownInfoItem(infoId: number) {
    if (!confirm('确定删除该条信息吗')) return
    try {
      await deleteKnownInfo(caseId, infoId)
      await loadKnownInfos()
    } catch (err) {
      console.error('删除失败', err)
    }
  }

  return {
    knownInfos,
    newInfoContent,
    editingId,
    editInfoContent,
    editTextareaRefs,
    loadKnownInfos,
    addKnownInfo,
    startEditInfo,
    saveEditInfo,
    deleteKnownInfoItem,
  }
}
