import { apiClient } from './client';

export async function downloadSessionReport(sessionId: number): Promise<void> {
  const response = await apiClient.get(`/sessions/${sessionId}/report`, {
    responseType: 'blob',
  });

  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `attendance_session_${sessionId}.xlsx`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function downloadDailyReport(dateIso: string): Promise<void> {
  const response = await apiClient.get('/reports/daily', {
    params: { date: dateIso },
    responseType: 'blob',
  });

  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `daily_report_${dateIso}.xlsx`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function checkSystemHealth(): Promise<{ status: string }> {
  const res = await apiClient.get<{ status: string }>('/health');
  return res.data;
}

