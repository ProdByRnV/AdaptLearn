import { describe, expect, it } from 'vitest'

import { DOMAINS, topicGraph, topicMap } from '@/test/fixtures'

import {
  BAND_PADDING,
  BAND_TITLE_ROOM,
  BAND_ROW,
  bandExtents,
  bandRows,
  endId,
  groupBands,
  groupBoxes,
  paintGroups,
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

  it('stacks a band per domain in curriculum order, each as tall as its busiest column', () => {
    const bands = groupBands(nodes, DOMAINS)
    // Foundations has one topic per column; Web Development's busiest column has two (CSS Basics
    // and JavaScript Fundamentals, after HTML Basics).
    const foundations = 1 * BAND_ROW + BAND_PADDING
    const web = 2 * BAND_ROW + BAND_PADDING
    const total = foundations + web
    expect(bands.get('foundations')).toBe(foundations / 2 - total / 2)
    expect(bands.get('web-development')).toBe(foundations + web / 2 - total / 2)
  })

  it('gives every topic its own row in its band, next to its prerequisites', () => {
    const rows = bandRows(nodes, DOMAINS)
    const bands = groupBands(nodes, DOMAINS)
    const half = BAND_ROW / 2
    // Alone in their columns, Foundations topics sit on the band's centre line.
    expect(rows.get('command_line')).toBe(bands.get('foundations'))
    expect(rows.get('git_basics')).toBe(bands.get('foundations'))
    const web = bands.get('web-development')
    expect(rows.get('html_basics')).toBe(web)
    // Two topics in a column, one row apart; ties keep the API's order.
    expect([rows.get('css_basics'), rows.get('javascript_fundamentals')]).toEqual([web - half, web + half])
    // Each follows its prerequisite: Flexbox (after CSS) above React Fundamentals (after JavaScript).
    expect([rows.get('flexbox'), rows.get('react_fundamentals')]).toEqual([web - half, web + half])
    // Deployment Basics needs React Router and Command Line, far up in Foundations, so it goes above React Hooks.
    expect(rows.get('deployment_basics')).toBeLessThan(rows.get('react_hooks'))
    // Every topic in a band stays inside it.
    for (const node of nodes.filter((n) => n.home_domain === 'web-development')) {
      expect(Math.abs(rows.get(node.id) - web)).toBeLessThanOrEqual(half)
    }
  })

  it("gives each band a top and bottom that meet the next band's, around its centre", () => {
    const bands = bandExtents(nodes, DOMAINS)
    const foundations = bands.get('foundations')
    const web = bands.get('web-development')
    expect(foundations.bottom).toBe(web.top)
    expect(foundations.bottom - foundations.top).toBe(1 * BAND_ROW + BAND_PADDING)
    expect(web.bottom - web.top).toBe(2 * BAND_ROW + BAND_PADDING)
    expect(foundations.top).toBe(-web.bottom) // the stack is centred on 0
    expect(groupBands(nodes, DOMAINS).get('web-development')).toBe(web.centre)
  })

  it('leaves out domains without topics', () => {
    const bands = groupBands(nodes, [...DOMAINS, { id: 'empty', name: 'Empty' }])
    expect([...bands.keys()]).toEqual(['foundations', 'web-development'])
  })

  it('boxes each domain around its placed topics, with room for its name', () => {
    const placed = [
      { id: 'a', home_domain: 'foundations', x: 0, y: 0 },
      { id: 'b', home_domain: 'foundations', x: 100, y: 50 },
      { id: 'c', home_domain: 'web-development' },
    ]
    const [box, ...rest] = groupBoxes(placed, DOMAINS, 1)
    expect(rest).toEqual([])
    // 50 to each side and 40 below for labels, 20 above plus room for the domain's name.
    expect(box).toMatchObject({ id: 'foundations', name: 'Foundations', x: -50, width: 200 })
    expect(box.y).toBe(-20 - 20)
    expect(box.height).toBe(50 + 20 + 40 + 20)
    // Zoomed out, the name is drawn larger, so it gets more room.
    expect(groupBoxes(placed, DOMAINS, LABEL_MIN_SCALE / 2)[0].y).toBeLessThan(box.y)
  })

  it("with bands, each box spans its domain's band, so boxes never overlap at any zoom", () => {
    // Seen with Python: a topic pulled towards a prerequisite two domains away made boxes overlap.
    const bands = new Map([
      ['foundations', { top: -300, centre: -200, bottom: -100 }],
      ['web-development', { top: -100, centre: 0, bottom: 100 }],
    ])
    const placed = [
      { id: 'a', home_domain: 'foundations', x: 0, y: -250 },
      { id: 'b', home_domain: 'foundations', x: 100, y: -150 },
      { id: 'c', home_domain: 'web-development', x: 0, y: 0 },
    ]
    for (const scale of [1, 0.2]) {
      const [foundations, web] = groupBoxes(placed, DOMAINS, scale, bands)
      expect(foundations).toMatchObject({ x: -50, width: 200, y: -297, height: 194 })
      expect(web).toMatchObject({ y: -97, height: 194 })
      expect(foundations.y + foundations.height).toBeLessThan(web.y)
    }
  })

  it('draws each domain behind its topics, with its name larger when zoomed out', () => {
    const placed = nodes.map((n, i) => ({ ...n, x: i * 10, y: n.home_domain === 'foundations' ? 0 : 100 }))
    const texts = []
    const ctx = {
      save() {},
      restore() {},
      beginPath() {},
      rect() {},
      fill() {},
      stroke() {},
      fillText(text) {
        texts.push([text, this.font])
      },
    }
    const palette = { primary: '#0f766e', primaryDark: '#134e4a', link: '#cbd5e1' }
    paintGroups(ctx, 1, placed, DOMAINS, palette)
    paintGroups(ctx, LABEL_MIN_SCALE / 2, placed, DOMAINS, palette)
    expect(texts.map(([text]) => text)).toEqual(['Foundations', 'Web Development', 'Foundations', 'Web Development'])
    const size = (font) => Number.parseFloat(font.split(' ')[1])
    // Font sizes are in graph units: the size on screen is size * scale.
    expect(size(texts[0][1])).toBe(12)
    expect(size(texts[2][1]) * (LABEL_MIN_SCALE / 2)).toBeCloseTo(20)
  })

  it('with bands, keeps each domain name above its first row of topics however far out it is zoomed', () => {
    // Seen with five domains: zoomed far out, a 20 px name covered the top row of topics.
    const bands = bandExtents(nodes, DOMAINS)
    const rows = bandRows(nodes, DOMAINS)
    const placed = nodes.map((n, i) => ({ ...n, x: i * 10, y: rows.get(n.id) }))
    const palette = { primary: '#0f766e', primaryDark: '#134e4a', link: '#cbd5e1' }
    for (const scale of [1, LABEL_MIN_SCALE / 2, 0.05]) {
      const texts = []
      const ctx = {
        save() {}, restore() {}, beginPath() {}, rect() {}, fill() {}, stroke() {},
        fillText(text, x, y) {
          texts.push({ text, y, size: Number.parseFloat(this.font.split(' ')[1]) })
        },
      }
      paintGroups(ctx, scale, placed, DOMAINS, palette, bands)
      expect(texts).toHaveLength(2)
      for (const { text, y, size } of texts) {
        const id = DOMAINS.find((d) => d.name === text).id
        const firstRow = Math.min(...placed.filter((n) => n.home_domain === id).map((n) => n.y))
        expect(y + size).toBeLessThan(firstRow - NODE_RADIUS)
      }
      // Where there is room, the names keep their usual size on screen.
      if (scale === LABEL_MIN_SCALE / 2) expect(texts[0].size * scale).toBeCloseTo(20)
      expect(texts[0].size).toBeLessThanOrEqual(BAND_TITLE_ROOM)
    }
  })
})
