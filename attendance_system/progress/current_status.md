# وضعیت فعلی پروژه (Backend Only)

**آخرین به‌روزرسانی:** 2026-10-24

** آخرین استیج تکمیل‌شده:** هیچکدام

**استیج فعلی:** استیج ۱ — ساخت ساختار پروژه

**فایل‌های ساخته‌شده تا الان:**
- backend/__init__.py
- backend/config.py
- backend/requirements.txt
- backend/.gitignore
- progress/current_status.md

**تست شده؟** خیر

**تصمیم‌های گرفته‌شده:**
- FastAPI + SQLite
- فیلدهای دانشجو: student_id, full_name, major, term
- یک درس در نسخه فعلی
- تأخیر با آستانه ذخیره‌شده روی جلسه (پیش‌فرض ۱۰ دقیقه)
- اکسل = لیست کامل با وضعیت حاضر/تأخیر/غایب
- ثبت عکس دستی در known_faces/<student_id>/
- چهره ناشناس فقط لاگ

**باگ‌های شناخته‌شده:**
- پروژه yeni initialized، تست‌های دستی نیاز دارد

**دستور بعدی:** شروع استیج ۲ —database.py + models.py + schemas.py