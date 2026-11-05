import React, { useEffect, useState } from 'react';
import { Settings, ShieldCheck, Cpu, HardDrive, Database, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Badge } from '../../components/ui/Badge';
import { checkSystemHealth } from '../../api/reports';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<string>('بررسی...');
  const [online, setOnline] = useState(false);

  useEffect(() => {
    checkSystemHealth()
      .then((res) => {
        setHealth(res.status);
        setOnline(true);
      })
      .catch(() => {
        setHealth('قطع ارتباط');
        setOnline(false);
      });
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-xl font-bold text-ink">تنظیمات و وضعیت سامانه</h2>
        <p className="text-xs text-ink-muted mt-1">
          بررسی معماری پردازش تصویر، پایگاه‌داده و شرایط عملکرد آفلاین سامانه
        </p>
      </div>

      <div className="bg-surface rounded-2xl border border-bone p-6 shadow-soft space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-bone/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-warmMuted flex items-center justify-center text-ink">
              <ShieldCheck className="w-5 h-5 text-brand" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-ink">وضعیت اتصال به وب‌سرویس FastAPI</h3>
              <p className="text-[11px] text-ink-muted">نشانی سرور: http://127.0.0.1:8000</p>
            </div>
          </div>

          <Badge variant={online ? 'present' : 'absent'} pulse={online}>
            {online ? 'ارتباط برقرار است (OK)' : 'خطای اتصال'}
          </Badge>
        </div>

        {/* System Specs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-warmMuted/60 border border-bone space-y-1.5">
            <div className="flex items-center gap-2 font-semibold text-ink">
              <Cpu className="w-4 h-4 text-brand" />
              <span>موتور هوش مصنوعی و تشخیص</span>
            </div>
            <p className="text-ink-muted">مدل HOG (پردازش روی CPU بدون نیاز به گرافیک)</p>
            <div className="text-[11px] text-ink-muted font-mono mt-1">
              Tolerance: 0.55 | Margin: 0.05
            </div>
          </div>

          <div className="p-4 rounded-xl bg-warmMuted/60 border border-bone space-y-1.5">
            <div className="flex items-center gap-2 font-semibold text-ink">
              <Database className="w-4 h-4 text-brand" />
              <span>پایگاه‌داده رابطه‌ای</span>
            </div>
            <p className="text-ink-muted">SQLite ۳ داخلی با رعایت کلیدهای خارجی و ایندکس یکتا</p>
            <div className="text-[11px] text-ink-muted font-mono mt-1">
              data/attendance.db
            </div>
          </div>

          <div className="p-4 rounded-xl bg-warmMuted/60 border border-bone space-y-1.5">
            <div className="flex items-center gap-2 font-semibold text-ink">
              <HardDrive className="w-4 h-4 text-brand" />
              <span>حفظ حریم خصوصی و پردازش آفلاین</span>
            </div>
            <p className="text-ink-muted">
              تمام تصاویر و بردارهای چهره به صورت محلی ذخیره شده و هیچ دیتایی به اینترنت ارسال نمی‌شود.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-warmMuted/60 border border-bone space-y-1.5">
            <div className="flex items-center gap-2 font-semibold text-ink">
              <CheckCircle2 className="w-4 h-4 text-accent-emerald" />
              <span>آستانه فریم‌های متوالی</span>
            </div>
            <p className="text-ink-muted">
              حداقل ۳ فریم پشت سر هم برای جلوگیری از ثبت اشتباه یا عبور لحظه‌ای چهره.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

