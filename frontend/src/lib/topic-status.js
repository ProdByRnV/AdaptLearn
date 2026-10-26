// Topic statuses returned by the API, styled with the AdaptLearn.pdf status legend.
// The fills are light (amber, mint, teal-500), so they carry dark ink text; only the slate
// "locked" fill is dark enough for white text.
export const TOPIC_STATUS = {
  completed: { label: 'Completed', badgeClass: 'bg-status-completed text-ink' },
  in_progress: { label: 'In progress', badgeClass: 'bg-status-in-progress text-ink' },
  unlocked: { label: 'Unlocked', badgeClass: 'bg-status-unlocked text-ink' },
  locked: { label: 'Locked', badgeClass: 'bg-status-locked text-white' },
}

export const TOPIC_STATUS_ORDER = ['completed', 'in_progress', 'unlocked', 'locked']
