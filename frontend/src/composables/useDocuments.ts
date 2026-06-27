import { ref } from 'vue'
import { uploadDocument, getDocument } from '@/api/index'

export function useDocuments(caseId: number) {
  const fileInput = ref<HTMLInputElement | null>(null)
  const uploading = ref(false)
  const docList = ref<any[]>([])

  async function loadDocuments() {
    try {
      const res = await getDocument(caseId)
      docList.value = res.data
    } catch (err) {
      console.error('加载文档列表失败', err)
    }
  }

  function triggerFileInput() {
    fileInput.value?.click()
  }

  async function handleFileSelect(event: Event) {
    const input = event.target as HTMLInputElement
    if (input.files && input.files.length) {
      await uploadDocFile(input.files[0])
      input.value = ''
    }
  }

  async function handleDrop(event: DragEvent) {
    const files = event.dataTransfer?.files
    if (files && files.length) {
      await uploadDocFile(files[0])
    }
  }

  async function uploadDocFile(file: File) {
    if (!file.name.endsWith('.txt')) {
      alert('抱歉,目前只支持txt文件')
      return
    }
    uploading.value = true
    try {
      await uploadDocument(caseId, file)
      await loadDocuments()
      alert('上传成功')
    } catch (err: any) {
      console.error('上传失败', err)
      alert(err.response?.data?.detail || '上传失败')
    } finally {
      uploading.value = false
    }
  }

  return {
    fileInput,
    uploading,
    docList,
    loadDocuments,
    triggerFileInput,
    handleFileSelect,
    handleDrop,
  }
}
