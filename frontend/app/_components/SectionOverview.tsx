import Image from "next/image";
import Link from "next/link";
import { sectionCards } from "../_data/dashboard";

export function SectionOverview() {
  return (
    <section className="space-y-5">
      <Link
        href="/learn"
        className="flex items-center gap-4 border-b border-slate-600 pb-6 text-xl font-black text-slate-400 transition hover:text-white"
      >
        <span aria-hidden="true">{"<"}</span>
        <span>Back</span>
      </Link>

      {sectionCards.map((section) => (
        <article
          key={section.title}
          className={[
            "relative overflow-hidden rounded-[1.375rem] border p-6",
            section.status === "complete"
              ? "border-slate-600 bg-[#172a31] bg-[linear-gradient(135deg,transparent_0_20%,rgba(255,255,255,0.04)_20%_42%,transparent_42%_58%,rgba(255,255,255,0.04)_58%_78%,transparent_78%)]"
              : "border-transparent bg-[#20353d]",
            section.status === "locked" ? "opacity-45" : "",
          ].join(" ")}
        >
          <div className="relative z-10 grid gap-6 lg:grid-cols-[1fr_20rem] lg:items-center">
            <div>
              <h2 className="text-3xl font-black text-white">{section.title}</h2>
              <p className="mt-5 text-sm font-black uppercase tracking-wide text-lime-400">
                {section.progressLabel} - {section.unitCount} units
              </p>
            </div>

            <div className="rounded-2xl bg-[#0f2026] p-5 text-xl font-black leading-relaxed text-white shadow-lg">
              {section.description}
            </div>
          </div>

          {section.status === "active" && (
            <div className="relative z-10 mt-8 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
              <Link
                href="/learn"
                className="grid h-16 place-items-center rounded-2xl bg-sky-400 px-8 text-base font-black uppercase text-white shadow-[0_5px_0_#168ec3] transition hover:-translate-y-0.5 md:w-80"
              >
                {section.actionLabel}
              </Link>
              <Image
                src="/Duo_butterfly.gif"
                alt="Duo mascot"
                width={180}
                height={180}
                unoptimized
                className="mx-auto h-36 w-36 object-contain md:mx-0 md:h-44 md:w-44"
              />
            </div>
          )}

          {section.status === "complete" && (
            <Link
              href="/learn"
              className="absolute right-6 top-1/2 hidden h-16 -translate-y-1/2 place-items-center rounded-2xl border-2 border-slate-600 px-6 text-sm font-black uppercase text-sky-300 shadow-[0_5px_0_#263b44] transition hover:border-sky-400 md:grid"
            >
              {section.actionLabel}
            </Link>
          )}
        </article>
      ))}
    </section>
  );
}
