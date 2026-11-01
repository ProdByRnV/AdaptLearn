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

/** A hex colour (#rrggbb) at the given opacity; other colour formats are returned unchanged. */
export function withAlpha(colour, alpha) {
  if (!/^#[0-9a-f]{6}$/i.test(colour)) return colour
  return colour + Math.round(alpha * 255).toString(16).padStart(2, '0')
}

/**
 * Colours for the canvas, read from the palette tokens in index.css so the graph matches the badges.
 * linkFaint is for links between domains on the whole map, which would otherwise criss-cross it.
 */
export function readPalette(element = document.documentElement) {
  const styles = getComputedStyle(element)
  const token = (name, fallback) => styles.getPropertyValue(name).trim() || fallback
  const link = token('--input', FALLBACK_PALETTE.link)
  return {
    completed: token('--status-completed', FALLBACK_PALETTE.completed),
    in_progress: token('--status-in-progress', FALLBACK_PALETTE.in_progress),
    unlocked: token('--status-unlocked', FALLBACK_PALETTE.unlocked),
    locked: token('--status-locked', FALLBACK_PALETTE.locked),
    ink: token('--ink', FALLBACK_PALETTE.ink),
    primary: token('--primary', FALLBACK_PALETTE.primary),
    primaryDark: token('--primary-dark', FALLBACK_PALETTE.primaryDark),
    muted: token('--muted-foreground', FALLBACK_PALETTE.muted),
    link,
    linkFaint: withAlpha(link, 0.3),
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

/**
 * Prerequisites of a topic that aren't completed yet: what stands between the learner and it.
 * Those from other domains (external_prerequisites) come last, named with their domain.
 */
export function missingPrerequisites(topic, topicsById) {
  const internal = topic.prerequisites.map((id) => topicsById.get(id)).filter((t) => t && t.status !== 'completed')
  const external = (topic.external_prerequisites ?? [])
    .filter((p) => !p.completed)
    .map((p) => ({ ...p, name: `${p.name} (${p.domain_name})` }))
  return [...internal, ...external]
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

// --- The whole map: a tile per domain, packed into rows ------------------------------------

/** Spacing of a domain tile's columns (prerequisite depth within the domain) and rows, in graph units. */
export const TILE_COLUMN = 100
export const TILE_ROW = 50
/** Room either side of a tile's outer columns, for labels, which are wider than a topic. */
export const TILE_PAD_X = 55
/** Room above a tile's top row, where the domain's name is drawn, and below its bottom row's labels. */
export const TILE_TOP = 110
export const TILE_BOTTOM = 50
/** The space between neighbouring tiles. */
export const TILE_GAP = 40
const TITLE_INSET = 8
const TITLE_LINE_HEIGHT = 1.1
/**
 * The room for a domain's name above its tile's top row, in graph units: the space above the row,
 * less a topic's radius and a margin. Far zoomed out, the name shrinks to fit it.
 */
export const TILE_TITLE_ROOM = TILE_TOP - NODE_RADIUS - 16

/**
 * Prerequisite depth, as force-graph's left-to-right layout uses for columns: 0 for a topic with no
 * prerequisites on the graph, otherwise one more than its deepest prerequisite.
 */
export function topicDepths(nodes) {
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const depths = new Map()
  const visit = (id, trail) => {
    if (depths.has(id)) return depths.get(id)
    if (trail.has(id)) return 0 // The curriculum is validated as acyclic; this only stops a loop.
    trail.add(id)
    const prerequisites = (byId.get(id)?.prerequisites ?? []).filter((pre) => byId.has(pre))
    const depth = prerequisites.length ? 1 + Math.max(...prerequisites.map((pre) => visit(pre, trail))) : 0
    depths.set(id, depth)
    return depth
  }
  for (const node of nodes) visit(node.id, new Set())
  return depths
}

/**
 * One domain's topics laid out as on the domain's own graph: a column per prerequisite depth within
 * the domain (prerequisites from other domains don't count) and, within a column, rows TILE_ROW
 * apart in the order of where their prerequisites are, so lines cross as little as possible; ties
 * keep the API's order. Positions are offsets from the tile's top-left corner, with the top row
 * TILE_TOP down.
 */
export function domainTile(nodes) {
  const depths = topicDepths(nodes)
  const order = new Map(nodes.map((node, i) => [node.id, i]))
  const columns = new Map()
  for (const node of nodes) {
    const depth = depths.get(node.id)
    if (!columns.has(depth)) columns.set(depth, [])
    columns.get(depth).push(node)
  }
  const busiest = Math.max(...[...columns.values()].map((column) => column.length))
  const middle = TILE_TOP + ((busiest - 1) * TILE_ROW) / 2
  const offsets = new Map()
  const anchor = (node) => {
    const placed = node.prerequisites.filter((pre) => offsets.has(pre)).map((pre) => offsets.get(pre).y)
    return placed.length ? placed.reduce((a, b) => a + b, 0) / placed.length : middle
  }
  for (const depth of [...columns.keys()].sort((a, b) => a - b)) {
    const sorted = columns
      .get(depth)
      .map((node) => ({ node, at: anchor(node) }))
      .sort((a, b) => a.at - b.at || order.get(a.node.id) - order.get(b.node.id))
    sorted.forEach(({ node }, i) =>
      offsets.set(node.id, {
        x: TILE_PAD_X + depth * TILE_COLUMN,
        y: middle + (i - (sorted.length - 1) / 2) * TILE_ROW,
      }),
    )
  }
  return {
    width: Math.max(...columns.keys()) * TILE_COLUMN + 2 * TILE_PAD_X,
    height: TILE_TOP + (busiest - 1) * TILE_ROW + TILE_BOTTOM,
    offsets,
  }
}

/** Tiles in curriculum order, filled into rows no wider than `limit` (a tile wider than that gets a row of its own). */
export function packRows(tiles, limit) {
  const rows = []
  for (const tile of tiles) {
    const row = rows.at(-1)
    if (row && row.width + TILE_GAP + tile.width <= limit) {
      row.tiles.push(tile)
      row.width += TILE_GAP + tile.width
      row.height = Math.max(row.height, tile.height)
    } else {
      rows.push({ tiles: [tile], width: tile.width, height: tile.height })
    }
  }
  return rows
}

/**
 * The whole map: a tile per domain in curriculum order, filled into rows like words on a page.
 * Of every way to break the rows, it keeps the one that fits the view (width / height = `aspect`)
 * at the largest zoom. Tiles in a row share its height, and each row is stretched to the widest,
 * so the tiles form a grid. Centred on 0. Domains with no topics are left out.
 * Returns each topic's position and each domain's tile ({id, name, x, y, width, height}).
 */
export function mapLayout(nodes, groups, aspect = 1) {
  const tiles = groups.flatMap((group) => {
    const own = nodes.filter((node) => node.home_domain === group.id)
    return own.length ? [{ id: group.id, name: group.name, ...domainTile(own) }] : []
  })
  const positions = new Map()
  if (tiles.length === 0) return { positions, tiles: [] }

  // Every row width worth trying: the width of each run of consecutive tiles.
  const limits = new Set()
  tiles.forEach((_, start) => {
    let width = -TILE_GAP
    for (const tile of tiles.slice(start)) limits.add((width += TILE_GAP + tile.width))
  })
  let best = null
  for (const limit of limits) {
    const rows = packRows(tiles, limit)
    const width = Math.max(...rows.map((row) => row.width))
    const height = rows.reduce((sum, row) => sum + row.height, 0) + (rows.length - 1) * TILE_GAP
    const scale = Math.min(aspect / width, 1 / height)
    if (!best || scale > best.scale) best = { rows, width, height, scale }
  }

  const placed = []
  let y = -best.height / 2
  for (const row of best.rows) {
    const extra = (best.width - row.width) / row.tiles.length
    let x = -best.width / 2
    for (const tile of row.tiles) {
      for (const [id, at] of tile.offsets) positions.set(id, { x: x + at.x, y: y + at.y })
      placed.push({ id: tile.id, name: tile.name, x, y, width: tile.width + extra, height: row.height })
      x += tile.width + extra + TILE_GAP
    }
    y += row.height + TILE_GAP
  }
  return { positions, tiles: placed }
}

/**
 * Draw each domain's tile under the topics, named in its corner. Zoomed out, where topic labels
 * are hidden, the names are drawn large so the map reads as its domains, but never larger than the
 * room above the tile's top row, or wider than the tile, so a name doesn't cover topics or run
 * into the next domain. A long name in a narrow tile goes onto two lines when that lets it be larger.
 */
export function paintGroups(ctx, scale, tiles, palette) {
  const wanted = (scale < LABEL_MIN_SCALE ? 20 : 12) / scale
  const inset = Math.min(6 / scale, TITLE_INSET)
  const room = TILE_TITLE_ROOM - inset
  const font = (size) => `600 ${size}px "Geist Variable", system-ui, sans-serif`
  // The largest size at which these lines fit the tile's width and the room above its top row.
  const fit = (lines, width) => {
    const size = Math.min(wanted, room / (1 + (lines.length - 1) * TITLE_LINE_HEIGHT))
    ctx.font = font(size)
    const widest = Math.max(...lines.map((line) => ctx.measureText(line).width))
    return widest > width ? (size * width) / widest : size
  }
  for (const tile of tiles) {
    ctx.save()
    ctx.beginPath()
    ctx.rect(tile.x, tile.y, tile.width, tile.height)
    ctx.globalAlpha = 0.06
    ctx.fillStyle = palette.primary
    ctx.fill()
    ctx.globalAlpha = 0.8
    ctx.lineWidth = 1 / scale
    ctx.strokeStyle = palette.link
    ctx.stroke()
    ctx.globalAlpha = 1
    const width = tile.width - 2 * inset
    let lines = [tile.name]
    let size = fit(lines, width)
    const split = wrapLabel(tile.name, 0)
    if (split.length === 2 && fit(split, width) > size) {
      lines = split
      size = fit(split, width)
    }
    ctx.font = font(size)
    ctx.textAlign = 'left'
    ctx.textBaseline = 'top'
    ctx.fillStyle = palette.primaryDark
    lines.forEach((line, i) => ctx.fillText(line, tile.x + inset, tile.y + inset + i * size * TITLE_LINE_HEIGHT))
    ctx.restore()
  }
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
