import Link from "next/link";
import { FaArrowLeft, FaBookOpen, FaCheck, FaGift, FaStar } from "react-icons/fa6";
import { courseUnits, type CourseUnit, type LessonNode } from "../_data/dashboard";
import { MascotAnimation } from "./MascotAnimation";

const nodeOffset = {
  left: "self-start ml-[8%]",
  center: "self-center",
  right: "self-end mr-[8%]",
};

const nodeTone = {
  complete: "bg-lime-500 shadow-[0_8px_0_#45a900]",
  guide: "bg-lime-500 shadow-[0_8px_0_#45a900]",
  active: "bg-purple-400 shadow-[0_8px_0_#8f4ed3] ring-[0.65rem] ring-slate-600/70",
  locked: "bg-slate-700 shadow-[0_8px_0_#334155]",
  trophy: "bg-lime-500 shadow-[0_8px_0_#45a900]",
  story: "bg-pink-400 shadow-[0_8px_0_#be3d82]",
  reward: "bg-amber-400 shadow-[0_8px_0_#c47d00]",
};

const unitHeaderTone = {
  green: "bg-[#58cc02] shadow-[0_8px_0_#45a900]",
  purple: "bg-[#c46df4] shadow-[0_8px_0_#994bd0]",
  blue: "bg-sky-400 shadow-[0_8px_0_#168ec3]",
  amber: "bg-amber-400 shadow-[0_8px_0_#c47d00]",
};

export function LessonPath() {
  return (
    <section className="space-y-14">
      <Link
        href="/sections"
        className="inline-flex items-center gap-3 text-lg font-black text-slate-400 transition hover:text-white"
      >
        <FaArrowLeft aria-hidden />
        Sections
      </Link>

      {courseUnits.map((unit, index) => (
        <UnitPath key={unit.id} unit={unit} showMascot={index % 2 === 0} />
      ))}
    </section>
  );
}

function UnitPath({ unit, showMascot }: { unit: CourseUnit; showMascot: boolean }) {
  return (
    <article className="relative overflow-hidden rounded-[1.375rem] bg-[#10242a] p-5 md:p-6">
      <div
        className={[
          "sticky top-4 z-20 rounded-[1.375rem] p-5 md:p-6",
          unitHeaderTone[unit.color],
        ].join(" ")}
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="mb-2 flex items-center gap-2 text-sm font-extrabold uppercase text-white/85">
              <FaArrowLeft aria-hidden />
              Section {unit.section}, Unit {((unit.unit - 1) % 8) + 1}
            </p>
            <h2 className="max-w-xl text-2xl font-black leading-tight text-white md:text-3xl">
              {unit.title}
            </h2>
          </div>

          <button className="inline-flex h-14 items-center gap-3 rounded-2xl border-2 border-black/15 px-4 text-sm font-black uppercase text-white shadow-[0_4px_0_rgba(0,0,0,0.18)] transition hover:-translate-y-0.5">
            <FaBookOpen aria-hidden className="text-2xl" />
            Guidebook
          </button>
        </div>
      </div>

      <div className="mt-12 flex items-center gap-5 text-center text-sm font-black text-slate-500">
        <span className="h-px flex-1 bg-slate-600/70" />
        <span>{unit.title}</span>
        <span className="h-px flex-1 bg-slate-600/70" />
      </div>

      <div className="relative mx-auto mt-14 flex min-h-[34rem] max-w-md flex-col gap-10 pb-12">
        <div className="absolute left-1/2 top-8 h-[calc(100%-5rem)] w-1 -translate-x-1/2 rounded-full bg-slate-800/40" />
        {showMascot && (
          <div className="absolute left-[8%] top-36 hidden md:block">
            <MascotAnimation />
          </div>
        )}
        {!showMascot && (
          <div className="absolute right-[8%] top-52 hidden md:block">
            <MascotAnimation />
          </div>
        )}

        {unit.nodes.map((node) => (
          <PathNode key={node.id} node={node} />
        ))}
      </div>
    </article>
  );
}

function PathNode({ node }: { node: LessonNode }) {
  const isLocked = node.kind === "locked";
  const isReward = node.kind === "reward";

  return (
    <Link
      href={isLocked || isReward ? "/learn" : `/lesson/unit/${node.unit}/level/${node.level}`}
      className={[
        "path-node relative z-10 grid h-[5.25rem] w-[5.25rem] place-items-center rounded-full border-4 border-white/15 text-white transition focus:outline-none focus:ring-4 focus:ring-white/30",
        isLocked || isReward ? "cursor-default" : "hover:-translate-y-1",
        nodeOffset[node.offset],
        nodeTone[node.kind],
      ].join(" ")}
      aria-label={node.label}
    >
      {node.kind === "guide" ? (
        <FaBookOpen aria-hidden className="text-4xl" />
      ) : node.kind === "reward" ? (
        <FaGift aria-hidden className="text-4xl" />
      ) : node.kind === "active" ? (
        <FaStar aria-hidden className="text-4xl" />
      ) : node.kind === "locked" ? (
        <span className="text-3xl font-black text-slate-400">...</span>
      ) : (
        <FaCheck aria-hidden className="text-4xl" />
      )}
      <span className="absolute left-1/2 top-[calc(100%+0.75rem)] hidden w-40 -translate-x-1/2 rounded-xl bg-[#0f2026] px-3 py-2 text-center text-xs font-black uppercase text-white shadow-lg sm:block">
        {isReward ? "Reward spot" : `Lesson ${node.lesson}`}
      </span>
    </Link>
  );
}
