let cachedTexture = ''

function seedFromText(text: string) {
  let value = 2166136261
  for (let i = 0; i < text.length; i += 1) {
    value ^= text.charCodeAt(i)
    value = Math.imul(value, 16777619)
  }
  return value >>> 0
}

function createRandom(seed: number) {
  let state = seed || 1
  return () => {
    state ^= state << 13
    state ^= state >>> 17
    state ^= state << 5
    return (state >>> 0) / 4294967296
  }
}

function range(random: () => number, min: number, max: number) {
  return min + random() * (max - min)
}

export function createLinenTexture() {
  if (cachedTexture || typeof document === 'undefined') return cachedTexture

  const width = 1600
  const height = 1000
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) return ''

  const random = createRandom(seedFromText('detective-archive-linen-v1'))

  const base = context.createLinearGradient(0, 0, width, height)
  base.addColorStop(0, '#dfcfb1')
  base.addColorStop(.48, '#d6c3a3')
  base.addColorStop(1, '#cbb28d')
  context.fillStyle = base
  context.fillRect(0, 0, width, height)

  // Large, low-contrast dye variation. These broad fields prevent the cloth
  // from reading as one flat beige rectangle.
  for (let index = 0; index < 58; index += 1) {
    const x = random() * width
    const y = random() * height
    const radius = range(random, 90, 330)
    const light = random() > .52
    const wash = context.createRadialGradient(x, y, 0, x, y, radius)
    wash.addColorStop(0, light ? 'rgba(255,247,226,.055)' : 'rgba(104,77,47,.045)')
    wash.addColorStop(1, 'rgba(0,0,0,0)')
    context.fillStyle = wash
    context.fillRect(x - radius, y - radius, radius * 2, radius * 2)
  }

  context.lineCap = 'round'

  // Warp fibres: longer, mostly horizontal strands.
  for (let index = 0; index < 2100; index += 1) {
    const x = random() * width
    const y = random() * height
    const length = range(random, 8, 74)
    const drift = range(random, -2.4, 2.4)
    context.beginPath()
    context.moveTo(x, y)
    context.quadraticCurveTo(x + length * .52, y + drift, x + length, y + drift * .35)
    context.lineWidth = range(random, .32, .82)
    context.strokeStyle = random() > .44
      ? `rgba(255,249,232,${range(random, .065, .14)})`
      : `rgba(91,69,43,${range(random, .035, .095)})`
    context.stroke()
  }

  // Weft fibres: shorter vertical strands break the horizontal rhythm.
  for (let index = 0; index < 1650; index += 1) {
    const x = random() * width
    const y = random() * height
    const length = range(random, 5, 38)
    const drift = range(random, -1.9, 1.9)
    context.beginPath()
    context.moveTo(x, y)
    context.quadraticCurveTo(x + drift, y + length * .5, x + drift * .35, y + length)
    context.lineWidth = range(random, .3, .72)
    context.strokeStyle = random() > .48
      ? `rgba(250,241,218,${range(random, .05, .12)})`
      : `rgba(99,74,45,${range(random, .03, .085)})`
    context.stroke()
  }

  // Slubs and knots are sparse and irregular; they are the material's visual
  // signature, so they must not form another repeating dot pattern.
  for (let index = 0; index < 240; index += 1) {
    const x = random() * width
    const y = random() * height
    const length = range(random, 7, 30)
    const angle = random() > .32 ? range(random, -.18, .18) : range(random, 1.38, 1.76)
    context.beginPath()
    context.moveTo(x, y)
    context.lineTo(x + Math.cos(angle) * length, y + Math.sin(angle) * length)
    context.lineWidth = range(random, .8, 1.75)
    context.strokeStyle = random() > .5
      ? `rgba(255,247,225,${range(random, .1, .2)})`
      : `rgba(91,66,39,${range(random, .07, .15)})`
    context.stroke()
  }

  // A used board has a few punctures, never an evenly-distributed constellation.
  for (let index = 0; index < 44; index += 1) {
    const x = random() * width
    const y = random() * height
    const radius = range(random, .55, 1.35)
    context.beginPath()
    context.arc(x, y, radius + .8, 0, Math.PI * 2)
    context.fillStyle = 'rgba(255,245,222,.16)'
    context.fill()
    context.beginPath()
    context.arc(x + .35, y + .45, radius, 0, Math.PI * 2)
    context.fillStyle = `rgba(75,53,31,${range(random, .12, .24)})`
    context.fill()
  }

  const light = context.createRadialGradient(width * .34, height * .26, 30, width * .48, height * .46, width * .76)
  light.addColorStop(0, 'rgba(255,250,236,.09)')
  light.addColorStop(.56, 'rgba(255,255,255,0)')
  light.addColorStop(1, 'rgba(74,48,25,.12)')
  context.fillStyle = light
  context.fillRect(0, 0, width, height)

  try {
    cachedTexture = canvas.toDataURL('image/webp', .9)
  } catch {
    cachedTexture = canvas.toDataURL('image/png')
  }
  return cachedTexture
}
