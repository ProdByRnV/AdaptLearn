import { CircleSlash, Hourglass, SearchX } from 'lucide-react'
import { Link } from 'react-router'

import { EmptyState } from '@/components/common/EmptyState'
import { Button } from '@/components/ui/button'
import { useBackLink } from '@/hooks/useBackLink'

const ENDINGS = {
  expired: {
    icon: Hourglass,
    title: 'This quiz has expired',
    description: "Quizzes must be finished within 30 minutes of being created. It wasn't scored and doesn't count.",
  },
  submitted: {
    icon: CircleSlash,
    title: 'This quiz was already submitted',
    description: "It may have been finished in another tab. Your result is on the domain's dashboard.",
  },
  missing: {
    icon: SearchX,
    title: "We couldn't find this quiz",
    description: 'It may have been replaced by a newer quiz. Start a new one to continue.',
  },
}

/** The quiz can't continue: it expired, was submitted elsewhere, or no longer exists. */
export function QuizEnded({ reason, onRestart }) {
  const { icon, title, description } = ENDINGS[reason] ?? ENDINGS.missing
  const back = useBackLink()
  return (
    <EmptyState
      icon={icon}
      title={title}
      description={description}
      action={
        <div className="flex flex-wrap justify-center gap-2">
          <Button onClick={onRestart}>Start a new quiz</Button>
          <Button asChild variant="outline">
            <Link to={back.to}>{back.label}</Link>
          </Button>
        </div>
      }
    />
  )
}
