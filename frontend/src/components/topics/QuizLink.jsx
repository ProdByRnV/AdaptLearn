import { Link, useLocation } from 'react-router'

import { quizLinkState } from '@/lib/domains'

/** A link to a quiz that remembers the page it was opened from (see quizLinkState). */
export function QuizLink(props) {
  const location = useLocation()
  return <Link state={quizLinkState(location)} {...props} />
}
