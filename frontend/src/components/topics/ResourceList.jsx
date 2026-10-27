import { BookOpen, ExternalLink, FileText, PlayCircle } from 'lucide-react'

const TYPE = {
  docs: { icon: BookOpen, label: 'Docs' },
  article: { icon: FileText, label: 'Article' },
  video: { icon: PlayCircle, label: 'Video' },
}

/** Learning resources for a topic (PRD 14: shown for failed quizzes, attention topics, topic details). */
export function ResourceList({ resources }) {
  if (!resources?.length) return null
  return (
    <ul className="flex flex-col gap-1.5">
      {resources.map((resource) => {
        const { icon: Icon, label } = TYPE[resource.type] ?? TYPE.article
        return (
          <li key={resource.url}>
            <a
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`${resource.title} (${label}, opens in a new tab)`}
              className="group inline-flex items-start gap-2 rounded-md text-sm text-primary underline-offset-4 hover:underline focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
            >
              <Icon aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
              <span>{resource.title}</span>
              <ExternalLink aria-hidden="true" className="mt-0.5 size-3.5 shrink-0 opacity-60" />
            </a>
          </li>
        )
      })}
    </ul>
  )
}
