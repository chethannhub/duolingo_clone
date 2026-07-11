type LearningPanelProps = {
  children: React.ReactNode;
  className?: string;
};

export function LearningPanel({ children, className = "" }: LearningPanelProps) {
  return (
    <section
      className={[
        "rounded-2xl border-2 border-slate-200 bg-white p-6",
        className,
      ].join(" ")}
    >
      {children}
    </section>
  );
}

