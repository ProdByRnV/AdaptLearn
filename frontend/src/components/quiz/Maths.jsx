import { useEffect, useState } from 'react'
import { cn } from 'cn'

// KaTeX (and its stylesheet and fonts) is only downloaded once a question contains maths.
let katex = null
let loading = null

function loadKatex() {
  loading ??= Promise.all([import('katex'), import('katex/dist/katex.min.css')]).then(([module]) => {
    katex = module.default
    return katex
  })
  return loading
}

/**
 * LaTeX drawn with KaTeX, with MathML for screen readers. Until KaTeX has loaded (or if it can't
 * be), the source is shown as it was written. `trust` stays off, so a question can't add links or
 * other HTML through maths commands.
 */
export function Maths({ tex, display = false }) {
  const [renderer, setRenderer] = useState(() => katex)

  useEffect(() => {
    if (renderer) return undefined
    let alive = true
    loadKatex().then(
      (loaded) => alive && setRenderer(() => loaded),
      () => {}, // Offline or blocked: the source stays readable.
    )
    return () => {
      alive = false
    }
  }, [renderer])

  if (!renderer) {
    return <span className="font-mono text-[0.9em]">{display ? `\\[${tex}\\]` : `\\(${tex}\\)`}</span>
  }
  const html = renderer.renderToString(tex, {
    displayMode: display,
    output: 'htmlAndMathml',
    throwOnError: false,
    trust: false,
    strict: 'ignore',
  })
  return (
    <span
      data-maths={display ? 'block' : 'inline'}
      className={cn(display && 'my-2 block overflow-x-auto overflow-y-hidden')}
      // KaTeX builds this markup itself and escapes the source; with trust off it adds no links or scripts.
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
