"use client";

import { getLessonAttempt } from "@/lib/api/lessons";
import { useApiResource } from "./use-api-resource";

export function useLessonAttempt(attemptToken: string) {
  return useApiResource(() => getLessonAttempt(attemptToken), [attemptToken]);
}
