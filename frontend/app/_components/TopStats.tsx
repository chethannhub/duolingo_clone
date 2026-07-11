"use client";

import { useLearningPath } from "@/hooks/use-learning-path";
import { IconImage } from "./IconImage";

const fallbackStats = {
  streak: 0,
  totalXp: 0,
  gems: 0,
  hearts: 0,
};

export function TopStats() {
  const { data } = useLearningPath();
  const stats = (data?.topBar ?? fallbackStats) as typeof fallbackStats;
  const activeCourse = data?.activeCourse as { sourceLanguage?: string } | undefined;

  const items = [
    {
      label: activeCourse?.sourceLanguage?.toUpperCase() ?? "EN",
      icon: "/globe.svg",
      value: activeCourse?.sourceLanguage?.toUpperCase() ?? "EN",
      className: "text-slate-500",
    },
    {
      label: "Streak",
      icon: "/fire_icon.svg",
      value: stats.streak,
      className: "text-orange-500",
    },
    {
      label: "XP",
      icon: "/Icon=Lightning, Size=Small.svg",
      value: stats.totalXp,
      className: "text-amber-500",
    },
    {
      label: "Gems",
      icon: "/Icon=Gem, Size=Small.svg",
      value: stats.gems,
      className: "text-sky-500",
    },
    {
      label: "Hearts",
      icon: "/Icon=Heart, Size=Small.svg",
      value: stats.hearts,
      className: "text-rose-500",
    },
  ];

  return (
    <header className="sticky top-0 z-20 border-b-2 border-slate-100 bg-white/90 py-3 backdrop-blur xl:static xl:border-b-0 xl:bg-transparent">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 xl:justify-end">
        <a
          href="#"
          className="inline-flex items-center gap-2 rounded-xl px-2 py-2 text-sm font-extrabold uppercase text-slate-400 transition hover:text-slate-700 xl:hidden"
        >
          <span aria-hidden="true">{"<"}</span>
          Back
        </a>

        <div className="flex items-center gap-4 sm:gap-7">
          {items.map((item) => (
            <div
              key={item.label}
              className="flex items-center gap-2 text-sm font-extrabold sm:text-base"
              title={item.label}
            >
              <IconImage src={item.icon} alt="" size={32} className="h-8 w-8" />
              <span className={item.className}>{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </header>
  );
}
