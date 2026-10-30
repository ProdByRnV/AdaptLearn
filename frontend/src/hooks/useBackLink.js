import { useLocation } from 'react-router'

import { backLink } from '@/lib/domains'

/** The quiz page's way back ({to, label}): to the page the quiz was opened from, otherwise home. */
export function useBackLink() {
  return backLink(useLocation().state?.from)
}
