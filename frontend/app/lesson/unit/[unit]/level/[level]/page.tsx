import Link from "next/link";
import { courseFlow, lessonNodes } from "../../../../../_data/dashboard";
import { FaHeart, FaXmark } from "react-icons/fa6";

type LessonPageProps = {
  params: Promise<{
    unit: string;
    level: string;
  }>;
};

export default async function LessonPage({ params }: LessonPageProps) {
  const { unit, level } = await params;
  const lesson = lessonNodes.find(
    (node) => String(node.unit) === unit && String(node.level) === level,
  );
  const questions = lesson?.questions ?? [];
  const firstQuestion = questions[0];

  return (
    <main className="flex min-h-dvh flex-col bg-[#0b1d22] text-slate-100">
      <header className="mx-auto flex w-full max-w-7xl items-center gap-8 px-5 py-10">
        <Link
          href="/learn"
          aria-label="Close lesson"
          className="grid h-12 w-12 shrink-0 place-items-center rounded-full text-slate-500 transition hover:bg-white/5 hover:text-white"
        >
          <FaXmark aria-hidden className="text-3xl" />
        </Link>
        <div className="h-5 flex-1 overflow-hidden rounded-full bg-slate-700">
          <div className="h-full w-[8%] rounded-full bg-lime-400" />
        </div>
        <div className="flex items-center gap-3 text-xl font-black text-rose-400">
          <FaHeart aria-hidden />
          5
        </div>
      </header>

      <section className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-5 pb-10 pt-6">
        <p className="mb-8 text-sm font-black uppercase tracking-wide text-slate-500">
          {courseFlow.course} - Unit {unit} - Lesson {level} - 10 questions
        </p>
        <h1 className="text-4xl font-black text-white">Fill in the blanks</h1>

        <div className="mt-16 text-2xl font-black leading-[3.5rem] text-slate-100">
          <span className="border-b-4 border-dotted border-slate-500 pb-1">
            My seat isn&apos;t very
          </span>{" "}
          <span className="mx-2 inline-block w-28 border-b-2 border-slate-500" />
          <span className="border-b-4 border-dotted border-slate-500 pb-1">
            , but it&apos;s much
          </span>{" "}
          <span className="mx-2 inline-block w-36 border-b-2 border-slate-500" />
          <span className="border-b-4 border-dotted border-slate-500 pb-1">
            than those seats.
          </span>
        </div>

        <div className="mt-32 flex flex-wrap justify-center gap-3">
          {(firstQuestion?.choices ?? ["small", "smaller"]).slice(0, 2).map((choice) => (
            <button
              key={choice}
              className="rounded-2xl border-2 border-slate-600 px-6 py-4 text-xl font-black text-slate-100 shadow-[0_4px_0_#33414a] transition hover:-translate-y-0.5 hover:border-sky-400"
            >
              {choice}
            </button>
          ))}
        </div>

        <div className="mt-14 rounded-2xl border border-slate-700 bg-[#10242a] p-4">
          <p className="mb-3 text-sm font-black uppercase text-slate-500">
            Lesson question set
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            {questions.map((question) => (
              <div
                key={question.id}
                className="rounded-xl bg-[#0f2026] px-4 py-3 text-sm font-bold text-slate-300"
              >
                {question.id}. {question.type}
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-700 px-5 py-8">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-5">
          <button className="h-16 w-48 rounded-2xl border-2 border-slate-600 text-lg font-black uppercase text-slate-600 shadow-[0_4px_0_#26343b]">
            Skip
          </button>
          <button className="h-16 w-48 rounded-2xl bg-slate-600 text-lg font-black uppercase text-slate-500">
            Check
          </button>
        </div>
      </footer>
    </main>
  );
}
