export type NavItem = {
  label: string;
  icon: string;
  href: string;
  active?: boolean;
};

export type Stat = {
  label: string;
  value: string;
  icon: string;
  tone: "neutral" | "hot" | "sky" | "heart";
};

export type LessonNode = {
  id: number;
  section: number;
  unit: number;
  level: number;
  lesson: number;
  kind: "complete" | "guide" | "active" | "locked" | "trophy" | "story" | "reward";
  label: string;
  offset: "left" | "center" | "right";
  exerciseTypes: string[];
  questions: ExerciseQuestion[];
};

export type CourseUnit = {
  id: number;
  section: number;
  unit: number;
  title: string;
  color: "green" | "purple" | "blue" | "amber";
  nodes: LessonNode[];
};

export type ExerciseQuestion = {
  id: number;
  type: string;
  prompt: string;
  choices: string[];
  answer: string;
};

export type SectionCard = {
  id: number;
  title: string;
  status: "complete" | "active" | "locked";
  progressLabel: string;
  description: string;
  actionLabel: string;
  unitCount: number;
};

export const navItems: NavItem[] = [
  { label: "Learn", icon: "/Icon=House, Size=Small.svg", href: "/learn" },
  { label: "Letters", icon: "/globe.svg", href: "/learn" },
  { label: "Practice", icon: "/Icon=Weights, Size=Small.svg", href: "/learn" },
  { label: "Leaderboards", icon: "/Icon=Trophy, Size=Small.svg", href: "/learn" },
  { label: "Quests", icon: "/Icon=Shiny Gold Chest, Size=Small.svg", href: "/learn" },
  { label: "Shop", icon: "/window.svg", href: "/learn" },
  { label: "Profile", icon: "/Icon=Duo Pro, Size=Small.svg", href: "/learn" },
  { label: "More", icon: "/Icon=More, Size=Small.svg", href: "/learn" },
];

export const stats: Stat[] = [
  { label: "English", value: "80", icon: "/globe.svg", tone: "neutral" },
  { label: "Streak", value: "1", icon: "/fire_icon.svg", tone: "hot" },
  { label: "Gems", value: "505", icon: "/Icon=Gem, Size=Small.svg", tone: "sky" },
  { label: "Hearts", value: "5", icon: "/Icon=Heart, Size=Small.svg", tone: "heart" },
];

const unitTitles = [
  "Gratitude: Show appreciation for help",
  "Gratitude: Respond to unexpected gestures",
  "Travel: Ask about transportation",
  "Travel: Check in at a hotel",
  "Food: Order with confidence",
  "Stories: Talk about your day",
  "Plans: Discuss future goals",
  "Review: Strengthen everything",
];

const exerciseTypes = [
  "Fill in the blanks",
  "Match pairs",
  "Translate",
  "Listen and choose",
  "Speak the sentence",
  "Select meaning",
  "Type what you hear",
  "Build the sentence",
  "Read and answer",
  "Complete the chat",
];

const offsets: LessonNode["offset"][] = ["center", "right", "right", "left", "center"];
const oppositeOffsets: LessonNode["offset"][] = ["center", "left", "left", "right", "center"];

function createQuestions(section: number, unit: number, lesson: number) {
  return exerciseTypes.map((type, index) => ({
    id: index + 1,
    type,
    prompt:
      index % 2 === 0
        ? "My seat isn't very _____, but it's much _____ than those seats."
        : `Section ${section}, Unit ${unit}, Lesson ${lesson}: choose the best answer.`,
    choices: ["small", "smaller", "comfortable", "thanks"],
    answer: index % 2 === 0 ? "smaller" : "thanks",
  }));
}

export const courseUnits: CourseUnit[] = Array.from({ length: 4 }).flatMap((_, sectionIndex) =>
  Array.from({ length: 8 }).map((__, unitIndex) => {
    const section = sectionIndex + 1;
    const unit = sectionIndex * 8 + unitIndex + 1;
    const unitInSection = unitIndex + 1;
    const isOpposite = unitInSection % 2 === 0;
    const sectionProgressBoundary = section === 1 && unitInSection <= 2;
    const activeUnit = section === 2 && unitInSection === 1;
    const color = (["green", "purple", "blue", "amber"] as const)[unitIndex % 4];
    const nodeOffsets = isOpposite ? oppositeOffsets : offsets;

    return {
      id: unit,
      section,
      unit,
      title: unitTitles[unitIndex],
      color,
      nodes: nodeOffsets.map((offset, index) => {
        const lesson = index + 1;
        const isReward = lesson === 5;
        const kind: LessonNode["kind"] = isReward
          ? "reward"
          : sectionProgressBoundary
            ? "complete"
            : activeUnit && lesson === 1
              ? "active"
              : activeUnit && lesson === 2
                ? "guide"
                : activeUnit
                  ? "locked"
                  : "locked";

        return {
          id: unit * 10 + lesson,
          section,
          unit,
          level: lesson,
          lesson,
          kind,
          label: isReward ? "Reward" : `Lesson ${lesson}`,
          offset,
          exerciseTypes,
          questions: createQuestions(section, unit, lesson),
        };
      }),
    };
  }),
);

export const lessonNodes = courseUnits.flatMap((unit) => unit.nodes);

export const sectionCards: SectionCard[] = [
  {
    id: 1,
    title: "Section 1",
    status: "complete",
    progressLabel: "Completed",
    description: "Warm up with travel phrases and everyday questions.",
    actionLabel: "Review",
    unitCount: 8,
  },
  {
    id: 2,
    title: "Section 2",
    status: "active",
    progressLabel: "1%",
    description: "I can express myself appropriately depending on the context.",
    actionLabel: "Continue",
    unitCount: 8,
  },
  {
    id: 3,
    title: "Section 3",
    status: "locked",
    progressLabel: "180 units",
    description: "I am able to discuss abstract topics, hopes, goals, and projects.",
    actionLabel: "Locked",
    unitCount: 8,
  },
  {
    id: 4,
    title: "Section 4",
    status: "locked",
    progressLabel: "Advanced",
    description: "I can handle longer conversations and explain ideas clearly.",
    actionLabel: "Locked",
    unitCount: 8,
  },
];

export const courseFlow = {
  course: "English",
  section: "Section 1",
  unit: "Unit 2",
  level: "Level 1",
  lesson: "Solo trip: Ask about transportation",
  exercises: ["Match pairs", "Translate", "Listen", "Speak", "Select meaning"],
};

export const questItems = [
  { label: "Earn 10 XP", progress: "10 / 10", complete: true },
  { label: "Finish 1 lesson", progress: "0 / 1", complete: false },
];

export const discoveryLinks = [
  "Foreign Language Study",
  "Translation Tools",
  "Machine Learning",
];
