import { apiRequest } from "./client";

export function getHearts() {
  return apiRequest<Record<string, unknown>>("/me/hearts");
}

export function refillHearts(
  idempotencyKey: string,
  payload: { method: "practice" | "gems" | "mock"; cost?: number },
) {
  return apiRequest<Record<string, unknown>>("/me/hearts/refill", {
    method: "POST",
    idempotencyKey,
    body: payload,
  });
}

export function claimReward(rewardId: number, idempotencyKey: string) {
  return apiRequest<Record<string, unknown>>(`/me/rewards/${rewardId}/claim`, {
    method: "POST",
    idempotencyKey,
  });
}

export function getDailyGoal() {
  return apiRequest<Record<string, unknown>>("/me/daily-goal");
}

export function updateDailyGoal(dailyGoalXp: number) {
  return apiRequest<Record<string, unknown>>("/me/daily-goal", {
    method: "PATCH",
    body: { daily_goal_xp: dailyGoalXp },
  });
}
