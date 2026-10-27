import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'

/**
 * Confirms leaving a running quiz (browser back button, or a link) through the router's blocker.
 * Cancel and Esc close the dialog, which resets the blocker; Leave lets the navigation through.
 */
export function LeaveQuizDialog({ blocker }) {
  const open = blocker.state === 'blocked'
  return (
    <AlertDialog open={open} onOpenChange={(next) => !next && open && blocker.reset()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-ink">Leave the quiz?</AlertDialogTitle>
          <AlertDialogDescription className="text-body">
            Your locked-in answers are saved and you can resume later, but the current question's timer keeps
            running and time away from the quiz lowers your integrity score.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Stay in the quiz</AlertDialogCancel>
          <Button variant="destructive" onClick={() => blocker.proceed()}>
            Leave
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
