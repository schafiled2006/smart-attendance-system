# BACKEND ONLY CONTEXT
# سیستم حضور و غیاب هوشمند — فقط بک‌اند
این فایل را کامل به مدل بده. مدل موظف است هر بار قبل از هر کاری آن را بخوان.

---
## قوانین اجباری برای مدل (هر بار قبل از شروع کار)

1. **اول این فایل را کامل بخوان.**
2. بلافاصله فایل `progress/current_status.md` را بخوان و ببین آخرین وضعیت چیست.
3. اگر کار قبلی نصفه مانده، **حتماً از همان نقطه ادامه بده** و از اول شروع نکن.
4. بعد از اتمام هر استیج یا هر زمان که کار را متوقف می‌کنی، فایل `progress/current_status.md` را آپدیت کن و این موارد را بنویس:
      - آخرین استیج تکمیل‌شده
      - استیج فعلی
      - فایل‌هایی که ساخته یا تغییر کرده‌اند
      - آیا تست شده یا نه
      - مشکل یا نکته باقی‌مانده
      - دستور بعدی
5. بدون اجازهٔ صریح کاربر، تکنولوژی، ساختار پوشه‌ها یا امsigها توابع را تغییر نده.
6. فایل‌های استیج‌های قبلی فقط برای رفع باگ دست بخورند و در `current_status.md` ثبت شوند.
7. هر بار فقط **یک استیج** انجام بده و بعد از آن منتظر تأیید کاربر بمان (مگر اینکه کاربر صریحاً بگوید همه را پشت سر هم انجام بده).

---

## هدف پروژه (فقط بک‌اند)

ساخت بک‌اند کامل و آفلاین برای سامانه حضور و غیاب هوشمند با تشخیص چهره.

- زبان: Python 3.10 یا 3.11 (ویندوز)
- فریم‌ورک API: **FastAPI**
- دیتابیس: **SQLite**
- تشخیص چهره: `face_recognition` + OpenCV
- خروجی گزارش: Excel (openpyxl / pandas)
- تعداد دانشجو: حدود ۴۰ تا ۵۰ نفر
- یک کلاس/درس در نسخه فعلی
- تست اولیه با دوربین لپ‌تاپ و دوربین گوشی (IP Webcam)

فرانت‌اند جداگانه با React/Vite نوشته شده و این بک‌اند باید API مناسب برای آن فراهم کند.  
ریپوی فرانت فعلی (`HosinNiazi/Smart-Attendance-System`) بعداً حذف/جایگزین می‌شود؛ بنابراین بک‌اند را مستقل و تمیز بساز.

---

## تصمیم‌های قطعی (تغییر نده)

| موضوع | تصمیم |
|-------|--------|
| سیستم‌ operativo | ویندوز |
| معماری | FastAPI + SQLite (بدون Node و بدون SQL Server) |
| احراز هویت | فعلاً شبیه‌سازی‌شده (هر نام کاربری وارد شود). بعداً اضافه می‌شود. |
| دانشجو | فقط: شماره دانشجویی، نام و نام‌خانوادگی، رشته، ترم |
|درس | یک درس در نسخه فعلی (جدول courses وجود داشته باشد) |
| ثبت عکس | دستی: عکس‌ها در `known_faces/<student_id>/` قرار می‌گیرند و یک endpoint/دستور آن‌ها را پردازش می‌کند |
| چهره ناشناس | فقط در لاگ ثبت شود، حضور ثبت نشود |
| وضعیت حضور | حاضر / تأخیر / غایب |
| محاسبه تأخیر | بر اساس `late_threshold_minutes` ذخیره‌شده روی همان جلسه (پیش‌فرض ۱۰ دقیقه) |
| گزارش اکسل | لیست کامل کلاس با ستون وضعیت (حاضر/تأخیر/غایب) + ساعت ورود |
| تاریخ | در دیتابیس میلادی (ISO) ذخیره شود؛ در اکسل و پاسخ‌های API تاریخ شمسی هم نمایش داده شود |
| جلوگیری از تکرار | در سطح دیتابیس با UNIQUE(session_id, student_id) و در_logic سرویس |

---

## ساختار پروژه (بک‌اند)

```text
attendance_system/
├── backend/
│   ├── __init__.py
│   ├── main.py                 # نقطه ورود FastAPI
│   ├── config.py               # تنظیمات مرکزی
│   ├── database.py             # اتصال SQLite + init_db
│   ├── models.py               # مدل‌های SQLAlchemy یا dataclass + schema
│   ├── schemas.py              # Pydantic models برای request/response
│   ├── routers/
│   │   ├── students.py
│   │   ├── courses.py
│   │   ├── sessions.py
│   │   ├── attendance.py
│   │   ├── reports.py
│   │   └── recognition.py      # endpointهای تشخیص چهره
│   ├── services/
│   │   ├── enrollment.py       # ثبت‌نام + میانگین embedding
│   │   ├── session_manager.py
│   │   ├── attendance_service.py
│   │   ├── report_service.py
│   │   └── face_engine.py      # بارگذاری embeddingها + مقایسه
│   └── utils.py
│
├── known_faces/                # known_faces/<student_id>/*.jpg
├── embeddings/                 # فایل‌های .npy یا .pkl
├── reports/                    # خروجی اکسل
├── logs/                       # app.log
├── data/
│   └── attendance.db
│
├── progress/
│   └── current_status.md
│
├── PROJECT_CONTEXT.md          # همین فایل یا کپی از آن
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ساختار دیتابیس (قطعی)

### جدول students
- id INTEGER PRIMARY KEY AUTOINCREMENT
- student_id TEXT UNIQUE NOT NULL          -- شماره دانشجویی
- full_name TEXT NOT NULL
- major TEXT                              -- رشته
- term TEXT                               -- ترم
- embedding_file TEXT                     -- مسیر فایل embedding
- created_at TEXT

### جدول courses
- id INTEGER PRIMARY KEY AUTOINCREMENT
- course_code TEXT UNIQUE
- title TEXT NOT NULL
- teacher TEXT
- created_at TEXT

(در نسخه فعلی فقط یک ردیف کافی است.)

### جدول sessions
- session_id TEXT PRIMARY KEY
- course_id INTEGER
- start_time TEXT NOT NULL                 -- ISO datetime
- end_time TEXT
- status TEXT NOT NULL                     -- active / closed
- late_threshold_minutes INTEGER DEFAULT 10
- note TEXT
- created_at TEXT

### جدول attendance
- id INTEGER PRIMARY KEY AUTOINCREMENT
- session_id TEXT NOT NULL
- student_id TEXT NOT NULL
- full_name TEXT
- status TEXT NOT NULL                    -- present / late / absent
- check_in_time TEXT                      -- فقط برای present و late
- confidence REAL
- camera_source TEXT                      -- laptop / phone / manual
- created_at TEXT
- UNIQUE(session_id, student_id)

---

## قراردادهای مهم توابع/سرویس‌ها

### enrollment
- `add_student(student_id, full_name, major, term, image_folder) -> dict`
  - حداقل ۳ و حداکثر ۵ عکس از پوشه را بخواند
  - میانگین embedding را محاسبه و در `embeddings/` ذخیره کند
  - رکورد را در students بنویسد
- `rebuild_embeddings()` برای بازسازی همه

### session_manager
- `start_session(course_id, late_threshold_minutes=10, note="") -> session_id`
- `close_session(session_id=None) -> bool`
- `get_active_session() -> dict | None`

### attendance_service
- `log_attendance(student_id, confidence, camera_source="laptop") -> dict`
  - اگر جلسه فعال نباشد → خطا
  - اگر قبلاً در این session ثبت شده → پیام «قبلاً ثبت شده»
  - زمان فعلی را با start_time + late_threshold مقایسه کند:
    - قبل از آستانه → status = present
    - بعد از آستانه → status = late
- `mark_absent(session_id, student_id)` (برای ثبت دستی)
- `process_recognition_result(recognized_list, camera_source) -> list`
  - تنها نقطه اتصال بین موتور تشخیص چهره و ثبت حضور
  - recognized_list = [{"student_id", "full_name", "confidence"}, ...]

### face_engine
- بارگذاری همه embeddingهای شناخته‌شده در حافظه
- `recognize_frame(frame_bgr) -> list[dict]`
  - رفتار با چندین چهره: همه را برگرداند
  - چهره ناشناس: در لاگ بنویسد و در خروجی نیاورد
  - فقط وقتی قبول کند که فاصله نزدیک‌ترین با فاصله دومین نزدیک‌ترین جدا باشد (margin)
  - tolerance فقط از config خوانده شود (۰.۵۰ تا ۰.۶۰)

---

## Endpointهای پیشنهادی FastAPI (حداقلی)

```
POST   /api/students                 # ثبت دانشجو (متادیتا)
POST   /api/students/{id}/enroll     # پردازش عکس‌های known_faces/<id>
GET    /api/students
DELETE /api/students/{id}

GET    /api/courses
POST   /api/courses

POST   /api/sessions/start
POST   /api/sessions/{id}/close
GET    /api/sessions/active
GET    /api/sessions/active

POST   /api/attendance/recognize     # دریافت نتیجه تشخیص یا فریم
POST   /api/attendance/manual        # ثبت دستی حاضر/غایب
GET    /api/attendance/session/{id}

GET    /api/reports/session/{id}/excel
GET    /api/reports/daily

GET    /api/health
```

CORS برای فرانت (localhost:5173) فعال باشد.

---

## تنظیمات (config.py)

```python
FACE_TOLERANCE = 0.55
FACE_MODEL = "hog"                 # hog برای CPU ویندوز
PROCESS_EVERY_N_FRAMES = 2
DEFAULT_LATE_THRESHOLD = 10
PHONE_CAMERA_URL = "http://192.168.x.x:8080/video"  # قابل تغییر
DB_PATH = "data/attendance.db"
```

---

## ترتیب استیج‌های بک‌اند (اجباری)

### استیج ۱ — ساختار progetto و فایل‌های پایه
- ساخت تمام فولدرها
- requirements.txt
- config.py
- .gitignore (شامل known_faces/, embeddings/, data/, logs/)
- progress/current_status.md
- PROJECT_CONTEXT.md (همین محتوا)

### استیج ۲ — database.py + models.py + schemas.py
- ایجاد سه/چهار جدول بالا
- init_db()
-	test ساخت دیتابیس

### استیج ۳ — enrollment.py + face_engine (بخش بارگذاری)
- ثبت دانشجو از پوشه عکس
- میانگین embedding
-	test با ۳ نفر نمونه

### استیج ۴ — session_manager.py
- start / close / get_active
- ذخیره late_threshold روی جلسه

### استیج ۵ — attendance_service.py
- log_attendance با محاسبه present/late
- جلوگیری از تکرار
- process_recognition_result

### استیج ۶ — report_service.py
- خروجی اکسل کامل با وضعیت و تاریخ شمسی

### استیج ۷ — routers + main.py (FastAPI)
- تمام endpointها
- CORS
-	test با Swagger (/docs)

### استیج ۸ — recognition endpoint + تست دوربین
- اتصال به دوربین لپ‌تاپ و IP Webcam
-	test کامل چرخه: تشخیص → ثبت → گزارش

### استیج ۹ — تست نهایی و رفع باگ
-	test با چند نفر واقعی
- بررسی ثبت تکراری، تأخیر، غایب، اکسل

---

## کارهایی که نباید بکyni

- Flask یا Django اضافه نکن.
- SQL Server یا PostgreSQL استفاده نکن.
- Node.js یا Express ننویس.
- ساختار پوشه‌ها را خودسرانه عوض نکن.
- از استیج‌ها جلو نزن.
- برای هر دانشجو فقط یک عکس قبول نکن (حداقل ۳).
- tolerance را هاردکد نکن؛ فقط از config بخوان.
- چهره ناشناس را به عنوان دانشجو ثبت نکن.
- تاریخشمسی را در دیتابیس به عنوان کلید اصلی استفاده نکن (فقط نمایش).
- بدون آپدیت current_status.md کار را رها نکن.

---

## نکات نصب روی ویندوز (حتماً در README بیاید)

```text
Python 3.10 یا 3.11 توصیه می‌شود.
pip install cmake
# اگر dlib نصب نشد، wheel آماده از:
# https://github.com/sachadee/Dlib
pip install dlib
pip install -r requirements.txt
```

requirements.txt پیشنهادی:
```
fastapi
uvicorn[standard]
python-multipart
opencv-python
face_recognition
numpy
pillow
pandas
openpyxl
sqlalchemy
pydantic
jdatetime          # برای تاریخ شمسی
```