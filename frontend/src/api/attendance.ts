import { apiClient } from './client';
import { RecognitionResponse, SessionAttendanceResponse } from './types';

export async function fetchSessionAttendance(sessionId: number): Promise<SessionAttendanceResponse> {
  const res = await apiClient.get<SessionAttendanceResponse>(`/sessions/${sessionId}/attendance`);
  return res.data;
}

export async function sendRecognitionFrame(sessionId: number, imageBlob: Blob): Promise<RecognitionResponse> {
  const formData = new FormData();
  formData.append('file', imageBlob, 'frame.jpg');

  const res = await apiClient.post<RecognitionResponse>(
    `/sessions/${sessionId}/recognize`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 10000,
    }
  );
  return res.data;
}

export async function markAttendanceManual(
  sessionId: number,
  studentId: string
): Promise<{ success: boolean; reason?: string }> {
  const res = await apiClient.put<{ success: boolean; reason?: string }>(
    `/sessions/${sessionId}/attendance/${encodeURIComponent(studentId)}`
  );
  return res.data;
}

export async function removeAttendanceManual(
  sessionId: number,
  studentId: string
): Promise<{ success: boolean }> {
  const res = await apiClient.delete<{ success: boolean }>(
    `/sessions/${sessionId}/attendance/${encodeURIComponent(studentId)}`
  );
  return res.data;
}

