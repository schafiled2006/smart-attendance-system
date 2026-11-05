export interface Student {
  student_id: string;
  full_name: string;
  major: string;
  term: string;
  embedding_path?: string | null;
  photo_count: number;
  created_at: string;
  has_embedding: boolean;
}

export interface StudentCreate {
  student_id: string;
  full_name: string;
  major?: string;
  term?: string;
}

export interface StudentUpdate {
  full_name?: string;
  major?: string;
  term?: string;
}

export interface ProcessPhotosResponse {
  accepted: number;
  rejected: Array<{ file: string; reason: string }>;
  warnings: Array<{ message: string }>;
  embedding_saved: boolean;
}

export interface Course {
  id: number;
  title: string;
  teacher: string;
  room: string;
}

export interface Session {
  id: number;
  course_id: number;
  started_at: string;
  ended_at: string | null;
  late_after_minutes: number;
  status: 'active' | 'closed';
}

export interface AttendanceItem {
  student_id: string;
  full_name: string;
  major: string;
  term: string;
  status: 'present' | 'late' | 'absent';
  checked_at: string | null;
  source: 'face' | 'manual' | null;
}

export interface SessionSummary {
  total: number;
  present: number;
  late: number;
  absent: number;
}

export interface SessionAttendanceResponse {
  attendance: AttendanceItem[];
  summary: SessionSummary;
}

export interface FaceItem {
  box: [number, number, number, number]; // [top, right, bottom, left] relative 0..1
  student_id: string | null;
  distance: number;
}

export interface RecognitionResponse {
  recorded: string[];
  already_present: string[];
  pending: Record<string, number>; // student_id -> consecutive frame streak
  unknown_count: number;
  faces: FaceItem[];
}

export interface ApiError {
  error: string;
  message: string;
}

