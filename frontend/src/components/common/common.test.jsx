import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { Loader, Spinner } from '@/components/common/Loader'
import { PageHeader } from '@/components/common/PageHeader'
import { ProgressBar } from '@/components/common/ProgressBar'
import { TopicStatusBadge } from '@/components/topics/TopicStatusBadge'
import { redirectTarget } from '@/lib/redirect'

describe('ProgressBar', () => {
  it.each([
    [42, '42%', '42'],
    [42.6, '43%', '43'],
    [-5, '0%', '0'],
    [140, '100%', '100'],
    [undefined, '0%', '0'],
  ])('value %s shows %s', (value, text, aria) => {
    render(<ProgressBar value={value} label="CSS Basics" />)
    expect(screen.getByText(text)).toBeInTheDocument()
    const bar = screen.getByRole('progressbar', { name: 'CSS Basics' })
    expect(bar).toHaveAttribute('aria-valuenow', aria)
  })
})

describe('TopicStatusBadge', () => {
  it.each([
    ['completed', 'Completed', 'bg-status-completed'],
    ['in_progress', 'In progress', 'bg-status-in-progress'],
    ['unlocked', 'Unlocked', 'bg-status-unlocked'],
    ['locked', 'Locked', 'bg-status-locked'],
  ])('%s', (status, label, fill) => {
    render(<TopicStatusBadge status={status} />)
    expect(screen.getByText(label)).toHaveClass(fill)
  })

  it('light fills use dark text; only locked uses white', () => {
    render(
      <>
        <TopicStatusBadge status="unlocked" />
        <TopicStatusBadge status="locked" />
      </>,
    )
    expect(screen.getByText('Unlocked')).toHaveClass('text-ink')
    expect(screen.getByText('Locked')).toHaveClass('text-white')
  })

  it('shows an unknown status as-is', () => {
    render(<TopicStatusBadge status="archived" />)
    expect(screen.getByText('archived')).toBeInTheDocument()
  })
})

describe('ErrorState', () => {
  it('shows the message and retries', async () => {
    const onRetry = vi.fn()
    render(<ErrorState title="Couldn't load topics" message="Server unavailable" onRetry={onRetry} />)
    expect(screen.getByRole('alert')).toHaveTextContent("Couldn't load topicsServer unavailable")
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('has no retry button without a handler', () => {
    render(<ErrorState message="Nope" />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})

describe('EmptyState, Loader, PageHeader', () => {
  it('EmptyState renders its title, description and action', () => {
    render(<EmptyState title="No topics yet" description="Pick a topic" action={<button type="button">Start</button>} />)
    expect(screen.getByRole('heading', { name: 'No topics yet' })).toBeInTheDocument()
    expect(screen.getByText('Pick a topic')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start' })).toBeInTheDocument()
  })

  it('Loader and Spinner announce themselves to screen readers', () => {
    render(
      <>
        <Loader label="Generating your quiz…" />
        <Spinner label="Saving" />
      </>,
    )
    const statuses = screen.getAllByRole('status')
    expect(statuses[0]).toHaveTextContent('Generating your quiz…')
    expect(statuses[1]).toHaveTextContent('Saving')
  })

  it('PageHeader renders a level-1 heading', () => {
    render(<PageHeader title="Dashboard" description="Your progress" actions={<button type="button">Act</button>} />)
    expect(screen.getByRole('heading', { level: 1, name: 'Dashboard' })).toBeInTheDocument()
  })
})

describe('redirectTarget', () => {
  it.each([
    [undefined, '/dashboard'],
    [{ pathname: '/login' }, '/dashboard'],
    [{ pathname: '/register' }, '/dashboard'],
    [{ pathname: '/graph' }, '/graph'],
    [{ pathname: '/quiz/css_basics', search: '?a=1', hash: '#q2' }, '/quiz/css_basics?a=1#q2'],
  ])('%j -> %s', (from, expected) => {
    expect(redirectTarget(from)).toBe(expected)
  })
})
