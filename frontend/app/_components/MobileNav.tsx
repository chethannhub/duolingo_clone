import Link from "next/link";
import { navItems } from "../_data/dashboard";
import { IconImage } from "./IconImage";

type MobileNavProps = {
  activeItem?: string;
};

export function MobileNav({ activeItem = "Learn" }: MobileNavProps) {
  return (
    <nav
      aria-label="Mobile navigation"
      className="fixed inset-x-0 bottom-0 z-30 border-t-2 border-slate-100 bg-white/95 px-2 py-2 backdrop-blur xl:hidden"
    >
      <div className="mx-auto grid max-w-2xl grid-cols-5 gap-1">
        {navItems.slice(0, 5).map((item) => (
          <Link
            href={item.href}
            key={item.label}
            className={[
              "flex flex-col items-center gap-1 rounded-xl px-2 py-2 text-[0.65rem] font-black uppercase",
              item.label === activeItem ? "bg-sky-50 text-sky-500" : "text-slate-500",
            ].join(" ")}
          >
            <IconImage src={item.icon} alt="" size={28} className="h-7 w-7" />
            <span className="max-w-full truncate">{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
