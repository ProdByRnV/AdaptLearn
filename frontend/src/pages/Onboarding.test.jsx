import { act, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser } from '@/api/auth'
import { tokenStorage } from '@/api/client'
import { fetchTopicGraph, markKnownTopics } from '@/api/topics'
import { topicGraph } from '@/test/fixtures'
import { deferred, httpError, LEARNER, networkError } from '@/test/helpers'
import { fetchDashboard } from '@/api/progress'
import { renderAt } from '@/test/render-app'

vi.mock('@/api/auth', () => ({ fetchCurrentUser: vi.fn(), loginRequest: vi.fn(), registerRequest: vi.fn() }))
vi.mock('@/api/progress', () => ({ fetchDashboard: vi.fn() }))
vi.mock('@/api/topics', () => ({ fetchLearningPath: vi.fn(), fetchTopicGraph: vi.fn(), markKnownTopics: vi.fn() }))

const box = (name) => screen.getByRole('checkbox', { name })
// The live region that announces the selection count.
const counter = () => screen.getByText((_, el) => el?.tagName === 'P' && el.getAttribute('aria-live') === 'polite')
const submitButton = () => screen.getByRole('button', { name: /^(Start from the beginning|Continue|Saving)/ })

async function open(graph = topicGraph()) {
  tokenStorage.set('jwt')
  fetchCurrentUser.mockResolvedValue(LEARNER)
  fetchTopicGraph.mockResolvedValue(graph)
  const user = userEvent.setup()
  const view = renderAt('/onboarding')
  await screen.findByRole('checkbox', { name: 'HTML Basics' })
  return { user, ...view }
}

function result(knownCount, added = []) {
  return { message: 'Onboarding saved', known_count: knownCount, added_prerequisites: added, recommended: [] }
}

beforeEach(() => {
  // The dashboard's own behaviour is tested in Dashboard.test.jsx; here it just stays loading.
  fetchDashboard.mockReturnValue(new Promise(() => {}))
  markKnownTopics.mockResolvedValue(result(0))
})

describe('loading', () => {
  it('shows a skeleton, then the domain, explanation and topics grouped by difficulty', async () => {
    tokenStorage.set('jwt')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    const graph = deferred()
    fetchTopicGraph.mockReturnValue(graph.promise)
    renderAt('/onboarding')
    expect(await screen.findByRole('status', { name: 'Loading topics' })).toBeInTheDocument()
    await act(async () => graph.resolve(topicGraph()))

    expect(screen.getByText('Web Development')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Choose topics you already feel comfortable with. AdaptLearn will skip them and start from the right place.',
      ),
    ).toBeInTheDocument()
    const headings = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)
    expect(headings).toEqual(['Beginner3 topics', 'Intermediate3 topics', 'Advanced2 topics', 'Expert1 topic'])
    const beginner = screen.getByRole('region', { name: /^Beginner/ })
    expect(within(beginner).getAllByRole('checkbox')).toHaveLength(3)
    expect(screen.getAllByRole('checkbox')).toHaveLength(9)
    expect(screen.queryByRole('status', { name: 'Loading topics' })).not.toBeInTheDocument()
  })

  it('offers a retry when the topics cannot be loaded', async () => {
    tokenStorage.set('jwt')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    fetchTopicGraph.mockRejectedValueOnce(httpError(503, 'Curriculum service is temporarily unavailable. Please try again shortly.'))
    const user = userEvent.setup()
    renderAt('/onboarding')
    expect(await screen.findByRole('heading', { name: "Couldn't load the topics" })).toBeInTheDocument()
    expect(screen.getByText(/Curriculum service is temporarily unavailable/)).toBeInTheDocument()

    fetchTopicGraph.mockResolvedValueOnce(topicGraph())
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('checkbox', { name: 'HTML Basics' })).toBeInTheDocument()
  })
})

describe('choosing topics', () => {
  it('starts with nothing selected', async () => {
    await open()
    expect(screen.getByText('No topics selected')).toBeInTheDocument()
    expect(submitButton()).toHaveTextContent('Start from the beginning')
    expect(screen.getAllByRole('checkbox').every((c) => !c.checked && !c.hasAttribute('aria-disabled'))).toBe(true)
    expect(screen.queryByRole('button', { name: 'Clear' })).not.toBeInTheDocument()
  })

  it('counts a selection and updates the button', async () => {
    const { user } = await open()
    await user.click(box('HTML Basics'))
    expect(box('HTML Basics')).toBeChecked()
    expect(counter()).toHaveTextContent('1 topic selected')
    expect(submitButton()).toHaveTextContent('Continue with 1 topic')
  })

  it('the whole card toggles the topic, and the keyboard works', async () => {
    const { user } = await open()
    await user.click(screen.getByText('What CSS Basics covers.'))
    expect(box('CSS Basics')).toBeChecked()
    box('Flexbox').focus()
    await user.keyboard(' ')
    expect(box('Flexbox')).toBeChecked()
    await user.keyboard(' ')
    expect(box('Flexbox')).not.toBeChecked()
  })

  it("ticks a topic's prerequisites too, explains why, and counts them", async () => {
    const { user } = await open()
    await user.click(box('React Hooks'))
    for (const name of ['Props & State', 'React Fundamentals', 'JavaScript Fundamentals', 'HTML Basics']) {
      expect(box(name)).toBeChecked()
      expect(box(name)).toHaveAttribute('aria-disabled', 'true')
      expect(box(name)).toHaveAccessibleDescription('Included: needed for React Hooks What ' + name + ' covers.')
    }
    expect(box('CSS Basics')).not.toBeChecked()
    expect(counter()).toHaveTextContent('5 topics selected (4 included as prerequisites)')
    expect(submitButton()).toHaveTextContent('Continue with 5 topics')
  })

  it('names every selected topic that needs a shared prerequisite', async () => {
    const { user } = await open()
    await user.click(box('React Hooks'))
    await user.click(box('React Router'))
    expect(box('React Fundamentals')).toHaveAccessibleDescription('Included: needed for React Hooks and React Router What React Fundamentals covers.')
  })

  it('unticking the topic releases its prerequisites', async () => {
    const { user } = await open()
    await user.click(box('Flexbox'))
    expect(box('CSS Basics')).toHaveAttribute('aria-disabled', 'true')
    await user.click(box('Flexbox'))
    expect(box('CSS Basics')).not.toBeChecked()
    expect(box('CSS Basics')).not.toHaveAttribute('aria-disabled')
    expect(screen.getByText('No topics selected')).toBeInTheDocument()
  })

  it('clicking a topic that is locked in (prerequisite or completed) changes nothing', async () => {
    const { user } = await open(topicGraph({ completed: ['html_basics'] }))
    await user.click(box('Flexbox'))
    await user.click(box('CSS Basics'))
    await user.click(box('HTML Basics'))
    expect(box('CSS Basics')).toBeChecked()
    expect(box('HTML Basics')).toBeChecked()
    expect(counter()).toHaveTextContent('2 topics selected (1 included as a prerequisite)')
  })

  it('Clear removes every selection', async () => {
    const { user } = await open()
    await user.click(box('Flexbox'))
    await user.click(box('React Router'))
    await user.click(screen.getByRole('button', { name: 'Clear' }))
    expect(screen.getAllByRole('checkbox').some((c) => c.checked)).toBe(false)
    expect(screen.getByText('No topics selected')).toBeInTheDocument()
  })

  it('a returning learner sees completed topics ticked and fixed, not counted again', async () => {
    const { user } = await open(topicGraph({ completed: ['html_basics', 'css_basics'] }))
    expect(screen.getByText(/Topics you have already completed are ticked/)).toBeInTheDocument()
    expect(box('HTML Basics')).toBeChecked()
    expect(box('HTML Basics')).toHaveAttribute('aria-disabled', 'true')
    expect(box('HTML Basics')).toHaveAccessibleDescription('Already completed What HTML Basics covers.')
    expect(submitButton()).toHaveTextContent('Continue to dashboard')
    await user.click(box('Flexbox'))
    expect(counter()).toHaveTextContent('1 topic selected')
  })
})

describe('saving', () => {
  it('sends only the chosen topics, then confirms on the dashboard', async () => {
    markKnownTopics.mockResolvedValue(result(5, ['html_basics', 'javascript_fundamentals', 'props_state', 'react_fundamentals']))
    const { user, router } = await open()
    await user.click(box('React Hooks'))
    await user.click(submitButton())
    expect(markKnownTopics).toHaveBeenCalledWith(['react_hooks'])
    const done = (await screen.findByText("You're all set")).closest('[role="status"]')
    expect(router.state.location.pathname).toBe('/dashboard')
    expect(done).toHaveTextContent("You're all set")
    expect(done).toHaveTextContent('5 topics are marked as known')
    expect(done).toHaveTextContent('HTML Basics, JavaScript Fundamentals, Props & State and 1 more')
  })

  it('saving with nothing selected starts from the beginning', async () => {
    const { user, router } = await open()
    await user.click(submitButton())
    expect(markKnownTopics).toHaveBeenCalledWith([])
    expect(await screen.findByText(/starting from the beginning/)).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/dashboard')
  })

  it('a returning learner who adds nothing just goes to the dashboard', async () => {
    const { user, router } = await open(topicGraph({ completed: ['html_basics'] }))
    await user.click(submitButton())
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    expect(router.state.location.pathname).toBe('/dashboard')
    expect(markKnownTopics).not.toHaveBeenCalled()
    expect(screen.queryByText("You're all set")).not.toBeInTheDocument()
  })

  it('shows progress and ignores extra clicks while saving', async () => {
    const pending = deferred()
    markKnownTopics.mockReturnValue(pending.promise)
    const { user } = await open()
    await user.click(box('Flexbox'))
    await user.click(submitButton())
    expect(submitButton()).toHaveTextContent('Saving…')
    expect(submitButton()).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Clear' })).toBeDisabled()
    await user.click(submitButton())
    expect(markKnownTopics).toHaveBeenCalledTimes(1)
    await act(async () => pending.resolve(result(3)))
  })

  it('a failed save keeps the selection and can be retried', async () => {
    markKnownTopics.mockRejectedValueOnce(networkError())
    const { user, router } = await open()
    await user.click(box('Flexbox'))
    await user.click(submitButton())
    expect(await screen.findByRole('alert')).toHaveTextContent("Can't reach the AdaptLearn server")
    expect(router.state.location.pathname).toBe('/onboarding')
    expect(box('Flexbox')).toBeChecked()
    expect(submitButton()).toBeEnabled()

    // Changing the selection clears the old error. (HTML Basics is locked in as Flexbox's prerequisite.)
    await user.click(box('React Router'))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()

    markKnownTopics.mockResolvedValueOnce(result(3))
    await user.click(submitButton())
    expect(await screen.findByText(/3 topics are marked as known/)).toBeInTheDocument()
  })
})
