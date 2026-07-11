import { MobileNav } from "./MobileNav";
import { RightRail } from "./RightRail";
import { Sidebar } from "./Sidebar";
import { TopStats } from "./TopStats";

type AppShellProps = {
  activeItem?: string;
  children: React.ReactNode;
  rightRail?: React.ReactNode;
};

export function AppShell({
  activeItem = "Learn",
  children,
  rightRail = <RightRail />,
}: AppShellProps) {
  return (
    <div className="h-dvh overflow-hidden bg-white text-[#3c3c3c]">
      <div className="flex h-full">
        <Sidebar activeItem={activeItem} />

        <main className="min-w-0 flex-1 overflow-y-auto pb-24 xl:pb-10">
          <div className="mx-auto flex max-w-[78rem] flex-col gap-8 px-4 md:px-8 xl:py-6">
            <TopStats />
            <div className="grid gap-10 xl:grid-cols-[minmax(0,40rem)_23rem] xl:justify-center">
              <section className="min-w-0">{children}</section>
              {rightRail}
            </div>
          </div>
        </main>
      </div>

      <MobileNav activeItem={activeItem} />
    </div>
  );
}
