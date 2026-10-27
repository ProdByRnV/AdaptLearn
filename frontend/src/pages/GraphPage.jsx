import { List, MousePointerClick, Network } from 'lucide-react'
import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router'
import { cn } from 'cn'

import { getErrorMessage } from '@/api/client'
import { fetchTopicGraph } from '@/api/topics'
import { ErrorState } from '@/components/common/ErrorState'
import { PageHeader } from '@/components/common/PageHeader'
import { GraphLegend } from '@/components/graph/GraphLegend'
import { TopicList } from '@/components/graph/TopicList'
import { TopicPanel } from '@/components/graph/TopicPanel'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useApiData } from '@/hooks/useApiData'
import { statusCounts, toGraphData } from '@/lib/graph'

// The graph library (canvas + d3) is only downloaded when this page shows the graph.
const KnowledgeGraph = lazy(() => import('@/components/graph/KnowledgeGraph'))

/**
 * The curriculum as an interactive graph (PRD: knowledge graph), or as a list. Selecting a topic
 * opens its detail panel; the selection lives in the URL (?topic=id) so it survives a reload and
 * other pages can link straight to a topic.
 */
export default function GraphPage() {
  const { data, error, loading, reload } = useApiData(fetchTopicGraph)
  const [params, setParams] = useSearchParams()
  const [view, setView] = useState('graph')

  const topics = useMemo(() => data?.nodes ?? [], [data])
  const topicsById = useMemo(() => new Map(topics.map((t) => [t.id, t])), [topics])
  const counts = useMemo(() => statusCounts(topics), [topics])
  const selected = topicsById.get(params.get('topic')) ?? null

  const select = useCallback(
    (id) => setParams(id ? { topic: id } : {}, { replace: true, preventScrollReset: true }),
    [setParams],
  )

  useEffect(() => {
    if (!selected) return undefined
    const onKey = (event) => event.key === 'Escape' && select(null)
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [selected, select])

  return (
    <>
      <PageHeader
        title="Knowledge graph"
        description={
          data
            ? `${counts.completed} of ${topics.length} topics completed. Select a topic to see its details.`
            : 'Every topic and the prerequisites between them.'
        }
        actions={
          <div role="group" aria-label="View" className="inline-flex rounded-lg border bg-card p-0.5">
            <ViewButton active={view === 'graph'} onClick={() => setView('graph')} icon={Network} label="Graph" />
            <ViewButton active={view === 'list'} onClick={() => setView('list')} icon={List} label="List" />
          </div>
        }
      />

      {loading && <Skeleton role="status" aria-label="Loading the knowledge graph" className="h-[32rem] rounded-xl" />}
      {error && (
        <ErrorState
          title="Couldn't load the knowledge graph"
          message={getErrorMessage(error)}
          onRetry={reload}
          className="rounded-xl border bg-card"
        />
      )}
      {data && (
        <div className="flex flex-col gap-4">
          <GraphLegend counts={counts} />
          <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
            {view === 'graph' ? (
              <GraphCard data={data} counts={counts} selectedId={selected?.id ?? null} onSelect={select} />
            ) : (
              <TopicList topics={topics} selectedId={selected?.id ?? null} onSelect={select} />
            )}
            {selected ? (
              <TopicPanel
                topic={selected}
                topics={topics}
                topicsById={topicsById}
                onSelect={select}
                onClose={() => select(null)}
              />
            ) : (
              <Card className="hidden items-center gap-2 px-5 py-10 text-center lg:flex">
                <MousePointerClick aria-hidden="true" className="size-6 text-primary" />
                <p className="text-sm text-body">Select a topic to see its details, prerequisites and resources.</p>
              </Card>
            )}
          </div>
        </div>
      )}
    </>
  )
}

function ViewButton({ active, onClick, icon: Icon, label }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        'inline-flex h-8 items-center gap-1.5 rounded-md px-3 text-sm font-medium transition-colors',
        'focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
        active ? 'bg-primary text-primary-foreground' : 'text-body hover:bg-muted',
      )}
    >
      <Icon aria-hidden="true" className="size-4" />
      {label}
    </button>
  )
}

/** The canvas, sized to its container. Described in text for screen readers, who can use the list. */
function GraphCard({ data, counts, selectedId, onSelect }) {
  const container = useRef(null)
  const [width, setWidth] = useState(0)
  const graphData = useMemo(() => toGraphData(data), [data])

  useEffect(() => {
    // The observer reports the first size too.
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    observer.observe(container.current)
    return () => observer.disconnect()
  }, [])

  const size = width || 800
  const height = Math.round(Math.min(620, Math.max(400, size * 0.62)))
  return (
    <Card className="overflow-hidden py-0">
      <p className="sr-only">
        {`Knowledge graph of ${data.nodes.length} topics: ${counts.completed} completed, ${counts.in_progress} in progress, ${counts.unlocked} unlocked and ${counts.locked} locked. Switch to the list view to browse them as text.`}
      </p>
      <div
        ref={container}
        className="bg-[radial-gradient(var(--border)_1px,transparent_1px)] [background-size:20px_20px]"
      >
        <Suspense fallback={<Skeleton role="status" aria-label="Drawing the graph" className="rounded-none" style={{ height }} />}>
          <KnowledgeGraph data={graphData} selectedId={selectedId} onSelect={onSelect} width={size} height={height} />
        </Suspense>
      </div>
    </Card>
  )
}
