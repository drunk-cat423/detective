export type BoardPoint = { x: number; y: number }

export function nodeSeed(id: string | number) {
  return Array.from(String(id)).reduce((sum, char) => sum + char.charCodeAt(0), 0)
}

export function pinPercent(id: string | number) {
  return 43 + (nodeSeed(id) % 15)
}

export function nodeSize(node: any) {
  const width = Number.parseFloat(String(node?.style?.width ?? '190')) || 190
  const height = Number.parseFloat(String(node?.style?.height ?? '124')) || 124
  return { width, height }
}

export function nodePinAnchor(node: any): BoardPoint {
  const { width } = nodeSize(node)
  return {
    x: Number(node?.position?.x ?? 0) + width * (pinPercent(node?.id) / 100),
    y: Number(node?.position?.y ?? 0),
  }
}
