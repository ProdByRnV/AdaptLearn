import { Maximize2, Minus, Plus } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef } from 'react'
import { forceCollide } from 'd3-force-3d'
import ForceGraph2D from 'react-force-graph-2d'

import { Button } from '@/components/ui/button'
import {
  endId,
  mapLayout,
  NODE_RADIUS,
  paintGroups,
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
 *
 * With `groups` (the whole map's domains), each domain gets a tile laid out like its own graph, the
 * tiles are packed into rows to suit the view's shape, and every topic is fixed in place, so there
 * is no simulation to wait for.
 */
export default function KnowledgeGraph({ data, groups = null, selectedId, onSelect, width, height }) {
  const graphRef = useRef(null)
  const fitted = useRef(false)
  const palette = useMemo(() => readPalette(), [])
  const related = useMemo(() => relatedIds(selectedId, data.nodes), [selectedId, data])
  const aspect = (width - 2 * FIT_PADDING) / Math.max(1, height - 2 * FIT_PADDING)
  const layout = useMemo(() => (groups ? mapLayout(data.nodes, groups, aspect) : null), [groups, data, aspect])
  // Pulled into place by forces instead, links between distant domains would drag topics out of
  // their tile.
  const graphData = useMemo(() => {
    if (!layout) return data
    return {
      ...data,
      nodes: data.nodes.map((node) => {
        const { x, y } = layout.positions.get(node.id) ?? { x: 0, y: 0 }
        return { ...node, x, y, fx: x, fy: y }
      }),
    }
  }, [layout, data])

  useEffect(() => {
    const graph = graphRef.current
    if (!graph) return
    graph.d3Force('collide', layout ? null : forceCollide(COLLIDE_RADIUS))
    graph.d3Force('charge')?.strength(layout ? 0 : -90)
    graph.d3ReheatSimulation()
  }, [graphData, layout])

  // The map's tiles are rearranged when the view changes shape: show the whole of it again.
  useEffect(() => {
    if (layout && fitted.current) graphRef.current?.zoomToFit(400, FIT_PADDING)
  }, [layout])

  // Centre the selected topic once it has a position (the layout writes positions into graphData).
  useEffect(() => {
    const node = graphData.nodes.find((n) => n.id === selectedId)
    if (node && Number.isFinite(node.x)) graphRef.current?.centerAt(node.x, node.y, 500)
  }, [selectedId, graphData])

  const linkActive = useCallback(
    (link) => Boolean(selectedId) && (endId(link.source) === selectedId || endId(link.target) === selectedId),
    [selectedId],
  )
  // On the whole map, links between domains are faint unless they touch the selection: Foundations'
  // topics alone lead into most other domains.
  const homes = useMemo(() => new Map(data.nodes.map((node) => [node.id, node.home_domain])), [data])
  const linkColour = (link) => {
    if (linkActive(link)) return palette.primary
    const across = layout && homes.get(endId(link.source)) !== homes.get(endId(link.target))
    return across ? palette.linkFaint : palette.link
  }

  // The first view, once the layout has settled: the whole graph if it is readable, else the start
  // of it; a topic opened from a link (?topic=) is centred instead. The whole map always starts
  // fitted: zoomed out, it reads as its domains.
  const showStart = () => {
    const graph = graphRef.current
    if (!graph) return
    const view = startView(graph.getGraphBbox(), width, height, FIT_PADDING)
    const selected = graphData.nodes.find((n) => n.id === selectedId)
    if ((view.fit || groups) && !selected) return graph.zoomToFit(400, FIT_PADDING)
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
        graphData={graphData}
        width={width}
        height={height}
        backgroundColor="rgba(0,0,0,0)"
        dagMode={layout ? undefined : 'lr'}
        dagLevelDistance={LEVEL_DISTANCE}
        nodeId="id"
        nodeRelSize={NODE_RADIUS}
        nodeVal={(node) => (node.id === selectedId ? (SELECTED_RADIUS / NODE_RADIUS) ** 2 : 1)}
        nodeLabel={() => ''}
        onRenderFramePre={layout ? (ctx, scale) => paintGroups(ctx, scale, layout.tiles, palette) : undefined}
        nodeCanvasObject={(node, ctx, scale) => paintNode(node, ctx, scale, { palette, selectedId, related })}
        nodePointerAreaPaint={(node, color, ctx, scale) => paintNodeArea(node, color, ctx, selectedId, scale)}
        linkColor={linkColour}
        linkWidth={(link) => (linkActive(link) ? 2 : 1)}
        linkDirectionalArrowLength={5}
        linkDirectionalArrowRelPos={1}
        linkDirectionalArrowColor={linkColour}
        enableNodeDrag={false}
        cooldownTicks={layout ? 1 : 120}
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
