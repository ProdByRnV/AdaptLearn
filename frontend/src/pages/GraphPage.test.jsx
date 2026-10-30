import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useImperativeHandle } from 'react'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser } from '@/api/auth'
import { tokenStorage } from '@/api/client'
import { fetchTopicGraph } from '@/api/topics'
import { topicGraph } from '@/test/fixtures'
import { deferred, httpError, LEARNER } from '@/test/helpers'
import { renderAt } from '@/test/render-app'

vi.mock('@/api/auth', () => ({ fetchCurrentUser: vi.fn(), loginRequest: vi.fn(), registerRequest: vi.fn() }))
vi.mock('@/api/topics', () => ({ fetchLearningPath: vi.fn(), fetchTopicGraph: vi.fn(), markKnownTopics: vi.fn() }))
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
})

/** topicGraph() with some statuses changed, e.g. {html_basics: 'completed', css_basics: 'in_progress'}. */
function graphWith(statuses = {}, changes = {}) {
  const data = topicGraph()
  data.nodes = data.nodes.map((n) => ({ ...n, ...(statuses[n.id] && { status: statuses[n.id] }), ...changes[n.id] }))
  return data
}

async function open(data = topicGraph(), entry = '/graph') {
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
    renderAt('/graph')
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
    renderAt('/graph')
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
    expect(screen.getByText('1 of 9 topics completed. Select a topic to see its details.')).toBeInTheDocument()
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
    await open(topicGraph(), '/graph?topic=css_basics')
    expect(within(panel()).getByRole('heading', { level: 2, name: 'CSS Basics' })).toBeInTheDocument()
    act(() => graph.props.onEngineStop())
    expect(graph.api.zoomToFit).not.toHaveBeenCalled()
    expect(graph.api.centerAt).toHaveBeenLastCalledWith(0, 5, 400)
  })

  it('shows the hint when the URL names a topic that does not exist', async () => {
    await open(topicGraph(), '/graph?topic=quantum_basics')
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
