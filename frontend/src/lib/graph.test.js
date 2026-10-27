import { describe, expect, it } from 'vitest'

import { topicGraph } from '@/test/fixtures'

import {
  endId,
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
