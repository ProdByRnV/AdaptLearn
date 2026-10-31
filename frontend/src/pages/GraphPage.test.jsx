import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useImperativeHandle } from 'react'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser } from '@/api/auth'
import { tokenStorage } from '@/api/client'
import { fetchCatalogue } from '@/api/domains'
import { fetchTopicGraph, fetchTopicMap } from '@/api/topics'
import { bandExtents, bandRows } from '@/lib/graph'
import { catalogue, topicGraph, topicMap } from '@/test/fixtures'
import { deferred, httpError, LEARNER } from '@/test/helpers'
import { renderAt } from '@/test/render-app'

vi.mock('@/api/auth', () => ({ fetchCurrentUser: vi.fn(), loginRequest: vi.fn(), registerRequest: vi.fn() }))
vi.mock('@/api/topics', () => ({ fetchTopicGraph: vi.fn(), fetchTopicMap: vi.fn(), markKnownTopics: vi.fn() }))
vi.mock('@/api/domains', () => ({ fetchCatalogue: vi.fn(), fetchHome: vi.fn(), joinDomain: vi.fn() }))
vi.mock('@/api/progress', () => ({ fetchDashboard: vi.fn(() => new Promise(() => {})) }))

// jsdom has no canvas. The fake keeps the library's contract: it receives the same props, places
// the nodes (as the simulation would), exposes the same imperative methods, and turns clicks on
// a node or the background into the same callbacks.
const graph = vi.hoisted(() => ({ props: null, api: null }))
vi.mock('react-force-graph-2d', () => ({
  default: function FakeForceGraph(props) {
    useImperativeHandle(props.ref, () => graph.api)
    graph.props = props
    props.graphData.nodes.forEach((node, i) => {
      node.x ??= i * 10
      node.y ??= 5
    })
    return (
      <div data-testid="force-graph">
        {props.graphData.nodes.map((node) => (
          <button key={node.id} type="button" onClick={() => props.onNodeClick(node)}>
            node {node.id}
          </button>
        ))}
        <button type="button" onClick={() => props.onBackgroundClick()}>
          background
        </button>
      </div>
    )
  },
}))

// The page lazy-loads the graph component. Load it once up front so the first test doesn't pay for a
// cold import (slow when the whole suite runs in parallel) inside its one-second wait.
beforeAll(() => import('@/components/graph/KnowledgeGraph'))

beforeEach(() => {
  graph.props = null
  graph.api = {
    centerAt: vi.fn(),
    zoom: vi.fn(() => 2),
    zoomToFit: vi.fn(),
    d3Force: vi.fn(() => ({ strength: vi.fn() })),
    d3ReheatSimulation: vi.fn(),
    getGraphBbox: vi.fn(() => ({ x: [0, 400], y: [-100, 100] })),
  }
  tokenStorage.set('jwt')
  fetchCurrentUser.mockResolvedValue(LEARNER)
  fetchCatalogue.mockResolvedValue(catalogue())
})

/** topicGraph() with some statuses changed, e.g. {html_basics: 'completed', css_basics: 'in_progress'}. */
function graphWith(statuses = {}, changes = {}) {
  const data = topicGraph()
  data.nodes = data.nodes.map((n) => ({ ...n, ...(statuses[n.id] && { status: statuses[n.id] }), ...changes[n.id] }))
  return data
}

const WEB = '/domains/web-development/graph'

async function open(data = topicGraph(), entry = WEB) {
  fetchTopicGraph.mockResolvedValue(data)
  const user = userEvent.setup()
  const view = renderAt(entry)
  await screen.findByTestId('force-graph')
  return { user, ...view }
}

const panel = () => screen.getByRole('complementary', { name: /./ })
const clickNode = (user, id) => user.click(screen.getByRole('button', { name: `node ${id}` }))

describe('the graph', () => {
  it('shows a placeholder while loading, then every topic and prerequisite link', async () => {
    const pending = deferred()
    fetchTopicGraph.mockReturnValue(pending.promise)
    renderAt(WEB)
    expect(await screen.findByRole('status', { name: 'Loading the knowledge graph' })).toBeInTheDocument()
    await act(async () => pending.resolve(topicGraph()))
    await screen.findByTestId('force-graph')
    expect(graph.props.graphData.nodes.map((n) => n.id)).toEqual(topicGraph().nodes.map((n) => n.id))
    expect(graph.props.graphData.links).toEqual(topicGraph().links)
  })

  it('lays topics out by prerequisite depth with arrows pointing at what they unlock', async () => {
    await open()
    expect(graph.props.dagMode).toBe('lr')
    expect(graph.props.linkDirectionalArrowLength).toBeGreaterThan(0)
    expect(graph.props.linkDirectionalArrowRelPos).toBe(1)
    expect(graph.props.enableNodeDrag).toBe(false)
  })

  it('offers a retry when the graph cannot be loaded', async () => {
    fetchTopicGraph.mockRejectedValueOnce(httpError(503, 'Graph database is temporarily unavailable.'))
    const user = userEvent.setup()
    renderAt(WEB)
    expect(await screen.findByRole('heading', { name: "Couldn't load the knowledge graph" })).toBeInTheDocument()
    expect(screen.getByText('Graph database is temporarily unavailable.')).toBeInTheDocument()
    fetchTopicGraph.mockResolvedValueOnce(topicGraph())
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByTestId('force-graph')).toBeInTheDocument()
  })

  it('has a legend with the number of topics in each state', async () => {
    await open(graphWith({ html_basics: 'completed', css_basics: 'in_progress', javascript_fundamentals: 'unlocked' }))
    const legend = screen.getByRole('list', { name: 'Legend' })
    const items = within(legend).getAllByRole('listitem').map((li) => li.textContent)
    expect(items.slice(0, 4)).toEqual([
      'Completed1 topics, shown tick',
      'In progress1 topics, shown mastery ring',
      'Unlocked1 topics, shown outlined',
      'Locked6 topics, shown padlock',
    ])
    expect(items[4]).toBe('Prerequisite to the topic it unlocks')
    expect(screen.getByText('Web Development · 1 of 9 topics completed. Select a topic to see its details.')).toBeInTheDocument()
  })

  it('describes the graph in text for screen readers', async () => {
    await open()
    expect(
      screen.getByText(/Knowledge graph of 9 topics: 0 completed, 0 in progress, 1 unlocked and 8 locked\. Switch to the list view/),
    ).toBeInTheDocument()
  })

  it('zooms in, out and to fit, and fits once the layout settles', async () => {
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Zoom in' }))
    expect(graph.api.zoom).toHaveBeenLastCalledWith(2 * 1.4, 300)
    await user.click(screen.getByRole('button', { name: 'Zoom out' }))
    expect(graph.api.zoom).toHaveBeenLastCalledWith(2 / 1.4, 300)
    await user.click(screen.getByRole('button', { name: 'Fit the whole graph' }))
    expect(graph.api.zoomToFit).toHaveBeenCalledTimes(1)
    act(() => graph.props.onEngineStop())
    act(() => graph.props.onEngineStop())
    expect(graph.api.zoomToFit).toHaveBeenCalledTimes(2)
  })
})

describe('selecting a topic', () => {
  it('opens its details, centres it and remembers it in the URL', async () => {
    const { user, router } = await open()
    expect(screen.queryByRole('complementary')).not.toBeInTheDocument()
    await clickNode(user, 'html_basics')
    const details = panel()
    expect(within(details).getByRole('heading', { level: 2, name: 'HTML Basics' })).toHaveFocus()
    expect(within(details).getByText('Unlocked')).toBeInTheDocument()
    expect(within(details).getByText('Beginner')).toBeInTheDocument()
    expect(within(details).getByText('What HTML Basics covers.')).toBeInTheDocument()
    expect(within(details).getByText('10%')).toBeInTheDocument()
    expect(router.state.location.search).toBe('?topic=html_basics')
    expect(graph.props.nodeVal({ id: 'html_basics' })).toBeGreaterThan(graph.props.nodeVal({ id: 'css_basics' }))
    expect(graph.api.centerAt).toHaveBeenCalledWith(10, 5, 500)
  })

  it.each([
    ['unlocked', 'Start topic'],
    ['in_progress', 'Continue'],
    ['completed', 'Practise again'],
  ])('offers the quiz for a topic that is %s', async (status, label) => {
    const { user } = await open(graphWith({ html_basics: status }))
    await clickNode(user, 'html_basics')
    expect(within(panel()).getByRole('link', { name: `${label}: HTML Basics` })).toHaveAttribute('href', '/quiz/html_basics')
  })

  it('says what to complete first for a locked topic, and offers no quiz', async () => {
    const { user } = await open(
      graphWith({ html_basics: 'completed' }, { flexbox: { prerequisites: ['html_basics', 'css_basics'] } }),
    )
    await clickNode(user, 'flexbox')
    expect(within(panel()).getByText('Locked', { selector: 'p' })).toBeInTheDocument()
    expect(within(panel()).getByText('Complete CSS Basics to unlock it.')).toBeInTheDocument()
    expect(within(panel()).queryByRole('link', { name: /quiz|Start|Continue|Practise/ })).not.toBeInTheDocument()
  })

  it('lists prerequisites and what it unlocks, and moves between them', async () => {
    const { user, router } = await open()
    await clickNode(user, 'html_basics')
    const prerequisites = within(panel()).getByRole('region', { name: 'Prerequisites' })
    expect(prerequisites).toHaveTextContent('None. This is a starting topic.')
    const unlocks = within(panel()).getByRole('region', { name: 'Unlocks' })
    expect(within(unlocks).getAllByRole('button').map((b) => b.textContent)).toEqual([
      'CSS BasicsLocked',
      'JavaScript FundamentalsLocked',
    ])
    await user.click(within(unlocks).getByRole('button', { name: /CSS Basics/ }))
    expect(within(panel()).getByRole('heading', { level: 2, name: 'CSS Basics' })).toHaveFocus()
    expect(router.state.location.search).toBe('?topic=css_basics')
    await user.click(within(within(panel()).getByRole('region', { name: 'Prerequisites' })).getByRole('button', { name: /HTML Basics/ }))
    expect(within(panel()).getByRole('heading', { level: 2, name: 'HTML Basics' })).toBeInTheDocument()
  })

  it('shows learning resources as new-tab links', async () => {
    const { user } = await open(
      graphWith({}, { html_basics: { resources: [{ title: 'MDN: HTML', url: 'https://developer.mozilla.org/', type: 'docs' }] } }),
    )
    await clickNode(user, 'html_basics')
    const link = within(panel()).getByRole('link', { name: 'MDN: HTML (Docs, opens in a new tab)' })
    expect(link).toHaveAttribute('target', '_blank')
  })

  it('highlights the links of the selected topic', async () => {
    const { user } = await open()
    const link = { source: 'html_basics', target: 'css_basics' }
    const other = { source: 'css_basics', target: 'flexbox' }
    expect(graph.props.linkColor(link)).toBe(graph.props.linkColor(other))
    await clickNode(user, 'html_basics')
    expect(graph.props.linkColor(link)).not.toBe(graph.props.linkColor(other))
    expect(graph.props.linkWidth(link)).toBe(2)
    expect(graph.props.linkWidth(other)).toBe(1)
    // Resolved link ends (node objects) work the same.
    expect(graph.props.linkWidth({ source: { id: 'html_basics' }, target: { id: 'css_basics' } })).toBe(2)
  })

  it.each([
    ['the close button', (user) => user.click(screen.getByRole('button', { name: 'Close topic details' }))],
    ['Escape', (user) => user.keyboard('{Escape}')],
    ['a click on the background', (user) => user.click(screen.getByRole('button', { name: 'background' }))],
  ])('closes with %s', async (_, close) => {
    const { user, router } = await open()
    await clickNode(user, 'html_basics')
    await close(user)
    await waitFor(() => expect(screen.queryByRole('complementary')).not.toBeInTheDocument())
    expect(router.state.location.search).toBe('')
  })

  it('opens a topic from the URL and centres it once the layout settles', async () => {
    await open(topicGraph(), `${WEB}?topic=css_basics`)
    expect(within(panel()).getByRole('heading', { level: 2, name: 'CSS Basics' })).toBeInTheDocument()
    act(() => graph.props.onEngineStop())
    expect(graph.api.zoomToFit).not.toHaveBeenCalled()
    expect(graph.api.centerAt).toHaveBeenLastCalledWith(0, 5, 400)
  })

  it('shows the hint when the URL names a topic that does not exist', async () => {
    await open(topicGraph(), `${WEB}?topic=quantum_basics`)
    expect(screen.queryByRole('complementary')).not.toBeInTheDocument()
    expect(screen.getByText('Select a topic to see its details, prerequisites and resources.')).toBeInTheDocument()
  })
})

describe('list view', () => {
  it('shows every topic as text, grouped by status, with the same details panel', async () => {
    const { user } = await open(graphWith({ html_basics: 'completed', css_basics: 'unlocked' }))
    const graphButton = screen.getByRole('button', { name: 'Graph' })
    const listButton = screen.getByRole('button', { name: 'List' })
    expect(graphButton).toHaveAttribute('aria-pressed', 'true')
    await user.click(listButton)
    expect(listButton).toHaveAttribute('aria-pressed', 'true')
    expect(screen.queryByTestId('force-graph')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Completed (1)' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Unlocked (1)' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Locked (7)' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /In progress/ })).not.toBeInTheDocument()

    const css = screen.getByRole('button', { name: /^CSS Basics/ })
    expect(css).toHaveTextContent('Beginner · 10%')
    await user.click(css)
    expect(css).toHaveAttribute('aria-current', 'true')
    expect(within(panel()).getByRole('link', { name: 'Start topic: CSS Basics' })).toBeInTheDocument()

    await user.click(graphButton)
    expect(await screen.findByTestId('force-graph')).toBeInTheDocument()
    expect(panel()).toBeInTheDocument()
  })
})

describe('a domain', () => {
  it("loads the domain in the URL, with the switcher and a link to the domain's dashboard", async () => {
    await open()
    expect(fetchTopicGraph).toHaveBeenCalledWith('web-development')
    expect(screen.getByRole('button', { name: 'Web Development: switch domain' })).toBeInTheDocument()
    expect(within(screen.getByRole('main')).getByRole('link', { name: 'Dashboard' })).toHaveAttribute(
      'href',
      '/domains/web-development',
    )
  })

  it("the switcher opens the other domain's graph, not its dashboard", async () => {
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Web Development: switch domain' }))
    expect(await screen.findByRole('menuitem', { name: /Foundations/ })).toHaveAttribute('href', '/domains/foundations/graph')
  })

  it('names a prerequisite from another domain and links to it there', async () => {
    const { user } = await open(graphWith({ react_router: 'completed' }))
    await clickNode(user, 'deployment_basics')
    expect(within(panel()).getByText('Complete Command Line (Foundations) to unlock it.')).toBeInTheDocument()
    const prerequisites = within(panel()).getByRole('region', { name: 'Prerequisites' })
    expect(within(prerequisites).getByRole('button', { name: /React Router/ })).toBeInTheDocument()
    const external = within(prerequisites).getByRole('link', { name: /Command Line/ })
    expect(external).toHaveTextContent('Command LineIn FoundationsNot completed')
    expect(external).toHaveAttribute('href', '/domains/foundations/graph?topic=command_line')
  })

  it('a completed prerequisite from another domain no longer holds the topic back', async () => {
    const data = graphWith({ react_router: 'completed', deployment_basics: 'unlocked' })
    data.nodes.find((n) => n.id === 'deployment_basics').external_prerequisites[0].completed = true
    const { user } = await open(data)
    await clickNode(user, 'deployment_basics')
    expect(within(panel()).getByRole('link', { name: /Command Line/ })).toHaveTextContent('Completed')
    expect(within(panel()).getByRole('link', { name: 'Start topic: Deployment Basics' })).toBeInTheDocument()
  })

  it('a shared topic links to the other domains it belongs to', async () => {
    const { user } = await open(graphWith({}, { html_basics: { domains: ['foundations', 'web-development'] } }))
    await clickNode(user, 'html_basics')
    const domains = within(panel()).getByRole('region', { name: 'Also part of' })
    expect(within(domains).getByRole('link', { name: 'Foundations' })).toHaveAttribute(
      'href',
      '/domains/foundations/graph?topic=html_basics',
    )
    await clickNode(user, 'css_basics')
    expect(within(panel()).queryByRole('region', { name: 'Also part of' })).not.toBeInTheDocument()
  })

  it('says when nothing in this domain builds on a topic', async () => {
    const { user } = await open()
    await clickNode(user, 'deployment_basics')
    expect(within(panel()).getByRole('region', { name: 'Unlocks' })).toHaveTextContent('Nothing in this domain.')
  })

  it('an unknown domain says so and links to the catalogue', async () => {
    fetchTopicGraph.mockRejectedValue(httpError(404, "Unknown domain 'nope'"))
    renderAt('/domains/nope/graph')
    expect(await screen.findByRole('heading', { name: "We couldn't find that domain" })).toBeInTheDocument()
  })
})

describe('the full map', () => {
  async function openMap(entry = '/map') {
    fetchTopicMap.mockResolvedValue(topicMap())
    const user = userEvent.setup()
    const view = renderAt(entry)
    await screen.findByTestId('force-graph')
    return { user, ...view }
  }

  it('shows every topic in every domain, with prerequisites across domains as links', async () => {
    await openMap()
    expect(screen.getByRole('heading', { level: 1, name: 'Full map' })).toBeInTheDocument()
    expect(screen.getByText(/^Every domain: 0 of 11 topics completed\./)).toBeInTheDocument()
    expect(graph.props.graphData.nodes).toHaveLength(11)
    expect(graph.props.graphData.links).toContainEqual({ source: 'command_line', target: 'deployment_basics' })
    expect(fetchTopicGraph).not.toHaveBeenCalled()
  })

  it('groups topics by domain: a band per domain, and each domain drawn behind its topics', async () => {
    await openMap()
    // Every topic is fixed to its row in its domain's band (set once the graph has mounted).
    const rows = bandRows(topicMap().nodes, topicMap().domains)
    await waitFor(() => expect(graph.props.graphData.nodes.every((n) => n.fy === rows.get(n.id))).toBe(true))
    expect(graph.props.onRenderFramePre).toEqual(expect.any(Function))
    const ctx = { save: vi.fn(), restore: vi.fn(), beginPath: vi.fn(), rect: vi.fn(), fill: vi.fn(), stroke: vi.fn(), fillText: vi.fn() }
    act(() => graph.props.onRenderFramePre(ctx, 1))
    expect(ctx.fillText.mock.calls.map(([text]) => text)).toEqual(['Foundations', 'Web Development'])
    // Each domain's box spans its band (just inside its edges), so neighbouring boxes can't overlap.
    const bands = [...bandExtents(topicMap().nodes, topicMap().domains).values()]
    const boxes = ctx.rect.mock.calls.map(([, y, , height]) => [y, y + height])
    boxes.forEach(([top, bottom], i) => {
      expect(top).toBeCloseTo(bands[i].top, -1)
      expect(bottom).toBeCloseTo(bands[i].bottom, -1)
    })
    expect(boxes[0][1]).toBeLessThan(boxes[1][0])
  })

  it('always starts fitted, so it opens on the domains', async () => {
    await openMap()
    // The fake bounding box would be readable unfitted too; a map is fitted even when it isn't.
    graph.api.getGraphBbox.mockReturnValue({ x: [0, 4000], y: [-2000, 2000] })
    act(() => graph.props.onEngineStop())
    expect(graph.api.zoomToFit).toHaveBeenCalledTimes(1)
  })

  it("a domain's own graph isn't grouped", async () => {
    await open()
    expect(graph.props.onRenderFramePre).toBeUndefined()
    await waitFor(() => expect(graph.api.d3Force).toHaveBeenCalledWith('collide', expect.anything()))
    expect(graph.props.graphData.nodes.every((n) => n.fy === undefined)).toBe(true)
  })

  it('lists every domain a topic belongs to, each linking to that domain', async () => {
    const { user } = await openMap()
    await clickNode(user, 'git_basics')
    const domains = within(panel()).getByRole('region', { name: 'Part of' })
    expect(within(domains).getAllByRole('link').map((a) => [a.textContent, a.getAttribute('href')])).toEqual([
      ['Foundations', '/domains/foundations/graph?topic=git_basics'],
      ['Web Development', '/domains/web-development/graph?topic=git_basics'],
    ])
    // Every prerequisite is a topic on the map, so none is listed as being elsewhere.
    await clickNode(user, 'deployment_basics')
    const prerequisites = within(panel()).getByRole('region', { name: 'Prerequisites' })
    expect(within(prerequisites).getAllByRole('button').map((b) => b.textContent)).toEqual([
      'React RouterLocked',
      'Command LineUnlocked',
    ])
    expect(within(prerequisites).queryByRole('link')).not.toBeInTheDocument()
  })

  it('the list names the domain of each topic', async () => {
    const { user } = await openMap()
    await user.click(screen.getByRole('button', { name: 'List' }))
    expect(screen.getByRole('button', { name: /^Command Line/ })).toHaveTextContent('Foundations · Beginner · 10%')
    expect(screen.getByRole('button', { name: /^HTML Basics/ })).toHaveTextContent('Web Development · Beginner · 10%')
  })

  it('the old graph address opens the map, keeping the selected topic', async () => {
    const { router } = await openMap('/graph?topic=css_basics')
    expect(router.state.location.pathname).toBe('/map')
    expect(within(panel()).getByRole('heading', { level: 2, name: 'CSS Basics' })).toBeInTheDocument()
  })
})
