"use client";

import { useCallback, useEffect, useState } from "react";

type ApiResourceState<T> = {
  data: T | null;
  error: Error | null;
  loading: boolean;
  refetch: () => Promise<void>;
};

export function useApiResource<T>(load: () => Promise<T>, deps: unknown[] = []): ApiResourceState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await load());
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [load]);

  useEffect(() => {
    let active = true;

    load()
      .then((result) => {
        if (active) {
          setData(result);
          setError(null);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err as Error);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error, loading, refetch };
}
