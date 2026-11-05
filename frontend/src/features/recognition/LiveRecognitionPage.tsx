import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import {
  Camera,
  CheckCircle2,
  Clock,
  UserCheck,
  UserMinus,
  AlertCircle,
  Play,
  RotateCcw,
} from 'lucide-react';
import { CameraFeed } from './CameraFeed';
import { FaceOverlay } from './FaceOverlay';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { fetchStudents } from '../../api/students';
import {
  fetchSessionAttendance,
  sendRecognitionFrame,
  markAttendanceManual,
  removeAttendanceManual,
} from '../../api/attendance';
import { startSession } from '../../api/sessions';
import {
  AttendanceItem,
  FaceItem,
  Session,
  SessionSummary,
  Student,
} from '../../api/types';
import { getErrorMessage } from '../../api/client';

export const LiveRecognitionPage: React.FC = () => {
  const { activeSession, setActiveSession } = useOutletContext<{
    activeSession: Session | null;
    setActiveSession: React.Dispatch<React.SetStateAction<Session | null>>;
  }>();

  const [students, setStudents] = useState<Student[]>([]);
  const [attendanceList, setAttendanceList] = useState<AttendanceItem[]>([]);
  const [summary, setSummary] = useState<SessionSummary | null>(null);

  // Recognition state
  const [currentFaces, setCurrentFaces] = useState<FaceItem[]>([]);
  const [pendingStreaks, setPendingStreaks] = useState<Record<string, number>>({});
  const [recordedIds, setRecordedIds] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const isProcessingRef = useRef(false);

  // UI notifications
  const [notification, setNotification] = useState<string | null>(null);
  const [startLoading, setStartLoading] = useState(false);

  // Load students map
  useEffect(() => {
    fetchStudents()
      .then(setStudents)
      .catch((err) => console.error('Failed to load students:', err));
  }, []);

  // Load attendance records for active session
  const reloadAttendance = useCallback(async () => {
    if (!activeSession) return;
    try {
      const data = await fetchSessionAttendance(activeSession.id);
      setAttendanceList(data.attendance);
      setSummary(data.summary);
      const presentIds = data.attendance
        .filter((a) => a.status === 'present' || a.status === 'late')
        .map((a) => a.student_id);
      setRecordedIds(presentIds);
    } catch (err) {
      console.error('Failed to load session attendance:', err);
    }
  }, [activeSession]);

  useEffect(() => {
    reloadAttendance();
    const interval = setInterval(reloadAttendance, 8000); // Background refresh
    return () => clearInterval(interval);
  }, [reloadAttendance]);

  // Frame processing dispatch handler
  const handleFrameCapture = useCallback(
    async (imageBlob: Blob) => {
      if (!activeSession || isProcessingRef.current) return;

      isProcessingRef.current = true;
      setIsProcessing(true);

      try {
        const result = await sendRecognitionFrame(activeSession.id, imageBlob);

        // Update faces and bounding boxes
        setCurrentFaces(result.faces);
        setPendingStreaks(result.pending);

        // If newly recorded faces arrived
        if (result.recorded && result.recorded.length > 0) {
          setRecordedIds((prev) => Array.from(new Set([...prev, ...result.recorded])));
          setNotification(`حضور دانشجو (${result.recorded.join('، ')}) ثبت شد.`);
          setTimeout(() => setNotification(null), 4000);
          reloadAttendance();
        }
      } catch (err) {
        // Silent recovery on dropped frame
        console.warn('Recognition frame dropped or rejected:', err);
      } finally {
        isProcessingRef.current = false;
        setIsProcessing(false);
      }
    },
    [activeSession, reloadAttendance]
  );

  // Manual mark attendance
  const handleManualMark = async (studentId: string) => {
    if (!activeSession) return;
    try {
      await markAttendanceManual(activeSession.id, studentId);
      setNotification(`حضور دستی دانشجو ${studentId} ثبت شد.`);
      setTimeout(() => setNotification(null), 3000);
      reloadAttendance();
    } catch (err) {
      setNotification(getErrorMessage(err));
    }
  };

  // Manual remove attendance
  const handleManualRemove = async (studentId: string) => {
    if (!activeSession) return;
    try {
      await removeAttendanceManual(activeSession.id, studentId);
      setNotification(`رکورد حضور دانشجو ${studentId} حذف شد.`);
      setTimeout(() => setNotification(null), 3000);
      reloadAttendance();
    } catch (err) {
      setNotification(getErrorMessage(err));
    }
  };

  const handleStartSession = async () => {
    setStartLoading(true);
    try {
      const sess = await startSession(1, 10);
      setActiveSession(sess);
    } catch (err) {
      setNotification(getErrorMessage(err));
    } finally {
      setStartLoading(false);
    }
  };

  if (!activeSession) {
    return (
      <div className="max-w-xl mx-auto mt-12 p-8 bg-surface rounded-2xl border border-bone shadow-soft text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-brand/10 text-brand flex items-center justify-center mx-auto mb-2">
          <Camera className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-ink">جلسه فعالی برای کلاس باز نیست</h2>
        <p className="text-xs text-ink-muted leading-relaxed max-w-sm mx-auto">
          تشخیص خودکار و استخراج چهره نیازمند یک جلسه فعال کلاسی است تا زمان تأخیر و وضعیت ردیابی فریم‌ها محاسبه شود.
        </p>
        <div className="pt-4 flex items-center justify-center gap-3">
          <Button
            variant="primary"
            icon={<Play className="w-4 h-4" />}
            onClick={handleStartSession}
            loading={startLoading}
          >
            شروع جلسه جدید (۱۰ دقیقه تأخیر)
          </Button>
          <Link to="/sessions">
            <Button variant="outline">مشاهده تاریخچه جلسات</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Toast Alert */}
      {notification && (
        <div className="p-3 px-4 bg-ink text-white rounded-xl text-xs flex items-center justify-between shadow-lift animate-in fade-in slide-in-from-top-2">
          <span>{notification}</span>
          <button onClick={() => setNotification(null)} className="font-bold opacity-75 hover:opacity-100">
            ×
          </button>
        </div>
      )}

      {/* Main Grid: Left Video / Right Roster */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Camera Feed & Real-time Overlays (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-surface rounded-2xl p-5 border border-bone shadow-soft space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-bone/60 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-bold text-ink text-sm">دوربین تشخیص زنده</span>
                <Badge variant="present" size="sm" pulse>
                  در حال اسکن ۳ فریم متوالی
                </Badge>
              </div>
              <span className="text-ink-muted">جلسه #{activeSession.id}</span>
            </div>

            {/* Video Feed Box */}
            <CameraFeed
              onFrameCapture={handleFrameCapture}
              isProcessing={isProcessing}
              intervalMs={650}
            >
              <FaceOverlay
                faces={currentFaces}
                students={students}
                pendingStreaks={pendingStreaks}
                recordedList={recordedIds}
              />
            </CameraFeed>

            {/* Helper Tips */}
            <div className="p-3 bg-warmMuted/60 rounded-xl border border-bone/80 text-[11px] text-ink-muted flex items-center justify-between">
              <span>قانون ضد تقلب: دانشجو باید حداقل ۳ فریم پیاپی روبه‌روی وب‌کم قرار گیرد.</span>
              <span className="font-mono text-ink">مدل: HOG</span>
            </div>
          </div>
        </div>

        {/* Right Column: Live Session Attendance Roster (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Summary Mini Cards */}
          <div className="grid grid-cols-3 gap-2 text-center select-none">
            <div className="bg-surface p-3 rounded-xl border border-bone shadow-soft">
              <span className="text-[11px] text-accent-emerald font-medium block">حاضر</span>
              <span className="text-xl font-bold text-accent-emerald font-mono">
                {summary?.present ?? 0}
              </span>
            </div>
            <div className="bg-surface p-3 rounded-xl border border-bone shadow-soft">
              <span className="text-[11px] text-accent-amber font-medium block">تأخیر</span>
              <span className="text-xl font-bold text-accent-amber font-mono">
                {summary?.late ?? 0}
              </span>
            </div>
            <div className="bg-surface p-3 rounded-xl border border-bone shadow-soft">
              <span className="text-[11px] text-accent-crimson font-medium block">غایب</span>
              <span className="text-xl font-bold text-accent-crimson font-mono">
                {summary?.absent ?? 0}
              </span>
            </div>
          </div>

          {/* Roster Container */}
          <div className="bg-surface rounded-2xl border border-bone shadow-soft p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-bone/60">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-ink">لیست کلاسی و ثبت دستی</h3>
                <span className="text-xs text-ink-muted">({attendanceList.length} دانشجو)</span>
              </div>
              <button
                onClick={reloadAttendance}
                className="p-1 rounded text-ink-muted hover:text-ink hover:bg-warmMuted transition-colors"
                title="بروزرسانی فهرست"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Scrollable Student List */}
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
              {attendanceList.length === 0 ? (
                <div className="py-8 text-center text-xs text-ink-muted">
                  دانشجویی در پایگاه داده ثبت نشده است.
                </div>
              ) : (
                attendanceList.map((item) => {
                  const isPresentOrLate = item.status === 'present' || item.status === 'late';
                  return (
                    <div
                      key={item.student_id}
                      className={`p-3 rounded-xl border transition-all flex items-center justify-between text-xs ${
                        item.status === 'present'
                          ? 'bg-accent-emeraldLight/30 border-accent-emeraldBorder/80'
                          : item.status === 'late'
                          ? 'bg-accent-amberLight/30 border-accent-amberBorder/80'
                          : 'bg-warmMuted/40 border-bone hover:bg-warmMuted/80'
                      }`}
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-ink">{item.full_name}</span>
                          <Badge
                            variant={
                              item.status === 'present'
                                ? 'present'
                                : item.status === 'late'
                                ? 'late'
                                : 'closed'
                            }
                            size="sm"
                          >
                            {item.status === 'present'
                              ? 'حاضر'
                              : item.status === 'late'
                              ? 'تأخیر'
                              : 'غایب'}
                          </Badge>
                        </div>
                        <div className="text-[11px] text-ink-muted flex items-center gap-2">
                          <span className="font-mono">{item.student_id}</span>
                          {item.checked_at && (
                            <span>• ساعت {new Date(item.checked_at).toLocaleTimeString('fa-IR')}</span>
                          )}
                          {item.source && (
                            <span className="text-[10px] opacity-80">
                              ({item.source === 'face' ? 'تشخیص چهره' : 'دستی'})
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Manual Toggle Buttons */}
                      <div>
                        {isPresentOrLate ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-accent-crimson hover:bg-accent-crimsonLight text-[11px] px-2 py-1"
                            onClick={() => handleManualRemove(item.student_id)}
                            title="حذف حضور (تبدیل به غایب)"
                          >
                            <UserMinus className="w-3.5 h-3.5" />
                            <span>حذف</span>
                          </Button>
                        ) : (
                          <Button
                            variant="secondary"
                            size="sm"
                            className="text-[11px] px-2 py-1"
                            onClick={() => handleManualMark(item.student_id)}
                            title="ثبت دستی به عنوان حاضر"
                          >
                            <UserCheck className="w-3.5 h-3.5 text-accent-emerald" />
                            <span>ثبت حاضر</span>
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

