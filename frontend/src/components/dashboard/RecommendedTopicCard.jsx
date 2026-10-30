import { ArrowRight } from 'lucide-react'
import { ProgressBar } from '@/components/common/ProgressBar'
import { QuizLink } from '@/components/topics/QuizLink'
import { TopicStatusBadge } from '@/components/topics/TopicStatusBadge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { difficultyLabel, listNames, topicAction } from '@/lib/topics'

/**
 * A recommended next topic (PRD 9): name, description, difficulty, status, mastery,
 * prerequisite summary and the primary action. `domainNames`, when given, says which of the
 * learner's domains the topic counts towards (the home page, across domains).
 */
export function RecommendedTopicCard({ topic, retry, domainNames }) {
  const action = topicAction(topic, { retry })
  return (
    <Card className="h-full gap-4 px-5 py-5">
      <div className="flex flex-wrap items-center gap-2">
        <TopicStatusBadge status={topic.status} />
        <span className="text-xs font-medium text-muted-foreground">{difficultyLabel(topic.difficulty)}</span>
      </div>
      <div className="flex flex-col gap-1.5">
        <h3 className="text-base font-semibold text-ink">
          {topic.name}
        </h3>
        <p className="line-clamp-3 text-sm text-body">{topic.description}</p>
      </div>
      <p className="text-xs text-muted-foreground">
        {topic.prerequisite_names.length > 0
          ? `Builds on ${listNames(topic.prerequisite_names, 3)}`
          : 'No prerequisites'}
      </p>
      {domainNames?.length > 0 && (
        <p className="text-xs font-medium text-primary-dark">Counts towards {listNames(domainNames, 3)}</p>
      )}
      <div className="mt-auto flex flex-col gap-4">
        <ProgressBar value={topic.mastery} label="Mastery" />
        <Button asChild className="h-9 w-full">
          <QuizLink to={action.to} aria-label={`${action.label}: ${topic.name}`}>
            {action.label}
            <ArrowRight aria-hidden="true" />
          </QuizLink>
        </Button>
      </div>
    </Card>
  )
}
