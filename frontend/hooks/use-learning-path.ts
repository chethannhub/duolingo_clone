"use client";

import { getLearningPath } from "@/lib/api/learning-path";
import { useApiResource } from "./use-api-resource";

export function useLearningPath(sectionId?: number) {
  return useApiResource(() => getLearningPath(sectionId), [sectionId]);
}
