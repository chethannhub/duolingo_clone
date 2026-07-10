import { stats } from "../_data/dashboard";
import { IconImage } from "./IconImage";

const toneClass = {
  neutral: "text-slate-100",
  hot: "text-amber-400",
  sky: "text-sky-300",
  heart: "text-rose-400",
};

export function TopStats() {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-800/70 bg-[#0b1d22]/90 px-4 py-3 backdrop-blur md:px-8 xl:static xl:border-b-0 xl:bg-transparent xl:px-0 xl:py-0">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 xl:justify-end">
        <a
          href="#"
          className="inline-flex items-center gap-2 rounded-xl px-2 py-2 text-sm font-extrabold uppercase text-slate-400 transition hover:text-slate-100 xl:hidden"
        >
          <span aria-hidden="true">{"<"}</span>
          Back
        </a>

        <div className="flex items-center gap-3 sm:gap-6">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="flex items-center gap-2 text-sm font-extrabold sm:text-base"
              title={stat.label}
            >
              <IconImage src={stat.icon} alt="" size={32} className="h-8 w-8" />
              <span className={toneClass[stat.tone]}>{stat.value}</span>
            </div>
          ))}
        </div>
      </div>
    </header>
  );
}
