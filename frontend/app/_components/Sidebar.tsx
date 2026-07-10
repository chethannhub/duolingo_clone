import Image from "next/image";
import Link from "next/link";
import { navItems } from "../_data/dashboard";
import { IconImage } from "./IconImage";

type SidebarProps = {
  activeItem?: string;
};

export function Sidebar({ activeItem = "Learn" }: SidebarProps) {
  return (
    <aside className="hidden h-dvh w-[19.875rem] shrink-0 overflow-y-auto border-r border-slate-700/70 bg-[#0f2026] px-5 py-9 xl:block">
      <Image
        src="/logo/logo_lockup_green.svg"
        alt="Duolingo"
        width={164}
        height={40}
        priority
        className="mb-10 h-auto w-40"
      />

      <nav aria-label="Primary navigation" className="space-y-3">
        {navItems.map((item) => (
          <Link
            href={item.href}
            key={item.label}
            className={[
              "group flex h-16 items-center gap-6 rounded-2xl border px-5 text-[1.05rem] font-extrabold uppercase tracking-wide transition",
              item.label === activeItem
                ? "border-sky-400/80 bg-sky-400/10 text-sky-300"
                : "border-transparent text-slate-100 hover:border-slate-600 hover:bg-white/5",
            ].join(" ")}
          >
            <IconImage src={item.icon} alt="" size={36} className="h-9 w-9" />
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
