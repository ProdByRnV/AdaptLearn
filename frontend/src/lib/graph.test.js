import { describe, expect, it } from 'vitest'

import { DOMAINS, topicGraph, topicMap } from '@/test/fixtures'

import {
  domainTile,
  endId,
  mapLayout,
  packRows,
  paintGroups,
  TILE_BOTTOM,
  TILE_COLUMN,
  TILE_GAP,
  TILE_PAD_X,
  TILE_ROW,
  TILE_TITLE_ROOM,
  TILE_TOP,
  topicDepths,
  LABEL_MIN_SCALE,
  MIN_START_SCALE,
  startView,
  NODE_RADIUS,
  SELECTED_RADIUS,
  wrapLabel,
  missingPrerequisites,
  paintNode,
  paintNodeArea,
  readPalette,
  relatedIds,
  statusCounts,
  toGraphData,
  unlocksOf,
  withAlpha,
} from './graph'

const byId = (topics) => new Map(topics.map((t) => [t.id, t]))

describe('graph data', () => {
  it('copies nodes and links, since force-graph writes into them', () => {
    const graph = topicGraph()
    const data = toGraphData(graph)
    expect(data.nodes).toEqual(graph.nodes)
    expect(data.nodes[0]).not.toBe(graph.nodes[0])
    expect(data.links[0]).not.toBe(graph.links[0])
    data.links[0].source = { id: 'x' }
    expect(graph.links[0].source).toBe('html_basics')
  })

  it('finds what a topic unlocks', () => {
    expect(unlocksOf('html_basics', topicGraph().nodes).map((t) => t.id)).toEqual(['css_basics', 'javascript_fundamentals'])
    expect(unlocksOf('deployment_basics', topicGraph().nodes)).toEqual([])
  })

  it('lists only the prerequisites that are not completed', () => {
    const topics = topicGraph({ completed: ['html_basics'] }).nodes
    const flexbox = { id: 'x', prerequisites: ['html_basics', 'css_basics', 'missing_topic'] }
    expect(missingPrerequisites(flexbox, byId(topics)).map((t) => t.id)).toEqual(['css_basics'])
  })

  it('relates a topic to its prerequisites and what it unlocks', () => {
    const topics = topicGraph().nodes
    expect([...relatedIds('javascript_fundamentals', topics)].sort()).toEqual(
      ['html_basics', 'javascript_fundamentals', 'react_fundamentals'].sort(),
    )
    expect(relatedIds(null, topics)).toBeNull()
    expect(relatedIds('unknown', topics)).toBeNull()
  })

  it('counts topics per status', () => {
    expect(statusCounts(topicGraph({ completed: ['html_basics'] }).nodes)).toEqual({
      completed: 1,
      in_progress: 0,
      unlocked: 0,
      locked: 8,
    })
  })

  it('reads link ends before and after force-graph resolves them', () => {
    expect(endId('a')).toBe('a')
    expect(endId({ id: 'b' })).toBe('b')
  })
})

describe('wrapLabel', () => {
  it.each([
    ['Git Basics', ['Git Basics']],
    ['JavaScript Fundamentals', ['JavaScript', 'Fundamentals']],
    ['API Integration in React', ['API Integration', 'in React']],
    ['Forms & Accessibility', ['Forms &', 'Accessibility']],
    ['A very long name with many words', ['A very long name', 'with many words']],
  ])('%s', (name, lines) => {
    expect(wrapLabel(name)).toEqual(lines)
  })
})

describe('readPalette', () => {
  it('uses the palette tokens, with the PDF palette as a fallback', () => {
    const element = document.createElement('div')
    document.body.append(element)
    element.style.setProperty('--status-completed', '#123456')
    const palette = readPalette(element)
    expect(palette.completed).toBe('#123456')
    expect(palette.in_progress).toBe('#f59e0b')
    expect(palette.locked).toBe('#64748b')
    element.remove()
  })

  it('has a faint link colour for links between domains on the map', () => {
    expect(readPalette().linkFaint).toBe('#cbd5e14d')
    expect(withAlpha('#0f766e', 1)).toBe('#0f766eff')
    expect(withAlpha('rgb(1 2 3)', 0.3)).toBe('rgb(1 2 3)')
  })
})

/** A 2D context that records what was drawn, with the style in force at each call. */
function recordingContext() {
  const calls = []
  const ctx = { globalAlpha: 1 }
  for (const method of ['save', 'restore', 'beginPath', 'moveTo', 'lineTo', 'arc']) {
    ctx[method] = (...args) => calls.push({ method, args })
  }
  ctx.fillRect = (...args) => calls.push({ method: 'fillRect', args, fillStyle: ctx.fillStyle })
  for (const method of ['fill', 'stroke']) {
    ctx[method] = () => calls.push({ method, fillStyle: ctx.fillStyle, strokeStyle: ctx.strokeStyle, alpha: ctx.globalAlpha })
  }
  for (const method of ['fillText', 'strokeText']) {
    ctx[method] = (text, x, y) => calls.push({ method, text, x, y, fillStyle: ctx.fillStyle, font: ctx.font, alpha: ctx.globalAlpha })
  }
  return { ctx, calls }
}

const palette = readPalette()
const node = (status, extra = {}) => ({ id: 'n', name: 'Flexbox', status, mastery: 50, x: 10, y: 20, ...extra })

describe('paintNode', () => {
  it.each([
    ['completed', '#14b8a6'],
    ['in_progress', '#f59e0b'],
    ['unlocked', '#99f6e4'],
    ['locked', '#64748b'],
  ])('fills a %s topic with its status colour and labels it', (status, colour) => {
    const { ctx, calls } = recordingContext()
    paintNode(node(status), ctx, 1, { palette, selectedId: null, related: null })
    expect(calls.find((c) => c.method === 'fill').fillStyle).toBe(colour)
    const label = calls.find((c) => c.method === 'fillText')
    expect(label).toMatchObject({ text: 'Flexbox', x: 10, y: 20 + NODE_RADIUS + 3 })
    expect(label.fillStyle).toBe(status === 'locked' ? palette.muted : palette.ink)
  })

  it('draws a different mark for each status, so colour is not the only cue', () => {
    const marks = {}
    for (const status of ['completed', 'in_progress', 'unlocked', 'locked']) {
      const { ctx, calls } = recordingContext()
      paintNode(node(status), ctx, 1, { palette, selectedId: null, related: null })
      marks[status] = calls
        .filter((c) => ['moveTo', 'fillRect', 'arc', 'stroke'].includes(c.method))
        .map((c) => (c.method === 'stroke' ? `stroke:${c.strokeStyle}` : c.method))
        .join(',')
    }
    expect(new Set(Object.values(marks)).size).toBe(4)
  })

  it('draws a padlock (body and shackle) on a locked topic', () => {
    const { ctx, calls } = recordingContext()
    paintNode(node('locked'), ctx, 1, { palette, selectedId: null, related: null })
    const body = calls.find((c) => c.method === 'fillRect')
    expect(body.fillStyle).toBe(palette.card)
    const [bx, by, bw, bh] = body.args
    expect(bx + bw / 2).toBeCloseTo(10) // centred on the node
    expect(by).toBeGreaterThan(20 - NODE_RADIUS)
    expect(by + bh).toBeLessThan(20 + NODE_RADIUS)
    const shackle = calls.filter((c) => c.method === 'arc')[1]
    expect(shackle.args.slice(3)).toEqual([Math.PI, 0]) // a half circle on top
    expect(calls.filter((c) => c.method === 'stroke').some((c) => c.strokeStyle === palette.card)).toBe(true)
  })

  it('shows mastery as an arc for a topic in progress', () => {
    const { ctx, calls } = recordingContext()
    paintNode(node('in_progress', { mastery: 25 }), ctx, 1, { palette, selectedId: null, related: null })
    const arc = calls.filter((c) => c.method === 'arc')[1]
    expect(arc.args[3]).toBeCloseTo(-Math.PI / 2)
    expect(arc.args[4]).toBeCloseTo(0) // a quarter of the way round
  })

  it('enlarges and rings the selected topic', () => {
    const { ctx, calls } = recordingContext()
    paintNode(node('unlocked'), ctx, 2, { palette, selectedId: 'n', related: new Set(['n']) })
    const arcs = calls.filter((c) => c.method === 'arc').map((c) => c.args[2])
    expect(arcs[0]).toBe(SELECTED_RADIUS)
    expect(arcs).toContain(SELECTED_RADIUS + 4)
    expect(calls.find((c) => c.method === 'fillText').font).toContain(`${13 / 2}px`)
  })

  it('fades topics unrelated to the selection', () => {
    const faded = recordingContext()
    paintNode(node('unlocked'), faded.ctx, 1, { palette, selectedId: 'other', related: new Set(['other']) })
    expect(faded.calls.find((c) => c.method === 'fill').alpha).toBe(0.25)
    const related = recordingContext()
    paintNode(node('unlocked'), related.ctx, 1, { palette, selectedId: 'other', related: new Set(['other', 'n']) })
    expect(related.calls.find((c) => c.method === 'fill').alpha).toBe(1)
  })

  it('keeps labels the same size on screen at any zoom', () => {
    const { ctx, calls } = recordingContext()
    paintNode(node('unlocked'), ctx, 4, { palette, selectedId: null, related: null })
    expect(calls.find((c) => c.method === 'fillText').font).toContain(`${11 / 4}px`)
  })

  it('wraps a long name onto two lines', () => {
    const { ctx, calls } = recordingContext()
    paintNode(node('unlocked', { name: 'API Integration in React' }), ctx, 1, { palette, selectedId: null, related: null })
    const lines = calls.filter((c) => c.method === 'fillText')
    expect(lines.map((c) => c.text)).toEqual(['API Integration', 'in React'])
    expect(lines[1].y).toBeGreaterThan(lines[0].y)
  })

  it('leaves labels out when zoomed too far out, except around the selection', () => {
    const scale = LABEL_MIN_SCALE - 0.1
    const plain = recordingContext()
    paintNode(node('unlocked'), plain.ctx, scale, { palette, selectedId: null, related: null })
    expect(plain.calls.some((c) => c.method === 'fillText')).toBe(false)
    const neighbour = recordingContext()
    paintNode(node('unlocked'), neighbour.ctx, scale, { palette, selectedId: 'x', related: new Set(['x', 'n']) })
    expect(neighbour.calls.some((c) => c.method === 'fillText')).toBe(true)
  })

  it('keeps the tap target at least 12 px on screen when zoomed out', () => {
    const { ctx, calls } = recordingContext()
    paintNodeArea(node('locked'), '#010203', ctx, null, 0.4)
    expect(calls.find((c) => c.method === 'arc').args[2]).toBe(12 / 0.4)
  })

  it('paints a clickable area a little larger than the node', () => {
    const { ctx, calls } = recordingContext()
    paintNodeArea(node('locked'), '#010203', ctx, null)
    expect(calls.find((c) => c.method === 'arc').args[2]).toBe(NODE_RADIUS + 4)
    expect(calls.find((c) => c.method === 'fill').fillStyle).toBe('#010203')
  })
})

describe('startView', () => {
  const bbox = { x: [0, 800], y: [-150, 150] }

  it('fits the whole graph when it is readable', () => {
    expect(startView(bbox, 1000, 500, 50)).toEqual({ fit: true })
  })

  it('on a narrow screen, starts at a readable zoom with the first column at the left', () => {
    const view = startView(bbox, 343, 400, 50)
    expect(view).toMatchObject({ fit: false, scale: MIN_START_SCALE, y: 0 })
    // The left edge of the view (centre minus half the width, in graph units) shows x = 0 after the padding.
    expect(view.x - (343 / 2) / MIN_START_SCALE).toBeCloseTo(-50 / MIN_START_SCALE)
  })

  it('copes with a graph of one topic', () => {
    expect(startView({ x: [5, 5], y: [5, 5] }, 343, 400, 50)).toEqual({ fit: true })
  })
})

describe('prerequisites from other domains', () => {
  it("missing ones come after this domain's, named with their domain", () => {
    const topics = topicGraph({ completed: ['react_router'] }).nodes
    const deployment = topics.find((t) => t.id === 'deployment_basics')
    expect(missingPrerequisites(deployment, byId(topics)).map((t) => t.name)).toEqual(['Command Line (Foundations)'])
  })

  it('completed ones are not missing', () => {
    const topics = topicGraph({ completed: ['command_line'] }).nodes
    const deployment = topics.find((t) => t.id === 'deployment_basics')
    expect(missingPrerequisites(deployment, byId(topics)).map((t) => t.name)).toEqual(['React Router'])
  })
})

describe('the whole map', () => {
  const { nodes } = topicMap()
  const web = nodes.filter((n) => n.home_domain === 'web-development')
  const palette = { primary: '#0f766e', primaryDark: '#134e4a', link: '#cbd5e1' }
  /** A canvas context that records tiles and names drawn, measuring text at 0.6 of the font size per letter. */
  const recordingContext = () => {
    const texts = []
    const ctx = {
      save() {}, restore() {}, beginPath() {}, fill() {}, stroke() {},
      rects: [],
      rect(x, y, width, height) {
        this.rects.push({ x, y, width, height })
      },
      measureText(text) {
        return { width: text.length * 0.6 * Number.parseFloat(this.font.split(' ')[1]) }
      },
      fillText(text, x, y) {
        texts.push({ text, x, y, size: Number.parseFloat(this.font.split(' ')[1]) })
      },
    }
    return { ctx, texts }
  }

  it('gives each topic its column: one past its deepest prerequisite', () => {
    const depths = topicDepths(nodes)
    expect(depths.get('command_line')).toBe(0)
    expect(depths.get('git_basics')).toBe(1)
    expect(depths.get('html_basics')).toBe(0)
    expect(depths.get('react_router')).toBe(3)
    // Command Line (column 0) doesn't pull it back; React Router (column 3) sets it.
    expect(depths.get('deployment_basics')).toBe(4)
  })

  it('ignores prerequisites that are not on the graph, and never loops', () => {
    const loop = [
      { id: 'a', prerequisites: ['b', 'missing'] },
      { id: 'b', prerequisites: ['a'] },
    ]
    const depths = topicDepths(loop)
    expect(depths.size).toBe(2)
    expect([...depths.values()].every(Number.isFinite)).toBe(true)
  })

  it("lays a domain's tile out like its own graph: a column per depth, its busiest column setting the height", () => {
    const tile = domainTile(web)
    // Five columns (HTML Basics to Deployment Basics); two topics in the busiest.
    expect(tile.width).toBe(4 * TILE_COLUMN + 2 * TILE_PAD_X)
    expect(tile.height).toBe(TILE_TOP + TILE_ROW + TILE_BOTTOM)
    const at = (id) => tile.offsets.get(id)
    expect(at('html_basics')).toEqual({ x: TILE_PAD_X, y: TILE_TOP + TILE_ROW / 2 })
    // Two topics in a column, one row apart; ties keep the API's order.
    expect([at('css_basics').y, at('javascript_fundamentals').y]).toEqual([TILE_TOP, TILE_TOP + TILE_ROW])
    // Each follows its prerequisite: Flexbox (after CSS) above React Fundamentals (after JavaScript).
    expect([at('flexbox').y, at('react_fundamentals').y]).toEqual([TILE_TOP, TILE_TOP + TILE_ROW])
    expect(at('flexbox').x).toBe(TILE_PAD_X + 2 * TILE_COLUMN)
  })

  it("counts only the domain's own prerequisites, so one from another domain doesn't move a topic", () => {
    // Deployment Basics also needs Command Line (Foundations): only React Router sets its column.
    const tile = domainTile(web)
    expect(tile.offsets.get('deployment_basics').x).toBe(tile.offsets.get('react_router').x + TILE_COLUMN)
  })

  it('fills tiles into rows in order, a tile wider than the limit getting a row of its own', () => {
    const tiles = [
      { width: 100, height: 50 },
      { width: 100, height: 80 },
      { width: 300, height: 60 },
      { width: 50, height: 40 },
    ]
    const rows = packRows(tiles, 250)
    expect(rows.map((row) => row.tiles.length)).toEqual([2, 1, 1])
    expect(rows[0]).toMatchObject({ width: 100 + TILE_GAP + 100, height: 80 })
    expect(rows[1]).toMatchObject({ width: 300, height: 60 })
  })

  it('breaks the rows to suit the shape of the view', () => {
    const tilesFor = (aspect) => mapLayout(nodes, DOMAINS, aspect).tiles
    // A wide view: both domains side by side, in curriculum order.
    const [foundations, webTile] = tilesFor(4)
    expect(foundations).toMatchObject({ id: 'foundations', name: 'Foundations', y: webTile.y })
    expect(webTile.x).toBe(foundations.x + foundations.width + TILE_GAP)
    // A square one: one above the other.
    const [top, bottom] = tilesFor(1)
    expect(bottom.y).toBe(top.y + top.height + TILE_GAP)
    expect(bottom.x).toBe(top.x)
  })

  it('makes the tiles a grid: a row shares its height, and every row is as wide as the widest', () => {
    const [top, bottom] = mapLayout(nodes, DOMAINS, 1).tiles
    expect(top.width).toBe(bottom.width)
    const [foundations, webTile] = mapLayout(nodes, DOMAINS, 4).tiles
    expect(foundations.height).toBe(webTile.height)
  })

  it('puts every topic in its own tile, below the room for the name, with the map centred on 0', () => {
    for (const aspect of [0.5, 1, 4]) {
      const { positions, tiles } = mapLayout(nodes, DOMAINS, aspect)
      expect(positions.size).toBe(nodes.length)
      for (const node of nodes) {
        const tile = tiles.find((t) => t.id === node.home_domain)
        const { x, y } = positions.get(node.id)
        expect(x).toBeGreaterThanOrEqual(tile.x + TILE_PAD_X)
        expect(x).toBeLessThanOrEqual(tile.x + tile.width - TILE_PAD_X)
        expect(y).toBeGreaterThanOrEqual(tile.y + TILE_TOP)
        expect(y).toBeLessThanOrEqual(tile.y + tile.height - TILE_BOTTOM)
      }
      const left = Math.min(...tiles.map((t) => t.x))
      const right = Math.max(...tiles.map((t) => t.x + t.width))
      const top = Math.min(...tiles.map((t) => t.y))
      const bottom = Math.max(...tiles.map((t) => t.y + t.height))
      expect(left + right).toBeCloseTo(0)
      expect(top + bottom).toBeCloseTo(0)
    }
  })

  it('leaves out domains without topics', () => {
    const { tiles } = mapLayout(nodes, [...DOMAINS, { id: 'empty', name: 'Empty' }])
    expect(tiles.map((t) => t.id)).toEqual(['foundations', 'web-development'])
    expect(mapLayout([], DOMAINS)).toEqual({ positions: new Map(), tiles: [] })
  })

  it('draws each domain behind its topics, with its name larger when zoomed out', () => {
    // Tiles wide enough for their names at any size.
    const tiles = mapLayout(nodes, DOMAINS, 4).tiles.map((tile) => ({ ...tile, width: 2000 }))
    const { ctx, texts } = recordingContext()
    paintGroups(ctx, 1, tiles, palette)
    paintGroups(ctx, LABEL_MIN_SCALE / 2, tiles, palette)
    expect(texts.map(({ text }) => text)).toEqual(['Foundations', 'Web Development', 'Foundations', 'Web Development'])
    expect(ctx.rects.slice(0, 2)).toEqual(tiles.map(({ x, y, width, height }) => ({ x, y, width, height })))
    // Font sizes are in graph units: the size on screen is size * scale.
    expect(texts[0].size).toBe(12)
    expect(texts[3].size * (LABEL_MIN_SCALE / 2)).toBeCloseTo(20)
  })

  it('keeps each domain name above its top row and inside its tile however far out it is zoomed', () => {
    // Seen with five domains: zoomed far out, a 20 px name covered the top row of topics.
    const { positions, tiles } = mapLayout(nodes, DOMAINS, 4)
    for (const scale of [1, LABEL_MIN_SCALE / 2, 0.05]) {
      const { ctx, texts } = recordingContext()
      paintGroups(ctx, scale, tiles, palette)
      expect(texts).toHaveLength(2)
      for (const { text, x, y, size } of texts) {
        const tile = tiles.find((t) => t.name === text)
        const firstRow = Math.min(...nodes.filter((n) => n.home_domain === tile.id).map((n) => positions.get(n.id).y))
        expect(y + size).toBeLessThan(firstRow - NODE_RADIUS)
        expect(size).toBeLessThanOrEqual(TILE_TITLE_ROOM)
        expect(x + text.length * 0.6 * size).toBeLessThanOrEqual(tile.x + tile.width)
      }
    }
  })

  it('shrinks a name that would run past the edge of a narrow tile', () => {
    const narrow = [{ id: 'foundations', name: 'Foundations', x: 0, y: 0, width: 70, height: 200 }]
    const { ctx, texts } = recordingContext()
    paintGroups(ctx, 1, narrow, palette)
    const [{ x, size }] = texts
    // As much room is left after the name as before it.
    expect(x + 'Foundations'.length * 0.6 * size).toBeCloseTo(70 - x)
    expect(size).toBeLessThan(12)
  })

  it('puts a long name in a narrow tile on two lines when that lets it be larger', () => {
    // Seen with thirteen domains: "Computer Science Core" shrank to a few pixels on one line.
    const narrow = [{ id: 'cs-core', name: 'Computer Science Core', x: 0, y: 0, width: 300, height: 300 }]
    const { ctx, texts } = recordingContext()
    paintGroups(ctx, 0.25, narrow, palette)
    expect(texts.map(({ text }) => text)).toEqual(['Computer', 'Science Core'])
    const [first, second] = texts
    expect(first.size).toBe(second.size)
    expect(second.y).toBeGreaterThan(first.y + first.size)
    // Both lines fit above the top row and inside the tile.
    expect(second.y + second.size).toBeLessThanOrEqual(TILE_TITLE_ROOM)
    expect(first.x + 'Science Core'.length * 0.6 * first.size).toBeLessThanOrEqual(300)
    // Larger than it could be on one line.
    expect(first.size).toBeGreaterThan((300 - 2 * first.x) / ('Computer Science Core'.length * 0.6))
  })
})
