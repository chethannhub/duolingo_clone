"use client";

import { useState } from "react";

import { createIdempotencyKey } from "@/lib/api/client";
import { LessonAnswer, submitAnswer } from "@/lib/api/lessons";

export function useSubmitAnswer(attemptToken: string) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  async function submit(payload: {
    exercise_id: number;
    response_time_ms?: number;
    answer: LessonAnswer;
  }) {
    if (submitting) {
      return null;
    }
    setSubmitting(true);
    setError(null);
    try {
      return await submitAnswer(attemptToken, createIdempotencyKey(), {
        ...payload,
        client_submission_id: createIdempotencyKey(),
      });
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setSubmitting(false);
    }
  }

  return { submit, submitting, error };
}
