import { apiClient } from './client';
import { Course, Session } from './types';

export async function fetchActiveSession(): Promise<Session | null> {
  const res = await apiClient.get<Session | null>('/sessions/active');
  return res.data;
}

export async function fetchSessions(limit: number = 50): Promise<Session[]> {
  const res = await apiClient.get<Session[]>('/sessions', { params: { limit } });
  return res.data;
}

export async function startSession(course_id: number = 1, late_after_minutes: number = 10): Promise<Session> {
  const res = await apiClient.post<Session>('/sessions/start', {
    course_id,
    late_after_minutes,
  });
  return res.data;
}

export async function closeSession(session_id?: number): Promise<Session> {
  const res = await apiClient.post<Session>('/sessions/close', {
    session_id: session_id ?? null,
  });
  return res.data;
}

export async function fetchCourses(): Promise<Course[]> {
  const res = await apiClient.get<Course[]>('/courses');
  return res.data;
}

