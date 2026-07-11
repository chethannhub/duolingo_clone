import { redirect } from "next/navigation";

type LessonPageProps = {
  params: Promise<{
    unit: string;
    level: string;
  }>;
};

export default async function LessonPage({ params }: LessonPageProps) {
  await params;
  redirect("/lesson");
}
