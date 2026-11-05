import React from 'react';
import { FaceItem, Student } from '../../api/types';

interface FaceOverlayProps {
  faces: FaceItem[];
  students: Student[];
  pendingStreaks: Record<string, number>;
  recordedList: string[];
}

export const FaceOverlay: React.FC<FaceOverlayProps> = ({
  faces,
  students,
  pendingStreaks,
  recordedList,
}) => {
  const studentMap = React.useMemo(() => {
    const map = new Map<string, string>();
    students.forEach((s) => map.set(s.student_id, s.full_name));
    return map;
  }, [students]);

  if (!faces || faces.length === 0) return null;

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden select-none">
      {faces.map((face, index) => {
        const [top, right, bottom, left] = face.box;

        // Coordinates as percentages of the video frame
        const topPct = top * 100;
        const heightPct = Math.max((bottom - top) * 100, 5);
        const widthPct = Math.max((right - left) * 100, 5);
        // Note: mirrored horizontally for user camera preview
        const leftPct = (1 - right) * 100;

        const isKnown = face.student_id !== null;
        const studentName = face.student_id
          ? studentMap.get(face.student_id) || face.student_id
          : 'ناشناس';

        const streak = face.student_id ? pendingStreaks[face.student_id] : 0;
        const isAlreadyRecorded = face.student_id
          ? recordedList.includes(face.student_id)
          : false;

        const borderColor = isKnown
          ? isAlreadyRecorded
            ? 'border-accent-emerald bg-accent-emerald/10'
            : 'border-accent-amber bg-accent-amber/10'
          : 'border-accent-crimson bg-accent-crimson/10';

        const tagColor = isKnown
          ? isAlreadyRecorded
            ? 'bg-accent-emerald text-white'
            : 'bg-accent-amber text-white'
          : 'bg-accent-crimson text-white';

        return (
          <div
            key={index}
            className={`absolute border-2 rounded-xl transition-all duration-150 ${borderColor}`}
            style={{
              top: `${topPct}%`,
              left: `${leftPct}%`,
              width: `${widthPct}%`,
              height: `${heightPct}%`,
            }}
          >
            {/* Header Tag with Name and Streak */}
            <div
              className={`absolute -top-7 right-0 px-2 py-0.5 rounded-md text-[11px] font-semibold whitespace-nowrap shadow-soft flex items-center gap-1.5 ${tagColor}`}
            >
              <span>{studentName}</span>

              {streak && streak > 0 && !isAlreadyRecorded ? (
                <span className="bg-black/30 px-1 rounded text-[10px] font-mono">
                  {streak}/3
                </span>
              ) : null}

              {isAlreadyRecorded && (
                <span className="text-[10px] bg-white/20 px-1 rounded">ثبت شد</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

