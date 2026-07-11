"use client";

import Link from "next/link";
import { FaArrowLeft, FaBookOpen, FaCheck, FaGift, FaLock, FaStar } from "react-icons/fa6";

import { useLearningPath } from "@/hooks/use-learning-path";
import { MascotAnimation } from "./MascotAnimation";
import { LearningPanel } from "./LearningPanel";

type Lesson = {
  id: number;
  title: string;
  position: number;
  completed: boolean;
};

type LevelPathItem = {
  id: number;
  type: "level";
  position: number;
  state: "locked" | "available" | "current" | "completed";
  level: {
    id: number;
    title: string;
    lessons: Lesson[];
  };
};

type RewardPathItem = {
  id: number;
  type: "reward";
  position: number;
  state: "locked" | "claimable" | "claimed";
  reward: {
    id: number;
    title: string;
    gemsReward: number;
  };
};

type Unit = {
  id: number;
  position: number;
  title: string;
  description?: string | null;
  pathItems: Array<LevelPathItem | RewardPathItem>;
};

type Section = {
  id: number;
  position: number;
  title: string;
  units: Unit[];
};

const nodeOffset = ["self-start ml-[8%]", "self-center", "self-end mr-[8%]", "self-center"];

export function LessonPath() {
  const { data, loading, error, refetch } = useLearningPath();
  const sections = (data?.sections ?? []) as Section[];

  if (loading) {
    return (
      <LearningPanel className="grid min-h-96 place-items-center p-8 text-center">
        <div>
          <div className="mx-auto mb-5 h-14 w-14 animate-spin rounded-full border-8 border-slate-100 border-t-lime-500" />
          <p className="text-xl font-black text-slate-700">Loading your course...</p>
        </div>
      </LearningPanel>
    );
  }

  if (error) {
    return (
      <LearningPanel className="p-8 text-center">
        <h2 className="text-2xl font-black text-slate-800">Could not load lessons</h2>
        <p className="mt-3 font-bold text-slate-500">{error.message}</p>
        <button
          onClick={refetch}
          className="mt-6 h-12 rounded-2xl bg-lime-500 px-7 text-sm font-black uppercase text-white shadow-[0_5px_0_#45a900]"
        >
          Try again
        </button>
      </LearningPanel>
    );
  }

  return (
    <section className="space-y-14">
      <Link
        href="/sections"
        className="inline-flex items-center gap-3 text-lg font-black text-slate-400 transition hover:text-slate-700"
      >
        <FaArrowLeft aria-hidden />
        Sections
      </Link>

      {sections.flatMap((section) =>
        section.units.map((unit, index) => (
          <UnitPath
            key={unit.id}
            section={section}
            unit={unit}
            showMascot={(section.position + index) % 2 === 0}
          />
        )),
      )}
    </section>
  );
}

function UnitPath({
  section,
  unit,
  showMascot,
}: {
  section: Section;
  unit: Unit;
  showMascot: boolean;
}) {
  return (
    <LearningPanel className="relative overflow-hidden p-4 md:p-5">
      <div className="sticky top-4 z-20 rounded-2xl bg-[#58cc02] p-5 shadow-[0_8px_0_#45a900] md:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="mb-2 flex items-center gap-2 text-sm font-extrabold uppercase text-white/85">
              <FaArrowLeft aria-hidden />
              Section {section.position}, Unit {unit.position}
            </p>
            <h2 className="max-w-xl text-2xl font-black leading-tight text-white md:text-3xl">
              {unit.title}
            </h2>
          </div>

          <Link
            href={`/learn?unit=${unit.id}`}
            className="inline-flex h-14 items-center gap-3 rounded-2xl border-2 border-black/15 px-4 text-sm font-black uppercase text-white shadow-[0_4px_0_rgba(0,0,0,0.18)] transition hover:-translate-y-0.5"
          >
            <FaBookOpen aria-hidden className="text-2xl" />
            Guidebook
          </Link>
        </div>
      </div>

      <div className="mt-12 flex items-center gap-5 text-center text-sm font-black text-slate-400">
        <span className="h-px flex-1 bg-slate-200" />
        <span>{unit.description || unit.title}</span>
        <span className="h-px flex-1 bg-slate-200" />
      </div>

      <div className="relative mx-auto mt-14 flex min-h-[34rem] max-w-md flex-col gap-10 pb-12">
        <div className="absolute left-1/2 top-8 h-[calc(100%-5rem)] w-1 -translate-x-1/2 rounded-full bg-slate-100" />
        {showMascot ? (
          <div className="absolute left-[8%] top-36 hidden md:block">
            <MascotAnimation />
          </div>
        ) : (
          <div className="absolute right-[8%] top-52 hidden md:block">
            <MascotAnimation />
          </div>
        )}

        {unit.pathItems.map((item, index) => (
          <PathNode key={item.id} item={item} className={nodeOffset[index % nodeOffset.length]} />
        ))}
      </div>
    </LearningPanel>
  );
}

function PathNode({
  item,
  className,
}: {
  item: LevelPathItem | RewardPathItem;
  className: string;
}) {
  if (item.type === "reward") {
    const tone =
      item.state === "locked"
        ? "bg-slate-200 text-slate-400 shadow-[0_8px_0_#cbd5e1]"
        : "bg-amber-400 text-white shadow-[0_8px_0_#c47d00]";
    return (
      <div
        className={[
          "path-node relative z-10 grid h-[5.25rem] w-[5.25rem] place-items-center rounded-full border-4 border-white",
          tone,
          className,
        ].join(" ")}
        aria-label={item.reward.title}
      >
        <FaGift aria-hidden className="text-4xl" />
        <span className="absolute left-1/2 top-[calc(100%+0.75rem)] hidden w-44 -translate-x-1/2 rounded-xl border-2 border-slate-100 bg-white px-3 py-2 text-center text-xs font-black uppercase text-slate-600 shadow-lg sm:block">
          {item.state === "claimable" ? `Claim ${item.reward.gemsReward} gems` : item.reward.title}
        </span>
      </div>
    );
  }

  const firstLesson = item.level.lessons.find((lesson) => !lesson.completed) ?? item.level.lessons[0];
  const isLocked = item.state === "locked" || !firstLesson;
  const tone =
    item.state === "completed"
      ? "bg-lime-500 shadow-[0_8px_0_#45a900]"
      : item.state === "current"
        ? "bg-purple-400 shadow-[0_8px_0_#8f4ed3] ring-[0.65rem] ring-slate-600/70"
        : isLocked
          ? "bg-slate-200 shadow-[0_8px_0_#cbd5e1]"
          : "bg-lime-500 shadow-[0_8px_0_#45a900]";
  const icon =
    item.state === "completed" ? (
      <FaCheck aria-hidden className="text-4xl" />
    ) : isLocked ? (
      <FaLock aria-hidden className="text-3xl text-slate-400" />
    ) : (
      <FaStar aria-hidden className="text-4xl" />
    );

  return (
    <Link
      href={isLocked ? "/learn" : `/lesson?lessonId=${firstLesson.id}`}
      className={[
        "path-node relative z-10 grid h-[5.25rem] w-[5.25rem] place-items-center rounded-full border-4 border-white text-white transition focus:outline-none focus:ring-4 focus:ring-sky-200",
        isLocked ? "cursor-default" : "hover:-translate-y-1",
        tone,
        className,
      ].join(" ")}
      aria-label={item.level.title}
    >
      {icon}
      <span className="absolute left-1/2 top-[calc(100%+0.75rem)] hidden w-44 -translate-x-1/2 rounded-xl border-2 border-slate-100 bg-white px-3 py-2 text-center text-xs font-black uppercase text-slate-600 shadow-lg sm:block">
        {firstLesson ? firstLesson.title : item.level.title}
      </span>
    </Link>
  );
}
