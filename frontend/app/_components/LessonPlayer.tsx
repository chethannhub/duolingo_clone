"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  FaArrowRight,
  FaCheck,
  FaGem,
  FaHeart,
  FaRotateRight,
  FaXmark,
} from "react-icons/fa6";

const API_BASES = process.env.NEXT_PUBLIC_API_BASE_URL
  ? [process.env.NEXT_PUBLIC_API_BASE_URL]
  : ["http://localhost:8000", "http://localhost:8001"];
const LEARNER_ID = 1;

type Learner = {
  id: number;
  name: string;
  totalXp: number;
  todayXp: number;
  dailyXpGoal: number;
  currentStreak: number;
  longestStreak: number;
  hearts: number;
  maxHearts: number;
  gems: number;
};

type LessonOption = {
  id: number;
  text: string;
  pairKey: string | null;
};

type LessonExercise = {
  id: number;
  type: "multiple_choice" | "fill_blank" | "type_answer" | "word_bank" | "match_pairs";
  question: string;
  prompt: string | null;
  explanation: string | null;
  orderIndex: number;
  options: LessonOption[];
};

type Lesson = {
  id: number;
  title: string;
  xpReward: number;
  level: {
    title: string;
    unit: {
      title: string;
      section: {
        title: string;
      };
    };
  };
  exercises: LessonExercise[];
};

type Attempt = {
  id: number;
  correctCount: number;
  wrongCount: number;
};

type AnswerResult = {
  correct: boolean;
  correctAnswer: string;
  explanation: string | null;
  learner: Learner;
  attempt: Attempt;
};

type CompletionResult = {
  xpEarned: number;
  correctCount: number;
  wrongCount: number;
  learner: Learner;
};

type MatchSelection = {
  left?: LessonOption;
  right?: LessonOption;
};

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let lastError: unknown;

  for (const apiBase of API_BASES) {
    try {
      const response = await fetch(`${apiBase}${path}`, {
        ...init,
        headers: {
          "Content-Type": "application/json",
          ...init?.headers,
        },
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail ?? "Something went wrong");
      }

      return response.json();
    } catch (caught) {
      lastError = caught;
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Backend is unavailable");
}

export function LessonPlayer() {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [learner, setLearner] = useState<Learner | null>(null);
  const [attemptId, setAttemptId] = useState<number | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState("");
  const [wordBank, setWordBank] = useState<string[]>([]);
  const [matchedPairs, setMatchedPairs] = useState<string[]>([]);
  const [matchSelection, setMatchSelection] = useState<MatchSelection>({});
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [completion, setCompletion] = useState<CompletionResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const hasLoaded = useRef(false);

  const exercise = lesson?.exercises[currentIndex] ?? null;
  const progress = lesson ? ((currentIndex + (result ? 1 : 0)) / lesson.exercises.length) * 100 : 0;
  const canCheck = useMemo(() => {
    if (!exercise || result) return false;
    if (exercise.type === "match_pairs") return matchedPairs.length >= exercise.options.length / 2;
    return selectedAnswer.trim().length > 0;
  }, [exercise, matchedPairs.length, result, selectedAnswer]);

  useEffect(() => {
    if (hasLoaded.current) return;
    hasLoaded.current = true;
    loadLesson();
  }, []);

  async function loadLesson() {
    setIsLoading(true);
    setError("");

    try {
      const [nextLesson, profile] = await Promise.all([
        apiFetch<Lesson>(`/api/lessons/next?learner_id=${LEARNER_ID}`),
        apiFetch<Learner>(`/api/learners/${LEARNER_ID}`),
      ]);

      setLesson(nextLesson);
      setLearner(profile);

      const attempt = await apiFetch<{ id: number; learner: Learner }>("/api/lesson-attempts", {
        method: "POST",
        body: JSON.stringify({
          learner_id: LEARNER_ID,
          lesson_id: nextLesson.id,
        }),
      });

      setAttemptId(attempt.id);
      setLearner(attempt.learner);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load lesson");
    } finally {
      setIsLoading(false);
    }
  }

  function resetExerciseState() {
    setSelectedAnswer("");
    setWordBank([]);
    setMatchedPairs([]);
    setMatchSelection({});
    setResult(null);
  }

  async function submitAnswer() {
    if (!exercise || !attemptId || !canCheck) return;
    setIsSubmitting(true);

    const answer = exercise.type === "match_pairs" ? matchedPairs.join(",") : selectedAnswer;

    try {
      const answerResult = await apiFetch<AnswerResult>(
        `/api/lesson-attempts/${attemptId}/answer`,
        {
          method: "POST",
          body: JSON.stringify({
            learner_id: LEARNER_ID,
            exercise_id: exercise.id,
            answer,
          }),
        },
      );
      setResult(answerResult);
      setLearner(answerResult.learner);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not check answer");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function continueLesson() {
    if (!lesson || !attemptId) return;

    const isLast = currentIndex >= lesson.exercises.length - 1;
    if (!isLast) {
      setCurrentIndex((value) => value + 1);
      resetExerciseState();
      return;
    }

    setIsSubmitting(true);
    try {
      const completed = await apiFetch<CompletionResult>(
        `/api/lesson-attempts/${attemptId}/complete`,
        {
          method: "POST",
          body: JSON.stringify({ learner_id: LEARNER_ID }),
        },
      );
      setCompletion(completed);
      setLearner(completed.learner);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not finish lesson");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function regainHeart() {
    try {
      const updated = await apiFetch<Learner>("/api/learners/regain-heart", {
        method: "POST",
        body: JSON.stringify({ learner_id: LEARNER_ID, cost: 50 }),
      });
      setLearner(updated);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not regain a heart");
    }
  }

  function toggleWord(word: string) {
    const next = wordBank.includes(word)
      ? wordBank.filter((item) => item !== word)
      : [...wordBank, word];
    setWordBank(next);
    setSelectedAnswer(next.join(" "));
  }

  function selectMatch(option: LessonOption, side: "left" | "right") {
    const nextSelection = { ...matchSelection, [side]: option };

    if (nextSelection.left && nextSelection.right) {
      if (nextSelection.left.pairKey === nextSelection.right.pairKey) {
        const pair = `${nextSelection.left.pairKey}:${nextSelection.right.text.toLowerCase()}`;
        setMatchedPairs((pairs) => [...new Set([...pairs, pair])]);
      }
      setMatchSelection({});
      return;
    }

    setMatchSelection(nextSelection);
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

  if (error && !lesson) {
    return <LessonError message={error} onRetry={loadLesson} />;
  }

  if (!lesson || !learner || !exercise) {
    return <LessonError message="No lesson is available." onRetry={loadLesson} />;
  }

  if (completion) {
    return (
      <main className="grid min-h-dvh place-items-center bg-white px-5">
        <section className="w-full max-w-xl rounded-2xl border-2 border-slate-100 p-8 text-center">
          <div className="mx-auto grid h-24 w-24 place-items-center rounded-full bg-lime-500 text-white shadow-[0_8px_0_#45a900]">
            <FaCheck aria-hidden className="text-5xl" />
          </div>
          <h1 className="mt-8 text-4xl font-black text-slate-800">Lesson complete!</h1>
          <p className="mt-3 text-lg font-bold text-slate-500">
            You earned {completion.xpEarned} XP and kept your streak alive.
          </p>
          <div className="mt-8 grid grid-cols-3 gap-3">
            <ResultStat label="XP" value={`+${completion.xpEarned}`} />
            <ResultStat label="Correct" value={String(completion.correctCount)} />
            <ResultStat label="Streak" value={String(completion.learner.currentStreak)} />
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
          {learner.hearts}
        </div>
        <div className="hidden items-center gap-3 text-xl font-black text-sky-500 sm:flex">
          <FaGem aria-hidden />
          {learner.gems}
        </div>
      </header>

      <section className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-5 pb-8 pt-4">
        <p className="text-sm font-black uppercase text-slate-400">
          {lesson.level.unit.section.title} - {lesson.level.unit.title} - {lesson.title}
        </p>
        <h1 className="mt-6 text-3xl font-black text-slate-800 md:text-4xl">
          {exercise.prompt ?? exercise.question}
        </h1>

        <div className="mt-12">
          <ExerciseView
            exercise={exercise}
            selectedAnswer={selectedAnswer}
            setSelectedAnswer={setSelectedAnswer}
            wordBank={wordBank}
            toggleWord={toggleWord}
            matchSelection={matchSelection}
            matchedPairs={matchedPairs}
            selectMatch={selectMatch}
            disabled={Boolean(result)}
          />
        </div>

        {error && (
          <p className="mt-8 rounded-xl bg-rose-50 px-4 py-3 font-bold text-rose-600">{error}</p>
        )}
      </section>

      <footer
        className={[
          "border-t-2 px-5 py-5",
          result?.correct ? "border-lime-200 bg-lime-50" : result ? "border-rose-200 bg-rose-50" : "border-slate-100 bg-white",
        ].join(" ")}
      >
        <div className="mx-auto flex max-w-5xl flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          {result ? (
            <div>
              <p
                className={[
                  "text-2xl font-black",
                  result.correct ? "text-lime-600" : "text-rose-600",
                ].join(" ")}
              >
                {result.correct ? "Excellent!" : "Correct answer: " + result.correctAnswer}
              </p>
              {result.explanation && (
                <p className="mt-1 font-bold text-slate-500">{result.explanation}</p>
              )}
            </div>
          ) : learner.hearts <= 0 ? (
            <div>
              <p className="text-2xl font-black text-rose-600">You are out of hearts</p>
              <p className="font-bold text-slate-500">Spend 50 gems to regain one heart.</p>
            </div>
          ) : (
            <button
              onClick={regainHeart}
              className="inline-flex h-14 items-center justify-center gap-3 rounded-2xl border-2 border-slate-200 px-6 text-sm font-black uppercase text-slate-500 shadow-[0_4px_0_#e2e8f0] transition hover:-translate-y-0.5"
            >
              <FaRotateRight aria-hidden />
              Regain heart
            </button>
          )}

          {learner.hearts <= 0 && !result ? (
            <button
              onClick={regainHeart}
              className="h-14 rounded-2xl bg-rose-500 px-8 text-sm font-black uppercase text-white shadow-[0_5px_0_#be123c]"
            >
              Use 50 gems
            </button>
          ) : (
            <button
              onClick={result ? continueLesson : submitAnswer}
              disabled={isSubmitting || (!result && !canCheck)}
              className="inline-flex h-14 items-center justify-center gap-3 rounded-2xl bg-lime-500 px-8 text-sm font-black uppercase text-white shadow-[0_5px_0_#45a900] transition hover:-translate-y-0.5 disabled:bg-slate-200 disabled:text-slate-400 disabled:shadow-[0_5px_0_#cbd5e1]"
            >
              {result ? "Continue" : "Check"}
              {result && <FaArrowRight aria-hidden />}
            </button>
          )}
        </div>
      </footer>
    </main>
  );
}

function ExerciseView({
  exercise,
  selectedAnswer,
  setSelectedAnswer,
  wordBank,
  toggleWord,
  matchSelection,
  matchedPairs,
  selectMatch,
  disabled,
}: {
  exercise: LessonExercise;
  selectedAnswer: string;
  setSelectedAnswer: (answer: string) => void;
  wordBank: string[];
  toggleWord: (word: string) => void;
  matchSelection: MatchSelection;
  matchedPairs: string[];
  selectMatch: (option: LessonOption, side: "left" | "right") => void;
  disabled: boolean;
}) {
  if (exercise.type === "type_answer") {
    return (
      <div>
        <p className="mb-6 text-2xl font-black text-slate-700">{exercise.question}</p>
        <input
          value={selectedAnswer}
          onChange={(event) => setSelectedAnswer(event.target.value)}
          disabled={disabled}
          className="h-16 w-full rounded-2xl border-2 border-slate-200 px-5 text-xl font-bold outline-none focus:border-sky-300"
          placeholder="Type your answer"
        />
      </div>
    );
  }

  if (exercise.type === "word_bank") {
    return (
      <div>
        <p className="mb-6 text-2xl font-black text-slate-700">{exercise.question}</p>
        <div className="mb-8 min-h-20 rounded-2xl border-2 border-dashed border-slate-200 p-4 text-xl font-black text-slate-700">
          {wordBank.length ? wordBank.join(" ") : "Tap words to build the sentence"}
        </div>
        <div className="flex flex-wrap justify-center gap-3">
          {exercise.options.map((option) => (
            <button
              key={option.id}
              onClick={() => toggleWord(option.text)}
              disabled={disabled}
              className={[
                "rounded-2xl border-2 px-6 py-4 text-xl font-black shadow-[0_4px_0_#e2e8f0] transition hover:-translate-y-0.5",
                wordBank.includes(option.text)
                  ? "border-sky-300 bg-sky-50 text-sky-600"
                  : "border-slate-200 bg-white text-slate-700",
              ].join(" ")}
            >
              {option.text}
            </button>
          ))}
        </div>
      </div>
    );
  }

  if (exercise.type === "match_pairs") {
    const columns = exercise.options.reduce(
      (acc, option, index) => {
        acc[index % 2 === 0 ? "left" : "right"].push(option);
        return acc;
      },
      { left: [] as LessonOption[], right: [] as LessonOption[] },
    );

    return (
      <div>
        <p className="mb-6 text-2xl font-black text-slate-700">{exercise.question}</p>
        <div className="grid gap-4 sm:grid-cols-2">
          {(["left", "right"] as const).map((side) => (
            <div key={side} className="grid gap-3">
              {columns[side].map((option) => {
                const isSelected = matchSelection[side]?.id === option.id;
                const isMatched = matchedPairs.some((pair) => pair.startsWith(`${option.pairKey}:`));

                return (
                  <button
                    key={option.id}
                    onClick={() => selectMatch(option, side)}
                    disabled={disabled || isMatched}
                    className={[
                      "h-16 rounded-2xl border-2 px-5 text-xl font-black shadow-[0_4px_0_#e2e8f0] transition hover:-translate-y-0.5",
                      isSelected
                        ? "border-sky-300 bg-sky-50 text-sky-600"
                        : isMatched
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
      </div>
    );
  }

  return (
    <div>
      <p className="mb-8 text-2xl font-black text-slate-700">{exercise.question}</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {exercise.options.map((option) => (
          <button
            key={option.id}
            onClick={() => setSelectedAnswer(option.text)}
            disabled={disabled}
            className={[
              "min-h-16 rounded-2xl border-2 px-5 py-4 text-xl font-black shadow-[0_4px_0_#e2e8f0] transition hover:-translate-y-0.5",
              selectedAnswer === option.text
                ? "border-sky-300 bg-sky-50 text-sky-600"
                : "border-slate-200 bg-white text-slate-700",
            ].join(" ")}
          >
            {option.text}
          </button>
        ))}
      </div>
    </div>
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
