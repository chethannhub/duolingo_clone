"use client";

import { getWeeklyLeaderboard } from "@/lib/api/leaderboard";
import { useApiResource } from "./use-api-resource";

export function useLeaderboard(limit = 20) {
  return useApiResource(() => getWeeklyLeaderboard(limit), [limit]);
}
