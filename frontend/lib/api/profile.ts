import { apiRequest } from "./client";

export function getProfile() {
  return apiRequest<Record<string, unknown>>("/me/profile");
}

export function getActivity() {
  return apiRequest<Record<string, unknown>>("/me/activity");
}

export function getAchievements() {
  return apiRequest<Record<string, unknown>>("/me/achievements");
}
