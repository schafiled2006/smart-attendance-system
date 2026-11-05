import React, { useEffect, useState, useMemo } from 'react';
import {
  UserPlus,
  Search,
  MoreVertical,
  Camera,
  Edit2,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Clock,
  Filter,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { StudentModal } from './StudentModal';
import { PhotoUploadManager } from './PhotoUploadManager';
import { fetchStudents, deleteStudent } from '../../api/students';
import { Student } from '../../api/types';
import { getErrorMessage } from '../../api/client';

export const StudentsPage: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterMode, setFilterMode] = useState<'all' | 'ready' | 'pending'>('all');

  // Modal states
  const [isStudentModalOpen, setIsStudentModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [processingStudent, setProcessingStudent] = useState<Student | null>(null);

  // Delete confirmation
  const [deletingStudent, setDeletingStudent] = useState<Student | null>(null);
  const [forceDelete, setForceDelete] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadStudents = async () => {
    try {
      setLoading(true);
      const data = await fetchStudents();
      setStudents(data);
    } catch (err) {
      setErrorMsg(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStudents();
  }, []);

  const filteredStudents = useMemo(() => {
    return students.filter((s) => {
      const matchSearch =
        s.full_name.toLowerCase().includes(search.toLowerCase()) ||
        s.student_id.toLowerCase().includes(search.toLowerCase()) ||
        s.major.toLowerCase().includes(search.toLowerCase());

      if (!matchSearch) return false;

      if (filterMode === 'ready') return s.has_embedding;
      if (filterMode === 'pending') return !s.has_embedding;
      return true;
    });
  }, [students, search, filterMode]);

  const handleDelete = async () => {
    if (!deletingStudent) return;
    setDeleteLoading(true);
    setErrorMsg(null);

    try {
      await deleteStudent(deletingStudent.student_id, forceDelete);
      setDeletingStudent(null);
      setForceDelete(false);
      loadStudents();
    } catch (err) {
      const msg = getErrorMessage(err);
      if (msg.includes('حضور ثبت‌شده دارد') || msg.includes('attendance')) {
        setForceDelete(true);
      }
      setErrorMsg(msg);
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Page Title & Add Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-ink">مدیریت دانشجویان</h2>
          <p className="text-xs text-ink-muted mt-1">
            ثبت اطلاعات، بارگذاری تصاویر و استخراج بردارهای ۱۲۸ بعدی جهت شناسایی در کلاس
          </p>
        </div>
        <Button
          variant="primary"
          icon={<UserPlus className="w-4 h-4" />}
          onClick={() => {
            setEditingStudent(null);
            setIsStudentModalOpen(true);
          }}
        >
          افزودن دانشجوی جدید
        </Button>
      </div>

      {/* Global Error Banner */}
      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-accent-crimsonLight border border-accent-crimsonBorder text-xs text-accent-crimson flex items-center justify-between">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="font-bold text-sm">
            ×
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-surface p-4 rounded-xl border border-bone shadow-soft flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute right-3.5 top-3 text-ink-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="جستجو با شماره دانشجویی، نام یا رشته..."
            className="w-full pr-10 pl-4 py-2 rounded-lg border border-bone bg-canvas text-xs text-ink placeholder:text-ink-muted focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand/30 transition-all"
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-warmMuted rounded-lg border border-bone self-stretch sm:self-auto text-xs">
          <button
            onClick={() => setFilterMode('all')}
            className={`px-3 py-1.5 rounded-md font-medium transition-all ${
              filterMode === 'all'
                ? 'bg-surface text-ink shadow-soft'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            همه ({students.length})
          </button>
          <button
            onClick={() => setFilterMode('ready')}
            className={`px-3 py-1.5 rounded-md font-medium transition-all ${
              filterMode === 'ready'
                ? 'bg-surface text-ink shadow-soft'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            دارای امبدینگ ({students.filter((s) => s.has_embedding).length})
          </button>
          <button
            onClick={() => setFilterMode('pending')}
            className={`px-3 py-1.5 rounded-md font-medium transition-all ${
              filterMode === 'pending'
                ? 'bg-surface text-ink shadow-soft'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            نیازمند پردازش ({students.filter((s) => !s.has_embedding).length})
          </button>
        </div>
      </div>

      {/* Students List Container */}
      <div className="bg-surface rounded-xl border border-bone shadow-soft overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-ink-muted">
            در حال بارگذاری اطلاعات دانشجویان...
          </div>
        ) : filteredStudents.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <p className="text-sm font-semibold text-ink">دانشجویی یافت نشد</p>
            <p className="text-xs text-ink-muted">
              {search
                ? 'عبارت جستجوی واردشده با هیچ دانشجویی مطابقت ندارد.'
                : 'هنوز هیچ دانشجویی در سیستم ثبت نشده است.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs">
              <thead className="bg-warmMuted/60 border-b border-bone text-ink-muted font-medium">
                <tr>
                  <th className="py-3 px-4">شماره دانشجویی</th>
                  <th className="py-3 px-4">نام و نام خانوادگی</th>
                  <th className="py-3 px-4">رشته و ترم</th>
                  <th className="py-3 px-4">وضعیت امبدینگ</th>
                  <th className="py-3 px-4">عکس‌ها</th>
                  <th className="py-3 px-4 text-left">عملیات</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-bone/60">
                {filteredStudents.map((s) => (
                  <tr
                    key={s.student_id}
                    className="hover:bg-warmMuted/30 transition-colors"
                  >
                    <td className="py-3.5 px-4 font-mono font-medium text-ink" dir="ltr">
                      {s.student_id}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-ink">
                      {s.full_name}
                    </td>
                    <td className="py-3.5 px-4 text-ink-muted">
                      {s.major || '—'} {s.term ? `(ترم ${s.term})` : ''}
                    </td>
                    <td className="py-3.5 px-4">
                      {s.has_embedding ? (
                        <Badge variant="present">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>آماده تشخیص</span>
                        </Badge>
                      ) : (
                        <Badge variant="late">
                          <Clock className="w-3 h-3" />
                          <span>نیازمند پردازش</span>
                        </Badge>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-ink-muted">
                      <span className="font-mono">{s.photo_count}</span> تصویر
                    </td>
                    <td className="py-3.5 px-4 text-left">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="secondary"
                          size="sm"
                          icon={<Camera className="w-3.5 h-3.5" />}
                          onClick={() => setProcessingStudent(s)}
                        >
                          پردازش عکس
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Edit2 className="w-3.5 h-3.5" />}
                          onClick={() => {
                            setEditingStudent(s);
                            setIsStudentModalOpen(true);
                          }}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-accent-crimson hover:bg-accent-crimsonLight"
                          icon={<Trash2 className="w-3.5 h-3.5" />}
                          onClick={() => {
                            setDeletingStudent(s);
                            setForceDelete(false);
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Student Add / Edit Modal */}
      <StudentModal
        isOpen={isStudentModalOpen}
        onClose={() => setIsStudentModalOpen(false)}
        studentToEdit={editingStudent}
        onSuccess={loadStudents}
      />

      {/* Photo Processing Modal */}
      <PhotoUploadManager
        isOpen={Boolean(processingStudent)}
        onClose={() => setProcessingStudent(null)}
        student={processingStudent}
        onProcessed={loadStudents}
      />

      {/* Delete Confirmation Modal */}
      {deletingStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-ink/30 backdrop-blur-sm"
            onClick={() => setDeletingStudent(null)}
          />
          <div className="relative bg-surface rounded-2xl p-6 max-w-sm w-full border border-bone shadow-lift space-y-4 z-10">
            <div className="w-10 h-10 rounded-full bg-accent-crimsonLight text-accent-crimson flex items-center justify-center mb-2">
              <AlertCircle className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-ink">
              حذف دانشجوی «{deletingStudent.full_name}»
            </h3>
            <p className="text-xs text-ink-muted leading-relaxed">
              آیا از حذف این دانشجو اطمینان دارید؟ پوشه عکس‌ها و امبدینگ مربوطه نیز حذف خواهد شد.
            </p>

            {forceDelete && (
              <div className="p-3 bg-accent-amberLight border border-accent-amberBorder rounded-lg text-xs text-accent-amber">
                این دانشجو دارای سوابق حضور است. با تایید مجدد، حضورهای او نیز حذف خواهند شد.
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDeletingStudent(null)}
                disabled={deleteLoading}
              >
                انصراف
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleDelete}
                loading={deleteLoading}
              >
                {forceDelete ? 'حذف اجباری (Force)' : 'حذف قطعی'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

