import { ArrowRight, Lock, Sparkles, X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { Link } from 'react-router'

import { ProgressBar } from '@/components/common/ProgressBar'
import { ResourceList } from '@/components/topics/ResourceList'
import { StatusDot } from '@/components/topics/StatusDot'
import { TopicStatusBadge } from '@/components/topics/TopicStatusBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { missingPrerequisites, unlocksOf } from '@/lib/graph'
import { TOPIC_STATUS } from '@/lib/topic-status'
import { difficultyLabel, listNames, topicAction } from '@/lib/topics'

/**
 * Details of the selected topic: status, difficulty, description, mastery, a lock-aware action
 * (a quiz link, or what to complete first), prerequisites and what it unlocks (both clickable),
 * and learning resources. The heading takes focus when the topic changes.
 */
export function TopicPanel({ topic, topics, topicsById, onSelect, onClose }) {
  const headingRef = useRef(null)
  const prerequisites = topic.prerequisites.map((id) => topicsById.get(id)).filter(Boolean)
  const unlocks = unlocksOf(topic.id, topics)
  const missing = missingPrerequisites(topic, topicsById)
  const action = topicAction(topic)

  useEffect(() => {
    headingRef.current?.focus({ preventScroll: true })
  }, [topic.id])

  return (
    <aside aria-labelledby="topic-panel-heading">
      <Card className="gap-5 px-5 py-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <TopicStatusBadge status={topic.status} />
              <span className="text-xs font-medium text-muted-foreground">{difficultyLabel(topic.difficulty)}</span>
              {topic.mastered && (
                <Badge className="bg-primary-dark text-white">
                  <Sparkles aria-hidden="true" />
                  Mastered
                </Badge>
              )}
            </div>
            <h2 id="topic-panel-heading" ref={headingRef} tabIndex={-1} className="text-lg font-semibold text-ink outline-none">
              {topic.name}
            </h2>
          </div>
          <Button variant="ghost" size="icon-sm" aria-label="Close topic details" onClick={onClose} className="-mt-1 -mr-2">
            <X aria-hidden="true" />
          </Button>
        </div>

        <p className="text-sm text-body">{topic.description}</p>
        <ProgressBar value={topic.mastery} label="Mastery" />

        {topic.status === 'locked' ? (
          <div className="flex gap-3 rounded-lg border border-dashed border-input bg-muted/50 px-3 py-3 text-sm">
            <Lock aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-status-locked" />
            <div className="flex flex-col gap-1">
              <p className="font-medium text-ink">Locked</p>
              <p className="text-body">
                Complete {missing.length > 0 ? listNames(missing.map((t) => t.name), 4) : 'its prerequisites'} to unlock it.
              </p>
            </div>
          </div>
        ) : (
          <Button asChild className="h-10 w-full">
            <Link to={action.to} aria-label={`${action.label}: ${topic.name}`}>
              {action.label}
              <ArrowRight aria-hidden="true" />
            </Link>
          </Button>
        )}

        <TopicLinks
          title="Prerequisites"
          empty="None. This is a starting topic."
          topics={prerequisites}
          onSelect={onSelect}
        />
        <TopicLinks title="Unlocks" empty="Nothing. This is a final topic." topics={unlocks} onSelect={onSelect} />

        {topic.resources?.length > 0 && (
          <section aria-labelledby="topic-resources-heading" className="flex flex-col gap-2">
            <h3 id="topic-resources-heading" className="text-sm font-semibold text-ink">
              Resources
            </h3>
            <ResourceList resources={topic.resources} />
          </section>
        )}
      </Card>
    </aside>
  )
}

function TopicLinks({ title, empty, topics, onSelect }) {
  const id = `topic-${title.toLowerCase()}-heading`
  return (
    <section aria-labelledby={id} className="flex flex-col gap-2">
      <h3 id={id} className="text-sm font-semibold text-ink">
        {title}
      </h3>
      {topics.length === 0 ? (
        <p className="text-sm text-muted-foreground">{empty}</p>
      ) : (
        <ul className="flex flex-col gap-1">
          {topics.map((topic) => (
            <li key={topic.id}>
              <button
                type="button"
                onClick={() => onSelect(topic.id)}
                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm text-ink hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
              >
                <StatusDot status={topic.status} />
                <span className="flex-1">{topic.name}</span>
                <span className="text-xs text-muted-foreground">{TOPIC_STATUS[topic.status]?.label}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
