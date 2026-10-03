import { useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import { School } from '../types';
import { schools as bundled } from './schools';

const CACHE_KEY = 'schools-cache-v1';
const DATA_URL: string | undefined = Constants.expoConfig?.extra?.dataUrl;

export interface SchoolData { schools: School[]; updatedAt: string | null; source: 'bundled' | 'cache' | 'remote' }

/** Shows bundled/cached data immediately, then swaps in the latest remote data (no app-store release needed). */
export function useSchools(): SchoolData {
  const [data, setData] = useState<SchoolData>({ schools: bundled, updatedAt: null, source: 'bundled' });

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const cached = await AsyncStorage.getItem(CACHE_KEY);
        if (cached && alive) setData({ ...JSON.parse(cached), source: 'cache' });
      } catch {}
      if (!DATA_URL) return;
      try {
        const res = await fetch(DATA_URL);
        if (!res.ok) return;
        const json = await res.json();
        if (!Array.isArray(json.schools) || json.schools.length < 100) return; // sanity check
        const next = { schools: json.schools as School[], updatedAt: (json.updatedAt as string) ?? null };
        if (alive) setData({ ...next, source: 'remote' });
        AsyncStorage.setItem(CACHE_KEY, JSON.stringify(next)).catch(() => {});
      } catch {}
    })();
    return () => { alive = false; };
  }, []);

  return data;
}
