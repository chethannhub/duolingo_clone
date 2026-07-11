import { apiRequest } from "./client";

export function getWeeklyLeaderboard(limit = 20) {
  return apiRequest<Record<string, unknown>>(`/leaderboards/weekly?limit=${limit}`);
}
