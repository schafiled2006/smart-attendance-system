import React, { useEffect, useState } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import {
  CalendarCheck,
  Play,
  StopCircle,
  FileSpreadsheet,
  Camera,
  CheckCircle2,
  Clock,
  Eye,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import {
  fetchSessions,
  startSession,
  closeSession,
  fetchCourses,
} from '../../api/sessions';
import { fetchSessionAttendance } from '../../api/attendance';
import { downloadSessionReport } from '../../api/reports';
import {
  Course,
  Session,
  SessionAttendanceResponse,
} from '../../api/types';
import { getErrorMessage } from '../../api/client';

export const SessionsPage: React.FC = () => {
  const { activeSession, setActiveSession } = useOutletContext<{
    activeSession: Session | null;
    setActiveSession: React.Dispatch<React.SetStateAction<Session | null>>;
  }>();

  const [sessions, setSessions] = useState<Session[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  // Start Session Modal
  const [isStartOpen, setIsStartOpen] = useState(false);
  const [selectedCourseId, setSelectedCourseId] = useState<number>(1);
  const [lateThreshold, setLateThreshold] = useState<number>(10);
  const [startLoading, setStartLoading] = useState(false);

  // Session Details View Modal
  const [viewSessionId, setViewSessionId] = useState<number | null>(null);
  const [sessionDetail, setSessionDetail] = useState<SessionAttendanceResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Messages
  const [notification, setNotification] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sessList, courseList] = await Promise.all([
        fetchSessions(50),
        fetchCourses().catch(() => []),
      ]);
      setSessions(sessList);
      setCourses(courseList);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeSession]);

  const handleStartSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setStartLoading(true);
    setNotification(null);
    try {
      const sess = await startSession(selectedCourseId, lateThreshold);
      setActiveSession(sess);
      setIsStartOpen(false);
      setNotification(`جلسه کلاسی #${sess.id} با موفقیت شروع شد.`);
      loadData();
    } catch (err) {
      setNotification(getErrorMessage(err));
    } finally {
      setStartLoading(false);
    }
  };

  const handleCloseSession = async (sessionId?: number) => {
    setNotification(null);
    try {
      const closed = await closeSession(sessionId);
      if (activeSession && activeSession.id === closed.id) {
        setActiveSession(null);
      }
      setNotification(`جلسه #${closed.id} با موفقیت پایان یافت.`);
      loadData();
    } catch (err) {
      setNotification(getErrorMessage(err));
    }
  };

  const handleOpenDetail = async (id: number) => {
    setViewSessionId(id);
    setDetailLoading(true);
    try {
      const data = await fetchSessionAttendance(id);
      setSessionDetail(data);
    } catch (err) {
      setNotification(getErrorMessage(err));
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDownloadExcel = async (id: number) => {
    try {
      await downloadSessionReport(id);
      setNotification(`گزارش اکسل جلسه #${id} دریافت شد.`);
    } catch (err) {
      setNotification(getErrorMessage(err));
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-ink">جلسات کلاسی و حضور و غیاب</h2>
          <p className="text-xs text-ink-muted mt-1">
            شروع جلسات جدید، تنظیم حد تأخیر ورود، ثبت رکوردهای زمانی و صدور گزارشات
          </p>
        </div>

        {!activeSession ? (
          <Button
            variant="primary"
            icon={<Play className="w-4 h-4" />}
            onClick={() => setIsStartOpen(true)}
          >
            شروع جلسه جدید
          </Button>
        ) : (
          <div className="flex items-center gap-2">
            <Link to="/recognition">
              <Button variant="primary" icon={<Camera className="w-4 h-4" />}>
                پنجره اسکن زنده
              </Button>
            </Link>
            <Button
              variant="outline"
              icon={<StopCircle className="w-4 h-4" />}
              onClick={() => handleCloseSession(activeSession.id)}
            >
              پایان جلسه فعال
            </Button>
          </div>
        )}
      </div>

      {/* Notification Toast */}
      {notification && (
        <div className="p-3.5 rounded-xl bg-warmMuted border border-bone text-xs text-ink flex items-center justify-between">
          <span>{notification}</span>
          <button onClick={() => setNotification(null)} className="font-bold text-sm">
            ×
          </button>
        </div>
      )}

      {/* Sessions Table Container */}
      <div className="bg-surface rounded-xl border border-bone shadow-soft overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-ink-muted">
            در حال بارگذاری لیست جلسات...
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <CalendarCheck className="w-8 h-8 text-ink-muted mx-auto mb-2 opacity-50" />
            <p className="text-sm font-semibold text-ink">هیچ جلسه‌ای ثبت نشده است</p>
            <p className="text-xs text-ink-muted">
              برای آغاز فرآیند حضور و غیاب کلاسی، یک جلسه جدید ایجاد کنید.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs">
              <thead className="bg-warmMuted/60 border-b border-bone text-ink-muted font-medium">
                <tr>
                  <th className="py-3 px-4">شناسه</th>
                  <th className="py-3 px-4">وضعیت</th>
                  <th className="py-3 px-4">زمان شروع</th>
                  <th className="py-3 px-4">زمان پایان</th>
                  <th className="py-3 px-4">حد تأخیر</th>
                  <th className="py-3 px-4 text-left">عملیات</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-bone/60">
                {sessions.map((sess) => {
                  const isActive = sess.status === 'active';
                  return (
                    <tr
                      key={sess.id}
                      className={`hover:bg-warmMuted/30 transition-colors ${
                        isActive ? 'bg-brand-light/30' : ''
                      }`}
                    >
                      <td className="py-3.5 px-4 font-mono font-bold text-ink">
                        #{sess.id}
                      </td>
                      <td className="py-3.5 px-4">
                        <Badge variant={isActive ? 'present' : 'closed'} pulse={isActive}>
                          {isActive ? 'در حال برگزاری' : 'بسته شده'}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4 text-ink">
                        {new Date(sess.started_at).toLocaleString('fa-IR')}
                      </td>
                      <td className="py-3.5 px-4 text-ink-muted">
                        {sess.ended_at
                          ? new Date(sess.ended_at).toLocaleString('fa-IR')
                          : '—'}
                      </td>
                      <td className="py-3.5 px-4 text-ink-muted">
                        {sess.late_after_minutes} دقیقه
                      </td>
                      <td className="py-3.5 px-4 text-left">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            icon={<Eye className="w-3.5 h-3.5" />}
                            onClick={() => handleOpenDetail(sess.id)}
                          >
                            خلاصه
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            icon={<FileSpreadsheet className="w-3.5 h-3.5 text-accent-emerald" />}
                            onClick={() => handleDownloadExcel(sess.id)}
                            title="دانلود فایل اکسل جلسه"
                          >
                            اکسل
                          </Button>
                          {isActive && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-accent-crimson hover:bg-accent-crimsonLight"
                              onClick={() => handleCloseSession(sess.id)}
                            >
                              بستن
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Start Session Modal */}
      <Modal
        isOpen={isStartOpen}
        onClose={() => setIsStartOpen(false)}
        title="شروع جلسه کلاسی جدید"
        subtitle="مشخصات درس و آستانه مجاز تأخیر ورود دانشجو را معین فرمایید."
      >
        <form onSubmit={handleStartSession} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-ink mb-1.5">
              انتخاب درس
            </label>
            <select
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-lg border border-bone bg-canvas text-sm text-ink focus:outline-none focus:border-brand"
            >
              {courses.length > 0 ? (
                courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title} {c.teacher ? `(استاد: ${c.teacher})` : ''}
                  </option>
                ))
              ) : (
                <option value={1}>کلاس اصلی (پیش‌فرض)</option>
              )}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink mb-1.5">
              آستانه تأخیر (دقیقه)
            </label>
            <input
              type="number"
              min={1}
              max={120}
              required
              value={lateThreshold}
              onChange={(e) => setLateThreshold(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-lg border border-bone bg-canvas text-sm text-ink focus:outline-none focus:border-brand font-mono"
            />
            <p className="text-[11px] text-ink-muted mt-1">
              ورود بعد از این بازه زمانی به عنوان «تأخیر» در کارنامه جلسه ثبت می‌شود.
            </p>
          </div>

          <div className="flex items-center justify-end gap-2 pt-4 border-t border-bone/60">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsStartOpen(false)}
              disabled={startLoading}
            >
              انصراف
            </Button>
            <Button type="submit" variant="primary" loading={startLoading}>
              شروع رسمی جلسه
            </Button>
          </div>
        </form>
      </Modal>

      {/* Session Summary Detail Modal */}
      <Modal
        isOpen={Boolean(viewSessionId)}
        onClose={() => setViewSessionId(null)}
        title={`آمار و وضعیت جلسه #${viewSessionId}`}
        subtitle="جزئیات تفکیکی حضور و غیاب دانشجویان در این جلسه"
        maxWidth="lg"
      >
        {detailLoading ? (
          <div className="py-8 text-center text-xs text-ink-muted">
            در حال دریافت گزارش جلسه...
          </div>
        ) : sessionDetail ? (
          <div className="space-y-4">
            {/* Summary Numbers */}
            <div className="grid grid-cols-4 gap-2 text-center text-xs">
              <div className="p-3 bg-surface border border-bone rounded-xl">
                <span className="text-ink-muted block text-[11px]">مجموع</span>
                <span className="font-bold text-ink font-mono text-base">
                  {sessionDetail.summary.total}
                </span>
              </div>
              <div className="p-3 bg-accent-emeraldLight/40 border border-accent-emeraldBorder/80 rounded-xl">
                <span className="text-accent-emerald block text-[11px]">حاضر</span>
                <span className="font-bold text-accent-emerald font-mono text-base">
                  {sessionDetail.summary.present}
                </span>
              </div>
              <div className="p-3 bg-accent-amberLight/40 border border-accent-amberBorder/80 rounded-xl">
                <span className="text-accent-amber block text-[11px]">تأخیر</span>
                <span className="font-bold text-accent-amber font-mono text-base">
                  {sessionDetail.summary.late}
                </span>
              </div>
              <div className="p-3 bg-accent-crimsonLight/40 border border-accent-crimsonBorder/80 rounded-xl">
                <span className="text-accent-crimson block text-[11px]">غایب</span>
                <span className="font-bold text-accent-crimson font-mono text-base">
                  {sessionDetail.summary.absent}
                </span>
              </div>
            </div>

            {/* Student Attendance List */}
            <div className="max-h-64 overflow-y-auto divide-y divide-bone/60 border border-bone rounded-xl pr-1 text-xs">
              {sessionDetail.attendance.map((att) => (
                <div
                  key={att.student_id}
                  className="p-2.5 px-3 flex items-center justify-between"
                >
                  <div>
                    <span className="font-semibold text-ink">{att.full_name}</span>
                    <span className="text-ink-muted font-mono mr-2">({att.student_id})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {att.checked_at && (
                      <span className="text-[11px] text-ink-muted">
                        {new Date(att.checked_at).toLocaleTimeString('fa-IR')}
                      </span>
                    )}
                    <Badge
                      variant={
                        att.status === 'present'
                          ? 'present'
                          : att.status === 'late'
                          ? 'late'
                          : 'closed'
                      }
                      size="sm"
                    >
                      {att.status === 'present'
                        ? 'حاضر'
                        : att.status === 'late'
                        ? 'تأخیر'
                        : 'غایب'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-3 border-t border-bone/60">
              <Button variant="outline" size="sm" onClick={() => setViewSessionId(null)}>
                بستن
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
};

