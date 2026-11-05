import React, { useState, useEffect } from 'react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Student, StudentCreate, StudentUpdate } from '../../api/types';
import { createStudent, updateStudent } from '../../api/students';
import { getErrorMessage } from '../../api/client';

interface StudentModalProps {
  isOpen: boolean;
  onClose: () => void;
  studentToEdit: Student | null;
  onSuccess: () => void;
}

export const StudentModal: React.FC<StudentModalProps> = ({
  isOpen,
  onClose,
  studentToEdit,
  onSuccess,
}) => {
  const [studentId, setStudentId] = useState('');
  const [fullName, setFullName] = useState('');
  const [major, setMajor] = useState('');
  const [term, setTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (studentToEdit) {
      setStudentId(studentToEdit.student_id);
      setFullName(studentToEdit.full_name);
      setMajor(studentToEdit.major || '');
      setTerm(studentToEdit.term || '');
    } else {
      setStudentId('');
      setFullName('');
      setMajor('');
      setTerm('');
    }
    setError(null);
  }, [studentToEdit, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (studentToEdit) {
        const payload: StudentUpdate = {
          full_name: fullName,
          major,
          term,
        };
        await updateStudent(studentToEdit.student_id, payload);
      } else {
        const payload: StudentCreate = {
          student_id: studentId,
          full_name: fullName,
          major,
          term,
        };
        await createStudent(payload);
      }
      onSuccess();
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={studentToEdit ? 'ویرایش مشخصات دانشجو' : 'ثبت دانشجوی جدید'}
      subtitle={
        studentToEdit
          ? `شماره دانشجویی: ${studentToEdit.student_id}`
          : 'مشخصات فردی و تحصیلی دانشجو را جهت ورود به سامانه وارد نمایید.'
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-lg bg-accent-crimsonLight border border-accent-crimsonBorder text-xs text-accent-crimson">
            {error}
          </div>
        )}

        {!studentToEdit && (
          <div>
            <label className="block text-xs font-semibold text-ink mb-1.5">
              شماره دانشجویی (لاتین/یکتا) <span className="text-accent-crimson">*</span>
            </label>
            <input
              type="text"
              required
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="مثال: 40111033302502"
              className="w-full px-3.5 py-2.5 rounded-lg border border-bone bg-canvas text-sm text-ink focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand/30 transition-all font-mono text-left"
              dir="ltr"
            />
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-ink mb-1.5">
            نام و نام خانوادگی <span className="text-accent-crimson">*</span>
          </label>
          <input
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="مثال: علی رضایی"
            className="w-full px-3.5 py-2.5 rounded-lg border border-bone bg-canvas text-sm text-ink focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand/30 transition-all"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-ink mb-1.5">
              رشته تحصیلی
            </label>
            <input
              type="text"
              value={major}
              onChange={(e) => setMajor(e.target.value)}
              placeholder="مهندسی کامپیوتر"
              className="w-full px-3.5 py-2.5 rounded-lg border border-bone bg-canvas text-sm text-ink focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand/30 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink mb-1.5">
              ترم تحصیلی
            </label>
            <input
              type="text"
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              placeholder="مثال: 4"
              className="w-full px-3.5 py-2.5 rounded-lg border border-bone bg-canvas text-sm text-ink focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand/30 transition-all"
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-bone/60">
          <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
            انصراف
          </Button>
          <Button type="submit" variant="primary" loading={loading}>
            {studentToEdit ? 'ذخیره تغییرات' : 'ثبت دانشجو'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

