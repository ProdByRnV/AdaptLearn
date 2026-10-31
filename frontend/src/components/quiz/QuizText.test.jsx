import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { QuizText } from '@/components/quiz/QuizText'

// KaTeX is loaded on first use and kept, so the first test sees the loading state.
describe('maths', () => {
  it('shows the source until KaTeX has loaded, then draws it with MathML for screen readers', async () => {
    const { container } = render(<QuizText text={'What is \\( x^2 \\) when x = 3?'} />)
    expect(container).toHaveTextContent('What is \\(x^2\\) when x = 3?')
    await waitFor(() => expect(container.querySelector('.katex')).not.toBeNull())
    const maths = container.querySelector('[data-maths="inline"]')
    expect(maths.querySelector('math')).not.toBeNull()
    expect(maths.querySelector('annotation[encoding="application/x-tex"]')).toHaveTextContent('x^2')
    // The drawn version is hidden from screen readers, which read the MathML instead.
    expect(maths.querySelector('.katex-html')).toHaveAttribute('aria-hidden', 'true')
    expect(container).toHaveTextContent(/^What is .* when x = 3\?$/)
  })

  it('draws a displayed formula as a block that can scroll sideways', async () => {
    const { container } = render(<QuizText text={'Area:\n\\[ A = \\pi r^2 \\]'} />)
    await waitFor(() => expect(container.querySelector('.katex-display')).not.toBeNull())
    const block = container.querySelector('[data-maths="block"]')
    expect(block).toHaveClass('block', 'overflow-x-auto')
    expect(block.querySelector('annotation')).toHaveTextContent('A = \\pi r^2')
  })

  it('shows broken LaTeX as an error inside the text instead of failing the page', async () => {
    const { container } = render(<QuizText text={'Broken \\( \\frac{1 \\) here'} />)
    await waitFor(() => expect(container.querySelector('.katex-error')).not.toBeNull())
    expect(container).toHaveTextContent(/^Broken .* here$/)
  })

  it('never turns maths into links or other HTML', async () => {
    const { container } = render(
      <QuizText text={'Click \\( \\href{javascript:alert(1)}{x} \\url{https://example.com} \\)'} />,
    )
    await waitFor(() => expect(container.querySelector('.katex, .katex-error')).not.toBeNull())
    expect(container.querySelector('a')).toBeNull()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('keeps code and maths apart in one question', async () => {
    const { container } = render(<QuizText text={'`np.mean(x)` returns \\( \\bar{x} \\)'} />)
    await waitFor(() => expect(container.querySelector('.katex')).not.toBeNull())
    expect(container.querySelector('code')).toHaveTextContent('np.mean(x)')
    expect(container.querySelector('annotation')).toHaveTextContent('\\bar{x}')
  })
})
