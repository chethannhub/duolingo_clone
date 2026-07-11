import Image from "next/image";
import Link from "next/link";
import { navItems } from "../_data/dashboard";
import { IconImage } from "./IconImage";

type SidebarProps = {
  activeItem?: string;
};

export function Sidebar({ activeItem = "Learn" }: SidebarProps) {
  return (
    <aside className="hidden h-dvh w-64 shrink-0 overflow-y-auto border-r-2 border-slate-100 bg-white px-4 py-8 xl:block">
      <Image
        src="/logo/logo_lockup_green.svg"
        alt="Duolingo"
        width={164}
        height={40}
        priority
        className="mb-8 h-auto w-40"
      />

      <nav aria-label="Primary navigation" className="space-y-3">
        {navItems.map((item) => (
          <Link
            href={item.href}
            key={item.label}
            className={[
              "group flex h-14 items-center gap-4 rounded-xl border-2 px-4 text-[0.95rem] font-extrabold uppercase transition",
              item.label === activeItem
                ? "border-sky-300 bg-sky-50 text-sky-500"
                : "border-transparent text-slate-500 hover:border-slate-200 hover:bg-slate-50",
            ].join(" ")}
          >
            <IconImage src={item.icon} alt="" size={32} className="h-8 w-8" />
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
