import Image from "next/image";
import { questItems } from "../_data/dashboard";
import { IconImage } from "./IconImage";
import { LearningPanel } from "./LearningPanel";

export function RightRail() {
  return (
    <aside className="hidden h-dvh w-[23rem] shrink-0 overflow-y-auto px-1 pb-10 xl:block">
      <div className="space-y-5 pb-10">
      <LearningPanel>
        <div className="flex items-start justify-between gap-5">
          <div>
            <p className="mb-4 inline-flex rounded-md bg-gradient-to-r from-sky-400 to-violet-500 px-2 py-1 text-sm font-black italic text-white">
              SUPER
            </p>
            <h2 className="text-xl font-black text-slate-800">Try Super for free</h2>
            <p className="mt-4 text-base font-bold leading-7 text-slate-500">
              No ads, personalized practice, and unlimited Legendary!
            </p>
          </div>
          <Image
            src="/Duo_butterfly.gif"
            alt=""
            width={120}
            height={120}
            unoptimized
            className="h-28 w-28 object-contain"
          />
        </div>
        <button className="mt-8 h-14 w-full rounded-2xl bg-indigo-500 text-sm font-black uppercase text-white shadow-[0_5px_0_#3530d9] transition hover:-translate-y-0.5">
          Try 1 week free
        </button>
      </LearningPanel>

      <LearningPanel>
        <div className="mb-7 flex items-center justify-between">
          <h2 className="text-xl font-black text-slate-800">Bronze League</h2>
          <a href="#" className="text-sm font-black uppercase text-sky-500">
            View league
          </a>
        </div>
        <div className="flex items-center gap-6">
          <div className="grid h-20 w-20 place-items-center rounded-2xl bg-amber-200 shadow-inner">
            <IconImage src="/Icon=Trophy, Size=Small.svg" alt="" size={48} />
          </div>
          <div>
            <p className="font-black text-slate-800">You are ranked #16</p>
            <p className="mt-2 font-bold leading-7 text-slate-500">
              You have earned 75 XP this week so far
            </p>
          </div>
        </div>
      </LearningPanel>

      <LearningPanel>
        <div className="mb-7 flex items-center justify-between">
          <h2 className="text-xl font-black text-slate-800">Daily Quests</h2>
          <a href="#" className="text-sm font-black uppercase text-sky-500">
            View all
          </a>
        </div>
        <div className="space-y-5">
          {questItems.map((quest) => (
            <div key={quest.label} className="flex items-center gap-5">
              <IconImage src="/Icon=Lightning, Size=Small.svg" alt="" size={48} />
              <div className="min-w-0 flex-1">
                <div className="mb-3 flex justify-between gap-4 font-black text-slate-700">
                  <span>{quest.label}</span>
                  <span className="text-orange-500">{quest.progress}</span>
                </div>
                <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-orange-400"
                    style={{ width: quest.complete ? "100%" : "35%" }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </LearningPanel>

      </div>
    </aside>
  );
}
