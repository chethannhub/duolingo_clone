export const queryKeys = {
  learningPath: (sectionId?: number) => ["learning-path", sectionId] as const,
  lessonAttempt: (attemptToken: string) => ["lesson-attempt", attemptToken] as const,
  hearts: ["hearts"] as const,
  leaderboard: ["leaderboard", "weekly"] as const,
  profile: ["profile"] as const,
  achievements: ["achievements"] as const,
  activity: ["activity"] as const,
  settings: ["settings"] as const,
};
