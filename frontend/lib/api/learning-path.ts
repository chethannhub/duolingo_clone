import { apiRequest } from "./client";

export type LearningPathResponse = {
  learner: Record<string, unknown>;
  activeCourse: Record<string, unknown>;
  topBar: Record<string, unknown>;
  dailyGoal: Record<string, unknown>;
  sections: Array<Record<string, unknown>>;
};

export function getLearningPath(sectionId?: number) {
  const query = sectionId ? `?section_id=${sectionId}` : "";
  return apiRequest<LearningPathResponse>(`/me/learning-path${query}`);
}
