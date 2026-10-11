export type Submission = {
  rank: number; team: string; project: string; score: number; status: 'Verified' | 'Review'; risk: number; initials: string; tone: string
}

export const leaderboard: Submission[] = []

export const submissions: { project: string; team: string; submitted: string; status: string; score: string; progress: number; risk: string }[] = []

export const evaluation: { label: string; value: number; weight: number; color: string }[] = []
