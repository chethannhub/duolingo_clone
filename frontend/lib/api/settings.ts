import { apiRequest } from "./client";

export type SettingsUpdate = {
  sound_effects_enabled?: boolean;
  animations_enabled?: boolean;
  listening_exercises_enabled?: boolean;
  motivational_messages_enabled?: boolean;
  leaderboard_enabled?: boolean;
  dark_mode_enabled?: boolean;
  daily_reminder_time?: string | null;
};

export function getSettings() {
  return apiRequest<Record<string, unknown>>("/me/settings");
}

export function updateSettings(payload: SettingsUpdate) {
  return apiRequest<Record<string, unknown>>("/me/settings", {
    method: "PATCH",
    body: payload,
  });
}
