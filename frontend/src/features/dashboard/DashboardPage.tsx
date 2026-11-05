import React, { useEffect, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import {
  Users,
  CheckCircle2,
  Clock,
  UserX,
  Play,
  StopCircle,
  Camera,
  ArrowUpLeft,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { fetchStudents } from '../../api/students';
import { fetchSessionAttendance } from '../../api/attendance';
import { closeSession, startSession } from '../../api/sessions';
import { Session, SessionSummary, Student } from '../../api/types';
import { getErrorMessage } from '../../api/client';

export const DashboardPage: React.FC = () => {
  const { activeSession, setActiveSession } = useOutletContext<{
    activeSession: Session | null;
    setActiveSession: React.Dispatch<React.SetStateAction<Session | null>>;
  }>();

  const [students, setStudents] = useState<Student[]>([]);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      try {
        const studentList = await fetchStudents();
        if (isMounted) setStudents(studentList);

        if (activeSession) {
          const attendanceData = await fetchSessionAttendance(activeSession.id);
          if (isMounted) setSummary(attendanceData.summary);
        } else {
          if (isMounted) setSummary(null);
        }
      } catch (err) {
        console.error(err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    loadData();
    return () => {
      isMounted = false;
    };
  }, [activeSession]);

  const handleStartQuickSession = async () => {
    setActionLoading(true);
    setFeedback(null);
    try {
      const newSession = await startSession(1, 10);
      setActiveSession(newSession);
      setFeedback('جلسه جدید با موفقیت آغاز شد.');
    } catch (err) {
      setFeedback(getErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCloseActiveSession = async () => {
    if (!activeSession) return;
    setActionLoading(true);
    setFeedback(null);
    try {
      await closeSession(activeSession.id);
      setActiveSession(null);
      setFeedback('جلسه با موفقیت بسته شد.');
    } catch (err) {
      setFeedback(getErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const embeddedCount = students.filter((s) => s.has_embedding).length;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Feedback Banner */}
      {feedback && (
        <div className="p-4 rounded-xl bg-warmMuted border border-bone text-xs text-ink flex items-center justify-between">
          <span>{feedback}</span>
          <button
            onClick={() => setFeedback(null)}
            className="text-ink-muted hover:text-ink font-bold"
          >
            ×
          </button>
        </div>
      )}

      {/* Active Session Hero Widget */}
      <div className="bg-surface rounded-2xl border border-bone p-7 shadow-soft relative overflow-hidden">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                وضعیت لحظه‌ای کلاس
              </span>
              {activeSession ? (
                <Badge variant="present" pulse>
                  جلسه در جریان است
                </Badge>
              ) : (
                <Badge variant="closed">بدون جلسه فعال</Badge>
              )}
            </div>

            <h2 className="text-2xl font-bold text-ink">
              {activeSession
                ? `جلسه شماره #${activeSession.id} — کلاس اصلی`
                : 'کلاس در وضعیت آماده‌باش'}
            </h2>

            <p className="text-sm text-ink-muted max-w-xl">
              {activeSession
                ? `زمان شروع: ${new Date(activeSession.started_at).toLocaleTimeString('fa-IR')} | آستانه تأخیر: ${activeSession.late_after_minutes} دقیقه`
                : 'برای شروع ثبت خودکار حضور و غیاب توسط وب‌کم، یک جلسه کلاسی باز کنید.'}
            </p>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            {activeSession ? (
              <>
                <Link to="/recognition" className="flex-1 md:flex-initial">
                  <Button
                    variant="primary"
                    icon={<Camera className="w-4 h-4" />}
                  >
                    ورود به پنجره تشخیص
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  icon={<StopCircle className="w-4 h-4" />}
                  onClick={handleCloseActiveSession}
                  loading={actionLoading}
                >
                  پایان جلسه
                </Button>
              </>
            ) : (
              <Button
                variant="primary"
                icon={<Play className="w-4 h-4" />}
                onClick={handleStartQuickSession}
                loading={actionLoading}
              >
                شروع فوری جلسه (۱۰ دقیقه تاخیر)
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Students */}
        <div className="bg-surface rounded-xl border border-bone p-5 shadow-soft">
          <div className="flex items-center justify-between text-ink-muted mb-3">
            <span className="text-xs font-medium">دانشجویان ثبت‌شده</span>
            <Users className="w-4 h-4 text-ink-muted" />
          </div>
          <div className="text-3xl font-bold text-ink tracking-tight">
            {students.length}
          </div>
          <div className="text-[11px] text-ink-muted mt-2">
            {embeddedCount} نفر آماده تشخیص چهره
          </div>
        </div>

        {/* Present Count */}
        <div className="bg-surface rounded-xl border border-bone p-5 shadow-soft">
          <div className="flex items-center justify-between text-accent-emerald mb-3">
            <span className="text-xs font-medium">حاضرین در جلسه</span>
            <CheckCircle2 className="w-4 h-4 text-accent-emerald" />
          </div>
          <div className="text-3xl font-bold text-accent-emerald tracking-tight">
            {summary ? summary.present : '—'}
          </div>
          <div className="text-[11px] text-ink-muted mt-2">
            ورود به موقع قبل از حد تاخیر
          </div>
        </div>

        {/* Late Count */}
        <div className="bg-surface rounded-xl border border-bone p-5 shadow-soft">
          <div className="flex items-center justify-between text-accent-amber mb-3">
            <span className="text-xs font-medium">تأخیر در ورود</span>
            <Clock className="w-4 h-4 text-accent-amber" />
          </div>
          <div className="text-3xl font-bold text-accent-amber tracking-tight">
            {summary ? summary.late : '—'}
          </div>
          <div className="text-[11px] text-ink-muted mt-2">
            ورود پس از آستانه مجاز
          </div>
        </div>

        {/* Absent Count */}
        <div className="bg-surface rounded-xl border border-bone p-5 shadow-soft">
          <div className="flex items-center justify-between text-accent-crimson mb-3">
            <span className="text-xs font-medium">غایبین جلسه</span>
            <UserX className="w-4 h-4 text-accent-crimson" />
          </div>
          <div className="text-3xl font-bold text-accent-crimson tracking-tight">
            {summary ? summary.absent : '—'}
          </div>
          <div className="text-[11px] text-ink-muted mt-2">
            ثبت‌نشده تا این لحظه
          </div>
        </div>
      </div>

      {/* Quick Action Pathways */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Link
          to="/students"
          className="group bg-surface rounded-xl border border-bone p-5 hover:border-brand/40 transition-all shadow-soft flex flex-col justify-between"
        >
          <div>
            <h4 className="font-semibold text-sm text-ink group-hover:text-brand transition-colors">
              مدیریت دانشجویان و تصاویر
            </h4>
            <p className="text-xs text-ink-muted mt-1 leading-relaxed">
              افزودن دانشجوی جدید، بررسی تصاویر بارگذاری‌شده و تولید بردار میانگین چهره.
            </p>
          </div>
          <div className="flex items-center gap-1 text-xs text-brand font-medium mt-4">
            <span>مشاهده لیست</span>
            <ArrowUpLeft className="w-3.5 h-3.5" />
          </div>
        </Link>

        <Link
          to="/sessions"
          className="group bg-surface rounded-xl border border-bone p-5 hover:border-brand/40 transition-all shadow-soft flex flex-col justify-between"
        >
          <div>
            <h4 className="font-semibold text-sm text-ink group-hover:text-brand transition-colors">
              تاریخچه جلسات و کلاس‌ها
            </h4>
            <p className="text-xs text-ink-muted mt-1 leading-relaxed">
              مشاهده سوابق برگزاری جلسات گذشته، آمار ثبت‌شده و بستن جلسات فعال.
            </p>
          </div>
          <div className="flex items-center gap-1 text-xs text-brand font-medium mt-4">
            <span>مشاهده جلسات</span>
            <ArrowUpLeft className="w-3.5 h-3.5" />
          </div>
        </Link>

        <Link
          to="/reports"
          className="group bg-surface rounded-xl border border-bone p-5 hover:border-brand/40 transition-all shadow-soft flex flex-col justify-between"
        >
          <div>
            <h4 className="font-semibold text-sm text-ink group-hover:text-brand transition-colors">
              خروجی گزارش اکسل
            </h4>
            <p className="text-xs text-ink-muted mt-1 leading-relaxed">
              تولید و دانلود گزارش‌های رسمی اکسل راست‌به‌چپ به تفکیک جلسه یا روزانه.
            </p>
          </div>
          <div className="flex items-center gap-1 text-xs text-brand font-medium mt-4">
            <span>دانلود گزارش‌ها</span>
            <ArrowUpLeft className="w-3.5 h-3.5" />
          </div>
        </Link>
      </div>
    </div>
  );
};

