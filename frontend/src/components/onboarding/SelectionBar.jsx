import { FormAlert } from '@/components/forms/FormAlert'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'

/** Sticky footer with the live selection count and the submit action. */
export function SelectionBar({ chosen, implied, submitLabel, submitting, error, onClear, onSubmit }) {
  const total = chosen + implied
  return (
    <div className="sticky bottom-0 z-30 -mx-4 mt-8 border-t bg-card/95 px-4 py-3 backdrop-blur supports-[backdrop-filter]:bg-card/85">
      <div className="mx-auto flex max-w-6xl flex-col gap-3">
        <FormAlert message={error} />
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p aria-live="polite" className="text-sm text-body">
            {total === 0 ? (
              'No topics selected'
            ) : (
              <>
                <span className="font-semibold text-ink">
                  {total} {total === 1 ? 'topic' : 'topics'} selected
                </span>
                {implied > 0 && ` (${implied} included as ${implied === 1 ? 'a prerequisite' : 'prerequisites'})`}
              </>
            )}
          </p>
          <div className="flex gap-2">
            {chosen > 0 && (
              <Button type="button" variant="ghost" size="lg" className="h-10" onClick={onClear} disabled={submitting}>
                Clear
              </Button>
            )}
            <Button type="button" size="lg" className="h-10 flex-1 sm:flex-none" onClick={onSubmit} disabled={submitting}>
              {submitting && <Loader2 aria-hidden="true" className="animate-spin" />}
              {submitting ? 'Saving…' : submitLabel}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
