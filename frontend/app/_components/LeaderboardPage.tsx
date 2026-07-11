import { AppShell } from "./AppShell";

const leaderboard = [
  { rank: 1, name: "Millie", xp: 565, avatar: "M", color: "bg-rose-500", accent: "" },
  { rank: 2, name: "Dylan Thompson", xp: 559, avatar: "DT", color: "bg-slate-800", accent: "100" },
  { rank: 3, name: "polina pronina", xp: 475, avatar: "pp", color: "bg-stone-600", accent: "" },
  { rank: 4, name: "Drake", xp: 400, avatar: "D", color: "bg-sky-400", accent: "" },
  { rank: 5, name: "tran tuan kiet", xp: 299, avatar: "tt", color: "bg-cyan-300", accent: "US" },
  { rank: 6, name: "gowon", xp: 280, avatar: "G", color: "bg-red-500", accent: "" },
  { rank: 7, name: "alizalund", xp: 272, avatar: "a", color: "bg-zinc-700", accent: "" },
  { rank: 8, name: "yash", xp: 255, avatar: "Y", color: "bg-lime-600", accent: "" },
  { rank: 9, name: "Jun", xp: 232, avatar: "J", color: "bg-violet-500", accent: "" },
  { rank: 10, name: "Camila", xp: 218, avatar: "C", color: "bg-amber-400", accent: "" },
];

const leagueSteps = [
  { label: "Bronze League", active: true },
  { label: "Silver League", active: false },
  { label: "Gold League", active: false },
  { label: "Sapphire League", active: false },
];

const statusTiles = ["😎", "🎉", "💪", "👀", "🍿", "🇺🇸", "😠", "100", "💩", "🏆", "🧺", "🐱"];
const footerLinks = ["About", "Blog", "Store", "Efficacy", "Careers", "Investors", "Terms", "Privacy"];

function RankBadge({ rank }: { rank: number }) {
  if (rank <= 3) {
    const colors = {
      1: "bg-amber-300 text-orange-500 shadow-[0_5px_0_#f4a400]",
      2: "bg-sky-100 text-sky-400 shadow-[0_5px_0_#a9c6d9]",
      3: "bg-orange-200 text-orange-500 shadow-[0_5px_0_#d88d42]",
    };

    return (
      <div
        className={[
          "grid h-11 w-9 place-items-center rounded-t-full rounded-b-md text-lg font-black",
          colors[rank as 1 | 2 | 3],
        ].join(" ")}
      >
        {rank}
      </div>
    );
  }

  return <div className="w-9 text-center text-lg font-black text-lime-600">{rank}</div>;
}

function Avatar({
  initials,
  color,
  accent,
}: {
  initials: string;
  color: string;
  accent: string;
}) {
  return (
    <div className="relative grid h-14 w-14 shrink-0 place-items-center rounded-full bg-slate-100">
      <div className={`grid h-full w-full place-items-center rounded-full ${color} text-lg font-black text-white`}>
        {initials}
      </div>
      {accent ? (
        <div className="absolute -right-3 -top-2 grid h-8 min-w-8 place-items-center rounded-full border-2 border-white bg-white px-1 text-[0.65rem] font-black text-red-500 shadow-sm">
          {accent}
        </div>
      ) : null}
    </div>
  );
}

function LeagueMedal() {
  return (
    <div className="mx-auto flex w-full max-w-sm items-end justify-center gap-8">
      {leagueSteps.map((step, index) => (
        <div key={step.label} className="grid place-items-center gap-3">
          <div
            className={[
              "grid rounded-[1.35rem] border-b-4",
              step.active
                ? "h-28 w-24 place-items-center border-[#c98745] bg-[#e6ad76]"
                : "h-16 w-16 place-items-center border-slate-200 bg-slate-100 opacity-80",
            ].join(" ")}
            title={step.label}
          >
            {step.active ? (
              <div className="grid h-20 w-20 place-items-center rounded-full bg-[#d59658] text-5xl text-[#9a6428]">
                <span className="-rotate-45">🗡</span>
              </div>
            ) : (
              <div className="grid h-9 w-9 place-items-center rounded-full bg-slate-200 text-slate-300">●</div>
            )}
          </div>
          {index === 0 ? <span className="sr-only">Current league</span> : null}
        </div>
      ))}
    </div>
  );
}

function LeaderboardList() {
  return (
    <div className="mt-8 border-t-2 border-slate-100">
      {leaderboard.map((user) => (
        <div
          key={user.rank}
          className="grid grid-cols-[2.75rem_4.5rem_minmax(0,1fr)_5rem] items-center gap-2 py-3 sm:grid-cols-[3rem_5rem_minmax(0,1fr)_6rem]"
        >
          <RankBadge rank={user.rank} />
          <Avatar initials={user.avatar} color={user.color} accent={user.accent} />
          <p className="truncate text-lg font-black text-slate-800">{user.name}</p>
          <p className="text-right text-base font-bold text-slate-500">{user.xp} XP</p>
        </div>
      ))}
    </div>
  );
}

function StatusRail() {
  return (
    <aside className="hidden w-[23rem] shrink-0 pb-10 xl:block">
      <div className="rounded-2xl border-2 border-slate-100 bg-white p-6">
        <div className="mb-7 flex items-center justify-between">
          <h2 className="text-xl font-black text-slate-700">Set your status</h2>
          <button className="text-sm font-black uppercase text-sky-500">Clear</button>
        </div>

        <div className="mb-8 flex justify-center">
          <div className="relative grid h-24 w-24 place-items-center rounded-full border-2 border-dashed border-slate-300 text-4xl font-black text-slate-400">
            C
            <div className="absolute -right-6 top-0 grid h-14 w-14 place-items-center rounded-full border-2 border-sky-400 bg-lime-500 text-2xl">
              😎
            </div>
            <span className="absolute -right-1 bottom-1 h-5 w-5 rounded-full border-2 border-white bg-lime-500" />
          </div>
        </div>

        <div className="grid grid-cols-6 gap-2">
          {statusTiles.map((tile, index) => (
            <button
              key={`${tile}-${index}`}
              className={[
                "grid h-14 w-14 place-items-center rounded-xl border-2 text-2xl font-black transition hover:border-sky-300",
                index === 0 ? "border-sky-400 bg-lime-500" : "border-slate-200 bg-white",
              ].join(" ")}
              aria-label={`Status ${index + 1}`}
            >
              {tile}
            </button>
          ))}
        </div>
      </div>

      <footer className="mx-auto mt-10 flex max-w-xs flex-wrap justify-center gap-x-6 gap-y-5 text-xs font-black uppercase text-slate-400">
        {footerLinks.map((link) => (
          <a key={link} href="#" className="hover:text-slate-600">
            {link}
          </a>
        ))}
      </footer>
    </aside>
  );
}

export function LeaderboardPage() {
  return (
    <AppShell activeItem="Leaderboards" rightRail={<StatusRail />}>
      <div className="pt-6 xl:pt-0">
        <LeagueMedal />

        <div className="mt-5 text-center">
          <h1 className="text-3xl font-black text-slate-800">Bronze League</h1>
          <p className="mt-5 text-2xl font-bold text-slate-500">Top 15 advance to the next league</p>
          <p className="mt-1 text-xl font-black text-amber-400">1 day</p>
        </div>

        <LeaderboardList />

        <div className="mt-6 rounded-2xl border-2 border-dashed border-slate-200 p-5 text-center xl:hidden">
          <div className="mx-auto mb-3 grid h-14 w-14 place-items-center rounded-full bg-lime-500 text-2xl">
            😎
          </div>
          <p className="text-base font-black text-slate-700">Set your status</p>
          <div className="mt-4 grid grid-cols-6 gap-2">
            {statusTiles.slice(0, 6).map((tile, index) => (
              <button
                key={`${tile}-mobile-${index}`}
                className="grid aspect-square place-items-center rounded-xl border-2 border-slate-200 text-xl"
                aria-label={`Status ${index + 1}`}
              >
                {tile}
              </button>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
