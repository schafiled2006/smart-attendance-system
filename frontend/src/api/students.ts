import { apiClient } from './client';
import { ProcessPhotosResponse, Student, StudentCreate, StudentUpdate } from './types';

export async function fetchStudents(): Promise<Student[]> {
  const res = await apiClient.get<Student[]>('/students');
  return res.data;
}

export async function createStudent(payload: StudentCreate): Promise<Student> {
  const res = await apiClient.post<Student>('/students', payload);
  return res.data;
}

export async function updateStudent(id: string, payload: StudentUpdate): Promise<Student> {
  const res = await apiClient.put<Student>(`/students/${encodeURIComponent(id)}`, payload);
  return res.data;
}

export async function deleteStudent(id: string, force: boolean = false): Promise<{ success: boolean; student_id: string }> {
  const res = await apiClient.delete<{ success: boolean; student_id: string }>(
    `/students/${encodeURIComponent(id)}`,
    { params: { force } }
  );
  return res.data;
}

export async function triggerProcessPhotos(id: string): Promise<ProcessPhotosResponse> {
  const res = await apiClient.post<ProcessPhotosResponse>(`/students/${encodeURIComponent(id)}/process-photos`);
  return res.data;
}

