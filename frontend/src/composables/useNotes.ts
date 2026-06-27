import { ref } from 'vue'
import {
  getNotes, createNote, updateNote, deleteNote,
  getConnections, createConnection, updateConnection, deleteConnection,
} from '@/api/index'

export function useNotes(caseId: number) {
  const nodes = ref<any[]>([])
  const edges = ref<any[]>([])
  const selectedNode = ref<any | null>(null)
  const vueFlowRef = ref<any>(null)

  const presetColors = [
    '#FFF9C4', '#FFCCBC', '#C8E6C9', '#BBDEFB',
    '#E1BEE7', '#FFE0B2', '#B2EBF2', '#F5F5F5',
  ]

  const centerPoint = { x: 400, y: 300 }

  async function loadNotes() {
    try {
      const res = await getNotes(caseId)
      const serverNotes = res.data
      nodes.value = serverNotes.map((n: any) => ({
        id: String(n.id),
        type: 'note',
        position: { x: n.pos_x, y: n.pos_y },
        data: {
          content: n.content,
          type: n.type,
          color: n.color,
          name: n.name || '',
        },
        style: { width: `${n.width}px`, height: `${n.height}px` },
      }))
    } catch (err) {
      console.error('加载便签失败', err)
    }
  }

  async function loadConnections() {
    try {
      const res = await getConnections(caseId)
      edges.value = res.data.map((c: any) => ({
        id: String(c.id),
        source: String(c.from_note_id),
        target: String(c.to_note_id),
        label: c.label,
      }))
    } catch (err) {
      console.error('加载连线失败', err)
    }
  }

  async function addNote(type: string) {
    const defaultColors: Record<string, string> = {
      clue: '#FFF9C4',
      suspect: '#FFCCBC',
    }
    const defaultName = type === 'suspect' ? '未知' : ''
    try {
      const res = await createNote(caseId, {
        type,
        content: type === 'clue' ? '新线索' : '新嫌疑人',
        name: defaultName,
        color: defaultColors[type],
        pos_x: Math.random() * 400,
        pos_y: Math.random() * 300,
        width: 200,
        height: 120,
      })
      nodes.value.push({
        id: String(res.data.id),
        type: 'note',
        position: { x: res.data.pos_x, y: res.data.pos_y },
        data: {
          content: res.data.content,
          type: res.data.type,
          name: res.data.name || '',
          color: res.data.color,
        },
        style: { width: `${res.data.width}px`, height: `${res.data.height}px` },
      })
    } catch (err) {
      console.error('创建便签失败', err)
    }
  }

  async function onConnect(connection: any) {
    const { source, target, sourceHandle, targetHandle } = connection
    if (edges.value.some((e: any) =>
      e.source === source && e.target === target &&
      e.sourceHandle === sourceHandle && e.targetHandle === targetHandle
    )) return

    if (source === target) return

    try {
      const res = await createConnection(caseId, {
        from_note_id: Number(source),
        to_note_id: Number(target),
        label: '',
      })
      edges.value.push({
        id: String(res.data.id),
        source,
        target,
        sourceHandle: sourceHandle ?? undefined,
        targetHandle: targetHandle ?? undefined,
        label: '',
      })
    } catch (err) {
      console.error('创建连线失败', err)
    }
  }

  async function onNodesChange(changes: any[]) {
    for (const change of changes) {
      if (change.type === 'position' && change.position) {
        await updateNote(caseId, Number(change.id), {
          pos_x: change.position.x,
          pos_y: change.position.y,
        })
      }
      if (change.type === 'dimensions' && change.dimensions) {
        await updateNote(caseId, Number(change.id), {
          width: change.dimensions.width,
          height: change.dimensions.height,
        })
      }
    }
  }

  function onEdgesChange() {}

  function selectNode({ node }: { node: any }) {
    selectedNode.value = node
  }

  function deselectNode() {
    selectedNode.value = null
  }

  async function saveSelectedNode() {
    if (!selectedNode.value) return
    const n = selectedNode.value
    try {
      await updateNote(caseId, Number(n.id), {
        content: n.data.content,
        type: n.data.type,
        color: n.data.color,
        name: n.data.name || '',
      })
      const idx = nodes.value.findIndex(node => node.id === n.id)
      if (idx !== -1) {
        nodes.value[idx].data = { ...n.data }
      }
      alert('保存成功')
    } catch (err) {
      console.error('保存便签失败', err)
    }
  }

  async function deleteSelectedNode() {
    if (!selectedNode.value) return
    if (!confirm('确认删除这个便签？关联的连线也会一并删除。')) return
    try {
      await deleteNote(caseId, Number(selectedNode.value.id))
      edges.value = edges.value.filter((e: any) => e.source !== selectedNode.value.id && e.target !== selectedNode.value.id)
      nodes.value = nodes.value.filter((n: any) => n.id !== selectedNode.value.id)
      selectedNode.value = null
    } catch (err) {
      console.error('删除便签失败', err)
    }
  }

  function goToCenter(vueFlowInstance?: any) {
    const instance = vueFlowInstance || vueFlowRef.value
    instance?.setCenter(centerPoint.x, centerPoint.y, { zoom: 1 })
  }

  // 连线备注相关
  const editingEdgeForLabel = ref<any>(null)
  const editEdgeLabelText = ref('')
  const editEdgePosition = ref({ x: 0, y: 0 })
  const edgeEditInput = ref<HTMLInputElement | null>(null)

  const defaultEdgeOptions = {
    labelStyle: {
      fontSize: '18px',
      fontWeight: 'bold',
      fill: '#333',
    },
    labelBgStyle: {
      fill: 'transparent',
    },
    labelBgPadding: [4, 4] as [number, number],
    labelBgBorderRadius: 4,
    style: {
      stroke: '#b1b1b7',
      strokeWidth: 2,
    },
  }

  function onEdgeDoubleClick(params: any) {
    const { edge, event } = params
    event.stopPropagation()

    editingEdgeForLabel.value = edge
    editEdgeLabelText.value = edge.label || ''
    editEdgePosition.value = { x: event.clientX, y: event.clientY }
  }

  async function saveEdgeLabelEdit() {
    if (!editingEdgeForLabel.value) return
    const edge = editingEdgeForLabel.value
    const newLabel = editEdgeLabelText.value.trim()
    const oldLabel = edge.label || ''

    if (newLabel !== oldLabel) {
      try {
        await updateConnection(caseId, parseInt(edge.id), { label: newLabel })
        const targetEdge = edges.value.find((e: any) => e.id === edge.id)
        if (targetEdge) targetEdge.label = newLabel
      } catch (err) {
        console.error('保存连线备注失败', err)
        alert('保存失败，请重试')
      }
    }
    editingEdgeForLabel.value = null
    editEdgeLabelText.value = ''
  }

  async function deleteCurrentEdge() {
    if (!editingEdgeForLabel.value) return
    const edge = editingEdgeForLabel.value
    const edgeId = edge.id

    if (!confirm('确定要删除这条连线吗？')) return

    const edgeToDelete = edge
    editingEdgeForLabel.value = null
    editEdgeLabelText.value = ''

    try {
      await deleteConnection(caseId, parseInt(edgeId))
      edges.value = edges.value.filter((e: any) => e.id !== edgeId)
    } catch (err: any) {
      console.error('删除连线失败', err)
      alert('删除失败：' + (err.response?.data?.detail || err.message))

      editingEdgeForLabel.value = edgeToDelete
      editEdgeLabelText.value = edgeToDelete.label || ''
    }
  }

  return {
    nodes,
    edges,
    selectedNode,
    vueFlowRef,
    presetColors,
    centerPoint,
    editingEdgeForLabel,
    editEdgeLabelText,
    editEdgePosition,
    edgeEditInput,
    defaultEdgeOptions,
    loadNotes,
    loadConnections,
    addNote,
    onConnect,
    onNodesChange,
    onEdgesChange,
    selectNode,
    deselectNode,
    saveSelectedNode,
    deleteSelectedNode,
    goToCenter,
    onEdgeDoubleClick,
    saveEdgeLabelEdit,
    deleteCurrentEdge,
  }
}
