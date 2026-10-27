import { Award, CheckCircle2, ClipboardCheck, Gauge, ListChecks, Network, PartyPopper, TrendingUp } from 'lucide-react'
import { useMemo } from 'react'
import { Link, useLocation } from 'react-router'

import { getErrorMessage } from '@/api/client'
import { fetchDashboard } from '@/api/progress'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { PageHeader } from '@/components/common/PageHeader'
import { AttentionCard } from '@/components/dashboard/AttentionCard'
import { MasteryOverview } from '@/components/dashboard/MasteryOverview'
import { RecentAttempts } from '@/components/dashboard/RecentAttempts'
import { RecommendedTopicCard } from '@/components/dashboard/RecommendedTopicCard'
import { StatCard } from '@/components/dashboard/StatCard'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { useApiData } from '@/hooks/useApiData'
import { useAuth } from '@/hooks/useAuth'
import { formatPercent } from '@/lib/format'
import { domainLabel, listNames } from '@/lib/topics'

export default function Dashboard() {
  const { user } = useAuth()
  const onboarding = useLocation().state?.onboarding
  const { data, error, loading, reload } = useApiData(fetchDashboard)

  return (
    <>
      <PageHeader
        title={`Welcome back, ${user.username}`}
        description={
          data
            ? `${domainLabel(data.domain)} · ${data.stats.completed_topics} of ${data.stats.total_topics} topics completed`
            : 'Your progress at a glance.'
        }
        actions={
          <Button asChild variant="outline" className="h-9">
            <Link to="/graph">
              <Network aria-hidden="true" />
              Knowledge graph
            </Link>
          </Button>
        }
      />
      {onboarding && <OnboardingDone {...onboarding} />}
      {loading && <DashboardSkeleton />}
      {error && (
        <ErrorState
          title="Couldn't load your dashboard"
          message={getErrorMessage(error)}
          onRetry={reload}
          className="rounded-xl border bg-card"
        />
      )}
      {data && <DashboardContent data={data} />}
    </>
  )
}

function DashboardContent({ data }) {
  const { stats, recommended, needs_attention: attention, recent_attempts: attempts, mastery } = data

  // "Retry quiz" when the learner's latest counted attempt on a topic failed, or it needs attention.
  const retryIds = useMemo(() => {
    const ids = new Set(attention.map((t) => t.id))
    const seen = new Set()
    for (const attempt of attempts) {
      if (!attempt.counted || seen.has(attempt.topic_id)) continue
      seen.add(attempt.topic_id)
      if (!attempt.passed) ids.add(attempt.topic_id)
    }
    return ids
  }, [attention, attempts])

  return (
    <div className="flex flex-col gap-10">
      {!data.onboarded && <OnboardingPrompt />}

      <section aria-labelledby="stats-heading">
        <h2 id="stats-heading" className="sr-only">
          Your progress
        </h2>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
          <StatCard
            label="Overall progress"
            value={formatPercent(stats.progress_percent)}
            detail={`${stats.completed_topics} of ${stats.total_topics} topics`}
            icon={TrendingUp}
            className="col-span-2 lg:col-span-1"
          >
            <Progress value={Math.round(stats.progress_percent)} aria-label="Overall progress" className="mt-1 h-1.5" />
          </StatCard>
          <StatCard
            label="Completed"
            value={stats.completed_topics}
            detail={`${stats.in_progress_topics} in progress`}
            icon={CheckCircle2}
          />
          <StatCard label="Mastered" value={stats.mastered_topics} detail="95% mastery or more" icon={Award} />
          <StatCard
            label="Average mastery"
            value={formatPercent(stats.average_mastery)}
            detail="Across your topics"
            icon={Gauge}
          />
          <StatCard
            label="Quiz attempts"
            value={stats.total_attempts}
            detail={
              stats.flagged_attempts > 0
                ? `${stats.flagged_attempts} flagged, didn't count`
                : 'All proctored'
            }
            icon={ClipboardCheck}
          />
        </div>
      </section>

      <section aria-labelledby="next-heading">
        <SectionHeading id="next-heading" title="Up next" hint="The easiest topics you can start now" />
        {data.curriculum_complete ? (
          <CurriculumComplete domain={data.domain} />
        ) : recommended.length === 0 ? (
          <EmptyState
            title="Nothing to start right now"
            description="Finish the topics you're working on to unlock the next ones."
          />
        ) : (
          <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {recommended.map((topic) => (
              <li key={topic.id}>
                <RecommendedTopicCard topic={topic} retry={retryIds.has(topic.id)} />
              </li>
            ))}
          </ul>
        )}
      </section>

      {attention.length > 0 && (
        <section aria-labelledby="attention-heading">
          <SectionHeading
            id="attention-heading"
            title="Needs attention"
            hint="Several attempts without much progress. Review the resources first."
          />
          <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {attention.map((topic) => (
              <li key={topic.id}>
                <AttentionCard topic={topic} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="grid gap-10 lg:grid-cols-2 lg:gap-6">
        <section aria-labelledby="recent-heading">
          <SectionHeading id="recent-heading" title="Recent quizzes" />
          <RecentAttempts attempts={attempts} />
        </section>
        <section aria-labelledby="mastery-heading">
          <SectionHeading id="mastery-heading" title="Mastery" />
          <MasteryOverview items={mastery} />
        </section>
      </div>
    </div>
  )
}

function SectionHeading({ id, title, hint }) {
  return (
    <div className="mb-3 flex flex-col gap-0.5">
      <h2 id={id} className="text-lg font-semibold text-ink">
        {title}
      </h2>
      {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
    </div>
  )
}

function OnboardingPrompt() {
  return (
    <Card className="flex-col gap-4 border border-primary/30 bg-accent/40 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 className="text-base font-semibold text-ink">Already know some of this?</h2>
        <p className="text-sm text-body">Tell us which topics you're comfortable with and we'll skip them.</p>
      </div>
      <Button asChild className="h-9 shrink-0">
        <Link to="/onboarding">
          <ListChecks aria-hidden="true" />
          Choose known topics
        </Link>
      </Button>
    </Card>
  )
}

function CurriculumComplete({ domain }) {
  return (
    <Card className="items-center gap-3 border border-primary/30 bg-accent/40 px-6 py-10 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-primary text-primary-foreground">
        <PartyPopper aria-hidden="true" className="size-6" />
      </div>
      <h3 className="text-lg font-semibold text-ink">You've completed the {domainLabel(domain)} curriculum</h3>
      <p className="max-w-md text-sm text-body">
        Every topic is done. Keep your mastery up by practising any topic from the knowledge graph.
      </p>
      <Button asChild variant="outline" className="mt-1 h-9">
        <Link to="/graph">Open the knowledge graph</Link>
      </Button>
    </Card>
  )
}

/** Confirmation after onboarding (US-04: the learner is sent to the dashboard). */
function OnboardingDone({ knownCount, addedPrerequisites = [] }) {
  return (
    <Alert role="status" className="mb-6 border-primary/30 bg-accent/40">
      <CheckCircle2 aria-hidden="true" className="text-primary" />
      <AlertTitle className="text-ink">You're all set</AlertTitle>
      <AlertDescription className="text-body">
        {knownCount === 0
          ? "You're starting from the beginning. Your first topics are ready."
          : `${knownCount} ${knownCount === 1 ? 'topic is' : 'topics are'} marked as known, so your path starts after them.`}
        {addedPrerequisites.length > 0 &&
          ` Their prerequisites were included too (${listNames(addedPrerequisites, 3)}).`}
      </AlertDescription>
    </Alert>
  )
}

function DashboardSkeleton() {
  return (
    <div role="status" aria-label="Loading your dashboard" className="flex flex-col gap-10">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        {Array.from({ length: 5 }, (_, i) => (
          <Skeleton key={i} className={i === 0 ? 'col-span-2 h-28 rounded-xl lg:col-span-1' : 'h-28 rounded-xl'} />
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }, (_, i) => (
          <Skeleton key={i} className="h-64 rounded-xl" />
        ))}
      </div>
    </div>
  )
}
