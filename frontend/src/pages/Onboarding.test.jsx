import { act, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser } from '@/api/auth'
import { tokenStorage } from '@/api/client'
import { fetchCatalogue } from '@/api/domains'
import { fetchTopicMap, markKnownTopics } from '@/api/topics'
import { topicMap } from '@/test/fixtures'
import { deferred, httpError, LEARNER, networkError } from '@/test/helpers'
import { fetchDashboard } from '@/api/progress'
import { renderAt } from '@/test/render-app'

vi.mock('@/api/auth', () => ({ fetchCurrentUser: vi.fn(), loginRequest: vi.fn(), registerRequest: vi.fn() }))
vi.mock('@/api/progress', () => ({ fetchDashboard: vi.fn() }))
vi.mock('@/api/topics', () => ({ fetchTopicGraph: vi.fn(), fetchTopicMap: vi.fn(), markKnownTopics: vi.fn() }))
vi.mock('@/api/domains', () => ({ fetchCatalogue: vi.fn(), fetchHome: vi.fn(), joinDomain: vi.fn() }))

const box = (name) => screen.getByRole('checkbox', { name })
// The live region that announces the selection count.
const counter = () => screen.getByText((_, el) => el?.tagName === 'P' && el.getAttribute('aria-live') === 'polite')
const submitButton = () => screen.getByRole('button', { name: /^(Start from the beginning|Continue|Saving)/ })

const WEB = '/domains/web-development/onboarding'

async function open(graph = topicMap(), entry = WEB) {
  tokenStorage.set('jwt')
  fetchCurrentUser.mockResolvedValue(LEARNER)
  fetchTopicMap.mockResolvedValue(graph)
  const user = userEvent.setup()
  const view = renderAt(entry)
  await screen.findAllByRole('checkbox')
  return { user, ...view }
}

function result(knownCount, added = []) {
  return { message: 'Onboarding saved', known_count: knownCount, added_prerequisites: added, recommended: [] }
}

beforeEach(() => {
  // The dashboard's own behaviour is tested in Dashboard.test.jsx; here it just stays loading.
  fetchDashboard.mockReturnValue(new Promise(() => {}))
  fetchCatalogue.mockReturnValue(new Promise(() => {}))
  markKnownTopics.mockResolvedValue(result(0))
})

describe('loading', () => {
  it('shows a skeleton, then the domain, explanation and topics grouped by difficulty', async () => {
    tokenStorage.set('jwt')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    const graph = deferred()
    fetchTopicMap.mockReturnValue(graph.promise)
    renderAt(WEB)
    expect(await screen.findByRole('status', { name: 'Loading topics' })).toBeInTheDocument()
    await act(async () => graph.resolve(topicMap()))

    expect(screen.getByText('Web Development')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Choose topics you already feel comfortable with. AdaptLearn will skip them and start from the right place.',
      ),
    ).toBeInTheDocument()
    const headings = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)
    expect(headings).toEqual(['Beginner4 topics', 'Intermediate3 topics', 'Advanced2 topics', 'Expert1 topic'])
    const beginner = screen.getByRole('region', { name: /^Beginner/ })
    expect(within(beginner).getAllByRole('checkbox')).toHaveLength(4)
    expect(screen.getAllByRole('checkbox')).toHaveLength(10)
    expect(screen.queryByRole('status', { name: 'Loading topics' })).not.toBeInTheDocument()
  })

  it('offers a retry when the topics cannot be loaded', async () => {
    tokenStorage.set('jwt')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    fetchTopicMap.mockRejectedValueOnce(httpError(503, 'Curriculum service is temporarily unavailable. Please try again shortly.'))
    const user = userEvent.setup()
    renderAt(WEB)
    expect(await screen.findByRole('heading', { name: "Couldn't load the topics" })).toBeInTheDocument()
    expect(screen.getByText(/Curriculum service is temporarily unavailable/)).toBeInTheDocument()

    fetchTopicMap.mockResolvedValueOnce(topicMap())
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
    const { user } = await open(topicMap({ completed: ['html_basics'] }))
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
    const { user } = await open(topicMap({ completed: ['html_basics', 'css_basics'] }))
    expect(screen.getByText(/Topics you have already completed, here or in another domain, are ticked/)).toBeInTheDocument()
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
    expect(markKnownTopics).toHaveBeenCalledWith('web-development', ['react_hooks'])
    const done = (await screen.findByText("You're all set")).closest('[role="status"]')
    expect(router.state.location.pathname).toBe('/domains/web-development')
    expect(done).toHaveTextContent("You're all set")
    expect(done).toHaveTextContent('5 topics are marked as known')
    expect(done).toHaveTextContent('HTML Basics, JavaScript Fundamentals, Props & State and 1 more')
  })

  it('saving with nothing selected starts from the beginning', async () => {
    const { user, router } = await open()
    await user.click(submitButton())
    expect(markKnownTopics).toHaveBeenCalledWith('web-development', [])
    expect(await screen.findByText(/starting from the beginning/)).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/domains/web-development')
  })

  it('a returning learner who adds nothing still saves, so the domain counts as set up', async () => {
    markKnownTopics.mockResolvedValue(result(1))
    const { user, router } = await open(topicMap({ completed: ['html_basics'] }))
    await user.click(submitButton())
    expect(markKnownTopics).toHaveBeenCalledWith('web-development', [])
    expect(await screen.findByText("You're all set")).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/domains/web-development')
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
    expect(router.state.location.pathname).toBe(WEB)
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

describe('domains', () => {
  it("only shows the domain's own topics, including those it shares", async () => {
    await open(topicMap(), '/domains/foundations/onboarding')
    expect(screen.getByText('Foundations')).toBeInTheDocument()
    expect(screen.getAllByRole('checkbox')).toHaveLength(2)
    expect(box('Command Line')).toBeInTheDocument()
    expect(box('Git Basics')).toBeInTheDocument()
    expect(screen.queryByRole('checkbox', { name: 'HTML Basics' })).not.toBeInTheDocument()
  })

  it('a shared topic completed through another domain is already ticked', async () => {
    await open(topicMap({ completed: ['command_line', 'git_basics'] }))
    expect(box('Git Basics')).toBeChecked()
    expect(box('Git Basics')).toHaveAccessibleDescription('Already completed What Git Basics covers.')
    expect(submitButton()).toHaveTextContent('Continue to dashboard')
  })

  it('names and counts prerequisites that come from other domains', async () => {
    const { user } = await open()
    expect(screen.queryByRole('region', { name: 'Included from other domains' })).not.toBeInTheDocument()
    await user.click(box('Git Basics'))
    const elsewhere = screen.getByRole('region', { name: 'Included from other domains' })
    expect(within(elsewhere).getByRole('listitem')).toHaveTextContent('Command Line (Foundations), needed for Git Basics')
    expect(counter()).toHaveTextContent('2 topics selected (1 included as a prerequisite)')

    await user.click(box('Deployment Basics'))
    expect(within(elsewhere).getByRole('listitem')).toHaveTextContent('needed for Git Basics and Deployment Basics')
  })

  it('a prerequisite from another domain that is already completed is not listed', async () => {
    const { user } = await open(topicMap({ completed: ['command_line'] }))
    await user.click(box('Git Basics'))
    expect(screen.queryByRole('region', { name: 'Included from other domains' })).not.toBeInTheDocument()
    expect(counter()).toHaveTextContent('1 topic selected')
  })

  it("saves for the domain in the URL and opens that domain's dashboard", async () => {
    markKnownTopics.mockResolvedValue(result(2, ['command_line']))
    const { user, router } = await open(topicMap(), '/domains/foundations/onboarding')
    await user.click(box('Git Basics'))
    await user.click(submitButton())
    expect(markKnownTopics).toHaveBeenCalledWith('foundations', ['git_basics'])
    expect(await screen.findByText(/Their prerequisites were included too \(Command Line\)/)).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/domains/foundations')
  })

  it('an unknown domain says so and links to the catalogue', async () => {
    tokenStorage.set('jwt')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    fetchTopicMap.mockResolvedValue(topicMap())
    renderAt('/domains/nope/onboarding')
    expect(await screen.findByRole('heading', { name: "We couldn't find that domain" })).toBeInTheDocument()
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  })
})
