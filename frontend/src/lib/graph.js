// Helpers for the knowledge graph page: data preparation, relationships and the canvas painter.

/** Node radius in graph units; arrows end at the node's edge because force-graph is told this size. */
export const NODE_RADIUS = 8
export const SELECTED_RADIUS = 10
/** Below this zoom, labels would overlap: only the selected topic and its neighbours are labelled. */
export const LABEL_MIN_SCALE = 0.7
const LABEL_LINE_CHARS = 14

const FALLBACK_PALETTE = {
  completed: '#14b8a6',
  in_progress: '#f59e0b',
  unlocked: '#99f6e4',
  locked: '#64748b',
  ink: '#0f172a',
  primary: '#0f766e',
  primaryDark: '#134e4a',
  muted: '#64748b',
  link: '#cbd5e1',
  card: '#ffffff',
}

/** Colours for the canvas, read from the palette tokens in index.css so the graph matches the badges. */
export function readPalette(element = document.documentElement) {
  const styles = getComputedStyle(element)
  const token = (name, fallback) => styles.getPropertyValue(name).trim() || fallback
  return {
    completed: token('--status-completed', FALLBACK_PALETTE.completed),
    in_progress: token('--status-in-progress', FALLBACK_PALETTE.in_progress),
    unlocked: token('--status-unlocked', FALLBACK_PALETTE.unlocked),
    locked: token('--status-locked', FALLBACK_PALETTE.locked),
    ink: token('--ink', FALLBACK_PALETTE.ink),
    primary: token('--primary', FALLBACK_PALETTE.primary),
    primaryDark: token('--primary-dark', FALLBACK_PALETTE.primaryDark),
    muted: token('--muted-foreground', FALLBACK_PALETTE.muted),
    link: token('--input', FALLBACK_PALETTE.link),
    card: token('--card', FALLBACK_PALETTE.card),
  }
}

/**
 * The API response as force-graph input. Copies every node and link, because force-graph writes
 * positions into nodes and replaces link ends with node objects.
 */
export function toGraphData(graph) {
  return {
    nodes: graph.nodes.map((node) => ({ ...node })),
    links: graph.links.map((link) => ({ ...link })),
  }
}

/** Topics that list `id` as a prerequisite. */
export function unlocksOf(id, topics) {
  return topics.filter((topic) => topic.prerequisites.includes(id))
}

/** Prerequisites of a topic that aren't completed yet: what stands between the learner and it. */
export function missingPrerequisites(topic, topicsById) {
  return topic.prerequisites.map((id) => topicsById.get(id)).filter((t) => t && t.status !== 'completed')
}

/** The selected topic plus its direct prerequisites and the topics it unlocks. */
export function relatedIds(selectedId, topics) {
  if (!selectedId) return null
  const selected = topics.find((t) => t.id === selectedId)
  if (!selected) return null
  return new Set([selectedId, ...selected.prerequisites, ...unlocksOf(selectedId, topics).map((t) => t.id)])
}

export function statusCounts(topics) {
  const counts = { completed: 0, in_progress: 0, unlocked: 0, locked: 0 }
  for (const topic of topics) counts[topic.status] = (counts[topic.status] ?? 0) + 1
  return counts
}

/**
 * A topic name as one line, or two balanced lines when it is long ("API Integration" / "in React"),
 * so labels of topics in neighbouring columns don't run into each other.
 */
export function wrapLabel(name, max = LABEL_LINE_CHARS) {
  const words = name.split(/\s+/).filter(Boolean)
  if (name.length <= max || words.length < 2) return [words.join(' ')]
  let best = null
  for (let i = 1; i < words.length; i++) {
    const lines = [words.slice(0, i).join(' '), words.slice(i).join(' ')]
    const longest = Math.max(lines[0].length, lines[1].length)
    if (!best || longest < best.longest) best = { lines, longest }
  }
  return best.lines
}

/** The id of a link end, before (string) or after (node object) force-graph has resolved it. */
export const endId = (end) => (typeof end === 'object' && end !== null ? end.id : end)

/**
 * Draw one topic. Colour shows the status, and so does a mark, so the states don't rely on colour
 * alone: a tick for completed, a mastery arc for in progress, a ring for unlocked, a padlock for
 * locked. Labels keep the same on-screen size at any zoom, and are left out when zoomed too far out
 * to read (except around the selection). With a selection, unrelated topics fade.
 */
export function paintNode(node, ctx, scale, { palette, selectedId, related }) {
  const selected = node.id === selectedId
  const radius = selected ? SELECTED_RADIUS : NODE_RADIUS
  const { x, y } = node
  ctx.save()
  ctx.globalAlpha = related && !related.has(node.id) ? 0.25 : 1

  ctx.beginPath()
  ctx.arc(x, y, radius, 0, 2 * Math.PI)
  ctx.fillStyle = palette[node.status] ?? palette.locked
  ctx.fill()

  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  if (node.status === 'completed') {
    ctx.beginPath()
    ctx.moveTo(x - radius * 0.45, y + radius * 0.02)
    ctx.lineTo(x - radius * 0.12, y + radius * 0.35)
    ctx.lineTo(x + radius * 0.48, y - radius * 0.32)
    ctx.strokeStyle = palette.card
    ctx.lineWidth = radius * 0.24
    ctx.stroke()
  } else if (node.status === 'in_progress') {
    ctx.beginPath()
    ctx.arc(x, y, radius + 2, -Math.PI / 2, -Math.PI / 2 + (2 * Math.PI * Math.min(100, node.mastery)) / 100)
    ctx.strokeStyle = palette.primaryDark
    ctx.lineWidth = 1.5
    ctx.stroke()
  } else if (node.status === 'unlocked') {
    ctx.beginPath()
    ctx.arc(x, y, radius, 0, 2 * Math.PI)
    ctx.strokeStyle = palette.primary
    ctx.lineWidth = 1.5
    ctx.stroke()
  } else {
    // Padlock: body and shackle.
    const w = radius * 0.8
    ctx.fillStyle = palette.card
    ctx.fillRect(x - w / 2, y - radius * 0.05, w, radius * 0.6)
    ctx.beginPath()
    ctx.arc(x, y - radius * 0.05, w * 0.32, Math.PI, 0)
    ctx.strokeStyle = palette.card
    ctx.lineWidth = radius * 0.16
    ctx.stroke()
  }

  if (selected) {
    ctx.beginPath()
    ctx.arc(x, y, radius + 4, 0, 2 * Math.PI)
    ctx.strokeStyle = palette.ink
    ctx.lineWidth = 2 / scale
    ctx.stroke()
  }

  if (scale >= LABEL_MIN_SCALE || selected || related?.has(node.id)) {
    const fontSize = (selected ? 13 : 11) / scale
    ctx.font = `${selected ? 600 : 500} ${fontSize}px "Geist Variable", system-ui, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    // A halo in the card colour keeps labels readable where they cross links.
    ctx.lineWidth = 3 / scale
    ctx.strokeStyle = palette.card
    ctx.fillStyle = node.status === 'locked' ? palette.muted : palette.ink
    wrapLabel(node.name).forEach((line, i) => {
      const lineY = y + radius + 3 / scale + i * fontSize * 1.15
      ctx.strokeText(line, x, lineY)
      ctx.fillText(line, x, lineY)
    })
  }
  ctx.restore()
}

/** Minimum tap radius on screen, in CSS pixels, so small zooms still leave a usable target. */
const MIN_TAP_RADIUS = 12

/** The clickable area of a topic: its circle plus some slack, never smaller than MIN_TAP_RADIUS. */
export function paintNodeArea(node, color, ctx, selectedId, scale = 1) {
  const radius = (node.id === selectedId ? SELECTED_RADIUS : NODE_RADIUS) + 4
  ctx.fillStyle = color
  ctx.beginPath()
  ctx.arc(node.x, node.y, Math.max(radius, MIN_TAP_RADIUS / scale), 0, 2 * Math.PI)
  ctx.fill()
}

/** The smallest zoom the first view uses: labels are drawn and nodes are big enough to tap. */
export const MIN_START_SCALE = 0.75

/**
 * The first view of the graph. If the whole graph fits at a readable zoom, fit it; otherwise (a
 * phone) zoom to MIN_START_SCALE with the first column, the starting topics, at the left edge.
 * bbox is force-graph's getGraphBbox(): {x: [min, max], y: [min, max]} in graph units.
 */
export function startView(bbox, width, height, padding) {
  const scale = Math.min(
    (width - 2 * padding) / Math.max(1, bbox.x[1] - bbox.x[0]),
    (height - 2 * padding) / Math.max(1, bbox.y[1] - bbox.y[0]),
  )
  if (scale >= MIN_START_SCALE) return { fit: true }
  return {
    fit: false,
    scale: MIN_START_SCALE,
    x: bbox.x[0] + (width / 2 - padding) / MIN_START_SCALE,
    y: (bbox.y[0] + bbox.y[1]) / 2,
  }
}
