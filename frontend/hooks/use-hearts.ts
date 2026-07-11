"use client";

import { createIdempotencyKey } from "@/lib/api/client";
import { getHearts, refillHearts } from "@/lib/api/gamification";
import { useApiResource } from "./use-api-resource";

export function useHearts() {
  const resource = useApiResource(getHearts, []);

  async function refill(method: "practice" | "gems" | "mock" = "gems", cost = 50) {
    const response = await refillHearts(createIdempotencyKey(), { method, cost });
    await resource.refetch();
    return response;
  }

  return { ...resource, refill };
}
