"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { FaArrowRight, FaCheck, FaGem, FaHeart, FaXmark } from "react-icons/fa6";

import { createIdempotencyKey } from "@/lib/api/client";
import { getLessonPreview, startLessonAttempt, submitAnswer, type LessonAnswer } from "@/lib/api/lessons";
import { getLearningPath } from "@/lib/api/learning-path";

type Learner = {
  hearts?: number;
  maxHearts?: number;
  gems?: number;
  streak?: number;
  totalXp?: number;
};

type ExerciseOption = {
  id: number | string;
  text: string;
  side?: "left" | "right";
};

type Exercise = {
  id: number;
  type: "multiple_choice" | "translate_word_bank" | "match_pairs" | "fill_blank" | "type_answer";
  instruction?: string;
  prompt?: string;
  hint?: string | null;
  orderIndex?: number;
  options: ExerciseOption[];
};

type AttemptResponse = {
  attemptToken: string;
  status: string;
  lessonId: number;
  currentExerciseIndex: number;
  totalExercises: number;
  correctCount: number;
  wrongCount: number;
  learner: Learner;
  currentExercise: Exercise | null;
};

type SubmitResponse = AttemptResponse & {
  result?: "correct" | "incorrect";
  feedbackTitle?: string;
  feedbackMessage?: string | null;
  correctAnswer?: string | null;
  heartLost?: boolean;
  currentHearts?: number;
  completion?: {
    xpEarned: number;
    levelCompleted: boolean;
    unlockedAchievements: Array<{ key: string; name: string }>;
  } | null;
};

type LessonPreview = {
  id: number;
  title: string;
  xpReward: number;
  estimatedMinutes: number;
  exerciseCount: number;
};

type MatchSelection = {
  left?: string;
  right?: string;
};

export function LessonPlayer() {
  const [lesson, setLesson] = useState<LessonPreview | null>(null);
  const [attempt, setAttempt] = useState<AttemptResponse | null>(null);
  const [selectedOptionId, setSelectedOptionId] = useState<number | null>(null);
  const [selectedWordIds, setSelectedWordIds] = useState<number[]>([]);
  const [textAnswer, setTextAnswer] = useState("");
  const [matchSelection, setMatchSelection] = useState<MatchSelection>({});
  const [matches, setMatches] = useState<Array<{ left_id: string; right_id: string }>>([]);
  const [feedback, setFeedback] = useState<SubmitResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const hasLoaded = useRef(false);

  const exercise = attempt?.currentExercise ?? null;
  const learner = attempt?.learner;
  const progress = attempt ? (attempt.currentExerciseIndex / attempt.totalExercises) * 100 : 0;

  const canCheck = useMemo(() => {
    if (!exercise || feedback) return false;
    if (exercise.type === "multiple_choice") return selectedOptionId !== null;
    if (exercise.type === "translate_word_bank") return selectedWordIds.length > 0;
    if (exercise.type === "match_pairs") {
      const pairCount = exercise.options.filter((option) => option.side === "left").length;
      return pairCount > 0 && matches.length >= pairCount;
    }
    return textAnswer.trim().length > 0;
  }, [exercise, feedback, matches.length, selectedOptionId, selectedWordIds.length, textAnswer]);

  useEffect(() => {
    if (hasLoaded.current) return;
    hasLoaded.current = true;
    void loadLesson();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadLesson() {
    setIsLoading(true);
    setError("");
    resetExerciseState();
    try {
      const lessonId = await getRequestedLessonId();
      const [preview, started] = await Promise.all([
        getLessonPreview(lessonId) as Promise<LessonPreview>,
        startLessonAttempt(lessonId, createIdempotencyKey()) as Promise<AttemptResponse>,
      ]);
      setLesson(preview);
      setAttempt(started);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load lesson");
    } finally {
      setIsLoading(false);
    }
  }

  async function getRequestedLessonId(): Promise<number> {
    const params = new URLSearchParams(window.location.search);
    const explicitLessonId = Number(params.get("lessonId"));
    if (Number.isInteger(explicitLessonId) && explicitLessonId > 0) {
      return explicitLessonId;
    }

    const path = await getLearningPath();
    for (const section of path.sections as Array<Record<string, unknown>>) {
      for (const unit of (section.units ?? []) as Array<Record<string, unknown>>) {
        for (const item of (unit.pathItems ?? []) as Array<Record<string, unknown>>) {
          if (item.type !== "level" || item.state === "locked") continue;
          const level = item.level as { lessons?: Array<{ id: number; completed?: boolean }> };
          const lesson = level.lessons?.find((entry) => !entry.completed) ?? level.lessons?.[0];
          if (lesson) return lesson.id;
        }
      }
    }
    throw new Error("No available lesson was found.");
  }

  function resetExerciseState() {
    setSelectedOptionId(null);
    setSelectedWordIds([]);
    setTextAnswer("");
    setMatchSelection({});
    setMatches([]);
    setFeedback(null);
  }

  function buildAnswer(): LessonAnswer | null {
    if (!exercise) return null;
    if (exercise.type === "multiple_choice" && selectedOptionId !== null) {
      return { type: "multiple_choice", selected_option_id: selectedOptionId };
    }
    if (exercise.type === "translate_word_bank") {
      return { type: "translate_word_bank", selected_option_ids: selectedWordIds };
    }
    if (exercise.type === "match_pairs") {
      return { type: "match_pairs", matches };
    }
    if (exercise.type === "fill_blank") {
      return { type: "fill_blank", text: textAnswer };
    }
    if (exercise.type === "type_answer") {
      return { type: "type_answer", text: textAnswer };
    }
    return null;
  }

  async function checkAnswer() {
    if (!attempt || !exercise || !canCheck) return;
    const answer = buildAnswer();
    if (!answer) return;

    setIsSubmitting(true);
    setError("");
    try {
      const response = (await submitAnswer(attempt.attemptToken, createIdempotencyKey(), {
        exercise_id: exercise.id,
        client_submission_id: createIdempotencyKey(),
        answer,
      })) as SubmitResponse;
      setFeedback(response);
      setAttempt((current) => (current ? { ...current, learner: response.learner } : response));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not check answer");
    } finally {
      setIsSubmitting(false);
    }
  }

  function continueLesson() {
    if (!feedback) return;
    setAttempt(feedback);
    resetExerciseState();
  }

  if (isLoading) {
    return (
      <main className="grid min-h-dvh place-items-center bg-white px-5">
        <div className="text-center">
          <div className="mx-auto mb-5 h-16 w-16 animate-spin rounded-full border-8 border-slate-100 border-t-lime-500" />
          <p className="text-xl font-black text-slate-700">Loading lesson...</p>
        </div>
      </main>
    );
  }

  if (error && !attempt) {
    return <LessonError message={error} onRetry={loadLesson} />;
  }

  if (feedback?.completion && !feedback.currentExercise) {
    return <CompletionScreen feedback={feedback} />;
  }

  if (!attempt || !exercise) {
    return <LessonError message="No lesson is available." onRetry={loadLesson} />;
  }

  return (
    <main className="flex min-h-dvh flex-col bg-white text-slate-700">
      <header className="mx-auto flex w-full max-w-7xl items-center gap-6 px-5 py-7">
        <Link
          href="/learn"
          aria-label="Close lesson"
          className="grid h-12 w-12 shrink-0 place-items-center rounded-full text-slate-400 transition hover:bg-slate-50 hover:text-slate-700"
        >
          <FaXmark aria-hidden className="text-3xl" />
        </Link>
        <div className="h-5 flex-1 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-lime-500" style={{ width: `${progress}%` }} />
        </div>
        <div className="flex items-center gap-3 text-xl font-black text-rose-500">
          <FaHeart aria-hidden />
          {learner?.hearts ?? 0}
        </div>
        <div className="hidden items-center gap-3 text-xl font-black text-sky-500 sm:flex">
          <FaGem aria-hidden />
          {learner?.gems ?? 0}
        </div>
      </header>

      <section className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-5 pb-8 pt-4">
        <p className="text-sm font-black uppercase text-slate-400">
          {lesson?.title ?? "Spanish lesson"} - exercise {Math.min(attempt.currentExerciseIndex + 1, attempt.totalExercises)} of {attempt.totalExercises}
        </p>
        <h1 className="mt-6 text-3xl font-black text-slate-800 md:text-4xl">
          {exercise.instruction || "Answer the prompt"}
        </h1>
        <p className="mt-4 text-2xl font-black text-slate-700">{exercise.prompt}</p>

        <div className="mt-12">
          <ExerciseView
            exercise={exercise}
            selectedOptionId={selectedOptionId}
            setSelectedOptionId={setSelectedOptionId}
            selectedWordIds={selectedWordIds}
            setSelectedWordIds={setSelectedWordIds}
            textAnswer={textAnswer}
            setTextAnswer={setTextAnswer}
            matchSelection={matchSelection}
            setMatchSelection={setMatchSelection}
            matches={matches}
            setMatches={setMatches}
            disabled={Boolean(feedback)}
          />
        </div>

        {error && (
          <p className="mt-8 rounded-xl bg-rose-50 px-4 py-3 font-bold text-rose-600">{error}</p>
        )}
      </section>

      <footer
        className={[
          "border-t-2 px-5 py-5",
          feedback?.result === "correct"
            ? "border-lime-200 bg-lime-50"
            : feedback
              ? "border-rose-200 bg-rose-50"
              : "border-slate-100 bg-white",
        ].join(" ")}
      >
        <div className="mx-auto flex max-w-5xl flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          {feedback ? (
            <div>
              <p
                className={[
                  "text-2xl font-black",
                  feedback.result === "correct" ? "text-lime-600" : "text-rose-600",
                ].join(" ")}
              >
                {feedback.feedbackTitle ?? (feedback.result === "correct" ? "Correct!" : "Not quite")}
              </p>
              {feedback.feedbackMessage && (
                <p className="mt-1 font-bold text-slate-500">{feedback.feedbackMessage}</p>
              )}
              {feedback.correctAnswer && feedback.result !== "correct" && (
                <p className="mt-1 font-bold text-slate-500">Correct answer: {feedback.correctAnswer}</p>
              )}
            </div>
          ) : (
            <div>
              <p className="text-2xl font-black text-slate-800">Ready?</p>
              <p className="font-bold text-slate-500">Check your answer to keep moving.</p>
            </div>
          )}

          <button
            onClick={feedback ? continueLesson : checkAnswer}
            disabled={isSubmitting || (!feedback && !canCheck)}
            className="inline-flex h-14 items-center justify-center gap-3 rounded-2xl bg-lime-500 px-8 text-sm font-black uppercase text-white shadow-[0_5px_0_#45a900] transition hover:-translate-y-0.5 disabled:bg-slate-200 disabled:text-slate-400 disabled:shadow-[0_5px_0_#cbd5e1]"
          >
            {feedback ? "Continue" : "Check"}
            {feedback && <FaArrowRight aria-hidden />}
          </button>
        </div>
      </footer>
    </main>
  );
}

function ExerciseView({
  exercise,
  selectedOptionId,
  setSelectedOptionId,
  selectedWordIds,
  setSelectedWordIds,
  textAnswer,
  setTextAnswer,
  matchSelection,
  setMatchSelection,
  matches,
  setMatches,
  disabled,
}: {
  exercise: Exercise;
  selectedOptionId: number | null;
  setSelectedOptionId: (id: number | null) => void;
  selectedWordIds: number[];
  setSelectedWordIds: (ids: number[]) => void;
  textAnswer: string;
  setTextAnswer: (answer: string) => void;
  matchSelection: MatchSelection;
  setMatchSelection: (selection: MatchSelection) => void;
  matches: Array<{ left_id: string; right_id: string }>;
  setMatches: (matches: Array<{ left_id: string; right_id: string }>) => void;
  disabled: boolean;
}) {
  if (exercise.type === "fill_blank" || exercise.type === "type_answer") {
    return (
      <input
        value={textAnswer}
        onChange={(event) => setTextAnswer(event.target.value)}
        disabled={disabled}
        className="h-16 w-full rounded-2xl border-2 border-slate-200 px-5 text-xl font-bold outline-none focus:border-sky-300"
        placeholder="Type your answer"
      />
    );
  }

  if (exercise.type === "translate_word_bank") {
    return (
      <div>
        <div className="mb-8 min-h-20 rounded-2xl border-2 border-dashed border-slate-200 p-4 text-xl font-black text-slate-700">
          {selectedWordIds.length
            ? selectedWordIds
                .map((id) => exercise.options.find((option) => option.id === id)?.text)
                .filter(Boolean)
                .join(" ")
            : "Tap words to build the sentence"}
        </div>
        <div className="flex flex-wrap justify-center gap-3">
          {exercise.options.map((option) => {
            const id = Number(option.id);
            const selected = selectedWordIds.includes(id);
            return (
              <button
                key={option.id}
                onClick={() =>
                  setSelectedWordIds(
                    selected ? selectedWordIds.filter((item) => item !== id) : [...selectedWordIds, id],
                  )
                }
                disabled={disabled}
                className={[
                  "rounded-2xl border-2 px-6 py-4 text-xl font-black shadow-[0_4px_0_#e2e8f0] transition hover:-translate-y-0.5",
                  selected ? "border-sky-300 bg-sky-50 text-sky-600" : "border-slate-200 bg-white text-slate-700",
                ].join(" ")}
              >
                {option.text}
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  if (exercise.type === "match_pairs") {
    const left = exercise.options.filter((option) => option.side === "left");
    const right = exercise.options.filter((option) => option.side === "right");

    function choose(option: ExerciseOption) {
      if (!option.side) return;
      const next = { ...matchSelection, [option.side]: String(option.id) };
      if (next.left && next.right) {
        const pair = { left_id: next.left, right_id: next.right };
        setMatches([...matches.filter((item) => item.left_id !== pair.left_id), pair]);
        setMatchSelection({});
      } else {
        setMatchSelection(next);
      }
    }

    return (
      <div className="grid gap-4 sm:grid-cols-2">
        {[left, right].map((column, index) => (
          <div key={index} className="grid gap-3">
            {column.map((option) => {
              const id = String(option.id);
              const selected = matchSelection[option.side!] === id;
              const matched = matches.some((match) => match.left_id === id || match.right_id === id);
              return (
                <button
                  key={option.id}
                  onClick={() => choose(option)}
                  disabled={disabled || matched}
                  className={[
                    "h-16 rounded-2xl border-2 px-5 text-xl font-black shadow-[0_4px_0_#e2e8f0] transition hover:-translate-y-0.5",
                    selected
                      ? "border-sky-300 bg-sky-50 text-sky-600"
                      : matched
                        ? "border-lime-200 bg-lime-50 text-lime-600"
                        : "border-slate-200 bg-white text-slate-700",
                  ].join(" ")}
                >
                  {option.text}
                </button>
              );
            })}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {exercise.options.map((option) => {
        const id = Number(option.id);
        return (
          <button
            key={option.id}
            onClick={() => setSelectedOptionId(id)}
            disabled={disabled}
            className={[
              "min-h-16 rounded-2xl border-2 px-5 py-4 text-xl font-black shadow-[0_4px_0_#e2e8f0] transition hover:-translate-y-0.5",
              selectedOptionId === id
                ? "border-sky-300 bg-sky-50 text-sky-600"
                : "border-slate-200 bg-white text-slate-700",
            ].join(" ")}
          >
            {option.text}
          </button>
        );
      })}
    </div>
  );
}

function CompletionScreen({ feedback }: { feedback: SubmitResponse }) {
  const completion = feedback.completion;
  return (
    <main className="grid min-h-dvh place-items-center bg-white px-5">
      <section className="w-full max-w-xl rounded-2xl border-2 border-slate-100 p-8 text-center">
        <div className="mx-auto grid h-24 w-24 place-items-center rounded-full bg-lime-500 text-white shadow-[0_8px_0_#45a900]">
          <FaCheck aria-hidden className="text-5xl" />
        </div>
        <h1 className="mt-8 text-4xl font-black text-slate-800">Lesson complete!</h1>
        <p className="mt-3 text-lg font-bold text-slate-500">
          You earned {completion?.xpEarned ?? 0} XP.
        </p>
        <div className="mt-8 grid grid-cols-3 gap-3">
          <ResultStat label="XP" value={`+${completion?.xpEarned ?? 0}`} />
          <ResultStat label="Correct" value={String(feedback.correctCount)} />
          <ResultStat label="Hearts" value={String(feedback.learner.hearts ?? 0)} />
        </div>
        <Link
          href="/learn"
          className="mt-8 inline-flex h-14 items-center justify-center rounded-2xl bg-lime-500 px-10 text-base font-black uppercase text-white shadow-[0_5px_0_#45a900] transition hover:-translate-y-0.5"
        >
          Continue
        </Link>
      </section>
    </main>
  );
}

function ResultStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border-2 border-slate-100 p-4">
      <p className="text-sm font-black uppercase text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-black text-slate-800">{value}</p>
    </div>
  );
}

function LessonError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <main className="grid min-h-dvh place-items-center bg-white px-5">
      <section className="w-full max-w-lg rounded-2xl border-2 border-slate-100 p-8 text-center">
        <h1 className="text-3xl font-black text-slate-800">Lesson unavailable</h1>
        <p className="mt-3 font-bold text-slate-500">{message}</p>
        <button
          onClick={onRetry}
          className="mt-8 h-14 rounded-2xl bg-lime-500 px-8 text-sm font-black uppercase text-white shadow-[0_5px_0_#45a900]"
        >
          Try again
        </button>
      </section>
    </main>
  );
}
