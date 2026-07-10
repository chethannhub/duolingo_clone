import { AppShell } from "./AppShell";
import { LessonPath } from "./LessonPath";

export function LearningDashboard() {
  return (
    <AppShell activeItem="Learn">
      <LessonPath />
    </AppShell>
  );
}
