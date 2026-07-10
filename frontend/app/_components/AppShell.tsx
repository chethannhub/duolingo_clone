import { MobileNav } from "./MobileNav";
import { RightRail } from "./RightRail";
import { Sidebar } from "./Sidebar";
import { TopStats } from "./TopStats";

type AppShellProps = {
  activeItem?: string;
  children: React.ReactNode;
};

export function AppShell({ activeItem = "Learn", children }: AppShellProps) {
  return (
    <div className="h-dvh overflow-hidden bg-[#0b1d22] text-slate-100">
      <div className="flex h-full">
        <Sidebar activeItem={activeItem} />

        <main className="min-w-0 flex-1 overflow-y-auto pb-24 xl:pb-10">
          <div className="mx-auto flex max-w-[88rem] flex-col gap-8 px-4 py-4 md:px-8 xl:py-10">
            <TopStats />
            <div className="grid gap-10 xl:grid-cols-[minmax(0,46.25rem)] 2xl:grid-cols-[minmax(0,46.25rem)_28.75rem] 2xl:justify-center">
              <section className="min-w-0">{children}</section>
              <RightRail />
            </div>
          </div>
        </main>
      </div>

      <MobileNav activeItem={activeItem} />
    </div>
  );
}
