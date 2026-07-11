import { apiRequest } from "./client";

export type AttemptMode = "standard" | "practice" | "review" | "legendary";

export type LessonAnswer =
  | { type: "multiple_choice"; selected_option_id: number }
  | { type: "translate_word_bank"; selected_option_ids: number[] }
  | { type: "match_pairs"; matches: Array<{ left_id: string; right_id: string }> }
  | { type: "fill_blank"; text: string }
  | { type: "type_answer"; text: string };

export function getLevelLessons(levelId: number) {
  return apiRequest<{ lessons: Array<Record<string, unknown>> }>(`/levels/${levelId}/lessons`);
}

export function getLessonPreview(lessonId: number) {
  return apiRequest<Record<string, unknown>>(`/lessons/${lessonId}/preview`);
}

export function startLessonAttempt(lessonId: number, idempotencyKey: string, mode: AttemptMode = "standard") {
  return apiRequest<Record<string, unknown>>(`/lessons/${lessonId}/attempts`, {
    method: "POST",
    idempotencyKey,
    body: { mode },
  });
}

export function getLessonAttempt(attemptToken: string) {
  return apiRequest<Record<string, unknown>>(`/lesson-attempts/${attemptToken}`);
}

export function submitAnswer(
  attemptToken: string,
  idempotencyKey: string,
  payload: {
    exercise_id: number;
    client_submission_id: string;
    response_time_ms?: number;
    answer: LessonAnswer;
  },
) {
  return apiRequest<Record<string, unknown>>(`/lesson-attempts/${attemptToken}/answers`, {
    method: "POST",
    idempotencyKey,
    body: payload,
  });
}

export function abandonAttempt(attemptToken: string) {
  return apiRequest<Record<string, unknown>>(`/lesson-attempts/${attemptToken}/abandon`, {
    method: "POST",
  });
}
