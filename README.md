# سیستم حضور و غیاب با تشخیص چهره — بک‌اند

بک‌اند آفلاین و CPU-only برای ثبت حضور با تشخیص چهره، با API مبتنی بر FastAPI،
دیتابیس SQLite و گزارش اکسل فارسی راست‌به‌چپ با تاریخ شمسی.

> این پروژه در استیج ۱ (ساختار پایه) است. ماژول‌های سرویس فعلاً خالی‌اند و در
> استیج‌های بعدی پیاده‌سازی می‌شوند.

## پیش‌نیازها

- ویندوز ۶۴ بیتی
- Python 3.11 (۶۴ بیتی)
- فقط CPU؛ نیازی به GPU/CUDA نیست
- در زمان اجرا به اینترنت یا سرویس ابری نیاز نیست

## نصب

```powershell
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install face_recognition --no-deps
```

`face_recognition` عمداً با `--no-deps` نصب می‌شود تا pip به‌جای استفاده از
wheel آمادهٔ `dlib-bin`، `dlib` را از سورس نسازد. اگر `dlib-bin` نصب نشد،
راه جایگزین نصب CMake و Visual Studio Build Tools و سپس `dlib` است.

اگر import خطای `pkg_resources` داد، `setuptools` را به نسخه‌ای که این ماژول
را دارد پایین بیاورید.

## بررسی محیط

```powershell
venv\Scripts\python.exe check_env.py
```

این اسکریپت همهٔ importها، نسخهٔ NumPy (باید کمتر از ۲ باشد)، منطقهٔ زمانی
`Asia/Tehran`، پوشه‌ها و اجرای `face_recognition.face_encodings` روی اولین
عکس موجود در `tests/data/` را بررسی می‌کند.

## تست‌ها

```powershell
venv\Scripts\python.exe -m pytest -v
```

تست‌های هر استیج در `tests/test_stageN_*.py` قرار می‌گیرند. تست‌هایی که به
عکس واقعی نیاز دارند، در صورت نبودن `tests/data/` رد (skip) می‌شوند.

## تنظیمات

همهٔ مقادیر در `backend/config.py` هستند. مسیر دیتابیس با متغیر محیطی
`ATTENDANCE_DB` قابل تغییر است (برای تست‌ها):

```powershell
$env:ATTENDANCE_DB = "$env:TEMP\attendance_test.db"
```

## ساختار

```text
backend/
├── config.py, errors.py, utils.py, models.py, database.py
├── recognition.py, enrollment.py, session_manager.py
├── attendance_service.py, report_service.py
└── api/app.py, api/schemas.py
known_faces/<student_id>/   # عکس‌های دستی دانشجو
embeddings/<student_id>.npy # میانگین انکودینگ چهره
reports/                    # خروجی اکسل
logs/app.log                # لاگ برنامه
data/attendance.db          # دیتابیس SQLite
tests/                      # تست‌های هر استیج
progress/current_status.md  # وضعیت جلسه کاری
```

پوشه‌های `known_faces/`، `embeddings/`، `data/`، `reports/`، `logs/` و
`tests/data/` حاوی دادهٔ حساس هستند و در `.gitignore` قرار دارند.
