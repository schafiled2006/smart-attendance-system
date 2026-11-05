import React, { useState } from 'react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Student, ProcessPhotosResponse } from '../../api/types';
import { triggerProcessPhotos } from '../../api/students';
import { getErrorMessage } from '../../api/client';
import { Camera, CheckCircle2, AlertTriangle, XCircle, FolderOpen } from 'lucide-react';

interface PhotoUploadManagerProps {
  isOpen: boolean;
  onClose: () => void;
  student: Student | null;
  onProcessed: () => void;
}

export const PhotoUploadManager: React.FC<PhotoUploadManagerProps> = ({
  isOpen,
  onClose,
  student,
  onProcessed,
}) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ProcessPhotosResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!student) return null;

  const handleProcess = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await triggerProcessPhotos(student.student_id);
      setResult(res);
      onProcessed();
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
      title={`پردازش تصاویر: ${student.full_name}`}
      subtitle={`شماره دانشجویی: ${student.student_id}`}
      maxWidth="lg"
    >
      <div className="space-y-5">
        {/* Step Guide Box */}
        <div className="p-4 rounded-xl bg-warmMuted/80 border border-bone text-xs space-y-2.5">
          <div className="flex items-center gap-2 font-semibold text-ink">
            <FolderOpen className="w-4 h-4 text-brand" />
            <span>مسیر قرارگیری تصاویر روی سرور:</span>
          </div>
          <code
            className="block p-2 rounded-lg bg-surface border border-bone font-mono text-[11px] text-ink text-left"
            dir="ltr"
          >
            known_faces/{student.student_id}/
          </code>
          <p className="text-ink-muted leading-relaxed">
            جهت استخراج دقیق امبدینگ، بین ۳ الی ۵ عکس واضح با نور طبیعی و فقط یک چهره درون این پوشه قرار دهید. سپس دکمه زیر را فشار دهید.
          </p>
        </div>

        {/* Current Status */}
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-surface border border-bone">
          <div className="text-xs">
            <span className="text-ink-muted">وضعیت فعلی امبدینگ: </span>
            <span className="font-semibold text-ink">
              {student.has_embedding ? 'ذخیره شده (آماده شناسایی)' : 'پردازش‌نشده'}
            </span>
          </div>
          <Badge variant={student.has_embedding ? 'present' : 'late'}>
            {student.photo_count} عکس ثبت‌شده
          </Badge>
        </div>

        {/* Error message */}
        {error && (
          <div className="p-3.5 rounded-lg bg-accent-crimsonLight border border-accent-crimsonBorder text-xs text-accent-crimson flex items-start gap-2">
            <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Processing Result Display */}
        {result && (
          <div className="p-4 rounded-xl bg-surface border border-bone space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-ink">
              {result.embedding_saved ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-accent-emerald" />
                  <span className="text-accent-emerald">پردازش موفقیت‌آمیز بود و امبدینگ ذخیره شد.</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 text-accent-amber" />
                  <span className="text-accent-amber">امبدینگ به دلیل کسری عکس‌های معتبر ذخیره نشد.</span>
                </>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs text-ink-muted pt-2 border-t border-bone/60">
              <div>عکس‌های پذیرفته‌شده: <strong className="text-ink font-mono">{result.accepted}</strong></div>
              <div>عکس‌های ردشده: <strong className="text-ink font-mono">{result.rejected.length}</strong></div>
            </div>

            {/* List of Rejected Files */}
            {result.rejected.length > 0 && (
              <div className="mt-2 space-y-1">
                <span className="text-[11px] font-semibold text-accent-crimson">موارد نامعتبر:</span>
                {result.rejected.map((item, idx) => (
                  <div key={idx} className="text-[11px] text-ink-muted bg-warmMuted p-1.5 rounded border border-bone flex justify-between">
                    <span className="font-mono">{item.file}</span>
                    <span>{item.reason === 'no_face' ? 'چهره‌ای یافت نشد' : item.reason === 'multiple_faces' ? 'چندین چهره شناسایی شد' : item.reason}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-bone/60">
          <Button variant="outline" onClick={onClose}>
            بستن
          </Button>
          <Button
            variant="primary"
            icon={<Camera className="w-4 h-4" />}
            onClick={handleProcess}
            loading={loading}
          >
            پردازش تصاویر و ساخت امبدینگ
          </Button>
        </div>
      </div>
    </Modal>
  );
};

