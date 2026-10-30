import { act, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser } from '@/api/auth'
import { tokenStorage } from '@/api/client'
import { fetchCatalogue, joinDomain } from '@/api/domains'
import { fetchDashboard } from '@/api/progress'
import { fetchTopicGraph, fetchTopicMap } from '@/api/topics'
import { catalogue, domainSummary } from '@/test/fixtures'
import { deferred, httpError, LEARNER } from '@/test/helpers'
import { renderAt } from '@/test/render-app'

vi.mock('@/api/auth', () => ({ fetchCurrentUser: vi.fn(), loginRequest: vi.fn(), registerRequest: vi.fn() }))
vi.mock('@/api/domains', () => ({ fetchCatalogue: vi.fn(), fetchHome: vi.fn(), joinDomain: vi.fn() }))
vi.mock('@/api/progress', () => ({ fetchDashboard: vi.fn() }))
vi.mock('@/api/topics', () => ({ fetchTopicGraph: vi.fn(), fetchTopicMap: vi.fn(), markKnownTopics: vi.fn() }))

beforeEach(() => {
  tokenStorage.set('jwt')
  fetchCurrentUser.mockResolvedValue(LEARNER)
  // Pages reached from here are tested in their own files; here they just stay loading.
  fetchDashboard.mockReturnValue(new Promise(() => {}))
  fetchTopicGraph.mockReturnValue(new Promise(() => {}))
  fetchTopicMap.mockReturnValue(new Promise(() => {}))
})

async function open(data = catalogue()) {
  fetchCatalogue.mockResolvedValue(data)
  const user = userEvent.setup()
  const view = renderAt('/domains')
  await screen.findAllByRole('article')
  return { user, ...view }
}

const card = (name) => screen.getByRole('article', { name })
const enrolled = (onboarded) => ({ domain: 'web-development', domain_name: 'Web Development', joined_at: '2026-10-31T00:00:00Z', onboarded })

describe('loading', () => {
  it('shows a placeholder until the domains arrive', async () => {
    const pending = deferred()
    fetchCatalogue.mockReturnValue(pending.promise)
    renderAt('/domains')
    expect(await screen.findByRole('status', { name: 'Loading domains' })).toBeInTheDocument()
    await act(async () => pending.resolve(catalogue()))
    expect(screen.getAllByRole('article')).toHaveLength(2)
  })

  it('offers a retry when the domains cannot be loaded', async () => {
    fetchCatalogue.mockRejectedValueOnce(httpError(503, 'Database is temporarily unavailable. Please try again shortly.'))
    const user = userEvent.setup()
    renderAt('/domains')
    expect(await screen.findByRole('heading', { name: "Couldn't load the domains" })).toBeInTheDocument()
    fetchCatalogue.mockResolvedValueOnce(catalogue())
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findAllByRole('article')).toHaveLength(2)
  })
})

describe('the catalogue', () => {
  it('lists every domain in order with what it covers and how big it is', async () => {
    await open()
    expect(screen.getByRole('heading', { level: 1, name: 'Domains' })).toBeInTheDocument()
    expect(screen.getByText(/Topics shared between domains count in each/)).toBeInTheDocument()
    const names = screen.getAllByRole('article').map((a) => within(a).getByRole('heading', { level: 2 }).textContent)
    expect(names).toEqual(['Foundations', 'Web Development'])
    expect(card('Foundations')).toHaveTextContent('The tools every programmer uses.')
    expect(card('Foundations')).toHaveTextContent('3 topics · 1 completed')
    expect(card('Web Development')).toHaveTextContent('30 topics · 1 completed')
  })

  it('a learner with no domain yet is told how to start', async () => {
    await open({ domains: [domainSummary()] })
    expect(screen.getByText(/Choose a domain to start\. We'll ask what you already know/)).toBeInTheDocument()
    expect(card('Web Development')).toHaveTextContent('30 topics')
    expect(within(card('Web Development')).queryByRole('progressbar')).not.toBeInTheDocument()
  })

  it('marks joined, suggested and completed domains', async () => {
    const data = catalogue()
    data.domains.push(domainSummary({ id: 'data-science', name: 'Data Science', joined: true, onboarded: true, curriculum_complete: true }))
    data.domains.push(domainSummary({ id: 'devops', name: 'DevOps' }))
    await open(data)
    expect(within(card('Foundations')).getByText('Joined')).toBeInTheDocument()
    expect(within(card('Web Development')).getByText('Head start')).toBeInTheDocument()
    expect(within(card('Data Science')).getByText('Completed')).toBeInTheDocument()
    expect(within(card('DevOps')).queryByText(/Joined|Head start|Completed/)).not.toBeInTheDocument()
  })

  it('a joined domain shows progress and opens its dashboard', async () => {
    await open()
    const foundations = card('Foundations')
    expect(within(foundations).getByRole('progressbar', { name: 'Progress' })).toHaveAttribute('aria-valuenow', '33')
    expect(within(foundations).getByRole('link', { name: 'Open Foundations' })).toHaveAttribute('href', '/domains/foundations')
    expect(foundations).not.toHaveTextContent('Already completed')
  })

  it('a joined domain not set up yet leads to its onboarding', async () => {
    const data = catalogue()
    data.domains[0] = { ...data.domains[0], onboarded: false }
    await open(data)
    expect(within(card('Foundations')).getByRole('link', { name: 'Finish setting up Foundations' })).toHaveAttribute(
      'href',
      '/domains/foundations/onboarding',
    )
  })

  it('a domain not joined shows the head start, a way to join and a preview', async () => {
    await open()
    const web = card('Web Development')
    expect(web).toHaveTextContent('Already completed: Git Basics')
    expect(web).toHaveTextContent('Ready to start: GitHub Collaboration')
    expect(within(web).getByRole('button', { name: 'Join Web Development' })).toHaveTextContent('Join')
    expect(within(web).getByRole('link', { name: 'Preview topics: Web Development' })).toHaveAttribute(
      'href',
      '/domains/web-development/graph',
    )
  })
})

describe('joining', () => {
  it('joins the domain and opens its onboarding', async () => {
    joinDomain.mockResolvedValue(enrolled(false))
    const { user, router } = await open()
    await user.click(screen.getByRole('button', { name: 'Join Web Development' }))
    expect(joinDomain).toHaveBeenCalledWith('web-development')
    expect(router.state.location.pathname).toBe('/domains/web-development/onboarding')
    expect(await screen.findByRole('heading', { name: 'What do you already know?' })).toBeInTheDocument()
  })

  it('opens the dashboard instead if the domain was already set up (e.g. joined in another tab)', async () => {
    joinDomain.mockResolvedValue(enrolled(true))
    const { user, router } = await open()
    await user.click(screen.getByRole('button', { name: 'Join Web Development' }))
    expect(router.state.location.pathname).toBe('/domains/web-development')
  })

  it('shows progress, ignores a second click, and explains a failure on that domain', async () => {
    const pending = deferred()
    joinDomain.mockReturnValueOnce(pending.promise)
    const data = catalogue()
    data.domains.push(domainSummary({ id: 'devops', name: 'DevOps' }))
    const { user, router } = await open(data)
    await user.click(screen.getByRole('button', { name: 'Join Web Development' }))
    const busy = screen.getByRole('button', { name: 'Join Web Development' })
    expect(busy).toHaveTextContent('Joining…')
    expect(busy).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Join DevOps' })).toBeDisabled()
    await user.click(busy)
    expect(joinDomain).toHaveBeenCalledTimes(1)

    await act(async () => pending.reject(httpError(404, "Unknown domain 'web-development'")))
    expect(within(card('Web Development')).getByRole('alert')).toHaveTextContent("Unknown domain 'web-development'")
    expect(within(card('DevOps')).queryByRole('alert')).not.toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/domains')
    expect(screen.getByRole('button', { name: 'Join Web Development' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Join DevOps' })).toBeEnabled()
  })
})
