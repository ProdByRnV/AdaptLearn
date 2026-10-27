import { Maximize2, Minus, Plus } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef } from 'react'
import { forceCollide } from 'd3-force-3d'
import ForceGraph2D from 'react-force-graph-2d'

import { Button } from '@/components/ui/button'
import {
  endId,
  NODE_RADIUS,
  paintNode,
  paintNodeArea,
  readPalette,
  relatedIds,
  SELECTED_RADIUS,
  startView,
} from '@/lib/graph'

// Graph units are about one screen pixel at zoom 1. Columns (prerequisite depth) are LEVEL_DISTANCE
// apart; within a column, collision keeps topics far enough apart for a two-line label.
const LEVEL_DISTANCE = 100
const COLLIDE_RADIUS = 25
// Leaves room for labels, which overhang the outermost nodes.
const FIT_PADDING = 64

/**
 * The curriculum as a directed graph (canvas, via react-force-graph-2d). Laid out left to right by
 * prerequisite depth, with arrows from each prerequisite to the topic it unlocks. Drag to pan,
 * scroll or pinch to zoom, or use the buttons. Loaded on demand: the library is only needed here.
 */
export default function KnowledgeGraph({ data, selectedId, onSelect, width, height }) {
  const graphRef = useRef(null)
  const fitted = useRef(false)
  const palette = useMemo(() => readPalette(), [])
  const related = useMemo(() => relatedIds(selectedId, data.nodes), [selectedId, data])

  useEffect(() => {
    const graph = graphRef.current
    if (!graph) return
    graph.d3Force('collide', forceCollide(COLLIDE_RADIUS))
    graph.d3Force('charge')?.strength(-90)
    graph.d3ReheatSimulation()
  }, [])

  // Centre the selected topic once it has a position.
  useEffect(() => {
    const node = data.nodes.find((n) => n.id === selectedId)
    if (node && Number.isFinite(node.x)) graphRef.current?.centerAt(node.x, node.y, 500)
  }, [selectedId, data])

  const linkActive = useCallback(
    (link) => Boolean(selectedId) && (endId(link.source) === selectedId || endId(link.target) === selectedId),
    [selectedId],
  )

  // The first view, once the layout has settled: the whole graph if it is readable, else the start
  // of it; a topic opened from a link (?topic=) is centred instead.
  const showStart = () => {
    const graph = graphRef.current
    if (!graph) return
    const view = startView(graph.getGraphBbox(), width, height, FIT_PADDING)
    const selected = data.nodes.find((n) => n.id === selectedId)
    if (view.fit && !selected) return graph.zoomToFit(400, FIT_PADDING)
    graph.zoom(view.fit ? graph.zoom() : view.scale, 400)
    graph.centerAt(selected?.x ?? view.x, selected?.y ?? view.y, 400)
  }

  const zoomBy = (factor) => {
    const graph = graphRef.current
    if (graph) graph.zoom(graph.zoom() * factor, 300)
  }

  return (
    <div className="relative">
      <ForceGraph2D
        ref={graphRef}
        graphData={data}
        width={width}
        height={height}
        backgroundColor="rgba(0,0,0,0)"
        dagMode="lr"
        dagLevelDistance={LEVEL_DISTANCE}
        nodeId="id"
        nodeRelSize={NODE_RADIUS}
        nodeVal={(node) => (node.id === selectedId ? (SELECTED_RADIUS / NODE_RADIUS) ** 2 : 1)}
        nodeLabel={() => ''}
        nodeCanvasObject={(node, ctx, scale) => paintNode(node, ctx, scale, { palette, selectedId, related })}
        nodePointerAreaPaint={(node, color, ctx, scale) => paintNodeArea(node, color, ctx, selectedId, scale)}
        linkColor={(link) => (linkActive(link) ? palette.primary : palette.link)}
        linkWidth={(link) => (linkActive(link) ? 2 : 1)}
        linkDirectionalArrowLength={5}
        linkDirectionalArrowRelPos={1}
        linkDirectionalArrowColor={(link) => (linkActive(link) ? palette.primary : palette.link)}
        enableNodeDrag={false}
        cooldownTicks={120}
        onEngineStop={() => {
          if (fitted.current) return
          fitted.current = true
          showStart()
        }}
        onNodeClick={(node) => onSelect(node.id)}
        onBackgroundClick={() => onSelect(null)}
      />
      <div className="absolute top-3 right-3 flex flex-col gap-1 rounded-lg border bg-card/95 p-1 shadow-sm">
        <Button variant="ghost" size="icon-sm" aria-label="Zoom in" onClick={() => zoomBy(1.4)}>
          <Plus aria-hidden="true" />
        </Button>
        <Button variant="ghost" size="icon-sm" aria-label="Zoom out" onClick={() => zoomBy(1 / 1.4)}>
          <Minus aria-hidden="true" />
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Fit the whole graph"
          onClick={() => graphRef.current?.zoomToFit(400, FIT_PADDING)}
        >
          <Maximize2 aria-hidden="true" />
        </Button>
      </div>
    </div>
  )
}
