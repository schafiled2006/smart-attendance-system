import axios, { AxiosError } from 'axios';
import { ApiError } from './types';

export const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 15000,
  headers: {
    'Accept': 'application/json',
  },
});

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<ApiError>;
    if (axiosErr.response?.data?.message) {
      return axiosErr.response.data.message;
    }
    if (axiosErr.message === 'Network Error') {
      return 'ارتباط با سرور برقرار نشد. لطفاً از روشن بودن سرور بک‌اند مطمئن شوید.';
    }
    return axiosErr.message || 'خطایی در ارسال درخواست رخ داد.';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'خطای ناشناخته رخ داده است.';
}

