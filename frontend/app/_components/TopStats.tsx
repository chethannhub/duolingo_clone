import { stats } from "../_data/dashboard";
import { IconImage } from "./IconImage";

const toneClass = {
  neutral: "text-slate-500",
  hot: "text-orange-500",
  sky: "text-sky-500",
  heart: "text-rose-500",
};

export function TopStats() {
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
