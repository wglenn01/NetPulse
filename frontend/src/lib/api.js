import axios from 'axios';
import { useCallback, useEffect, useRef, useState } from 'react';

const BASE = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const api = axios.create({ baseURL: BASE });

// Generic polling hook. Pass null path to disable.
export function usePoll(path, interval = 5000, enabled = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const timer = useRef(null);

  const load = useCallback(async () => {
    if (!path) return;
    try {
      const r = await api.get(path);
      setData(r.data);
      setError(null);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    if (!enabled) return;
    load();
    if (interval) {
      timer.current = setInterval(load, interval);
      return () => clearInterval(timer.current);
    }
  }, [load, interval, enabled]);

  return { data, loading, error, refresh: load, setData };
}
