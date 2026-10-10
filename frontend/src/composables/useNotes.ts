import { ref } from 'vue'
import {
  getNotes, createNote, updateNote, deleteNote,
  getConnections, createConnection, updateConnection, deleteConnection,
} from '@/api/index'

type CardStyle = 'torn' | 'memo' | 'index' | 'ticket' | 'clipping' | 'dossier'

const clueCardStyles: CardStyle[] = ['torn', 'memo', 'index', 'ticket', 'clipping']

function resolveCardStyle(id: string | number, type: string): CardStyle {
  if (type === 'suspect') return 'dossier'
  const seed = Array.from(String(id)).reduce((sum, char) => sum + char.charCodeAt(0), 0)
  return clueCardStyles[seed % clueCardStyles.length]
}

function cardDimensions(style: CardStyle) {
  const sizes: Record<CardStyle, { width: number; height: number }> = {
    torn: { width: 190, height: 124 },
    memo: { width: 178, height: 148 },
    index: { width: 206, height: 126 },
    ticket: { width: 214, height: 108 },
    clipping: { width: 184, height: 154 },
    dossier: { width: 202, height: 146 },
  }
  return sizes[style]
}

export function useNotes(caseId: number) {
  const nodes = ref<any[]>([])
  const edges = ref<any[]>([])
  const selectedNode = ref<any | null>(null)

  const presetColors = [
    '#F4EDDC', '#F7F3E8', '#F6F4EC', '#ECD3CD',
    '#CFC6E0', '#DDE3CC', '#D8BE8B', '#EFE9DC',
  ]

  const legacyPaperColors: Record<string, string> = {
    '#FFF9C4': '#F4EDDC',
    '#FFCCBC': '#ECD3CD',
    '#C8E6C9': '#DDE3CC',
    '#BBDEFB': '#E7ECE8',
    '#E1BEE7': '#CFC6E0',
    '#FFE0B2': '#D8BE8B',
    '#B2EBF2': '#E4ECE6',
    '#F5F5F5': '#F7F3E8',
  }

  async function loadNotes() {
    try {
      const res = await getNotes(caseId)
      const serverNotes = res.data
      nodes.value = serverNotes.map((n: any) => {
        const cardStyle = resolveCardStyle(n.id, n.type)
        const { width, height } = cardDimensions(cardStyle)
        return {
          id: String(n.id),
          position: { x: n.pos_x, y: n.pos_y },
          data: {
            content: n.content,
            type: n.type,
            color: legacyPaperColors[String(n.color).toUpperCase()] || n.color,
            name: n.name || '',
            cardStyle,
          },
          style: { width: `${width}px`, height: `${height}px` },
        }
      })
    } catch (err) {
      console.error('加载便签失败', err)
    }
  }

  async function loadConnections() {
    try {
      const res = await getConnections(caseId)
      edges.value = res.data.map((c: any) => {
        return {
          id: String(c.id),
          source: String(c.from_note_id),
          target: String(c.to_note_id),
          label: c.label,
        }
      })
    } catch (err) {
      console.error('加载连线失败', err)
    }
  }

  async function addNote(type: string, position?: { x: number; y: number }) {
    const defaultColors: Record<string, string> = {
      clue: '#F4EDDC',
      suspect: '#ECD3CD',
    }
    const defaultName = type === 'suspect' ? '未知' : ''
    try {
      const res = await createNote(caseId, {
        type,
        content: type === 'clue' ? '新线索' : '新嫌疑人',
        name: defaultName,
        color: defaultColors[type],
        pos_x: position?.x ?? Math.random() * 400,
        pos_y: position?.y ?? Math.random() * 300,
        width: type === 'suspect' ? 202 : 190,
        height: type === 'suspect' ? 142 : 124,
      })
      const cardStyle = resolveCardStyle(res.data.id, res.data.type)
      const { width, height } = cardDimensions(cardStyle)
      nodes.value.push({
        id: String(res.data.id),
        position: { x: res.data.pos_x, y: res.data.pos_y },
        data: {
          content: res.data.content,
          type: res.data.type,
          name: res.data.name || '',
          color: res.data.color,
          cardStyle,
        },
        style: { width: `${width}px`, height: `${height}px` },
      })
      return res.data
    } catch (err) {
      console.error('创建便签失败', err)
      return null
    }
  }

  async function onConnect(connection: { source: string; target: string }) {
    const { source, target } = connection
    if (edges.value.some(e => e.source === source && e.target === target)) return

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
      return true
    } catch (err) {
      console.error('保存便签失败', err)
      return false
    }
  }

  async function deleteSelectedNode(requireConfirmation = true) {
    if (!selectedNode.value) return false
    if (requireConfirmation && !confirm('确认删除这个便签？关联的连线也会一并删除。')) return false
    try {
      await deleteNote(caseId, Number(selectedNode.value.id))
      edges.value = edges.value.filter((e: any) => e.source !== selectedNode.value.id && e.target !== selectedNode.value.id)
      nodes.value = nodes.value.filter((n: any) => n.id !== selectedNode.value.id)
      selectedNode.value = null
      return true
    } catch (err) {
      console.error('删除便签失败', err)
      return false
    }
  }

  // 连线备注相关
  const editingEdgeForLabel = ref<any>(null)
  const editEdgeLabelText = ref('')
  const editEdgePosition = ref({ x: 0, y: 0 })

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
    presetColors,
    editingEdgeForLabel,
    editEdgeLabelText,
    editEdgePosition,
    loadNotes,
    loadConnections,
    addNote,
    onConnect,
    onNodesChange,
    selectNode,
    deselectNode,
    saveSelectedNode,
    deleteSelectedNode,
    onEdgeDoubleClick,
    saveEdgeLabelEdit,
    deleteCurrentEdge,
  }
}
