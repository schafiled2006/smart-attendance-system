# Complete Smart Attendance System Context & Codebase Export

> Single consolidated export file containing full project specification, architecture, current status, and complete source code.

## Table of Contents

- [Specification & Architecture (`PROJECT_CONTEXT.md`)](#project_context-md)
- [Current Status & Progress (`progress/current_status.md`)](#progress-current_status-md)
- [Rules & Operational Guidelines (`AGENTS.md`)](#agents-md)
- [Environment Setup & Verification (`check_env.py`)](#check_env-py)
- [Configuration & Constants (`backend/config.py`)](#backend-config-py)
- [Custom Exceptions (`backend/errors.py`)](#backend-errors-py)
- [Utilities & Helpers (`backend/utils.py`)](#backend-utils-py)
- [Database Models & Dataclasses (`backend/models.py`)](#backend-models-py)
- [Database Connection & Initialization (`backend/database.py`)](#backend-database-py)
- [Face Recognition Core (`backend/recognition.py`)](#backend-recognition-py)
- [Student Enrollment Service (`backend/enrollment.py`)](#backend-enrollment-py)
- [Session Management Service (`backend/session_manager.py`)](#backend-session_manager-py)
- [Attendance Core Logic (`backend/attendance_service.py`)](#backend-attendance_service-py)
- [Excel Report Generator (`backend/report_service.py`)](#backend-report_service-py)
- [CLI Formatter (Boxes & Tables) (`backend/cli_format.py`)](#backend-cli_format-py)
- [FastAPI Pydantic Schemas (`backend/api/schemas.py`)](#backend-api-schemas-py)
- [FastAPI App Endpoints (`backend/api/app.py`)](#backend-api-app-py)
- [Management CLI Tool (`manage.py`)](#manage-py)
- [Live Camera & Video Recognition Test (`main_test.py`)](#main_test-py)
- [Requirements (`requirements.txt`)](#requirements-txt)
- [Pytest Configuration (`pytest.ini`)](#pytest-ini)
- [Git Ignore Configuration (`.gitignore`)](#-gitignore)

---

<a id="project_context-md"></a>
## Specification & Architecture (`PROJECT_CONTEXT.md`)

```markdown
PROJECT CONTEXT: بک‌اند سیستم حضور و غیاب با تشخیص چهره

# ۰. قوانین اجباری برای مدل

- هر جلسه کاری، اول این فایل را کامل بخوان و بعد `progress/current_status.md` را.
- اگر استیجی نصفه مانده، از همان نقطه ادامه بده و از اول شروع نکن.
- در هر جلسه فقط یک استیج انجام بده. بعد از اتمام، تست‌های همان استیج را اجرا کن. فقط وقتی همه پاس شدند استیج را کامل اعلام کن، `current_status.md` را آپدیت کن و متوقف شو تا تأیید بگیری.
- بدون اجازه صریح، تکنولوژی، ساختار پوشه‌ها، نام جدول‌ها و ستون‌ها و امضای توابع این سند را تغییر نده. اگر تغییری لازم می‌دانی، اول در `current_status.md` بنویس و بپرس.
- فایل‌های استیج‌های قبلی فقط برای رفع باگ دست بخورند و تغییر در بخش «باگ‌های شناخته‌شده» ثبت شود.
- فقط ابزار و کتابخانه رایگان و متن‌باز. در زمان اجرا هیچ سرویس ابری یا اینترنتی نباید لازم باشد.
- چیزی را که در این سند نیست حدس نزن و بپرس.
- نام‌ها و کد به انگلیسی هستند. پیام‌های خطای کاربرمحور (که به API یا کاربر می‌رسند) فارسی‌اند.

# ۱. هدف و محیط

- سیستم حضور و غیاب خودکار و آفلاین با تشخیص چهره، برای یک کلاس با ۴۰ تا ۵۰ دانشجو.
- خروجی گزارش اکسل فارسی راست‌به‌چپ با تاریخ شمسی است.
- محیط: ویندوز، Python 3.11 (۶۴ بیتی)، venv، دستورات PowerShell.
- سخت‌افزار: فقط CPU. از GPU و CUDA استفاده نمی‌شود و تشخیص چهره با `model="hog"` انجام می‌شود.
- فرانت‌اند (React) جداگانه ساخته می‌شود و در این کانتکست نیست. بک‌اند فقط API می‌دهد.

# ۲. تکنولوژی‌ها و نصب

- کتابخانه‌ها: `opencv-python`، `numpy<2`، `pillow`، `dlib-bin`، `face_recognition`، `face_recognition_models`، `Click`، `openpyxl`، `jdatetime`، `tzdata` (برای zoneinfo روی ویندوز)، `fastapi`، `uvicorn`، `python-multipart`، `pytest`، `httpx`.
- `pandas` لازم نیست. اکسل مستقیم با `openpyxl` ساخته می‌شود.
- دیتابیس: `sqlite3` داخلی پایتون.

دستورات نصب:

```powershell
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install face_recognition --no-deps
```

- دلیل `--no-deps`: وقتی `dlib-bin` نصب است، `face_recognition` سعی می‌کند `dlib` را از سورس بسازد. اگر نصب `dlib-bin` جواب نداد، جایگزین آن CMake و Visual Studio Build Tools است.
- اگر هنگام import خطای `pkg_resources` آمد، `setuptools` را به نسخه‌ای که آن را دارد پایین بیاور.
- بعد از نصب موفق در استیج ۱، با `pip freeze` نسخه‌ها را در `requirements.txt` قفل کن.

# ۳. ساختار پروژه

```text
attendance_system/
├── backend/
│   ├── __init__.py
│   ├── config.py              # همه تنظیمات و مسیرها (تنها منبع مقادیر)
│   ├── errors.py              # خطاهای سفارشی
│   ├── utils.py               # ارقام، زمان، شمسی، لاگ
│   ├── models.py              # SQL جداول + dataclassها
│   ├── database.py            # اتصال و init_db
│   ├── recognition.py         # انکود چهره، کش embedding، مقایسه
│   ├── enrollment.py          # ثبت دانشجو + پردازش عکس‌ها
│   ├── session_manager.py     # مدیریت جلسه
│   ├── attendance_service.py  # ثبت حضور، محاسبه وضعیت، process_recognition_result
│   ├── report_service.py      # خروجی اکسل
│   └── api/
│       ├── __init__.py
│       ├── app.py             # FastAPI (فقط پوسته نازک، بدون منطق کسب‌وکار)
│       └── schemas.py
├── known_faces/<student_id>/  # عکس‌های دستی هر دانشجو (نام پوشه فقط شماره ASCII)
├── embeddings/<student_id>.npy
├── reports/
├── logs/app.log
├── data/attendance.db
├── tests/
├── progress/current_status.md
├── PROJECT_CONTEXT.md
├── .clinerules
├── .gitignore
├── check_env.py               # بررسی نصب کتابخانه‌ها
├── manage.py                  # دستورهای CLI غیرتعاملی (argparse)
├── main_test.py               # تست دوربین
├── requirements.txt
└── README.md
```

# ۴. مقادیر config.py

همه مسیرها با `pathlib` و نسبت به ریشه پروژه ساخته می‌شوند. مسیر دیتابیس با متغیر محیطی `ATTENDANCE_DB` قابل override است تا تست‌ها دیتابیس موقت بسازند.

```python
FACE_TOLERANCE = 0.55            # باید بین 0.5 و 0.6 بماند
MATCH_MARGIN = 0.05              # فاصله مجاز دومین نزدیک‌ترین از نزدیک‌ترین
MIN_PHOTOS = 3
MAX_PHOTOS = 5
REQUIRED_CONSECUTIVE_FRAMES = 3
DEFAULT_LATE_AFTER_MINUTES = 10
DETECTION_MODEL = "hog"
FRAME_MAX_WIDTH = 640            # فریم قبل از تشخیص کوچک می‌شود
PHOTO_MAX_SIDE = 1280
TIMEZONE = "Asia/Tehran"
CAMERA_SOURCE = 0                # یا "http://<ip>:8080/video" برای IP Webcam
PROCESS_EVERY_N_FRAMES = 3       # فقط برای main_test.py
API_HOST = "127.0.0.1"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:5173"]
```

# ۵. دیتابیس (قطعی، بدون تغییر)

```sql
CREATE TABLE IF NOT EXISTS students (
  student_id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  major TEXT NOT NULL DEFAULT '',
  term TEXT NOT NULL DEFAULT '',
  embedding_path TEXT,                 -- مسیر نسبی .npy ؛ NULL یعنی هنوز پردازش نشده
  photo_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  teacher TEXT NOT NULL DEFAULT '',
  room TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL REFERENCES courses(id),
  started_at TEXT NOT NULL,
  ended_at TEXT,
  late_after_minutes INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','closed'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_one_active_session
  ON sessions(status) WHERE status = 'active';

CREATE TABLE IF NOT EXISTS attendance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL REFERENCES sessions(id),
  student_id TEXT NOT NULL REFERENCES students(student_id),
  checked_at TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('face','manual')),
  confidence REAL,                     -- فاصله چهره؛ برای manual برابر NULL
  UNIQUE (session_id, student_id)
);
```

- هر اتصال با `PRAGMA foreign_keys=ON` و `row_factory = sqlite3.Row` باز می‌شود.
- `init_db()` باید idempotent باشد و اگر جدول `courses` خالی بود، یک درس پیش‌فرض («کلاس اصلی») بسازد.
- فقط ردیف «حاضر» ذخیره می‌شود. تأخیر و غیبت ذخیره نمی‌شوند و همیشه محاسبه می‌شوند.
- فهرست کلاس (roster) همه ردیف‌های جدول `students` است، چون فعلاً یک کلاس داریم.

# ۶. قواعد زمان و وضعیت

- همه زمان‌ها به‌صورت متن ISO 8601 با منطقه `Asia/Tehran` ذخیره می‌شوند، مثلاً `2026-10-24T10:05:00+03:30`. از `zoneinfo` استفاده کن.
- نمایش شمسی فقط در خروجی اکسل و در فیلدهای نمایشی API با `jdatetime` و ارقام ASCII انجام می‌شود. دیتابیس شمسی ندارد.
- `utils.normalize_digits()` ارقام فارسی و عربی را به ASCII تبدیل می‌کند. همه ورودی‌های `student_id` قبل از هر کاری از آن رد می‌شوند.
- وضعیت هر دانشجو در یک جلسه:
  - `present`: رکورد دارد و `checked_at - started_at <= late_after_minutes`
  - `late`: رکورد دارد و از آن حد گذشته
  - `absent`: رکورد ندارد
- برچسب‌های فارسی: حاضر، تأخیر، غایب.
- `late_after_minutes` هنگام شروع جلسه روی همان جلسه ذخیره می‌شود و بعداً تغییر نمی‌کند.
- تغییر دستی حضور (افزودن یا حذف) فقط روی جلسه فعال مجاز است. جلسه بسته‌شده قابل تغییر نیست.

# ۷. قواعد تشخیص چهره

- هر دانشجو ۳ تا ۵ عکس در `known_faces/<student_id>/` دارد (حداقل ۳، حداکثر ۵).
- هر عکس باید دقیقاً یک چهره داشته باشد. عکس‌های بدون چهره یا با چند چهره رد می‌شوند و دلیلشان گزارش می‌شود.
- جهت عکس با `ImageOps.exif_transpose` اصلاح می‌شود. ضلع بزرگ‌تر عکس به `PHOTO_MAX_SIDE` کوچک می‌شود.
- embedding دانشجو میانگین انکودینگ‌های ۱۲۸بعدی عکس‌های معتبر است و در `embeddings/<student_id>.npy` ذخیره می‌شود.
- اگر embedding جدید به embedding دانشجوی دیگری نزدیک‌تر از `FACE_TOLERANCE` بود، فقط هشدار در لاگ و در خروجی ثبت می‌شود و ثبت متوقف نمی‌شود.
- مقایسه در `recognition.py` انجام می‌شود:
  - بردارهای همه دانشجویان در یک ماتریس کش در حافظه نگه داشته می‌شوند و بعد از هر پردازش یا حذف دانشجو `reload_embeddings()` صدا زده می‌شود.
  - اگر دانشجویی نباشد، نتیجه `None` است.
  - تطابق فقط وقتی پذیرفته می‌شود که نزدیک‌ترین فاصله `<= FACE_TOLERANCE` باشد و فاصله دومین نزدیک‌ترین از اولی حداقل `MATCH_MARGIN` بیشتر باشد (اگر فقط یک دانشجو داریم، شرط margin حذف می‌شود).
  - چند چهره در یک فریم، هر کدام مستقل پردازش می‌شوند.
  - چهره ناشناس نادیده گرفته می‌شود و فقط در `logs/app.log` می‌آید (بدون ذخیره تصویر).
  - ثبت حضور فقط بعد از دیده‌شدن در `REQUIRED_CONSECUTIVE_FRAMES` فریم متوالی انجام می‌شود. اگر دانشجویی در یک فریم پردازش‌شده دیده نشود، شمارنده‌اش صفر می‌شود. شمارنده در حافظه نگه داشته می‌شود (در `StreakTracker`) و با بسته‌شدن جلسه پاک می‌شود.
  - جلوگیری از تکرار دو لایه دارد: قید `UNIQUE(session_id, student_id)` در دیتابیس و بررسی در `log_attendance`.

# ۸. قرارداد توابع (امضا ثابت است)

**`errors.py`**: کلاس پایه `AppError(code, message_fa)` و زیرکلاس‌های `StudentExistsError`، `StudentNotFoundError`، `StudentHasAttendanceError`، `NoFaceError`، `MultipleFacesError`، `NotEnoughPhotosError`، `SessionAlreadyActiveError`، `NoActiveSessionError`، `SessionNotFoundError`، `SessionClosedError`، `InvalidInputError`، `ReportEmptyError`.

**`utils.py`**:

- `normalize_digits(text: str) -> str`
- `now_tehran() -> datetime`
- `to_iso(dt) -> str`
- `parse_iso(s) -> datetime`
- `to_jalali_str(dt_or_iso, with_time=False) -> str`
- `setup_logging() -> None`: `RotatingFileHandler` روی `logs/app.log`، حداکثر ۱ مگابایت × ۳ فایل، UTF-8.

**`database.py`**: `get_connection() -> sqlite3.Connection`، `init_db() -> None`

**`models.py`**: رشته‌های SQL بالا و dataclassهای `Student`، `Course`، `Session`، `AttendanceRecord`.

**`recognition.py`**:

- `load_image_rgb(path) -> np.ndarray`
- `encode_single_face(rgb) -> np.ndarray`  # shape (128,); NoFaceError / MultipleFacesError
- `reload_embeddings() -> int`  # تعداد دانشجوی لودشده
- `match_encoding(enc) -> tuple[str | None, float]`  # تابع خالص و قابل تست با داده مصنوعی
- `recognize_frame(bgr) -> list[dict]`  # هر عضو: `{"student_id": str|None, "distance": float, "box": (top,right,bottom,left)}`، مختصات box نسبی بین ۰ و ۱ است

**`enrollment.py`**:

- `add_student(student_id, full_name, major="", term="") -> dict`  # پوشه `known_faces/<id>` را هم می‌سازد
- `process_photos(student_id) -> dict`  # `{"accepted": int, "rejected": [{"file","reason"}], "warnings": [...], "embedding_saved": bool}`
- `get_student(student_id) -> dict | None`
- `list_students() -> list[dict]`  # شامل فیلد `has_embedding`
- `update_student(student_id, full_name=None, major=None, term=None) -> dict`
- `delete_student(student_id, force=False) -> bool`  # اگر حضور ثبت‌شده دارد و force=False خطای `StudentHasAttendanceError`

**`session_manager.py`**:

- `start_session(course_id=1, late_after_minutes=None) -> dict`  # `SessionAlreadyActiveError` اگر جلسه فعال هست
- `close_session(session_id=None) -> dict`  # اگر None، جلسه فعال را می‌بندد
- `get_active_session() -> dict | None`
- `get_session(session_id) -> dict`
- `list_sessions(limit=50) -> list[dict]`

**`attendance_service.py`**:

- `log_attendance(session_id, student_id, source="face", confidence=None) -> bool`  # True اگر ثبت جدید و False اگر تکراری. برای `source=="face"` جلسه باید فعال باشد
- `remove_attendance(session_id, student_id) -> bool`  # فقط جلسه فعال
- `get_session_attendance(session_id) -> list[dict]`  # همه دانشجوها: `{student_id, full_name, major, term, status, checked_at, source}`
- `get_session_summary(session_id) -> dict`  # `{present, late, absent, total}`
- `process_recognition_result(session_id, matches: list[dict]) -> dict`  # تنها نقطه ورود ماژول بینایی به منطق حضور

الگوریتم `process_recognition_result`:

1. جلسه باید فعال باشد، وگرنه `NoActiveSessionError`.
2. چهره‌های ناشناس را در لاگ ثبت کن.
3. برای هر دانشجوی شناخته‌شده شمارنده را یکی زیاد کن و شمارنده دانشجوهای دیده‌نشده را صفر کن.
4. هر کس به آستانه رسید با `log_attendance` ثبت شود و از tracker حذف شود.
5. خروجی: `{"recorded": [...], "already_present": [...], "pending": {student_id: streak}, "unknown_count": int}`.

**`report_service.py`**:

- `export_session_report(session_id) -> Path`
- `export_daily_report(date_iso: str) -> Path`  # یک شیت برای هر جلسه آن روز؛ اگر جلسه‌ای نبود `ReportEmptyError`

فرمت اکسل:

- شیت راست‌به‌چپ (`rightToLeft = True`) با فونت فارسی مناسب و عرض ستون‌های تنظیم‌شده.
- بالای شیت: عنوان، نام درس، تاریخ شمسی، ساعت شروع و پایان و تعداد حاضر، تأخیر و غایب.
- ستون‌ها: ردیف، شماره دانشجویی (به‌صورت متن)، نام و نام خانوادگی، رشته، ترم، وضعیت، ساعت ورود، روش ثبت (چهره/دستی).
- همه دانشجوهای کلاس هستند و بر اساس شماره دانشجویی مرتب می‌شوند.
- نام فایل ASCII است، مثل `attendance_2026-10-24_1005.xlsx` در پوشه `reports/`.

# ۹. API (لایه نازک؛ بدون منطق کسب‌وکار)

- اجرا: `uvicorn backend.api.app:app --reload`. endpointها `def` معمولی هستند (نه `async`)، چون پردازش تصویر CPUمحور است. CORS برای `CORS_ORIGINS` فعال است.

- `GET /health`
- `GET /students`، `POST /students` (student_id, full_name, major, term)، `PUT /students/{id}`، `DELETE /students/{id}?force=false`
- `POST /students/{id}/process-photos`
- `GET /courses`
- `POST /sessions/start`، `POST /sessions/close`، `GET /sessions/active`، `GET /sessions`
- `GET /sessions/{id}/attendance` (فهرست محاسبه‌شده به‌همراه summary)
- `POST /sessions/{id}/recognize` (فایل تصویر JPEG/PNG، خروجی `process_recognition_result` به‌علاوه `faces: [{box, student_id}]`)
- `PUT /sessions/{id}/attendance/{student_id}` (ثبت دستی حاضر) و `DELETE` همان مسیر (حذف حضور)
- `GET /sessions/{id}/report` (دانلود اکسل)، `GET /reports/daily?date=YYYY-MM-DD`

- خطاها به‌صورت `{"error": code, "message": پیام فارسی}` برمی‌گردند. نگاشت status: NotFound → 404، Exists/AlreadyActive/HasAttendance/Closed → 409، InvalidInput/NotEnoughPhotos/NoFace/MultipleFaces → 422، NoActiveSession → 409.

# ۱۰. لاگ و حریم خصوصی

- در `logs/app.log` این‌ها ثبت می‌شوند: چهره ناشناس (با نزدیک‌ترین فاصله)، عکس ردشده، هشدار شباهت دو دانشجو، شروع و پایان جلسه و خطاها.
- پوشه‌های `known_faces/`، `embeddings/`، `data/`، `reports/` و `logs/` داده حساس‌اند و باید در `.gitignore` باشند.

# ۱۱. استیج‌ها و تعریف «تمام‌شدن»

هر استیج فقط با پاس‌شدن تست‌هایش کامل است.

1. **ساختار پایه**: ساخت همه پوشه‌ها و فایل‌های خالی، `config.py`، `errors.py`، `requirements.txt`، `.gitignore`، `.clinerules`، `check_env.py`. نصب `dlib-bin` و `face_recognition` را روی همین ویندوز تست و نسخه‌ها را قفل کن. تمام‌شدن: `python check_env.py` همه importها را OK نشان دهد و `face_recognition.face_encodings` روی یک عکس تستی اجرا شود.
2. **utils + database + models**: `init_db` جدول‌ها و درس پیش‌فرض را بسازد، دوبار اجرا خطا ندهد و نرمال‌سازی ارقام و تبدیل شمسی تست شده باشند.
3. **recognition.py**: `match_encoding` با بردارهای مصنوعی تست شود (پذیرش، رد با tolerance، رد با margin، حالت بدون دانشجو). تست با عکس واقعی در صورت وجود `tests/data/` اجرا شود و در غیر این صورت skip شود.
4. **enrollment.py**: ثبت ۳ دانشجوی نمونه با عکس واقعی، رد عکس بدون چهره، حداقل ۳ عکس و ذخیره‌شدن `.npy`.
5. **session_manager.py**: شروع و بستن جلسه، رد شروع جلسه دوم و `get_active_session`.
6. **attendance_service.py**: جلوگیری از ثبت تکراری، منطق ۳ فریم متوالی (با داده مصنوعی)، محاسبه صحیح حاضر، تأخیر و غایب، و ثبت دستی و حذف.
7. **report_service.py**: تولید فایل اکسل، بازکردن و بررسی ستون‌ها و راست‌به‌چپ بودن.
8. **API**: تست با `TestClient` برای همه endpointها و کدهای خطا.
9. **manage.py و main_test.py**:
   - دستورهای `manage.py`: `init-db`، `add-student`، `process-photos`، `list-students`، `start-session`، `close-session`، `report`.
   - `main_test.py`: اتصال به `CAMERA_SOURCE`، ابتدا فقط تست اتصال، بعد تشخیص و فراخوانی `process_recognition_result` روی هر N-امین فریم، نمایش کادر و نام در پنجره و خروج با `q`.
10. **تست نهایی**: چند نفر واقعی، حضور تکراری، خروجی اکسل، مستندسازی مشکلات در `README.md`.

# ۱۲. قوانین تست

- هر استیج یک فایل `tests/test_stageN_*.py` دارد.
- تست‌ها با دیتابیس موقت اجرا می‌شوند (`ATTENDANCE_DB`)، نه `data/attendance.db`.
- تست‌هایی که عکس واقعی می‌خواهند اگر `tests/data/` نبود skip می‌شوند.
```

---

<a id="progress-current_status-md"></a>
## Current Status & Progress (`progress/current_status.md`)

```markdown
# وضعیت جلسه کاری

**آخرین به‌روزرسانی:** 2026-11-02 (حذف کامل حروف فارسی از خروجی پیش‌فرض انگلیسی، جایگزین‌های ASCII، ساختار کارت و بخش‌بندی عمودی با خطوط تفکیک و Next step، دستورات status و session-summary، و ۱۹۱ تست پاس‌شده)
**آخرین استیج تکمیل‌شده:** استیج ۹ — CLI Management & Camera Smoke Test (کامل و تست‌شده)
**استیج فعلی:** استیج ۱۰ — تست نهایی جامع و مستندسازی در README.md (شروع نشده — منتظر تأیید)
**تست شده؟** بله — کل تست‌های پروژه: ۱۹۱ پاس، ۰ خطا، ۰ شکست، ۰ هشدار (۴۴.۴۴ ثانیه).

## تغییرات این جلسه (استیج ۹)

1. `backend/cli_format.py`:
   - تابع `sanitize_text(text, placeholder)` جهت جایگزینی عبارات غیر ASCII با شناسه جایگزین نظیر `(Persian name)` و `(Persian)`.
   - ارتقای `print_box`: پشتیبانی کامل از جداکننده‌ها و تیترهای بخش‌های درونی با کلید `---` به صورت خطوط افقی `+-- Section Title ----+`.
   - تابع `print_table`: حفظ جدول ASCII فشرده برای فلگ `--compact`.

2. `manage.py`:
   - تضمین عدم چاپ هیچ‌گونه کاراکتر فارسی در حالت پیش‌فرض (`--lang en`)؛ نمایش متون فارسی فیلدها با `(Persian name)` و `(Persian)`.
   - بازطراحی `list-students` به ساختار کارت‌های عمودی مجزا برای هر دانشجو با برچسب‌های انگلیسی تراز شده و خط خلاصه آمار در انتها؛ افزودن فلگ `--compact` برای جدول فشرده.
   - افزودن بخش‌های منظم (`Result` / `Status`، `Details`، و `Next step`) به خروجی تمام دستورات تغییردهنده وضعیت (`init-db`, `add-student`, `delete-student`, `process-photos`, `start-session`, `close-session`, `report`).
   - افزودن دستور جدید `status`: ارائه خلاصه جامع وضعیت سامانه (تعداد دانشجویان، وضعیت امبدینگ، جلسه فعال، تعداد کل جلسات و گزارش‌های اکسل).
   - افزودن دستور جدید `session-summary --id <id>`: چاپ عمودی و مرتب آمار حاضر/تأخیر/غایب/مجموع و فهرست رکوردهای دانشجویان به همراه وضعیت (بدون نام فارسی).
   - هشدار یک‌خطی انگلیسی در صورت استفاده از `--lang fa` مبنی بر عدم پشتیبانی احتمالی ترمینال از متن‌های دوجهته فارسی.
   - زیردستور `delete-student --id <id> [--force]` جهت حذف رکورد دانشجو با رعایت قیدهای حضور و غیاب.

3. `main_test.py`:
   - حذف کامل متون فارسی از پیام‌های خطای کنسول و خروجی‌های استاندارد؛ محدود ماندن کامل متن و فونت فارسی به کادر پنجره دوربین و کتابخانه Pillow.

4. `tests/test_stage9_cli.py`:
   - ارتقای تست‌های CLI به ۳۰ تست جامع.
   - افزودن تست‌های اختصاصی برای دستورات `status` و `session-summary`.
   - افزودن تست‌های سخت‌گیرانه `assert_no_persian` برای راستی‌آزمایی عدم وجود هرگونه کاراکتر غیر ASCII در خروجی دستورات انگلیسی.

5. `backend/report_service.py`:
   - اعتبارسنجی تاریخ میلادی با regex و strptime و خطای `InvalidInputError` برای تاریخ نامعتبر یا شمسی.

## باگ‌های شناخته‌شده و رفع‌شده

- به‌هم‌ریختگی متن و جداول در PowerShell 5.1: با حذف کاراکترهای فارسی از خروجی‌های استاندارد انگلیسی و جایگزینی با نشانگرهای متنی ASCII، نمایش خروجی در تمام نسخه‌های خط فرمان ویندوز و لینوکس کاملاً تراز و پایدار شد.
- سقف آرگومان limit در `list_sessions`: هنگام واکشی جلسات برای دستور `status` از `limit=500` استفاده شد تا خطای اعتبارسنجی حد بیشینه رخ ندهد.

## دستورات بعدی (منتظر تأیید)

- استیج ۱۰: تست نهایی جامع سیستم و مستندسازی در `README.md`.
```

---

<a id="agents-md"></a>
## Rules & Operational Guidelines (`AGENTS.md`)

```markdown
# AGENTS.md

Instructions for the coding agent working on this project (OpenCode reads this file automatically).
This file is authoritative. If `.clinerules` exists, it must say the same thing.
Do NOT regenerate, overwrite or "improve" this file with /init or any generator. Edit it only when I ask.

## 1. Start of every session
1. Read `PROJECT_CONTEXT.md` completely.
2. Read this file completely.
3. Read `progress/current_status.md` and continue from where it stopped.
4. If any of them is missing, tell me and stop. Do not recreate it silently.
5. This is a backend-only project. Ignore `SMART_ATTENDANCE_FRONTEND_SPEC.md`, `.claude/` and `blobs/`.

## 2. Permanent rules
- Do only ONE stage per session.
- A stage is complete only when its tests pass with pytest. Show the real test output. If tests were skipped, say so and do not call the stage fully verified.
- Do not change technologies, folder structure, database schema or function signatures without asking me first.
- Touch earlier stages' files only to fix bugs, and record each such change under "Known bugs" in `progress/current_status.md`.
- Use only free and open-source tools. The finished system must work fully offline.
- Use PowerShell commands (Windows). Run commands only inside this project folder.
- Never claim that something is installed, fixed or working unless you ran a command that proves it. Show the real output.
- Skills and generic workflows: do NOT use any generic skill workflow (spec, plan or test files, brainstorming and so on). The stage definition in `PROJECT_CONTEXT.md` is the spec. If a skill conflicts with `PROJECT_CONTEXT.md` or this file, `PROJECT_CONTEXT.md` and this file win.
- At the end of every session update `progress/current_status.md` and STOP. Do not start the next stage.

## 3. Safety rules for files and commands
- NEVER run a delete command (`Remove-Item`, `rm`, `del`, `rmdir`, or anything equivalent) without first asking me. When you ask, show the FULL absolute path and list what is inside it.
- NEVER delete or overwrite the project root folder or any parent folder.
- NEVER delete or overwrite: `PROJECT_CONTEXT.md`, `AGENTS.md`, `.clinerules`, `progress/`, `known_faces/`, `embeddings/`, `data/`, `tests/data/`, `.git/`.
- `venv/` may be deleted and recreated only if I explicitly ask.
- Before creating a file, check whether it already exists. If it exists, read it first and edit it instead of overwriting it.
- If you are not sure whether something should be changed or deleted, do not touch it. List it under "NEEDS MY DECISION".
- Do not run `git commit`, `git reset`, `git checkout` or `git clean` unless I ask.

## 4. Final report format (English, at the end of every session)
- DONE: what you completed in this session.
- CHANGED / DELETED: every file you edited, moved, renamed or deleted, with its path and the reason.
- TESTS: the exact command you ran and the result, including skipped tests and why.
- REMAINING: the stages and open issues that are still left.
- NEEDS MY DECISION: anything you were unsure about or skipped.
```

---

<a id="check_env-py"></a>
## Environment Setup & Verification (`check_env.py`)

```python
"""Verify that the Python environment is ready for the attendance system.

Run with the project virtualenv:

    venv\\Scripts\\python.exe check_env.py

The script checks every required import, the configured directories, the
Asia/Tehran timezone and finally runs ``face_recognition.face_encodings`` on
the first image found in ``tests/data/`` (if any).
"""
from __future__ import annotations

import sys
import traceback
from importlib import metadata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend import config  # noqa: E402

REQUIRED_MODULES = [
    "cv2",
    "numpy",
    "PIL",
    "dlib",
    "face_recognition",
    "face_recognition_models",
    "click",
    "openpyxl",
    "jdatetime",
    "tzdata",
    "fastapi",
    "uvicorn",
    "python_multipart",
    "pytest",
    "httpx",
]

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}

DISTRIBUTION_NAMES = {
    "cv2": "opencv-python",
    "PIL": "pillow",
    "dlib": "dlib-bin",
    "python_multipart": "python-multipart",
}


def _print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def _module_version(module_name: str, module) -> str:
    distribution = DISTRIBUTION_NAMES.get(module_name, module_name)
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return str(getattr(module, "__version__", "unknown"))


def check_imports() -> list[str]:
    """Import every required module and report its version."""
    _print_header("Imports")
    failures: list[str] = []
    for name in REQUIRED_MODULES:
        try:
            module = __import__(name)
        except Exception as exc:  # pragma: no cover - failure path
            failures.append(name)
            print(f"[FAIL] {name}: {exc}")
            traceback.print_exc(limit=1)
            continue
        print(f"[OK]   {name} {_module_version(name, module)}")
    return failures


def check_python() -> list[str]:
    _print_header("Python")
    print(f"executable: {sys.executable}")
    print(f"version:    {sys.version.split()[0]}")
    if sys.version_info[:2] != (3, 11):
        print("[WARN] Python 3.11 is required by PROJECT_CONTEXT.md.")
        return ["python_version"]
    print("[OK]   Python 3.11")
    return []


def check_numpy() -> list[str]:
    _print_header("NumPy")
    import numpy

    major = int(numpy.__version__.split(".")[0])
    if major >= 2:
        print(f"[FAIL] numpy {numpy.__version__} is >= 2; the project pins numpy<2.")
        return ["numpy_version"]
    print(f"[OK]   numpy {numpy.__version__} (< 2)")
    return []


def check_timezone() -> list[str]:
    _print_header("Timezone")
    try:
        from zoneinfo import ZoneInfo

        zone = ZoneInfo(config.TIMEZONE)
        print(f"[OK]   {config.TIMEZONE} -> {zone}")
        return []
    except Exception as exc:  # pragma: no cover - failure path
        print(f"[FAIL] timezone {config.TIMEZONE}: {exc}")
        return ["timezone"]


def check_directories() -> list[str]:
    _print_header("Directories")
    failures: list[str] = []
    for directory in (
        config.KNOWN_FACES_DIR,
        config.EMBEDDINGS_DIR,
        config.REPORTS_DIR,
        config.LOGS_DIR,
        config.DATA_DIR,
        PROJECT_ROOT / "tests" / "data",
    ):
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"[OK]   {directory}")
        except Exception as exc:  # pragma: no cover - failure path
            failures.append(str(directory))
            print(f"[FAIL] {directory}: {exc}")
    return failures


def check_face_encodings() -> list[str]:
    _print_header("Face recognition")
    import face_recognition
    import numpy as np
    from PIL import Image, ImageOps

    images = sorted(
        path
        for path in (PROJECT_ROOT / "tests" / "data").glob("*")
        if path.suffix.lower() in IMAGE_SUFFIXES
    )
    if not images:
        print(
            "[SKIP] No test image found in tests/data/. "
            "Place a JPG/PNG photo with a face there to run this check."
        )
        return []

    path = images[0]
    print(f"image: {path}")
    try:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((config.PHOTO_MAX_SIDE, config.PHOTO_MAX_SIDE))
            rgb = np.array(image)

        locations = face_recognition.face_locations(rgb, model=config.DETECTION_MODEL)
        encodings = face_recognition.face_encodings(
            rgb, known_face_locations=locations
        )
    except Exception as exc:  # pragma: no cover - failure path
        print(f"[FAIL] face_encodings raised: {exc}")
        traceback.print_exc(limit=2)
        return ["face_encodings"]

    print(f"faces detected: {len(locations)}")
    if not encodings:
        print("[FAIL] face_recognition.face_encodings returned no encoding.")
        return ["face_encodings"]

    print(f"encodings: {len(encodings)}, shape: {encodings[0].shape}")
    if encodings[0].shape != (128,):
        print("[FAIL] expected a 128-dimensional encoding.")
        return ["face_encodings"]
    print("[OK]   face_recognition.face_encodings")
    return []


def main() -> int:
    failures: list[str] = []
    failures += check_python()
    failures += check_imports()
    failures += check_numpy()
    failures += check_timezone()
    failures += check_directories()
    failures += check_face_encodings()

    _print_header("Result")
    if failures:
        print(f"[FAIL] {len(failures)} check(s) failed: {', '.join(failures)}")
        return 1
    print("[OK] Environment is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

<a id="backend-config-py"></a>
## Configuration & Constants (`backend/config.py`)

```python
"""Central configuration for the attendance system.

Every configurable value and every path lives here; other modules must import
from this module instead of hard-coding values.
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Face recognition
FACE_TOLERANCE = 0.55            # must stay between 0.5 and 0.6
MATCH_MARGIN = 0.05              # required gap between best and second best match
MIN_PHOTOS = 3
MAX_PHOTOS = 5
REQUIRED_CONSECUTIVE_FRAMES = 3
DEFAULT_LATE_AFTER_MINUTES = 10
DETECTION_MODEL = "hog"
FRAME_MAX_WIDTH = 640            # frames are downscaled before detection
PHOTO_MAX_SIDE = 1280
TIMEZONE = "Asia/Tehran"
CAMERA_SOURCE: int | str = 0     # or "http://<ip>:8080/video" for IP Webcam
PROCESS_EVERY_N_FRAMES = 3       # only used by main_test.py

# API
API_HOST = "127.0.0.1"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:5173"]

# Directories (all relative to the project root)
KNOWN_FACES_DIR = PROJECT_ROOT / "known_faces"
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "app.log"
DATA_DIR = PROJECT_ROOT / "data"


def get_db_path() -> Path:
    """Return the SQLite path, honouring the ATTENDANCE_DB override."""
    override = os.environ.get("ATTENDANCE_DB")
    if override:
        return Path(override).expanduser().resolve()
    return DATA_DIR / "attendance.db"


DB_PATH = get_db_path()
```

---

<a id="backend-errors-py"></a>
## Custom Exceptions (`backend/errors.py`)

```python
"""Custom application errors.

Every error carries a stable English ``code`` for the API and a Persian
``message_fa`` suitable for showing to the end user.
"""
from __future__ import annotations


class AppError(Exception):
    """Base class for all expected application errors."""

    def __init__(self, code: str, message_fa: str):
        self.code = code
        self.message_fa = message_fa
        super().__init__(message_fa)

    def to_dict(self) -> dict:
        return {"error": self.code, "message": self.message_fa}


class StudentExistsError(AppError):
    def __init__(self, student_id: str | None = None):
        message = "دانشجویی با این شماره قبلاً ثبت شده است."
        if student_id:
            message = f"دانشجویی با شماره «{student_id}» قبلاً ثبت شده است."
        super().__init__("student_exists", message)


class StudentNotFoundError(AppError):
    def __init__(self, student_id: str | None = None):
        message = "دانشجو یافت نشد."
        if student_id:
            message = f"دانشجوی «{student_id}» یافت نشد."
        super().__init__("student_not_found", message)


class StudentHasAttendanceError(AppError):
    def __init__(self, student_id: str | None = None):
        message = "این دانشجو سابقه حضور دارد و حذف آن مجاز نیست."
        if student_id:
            message = (
                f"دانشجوی «{student_id}» سابقه حضور دارد و حذف آن مجاز نیست."
            )
        super().__init__("student_has_attendance", message)


class NoFaceError(AppError):
    def __init__(self, detail: str | None = None):
        message = "در تصویر چهره‌ای پیدا نشد."
        if detail:
            message = f"{message} ({detail})"
        super().__init__("no_face", message)


class MultipleFacesError(AppError):
    def __init__(self, detail: str | None = None):
        message = "تصویر باید دقیقاً یک چهره داشته باشد."
        if detail:
            message = f"{message} ({detail})"
        super().__init__("multiple_faces", message)


class NotEnoughPhotosError(AppError):
    def __init__(self, required: int | None = None, found: int | None = None):
        message = "حداقل ۳ عکس معتبر برای ثبت دانشجو لازم است."
        if required is not None and found is not None:
            message = (
                f"حداقل {required} عکس معتبر لازم است؛ فقط {found} عکس پذیرفته شد."
            )
        super().__init__("not_enough_photos", message)


class SessionAlreadyActiveError(AppError):
    def __init__(self):
        super().__init__("session_already_active", "یک جلسه فعال از قبل وجود دارد.")


class NoActiveSessionError(AppError):
    def __init__(self):
        super().__init__("no_active_session", "جلسه فعالی وجود ندارد.")


class SessionNotFoundError(AppError):
    def __init__(self, session_id: int | None = None):
        message = "جلسه یافت نشد."
        if session_id is not None:
            message = f"جلسه با شناسه {session_id} یافت نشد."
        super().__init__("session_not_found", message)


class SessionClosedError(AppError):
    def __init__(self):
        super().__init__("session_closed", "جلسه بسته شده است و قابل تغییر نیست.")


class InvalidInputError(AppError):
    def __init__(self, message_fa: str | None = None):
        super().__init__(
            "invalid_input",
            message_fa or "ورودی نامعتبر است.",
        )


class ReportEmptyError(AppError):
    def __init__(self):
        super().__init__("report_empty", "داده‌ای برای تولید گزارش وجود ندارد.")


class PayloadTooLargeError(AppError):
    def __init__(self, message_fa: str | None = None):
        super().__init__(
            "payload_too_large",
            message_fa or "حجم فایل تصویر بیش از حد مجاز است (حداکثر ۱۰ مگابایت).",
        )
```

---

<a id="backend-utils-py"></a>
## Utilities & Helpers (`backend/utils.py`)

```python
"""Utility helpers: digits, Tehran time, Jalali dates and logging."""
from __future__ import annotations

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo

import jdatetime

from backend import config

_PERSIAN_ZERO = 0x06F0
_ARABIC_ZERO = 0x0660
_DIGIT_TRANSLATION: dict[int, str] = {}
for _digit in range(10):
    _DIGIT_TRANSLATION[_PERSIAN_ZERO + _digit] = str(_digit)
    _DIGIT_TRANSLATION[_ARABIC_ZERO + _digit] = str(_digit)

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_LOG_FILES: set[str] = set()


def _tehran() -> ZoneInfo:
    """Return the configured timezone, read from config at call time.

    Section 4 of PROJECT_CONTEXT.md requires every module to read settings
    as ``config.NAME`` at call time so tests can monkeypatch them.
    """
    return ZoneInfo(config.TIMEZONE)


def normalize_digits(text: str) -> str:
    """Convert Persian and Arabic-Indic digits to ASCII digits."""
    return text.translate(_DIGIT_TRANSLATION)


def now_tehran() -> datetime:
    """Return the current timezone-aware time in Asia/Tehran."""
    return datetime.now(_tehran())


def to_iso(dt: datetime) -> str:
    """Serialize a datetime as ISO 8601 in Asia/Tehran, without microseconds."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_tehran())
    return dt.astimezone(_tehran()).isoformat(timespec="seconds")


def parse_iso(s: str) -> datetime:
    """Parse an ISO 8601 string into an aware Asia/Tehran datetime."""
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_tehran())
    return dt.astimezone(_tehran())


def to_jalali_str(dt_or_iso: datetime | str, with_time: bool = False) -> str:
    """Format a datetime (or ISO string) as a Jalali date with ASCII digits."""
    dt = parse_iso(dt_or_iso) if isinstance(dt_or_iso, str) else dt_or_iso
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_tehran())
    jalali = jdatetime.datetime.fromgregorian(datetime=dt.astimezone(_tehran()))
    result = f"{jalali.year:04d}/{jalali.month:02d}/{jalali.day:02d}"
    if with_time:
        result += f" {jalali.hour:02d}:{jalali.minute:02d}"
    return result


def setup_logging() -> None:
    """Configure a rotating UTF-8 file logger on logs/app.log.

    Calling this function again for the same log file is a no-op, so repeated
    imports do not add duplicate handlers.
    """
    log_file = Path(config.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    key = str(log_file.resolve())
    if key in _LOG_FILES:
        return

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    _LOG_FILES.add(key)
```

---

<a id="backend-models-py"></a>
## Database Models & Dataclasses (`backend/models.py`)

```python
"""SQL table definitions and row dataclasses."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

STUDENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS students (
  student_id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  major TEXT NOT NULL DEFAULT '',
  term TEXT NOT NULL DEFAULT '',
  embedding_path TEXT,
  photo_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
""".strip()

COURSES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  teacher TEXT NOT NULL DEFAULT '',
  room TEXT NOT NULL DEFAULT ''
);
""".strip()

SESSIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL REFERENCES courses(id),
  started_at TEXT NOT NULL,
  ended_at TEXT,
  late_after_minutes INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','closed'))
);
""".strip()

ACTIVE_SESSION_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS ux_one_active_session
  ON sessions(status) WHERE status = 'active';
""".strip()

ATTENDANCE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS attendance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL REFERENCES sessions(id),
  student_id TEXT NOT NULL REFERENCES students(student_id),
  checked_at TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('face','manual')),
  confidence REAL,
  UNIQUE (session_id, student_id)
);
""".strip()

SCHEMA_SQL = "\n\n".join(
    [
        STUDENTS_TABLE_SQL,
        COURSES_TABLE_SQL,
        SESSIONS_TABLE_SQL,
        ACTIVE_SESSION_INDEX_SQL,
        ATTENDANCE_TABLE_SQL,
    ]
)


@dataclass
class Student:
    student_id: str
    full_name: str
    major: str = ""
    term: str = ""
    embedding_path: str | None = None
    photo_count: int = 0
    created_at: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Student":
        return cls(
            student_id=row["student_id"],
            full_name=row["full_name"],
            major=row["major"],
            term=row["term"],
            embedding_path=row["embedding_path"],
            photo_count=row["photo_count"],
            created_at=row["created_at"],
        )


@dataclass
class Course:
    id: int
    title: str
    teacher: str = ""
    room: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Course":
        return cls(
            id=row["id"],
            title=row["title"],
            teacher=row["teacher"],
            room=row["room"],
        )


@dataclass
class Session:
    id: int
    course_id: int
    started_at: str
    late_after_minutes: int
    status: str
    ended_at: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Session":
        return cls(
            id=row["id"],
            course_id=row["course_id"],
            started_at=row["started_at"],
            late_after_minutes=row["late_after_minutes"],
            status=row["status"],
            ended_at=row["ended_at"],
        )


@dataclass
class AttendanceRecord:
    id: int
    session_id: int
    student_id: str
    checked_at: str
    source: str
    confidence: float | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "AttendanceRecord":
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            student_id=row["student_id"],
            checked_at=row["checked_at"],
            source=row["source"],
            confidence=row["confidence"],
        )
```

---

<a id="backend-database-py"></a>
## Database Connection & Initialization (`backend/database.py`)

```python
"""SQLite connection helpers and database initialization."""
from __future__ import annotations

import sqlite3

from backend import config
from backend.models import SCHEMA_SQL

DEFAULT_COURSE_TITLE = "کلاس اصلی"


def get_connection() -> sqlite3.Connection:
    """Open the configured database with foreign keys on and Row access."""
    db_path = config.get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    """Create tables/indexes and the default course. Safe to call repeatedly."""
    connection = get_connection()
    try:
        connection.executescript(SCHEMA_SQL)
        row = connection.execute(
            "SELECT COUNT(*) AS course_count FROM courses"
        ).fetchone()
        if row["course_count"] == 0:
            connection.execute(
                "INSERT INTO courses (title, teacher, room) VALUES (?, ?, ?)",
                (DEFAULT_COURSE_TITLE, "", ""),
            )
        connection.commit()
    finally:
        connection.close()
```

---

<a id="backend-recognition-py"></a>
## Face Recognition Core (`backend/recognition.py`)

```python
"""Face encoding, embedding caching and matching.

Implemented in stage 3. All thresholds come from ``backend.config`` so tests
can monkeypatch them; embeddings are loaded from ``config.EMBEDDINGS_DIR``
(overridden to temporary directories in tests).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import cv2
import face_recognition
import numpy as np
from PIL import Image, ImageOps

from backend import config
from backend.errors import InvalidInputError, MultipleFacesError, NoFaceError

logger = logging.getLogger(__name__)

# ``None`` means the cache has not been loaded yet; {} means loaded and empty.
_EMBEDDINGS: dict[str, np.ndarray] | None = None


def load_image_rgb(path: str | os.PathLike) -> np.ndarray:
    """Load an image file as an RGB ``np.ndarray``, honouring EXIF rotation."""
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        return np.asarray(image)


def encode_single_face(rgb: np.ndarray) -> np.ndarray:
    """Return the 128-d encoding of the single face in ``rgb``.

    Raises ``NoFaceError`` when no face is found and ``MultipleFacesError``
    when more than one face is present.
    """
    rgb = np.asarray(rgb)
    locations = face_recognition.face_locations(rgb, model=config.DETECTION_MODEL)
    if not locations:
        raise NoFaceError()
    if len(locations) > 1:
        raise MultipleFacesError(f"تعداد چهره‌های شناسایی‌شده: {len(locations)}")
    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
    if not encodings:  # pragma: no cover - defensive, should not happen
        raise NoFaceError("چهره مکان‌یابی شد اما استخراج انکودینگ ناموفق بود")
    return np.asarray(encodings[0], dtype=np.float64)


def reload_embeddings() -> int:
    """(Re)load every ``<student_id>.npy`` stored in the embeddings folder.

    Invalid files (unreadable or not 128-d) are skipped with a warning.
    Returns the number of students loaded.
    """
    global _EMBEDDINGS
    embeddings: dict[str, np.ndarray] = {}
    embeddings_dir = Path(config.EMBEDDINGS_DIR)
    if embeddings_dir.is_dir():
        for path in sorted(embeddings_dir.glob("*.npy")):
            try:
                vector = np.load(path)
            except Exception as exc:
                logger.warning("خواندن embedding ناموفق بود: %s (%s)", path.name, exc)
                continue
            if vector.shape != (128,) or not np.isfinite(vector).all():
                logger.warning(
                    "embedding نامعتبر (ابعاد %s) نادیده گرفته شد: %s",
                    tuple(vector.shape),
                    path.name,
                )
                continue
            embeddings[path.stem] = np.asarray(vector, dtype=np.float64)
    _EMBEDDINGS = embeddings
    return len(_EMBEDDINGS)


def match_encoding(enc: np.ndarray) -> tuple[str | None, float]:
    """Match ``enc`` against the cached embeddings (pure, testable logic).

    Returns ``(student_id, best_distance)``. ``student_id`` is ``None`` when
    the encoding matches nobody, when the best distance exceeds
    ``FACE_TOLERANCE``, or when the second-nearest student is closer than
    ``MATCH_MARGIN`` to the best one (ambiguous). With a single enrolled
    student the margin rule is skipped; with no students at all the result is
    ``(None, inf)``.
    """
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        reload_embeddings()

    if not _EMBEDDINGS:
        return None, float("inf")

    enc = np.asarray(enc, dtype=np.float64)
    distances = {
        student_id: float(np.linalg.norm(vector - enc))
        for student_id, vector in _EMBEDDINGS.items()
    }
    best_id, best = min(distances.items(), key=lambda item: item[1])

    if best > config.FACE_TOLERANCE:
        return None, best

    if len(distances) > 1:
        second = min(d for sid, d in distances.items() if sid != best_id)
        if second < best + config.MATCH_MARGIN:
            return None, best

    return best_id, best


def recognize_frame(bgr: np.ndarray) -> list[dict]:
    """Detect and identify every face in a BGR video frame.

    Wide frames are downscaled so their width does not exceed
    ``FRAME_MAX_WIDTH`` before detection. Returns one dict per face:
    ``{"student_id": str | None, "distance": float, "box": (top, right, bottom, left)}``
    where box coordinates are relative to the original frame (0 to 1).
    """
    bgr = np.asarray(bgr)
    if bgr.ndim == 2:
        bgr = cv2.cvtColor(bgr, cv2.COLOR_GRAY2BGR)
    elif bgr.ndim == 3 and bgr.shape[2] == 4:
        bgr = cv2.cvtColor(bgr, cv2.COLOR_BGRA2BGR)
    elif bgr.ndim == 3 and bgr.shape[2] != 3:
        raise InvalidInputError("تعداد کانال‌های تصویر نامعتبر است.")
    height, width = bgr.shape[:2]
    scale = min(1.0, config.FRAME_MAX_WIDTH / width)
    if scale < 1.0:
        small = cv2.resize(
            bgr,
            (max(1, round(width * scale)), max(1, round(height * scale))),
        )
    else:
        small = bgr

    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb, model=config.DETECTION_MODEL)
    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)

    results: list[dict] = []
    for (top, right, bottom, left), enc in zip(locations, encodings):
        student_id, distance = match_encoding(enc)
        if student_id is None:
            logger.info("چهره ناشناس دیده شد (نزدیک‌ترین فاصله: %.3f)", distance)
        results.append(
            {
                "student_id": student_id,
                "distance": distance,
                "box": (top / height, right / width, bottom / height, left / width),
            }
        )
    return results
```

---

<a id="backend-enrollment-py"></a>
## Student Enrollment Service (`backend/enrollment.py`)

```python
"""Student enrollment and photo processing.

Stage 4. Business rules live here (see PROJECT_CONTEXT.md sections 7 and 8);
thresholds and paths are always read from ``backend.config`` at call time so
tests can monkeypatch them.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import cv2
import numpy as np

from backend import config, recognition
from backend.database import get_connection
from backend.errors import (
    InvalidInputError,
    NoFaceError,
    NotEnoughPhotosError,
    MultipleFacesError,
    StudentExistsError,
    StudentHasAttendanceError,
    StudentNotFoundError,
)
from backend.models import Student
from backend.utils import normalize_digits, now_tehran, to_iso

logger = logging.getLogger(__name__)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
STUDENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

REASON_NO_FACE = "no_face"
REASON_MULTIPLE_FACES = "multiple_faces"
REASON_UNREADABLE = "unreadable"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _clean_student_id(student_id: str) -> str:
    """Normalize digits and enforce the ASCII whitelist for student ids."""
    if not isinstance(student_id, str):
        raise InvalidInputError("شماره دانشجویی باید متن باشد.")
    cleaned = normalize_digits(student_id).strip()
    if not cleaned:
        raise InvalidInputError("شماره دانشجویی نمی‌تواند خالی باشد.")
    if not STUDENT_ID_PATTERN.match(cleaned):
        raise InvalidInputError(
            "شماره دانشجویی فقط می‌تواند شامل حروف انگلیسی، رقم، خط تیره و زیرخط باشد."
        )
    return cleaned


def _clean_text(value: str, field_fa: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise InvalidInputError(f"{field_fa} باید متن باشد.")
    return value.strip()


def _resolve_embedding(embedding_path: str | None) -> Path | None:
    """Resolve a stored ``embedding_path`` (relative to the project root)."""
    if not embedding_path:
        return None
    path = Path(embedding_path)
    return path if path.is_absolute() else config.PROJECT_ROOT / path


def _student_dict(row) -> dict:
    student = Student.from_row(row)
    embedding_path = student.embedding_path
    resolved = _resolve_embedding(embedding_path)
    has_embedding = resolved is not None and resolved.is_file()
    return {
        "student_id": student.student_id,
        "full_name": student.full_name,
        "major": student.major,
        "term": student.term,
        "embedding_path": embedding_path,
        "photo_count": student.photo_count,
        "created_at": student.created_at,
        "has_embedding": has_embedding,
    }


def _fetch_row(student_id: str):
    connection = get_connection()
    try:
        return connection.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
    finally:
        connection.close()


def _require_row(student_id: str):
    row = _fetch_row(student_id)
    if row is None:
        raise StudentNotFoundError(student_id)
    return row


def _prepare_rgb(path: Path) -> np.ndarray:
    """Load a photo, apply EXIF rotation and downscale its longest side."""
    rgb = recognition.load_image_rgb(path)
    height, width = rgb.shape[:2]
    scale = min(1.0, config.PHOTO_MAX_SIDE / max(width, height))
    if scale < 1.0:
        rgb = cv2.resize(
            rgb,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return rgb


def _photo_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def _existing_embeddings(exclude: str) -> dict[str, np.ndarray]:
    """Load other students' embeddings straight from disk (no cache coupling)."""
    embeddings: dict[str, np.ndarray] = {}
    embeddings_dir = Path(config.EMBEDDINGS_DIR)
    if not embeddings_dir.is_dir():
        return embeddings
    for path in sorted(embeddings_dir.glob("*.npy")):
        if path.stem == exclude:
            continue
        try:
            vector = np.load(path)
        except Exception:  # pragma: no cover - defensive
            continue
        if vector.shape == (128,) and np.isfinite(vector).all():
            embeddings[path.stem] = np.asarray(vector, dtype=np.float64)
    return embeddings


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def add_student(
    student_id: str,
    full_name: str,
    major: str = "",
    term: str = "",
) -> dict:
    """Register a student and create the ``known_faces/<student_id>`` folder."""
    student_id = _clean_student_id(student_id)
    full_name = _clean_text(full_name, "نام و نام خانوادگی")
    if not full_name:
        raise InvalidInputError("نام و نام خانوادگی نمی‌تواند خالی باشد.")
    major = _clean_text(major, "رشته")
    term = _clean_text(term, "ترم")

    if _fetch_row(student_id) is not None:
        raise StudentExistsError(student_id)

    folder = Path(config.KNOWN_FACES_DIR) / student_id
    folder.mkdir(parents=True, exist_ok=True)

    connection = get_connection()
    try:
        connection.execute(
            "INSERT INTO students (student_id, full_name, major, term, "
            "embedding_path, photo_count, created_at) VALUES (?, ?, ?, ?, NULL, 0, ?)",
            (student_id, full_name, major, term, to_iso(now_tehran())),
        )
        connection.commit()
    finally:
        connection.close()

    return _student_dict(_require_row(student_id))


def process_photos(student_id: str) -> dict:
    """Build the student's mean embedding from the photos in their folder.

    Returns ``{"accepted": int, "rejected": [{"file", "reason"}],
    "warnings": [...], "embedding_saved": bool}``.

    Raises ``NotEnoughPhotosError`` when fewer than ``MIN_PHOTOS`` photos are
    valid; in that case an existing embedding is never overwritten.
    """
    student_id = _clean_student_id(student_id)
    _require_row(student_id)

    folder = Path(config.KNOWN_FACES_DIR) / student_id
    photos = _photo_files(folder)
    warnings: list[dict] = []

    if len(photos) > config.MAX_PHOTOS:
        warnings.append(
            {
                "code": "photos_clipped",
                "message": (
                    f"تعداد عکس‌ها بیش از حد مجاز است؛ فقط {config.MAX_PHOTOS} "
                    "عکس اول پردازش شد."
                ),
                "total": len(photos),
                "used": config.MAX_PHOTOS,
            }
        )
        photos = photos[: config.MAX_PHOTOS]

    encodings: list[np.ndarray] = []
    rejected: list[dict] = []

    for path in photos:
        try:
            rgb = _prepare_rgb(path)
        except Exception as exc:
            logger.warning("عکس خوانده نشد: %s (%s)", path, exc)
            rejected.append({"file": path.name, "reason": REASON_UNREADABLE})
            continue

        try:
            encoding = recognition.encode_single_face(rgb)
        except MultipleFacesError:
            logger.warning("عکس با چند چهره رد شد: %s", path.name)
            rejected.append({"file": path.name, "reason": REASON_MULTIPLE_FACES})
            continue
        except NoFaceError:
            logger.warning("عکس بدون چهره رد شد: %s", path.name)
            rejected.append({"file": path.name, "reason": REASON_NO_FACE})
            continue

        encodings.append(encoding)

    accepted = len(encodings)
    if accepted < config.MIN_PHOTOS:
        logger.warning(
            "عکس‌های معتبر کافی نیست برای %s: %s از %s",
            student_id,
            accepted,
            config.MIN_PHOTOS,
        )
        error = NotEnoughPhotosError(required=config.MIN_PHOTOS, found=accepted)
        error.accepted = accepted
        error.rejected = rejected
        error.warnings = warnings
        raise error

    mean_embedding = np.mean(np.stack(encodings), axis=0)

    for other_id, other_vector in _existing_embeddings(exclude=student_id).items():
        distance = float(np.linalg.norm(other_vector - mean_embedding))
        if distance < config.FACE_TOLERANCE:
            logger.warning(
                "هشدار شباهت: %s به %s نزدیک است (فاصله %.3f)",
                student_id,
                other_id,
                distance,
            )
            warnings.append(
                {
                    "code": "similar_face",
                    "student_id": other_id,
                    "distance": round(distance, 4),
                    "message": "چهره این دانشجو به دانشجوی دیگری نزدیک است.",
                }
            )

    embeddings_dir = Path(config.EMBEDDINGS_DIR)
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    embedding_file = embeddings_dir / f"{student_id}.npy"
    np.save(embedding_file, mean_embedding)

    try:
        stored_path = embedding_file.resolve().relative_to(
            config.PROJECT_ROOT
        ).as_posix()
    except ValueError:  # embeddings folder outside the project (tests)
        stored_path = str(embedding_file.resolve())

    connection = get_connection()
    try:
        connection.execute(
            "UPDATE students SET embedding_path = ?, photo_count = ? "
            "WHERE student_id = ?",
            (stored_path, accepted, student_id),
        )
        connection.commit()
    finally:
        connection.close()

    recognition.reload_embeddings()

    return {
        "accepted": accepted,
        "rejected": rejected,
        "warnings": warnings,
        "embedding_saved": True,
    }


def get_student(student_id: str) -> dict | None:
    """Return a student as a dict (with ``has_embedding``) or ``None``."""
    student_id = _clean_student_id(student_id)
    row = _fetch_row(student_id)
    return _student_dict(row) if row is not None else None


def list_students() -> list[dict]:
    """Return every student ordered by student_id."""
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM students ORDER BY student_id"
        ).fetchall()
    finally:
        connection.close()
    return [_student_dict(row) for row in rows]


def update_student(
    student_id: str,
    full_name: str | None = None,
    major: str | None = None,
    term: str | None = None,
) -> dict:
    """Update the given metadata fields and return the updated student."""
    student_id = _clean_student_id(student_id)
    _require_row(student_id)

    updates: list[str] = []
    values: list[str] = []
    if full_name is not None:
        cleaned = _clean_text(full_name, "نام و نام خانوادگی")
        if not cleaned:
            raise InvalidInputError("نام و نام خانوادگی نمی‌تواند خالی باشد.")
        updates.append("full_name = ?")
        values.append(cleaned)
    if major is not None:
        updates.append("major = ?")
        values.append(_clean_text(major, "رشته"))
    if term is not None:
        updates.append("term = ?")
        values.append(_clean_text(term, "ترم"))

    if updates:
        values.append(student_id)
        connection = get_connection()
        try:
            connection.execute(
                f"UPDATE students SET {', '.join(updates)} WHERE student_id = ?",
                values,
            )
            connection.commit()
        finally:
            connection.close()

    return _student_dict(_require_row(student_id))


def delete_student(student_id: str, force: bool = False) -> bool:
    """Delete a student, keeping their photo folder.

    Raises ``StudentHasAttendanceError`` when attendance rows exist and
    ``force`` is false. The derived ``.npy`` file is removed and the
    recognition cache is reloaded.
    """
    student_id = _clean_student_id(student_id)
    _require_row(student_id)

    connection = get_connection()
    try:
        attendance_count = connection.execute(
            "SELECT COUNT(*) AS n FROM attendance WHERE student_id = ?",
            (student_id,),
        ).fetchone()["n"]
        if attendance_count and not force:
            raise StudentHasAttendanceError(student_id)

        with connection:
            if attendance_count:
                connection.execute(
                    "DELETE FROM attendance WHERE student_id = ?", (student_id,)
                )
            connection.execute(
                "DELETE FROM students WHERE student_id = ?", (student_id,)
            )
    finally:
        connection.close()

    embedding_file = Path(config.EMBEDDINGS_DIR) / f"{student_id}.npy"
    if embedding_file.is_file():
        try:
            embedding_file.unlink()
        except OSError as exc:  # pragma: no cover - Windows file locks
            logger.warning("حذف فایل embedding ناموفق بود: %s (%s)", embedding_file, exc)

    recognition.reload_embeddings()
    logger.info("دانشجو حذف شد: %s (force=%s)", student_id, force)
    return True
```

---

<a id="backend-session_manager-py"></a>
## Session Management Service (`backend/session_manager.py`)

```python
"""Session lifecycle management.

Implemented in stage 5.
"""
from __future__ import annotations

import logging
import sqlite3

from backend import config, database
from backend.errors import (
    InvalidInputError,
    NoActiveSessionError,
    SessionAlreadyActiveError,
    SessionClosedError,
    SessionNotFoundError,
)
from backend.utils import now_tehran, to_iso, setup_logging

logger = logging.getLogger(__name__)

SESSION_COLUMNS = ("id", "course_id", "started_at", "ended_at", "late_after_minutes", "status")
COURSE_COLUMNS = ("id", "title", "teacher", "room")


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict with exactly the table columns."""
    return {key: row[key] for key in row.keys()}


def _validate_late_after_minutes(value: int | None) -> int:
    """Return the effective late_after_minutes, applying defaults and validation."""
    if value is None:
        value = config.DEFAULT_LATE_AFTER_MINUTES
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidInputError("حد تأخير باید عدد صحیح باشد.")
    if value < 0 or value > 600:
        raise InvalidInputError("حد تأخير باید بین ۰ و ۶۰۰ دقیقه باشد.")
    return value


def start_session(course_id: int = 1, late_after_minutes: int | None = None) -> dict:
    """Start a new session.

    Raises:
        InvalidInputError: if the course does not exist or late_after_minutes
            is not an int in [0, 600].
        SessionAlreadyActiveError: if a session is already active.
    """
    late_after_minutes = _validate_late_after_minutes(late_after_minutes)
    setup_logging()

    connection = database.get_connection()
    try:
        # The course must exist.
        course = connection.execute(
            "SELECT id FROM courses WHERE id = ?", (course_id,)
        ).fetchone()
        if course is None:
            raise InvalidInputError(f"درس با شناسه {course_id} وجود ندارد.")

        started_at = to_iso(now_tehran())
        try:
            cursor = connection.execute(
                "INSERT INTO sessions (course_id, started_at, late_after_minutes, status) "
                "VALUES (?, ?, ?, 'active')",
                (course_id, started_at, late_after_minutes),
            )
            session_id = cursor.lastrowid
            connection.commit()
        except sqlite3.IntegrityError:
            # Partial unique index ux_one_active_session blocks a second active row.
            connection.rollback()
            raise SessionAlreadyActiveError()

        row = connection.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    finally:
        connection.close()

    logger.info(
        "Session started: id=%s course_id=%s late_after_minutes=%s",
        session_id,
        course_id,
        late_after_minutes,
    )
    return _row_to_dict(row)


def close_session(session_id: int | None = None) -> dict:
    """Close a session.

    If ``session_id`` is ``None`` the active session is closed.

    Raises:
        NoActiveSessionError: if ``session_id`` is None and no session is active.
        SessionNotFoundError: if the given id does not exist.
        SessionClosedError: if the given session is already closed.
    """
    setup_logging()
    connection = database.get_connection()
    try:
        if session_id is None:
            row = connection.execute(
                "SELECT * FROM sessions WHERE status = 'active' ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row is None:
                raise NoActiveSessionError()
            session_id = row["id"]
        else:
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if row is None:
                raise SessionNotFoundError(session_id)
            if row["status"] == "closed":
                raise SessionClosedError()

        ended_at = to_iso(now_tehran())
        connection.execute(
            "UPDATE sessions SET ended_at = ?, status = 'closed' WHERE id = ?",
            (ended_at, session_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    finally:
        connection.close()

    # Clear streak tracker for this session to prevent memory leaks
    from backend import attendance_service
    attendance_service.reset_session_tracker(session_id)

    logger.info("Session closed: id=%s", session_id)
    return _row_to_dict(row)


def get_active_session() -> dict | None:
    """Return the active session, or ``None`` if there is none."""
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM sessions WHERE status = 'active' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return _row_to_dict(row)


def get_session(session_id: int) -> dict:
    """Return a session by id.

    Raises:
        SessionNotFoundError: if no session with that id exists.
    """
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise SessionNotFoundError(session_id)
    return _row_to_dict(row)


def list_sessions(limit: int = 50) -> list[dict]:
    """Return all sessions, newest first.

    Raises:
        InvalidInputError: if ``limit`` is not an int in [1, 500].
    """
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise InvalidInputError("حد تعداد باید عدد صحیح باشد.")
    if limit < 1 or limit > 500:
        raise InvalidInputError("حد تعداد باید بین ۱ و ۵۰۰ باشد.")

    connection = database.get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    finally:
        connection.close()
    return [_row_to_dict(row) for row in rows]


def list_courses() -> list[dict]:
    """Return all courses ordered by id, with exactly the table columns."""
    setup_logging()
    connection = database.get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM courses ORDER BY id"
        ).fetchall()
    finally:
        connection.close()
    return [_row_to_dict(row) for row in rows]
```

---

<a id="backend-attendance_service-py"></a>
## Attendance Core Logic (`backend/attendance_service.py`)

```python
"""Attendance logic, streak tracking, and manual adjustments.

Implemented in stage 6.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import datetime, timedelta

from backend import config, database
from backend.errors import InvalidInputError, NoActiveSessionError, SessionNotFoundError
from backend.utils import now_tehran, to_iso, setup_logging

logger = logging.getLogger(__name__)

# Global streak tracker: session_id -> {student_id: streak_count}
streak_trackers: dict[int, dict[str, int]] = {}
_streak_lock = threading.Lock()


def reset_session_tracker(session_id: int) -> None:
    """Clear streak tracker for a specific session."""
    with _streak_lock:
        if session_id in streak_trackers:
            del streak_trackers[session_id]


def log_attendance(session_id: int, student_id: str, source: str = "face", confidence: float | None = None) -> bool:
    """Log attendance for a student in a session.
    
    Raises:
        NoActiveSessionError: if the session is not active.
        InvalidInputError: if source is not 'face' or 'manual'.
    """
    if source not in ("face", "manual"):
        raise InvalidInputError("منبع حضور باید 'face' یا 'manual' باشد.")
    
    setup_logging()
    connection = database.get_connection()
    try:
        # Check if session is active
        row = connection.execute(
            "SELECT status FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise SessionNotFoundError(session_id)
        if row["status"] != "active":
            raise NoActiveSessionError()

        # Check if student exists
        student_row = connection.execute(
            "SELECT student_id FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        if student_row is None:
            raise InvalidInputError(f"دانشجویی با شناسه {student_id} یافت نشد.")

        checked_at = to_iso(now_tehran())
        try:
            connection.execute(
                "INSERT INTO attendance (session_id, student_id, checked_at, source, confidence) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, student_id, checked_at, source, confidence),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            # UNIQUE constraint failed (already present)
            connection.rollback()
            return False
        
        logger.info("Attendance logged: session_id=%s student_id=%s source=%s", session_id, student_id, source)
        return True
    finally:
        connection.close()


def remove_attendance(session_id: int, student_id: str) -> bool:
    """Remove attendance record for a student in a session.
    
    Raises:
        NoActiveSessionError: if the session is not active.
    """
    setup_logging()
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT status FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise SessionNotFoundError(session_id)
        if row["status"] != "active":
            raise NoActiveSessionError()

        cursor = connection.execute(
            "DELETE FROM attendance WHERE session_id = ? AND student_id = ?",
            (session_id, student_id),
        )
        connection.commit()
        if cursor.rowcount > 0:
            logger.info("Attendance removed: session_id=%s student_id=%s", session_id, student_id)
            return True
        return False
    finally:
        connection.close()


def get_session_attendance(session_id: int) -> list[dict]:
    """Get attendance status for all students in a session.
    
    Returns a list of dicts with:
    student_id, full_name, major, term, status, checked_at, source
    """
    connection = database.get_connection()
    try:
        session_row = connection.execute(
            "SELECT started_at, late_after_minutes FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if session_row is None:
            raise SessionNotFoundError(session_id)
        
        started_at_str = session_row["started_at"]
        late_after_minutes = session_row["late_after_minutes"]
        
        # Parse started_at to datetime
        started_at = datetime.fromisoformat(started_at_str)
        late_threshold = started_at + timedelta(minutes=late_after_minutes)
        
        students = connection.execute(
            "SELECT student_id, full_name, major, term FROM students"
        ).fetchall()
        
        attendance_records = connection.execute(
            "SELECT student_id, checked_at, source FROM attendance WHERE session_id = ?",
            (session_id,)
        ).fetchall()
        
        attendance_map = {row["student_id"]: row for row in attendance_records}
        
        result = []
        for student in students:
            student_id = student["student_id"]
            record = attendance_map.get(student_id)
            
            if record is None:
                status = "absent"
                checked_at = None
                source = None
            else:
                checked_at_str = record["checked_at"]
                checked_at_dt = datetime.fromisoformat(checked_at_str)
                # مرز دقیق (برابر late_after_minutes) باید present باشد
                if checked_at_dt <= late_threshold:
                    status = "present"
                else:
                    status = "late"
                checked_at = checked_at_str
                source = record["source"]
            
            result.append({
                "student_id": student_id,
                "full_name": student["full_name"],
                "major": student["major"],
                "term": student["term"],
                "status": status,
                "checked_at": checked_at,
                "source": source,
            })
        
        return result
    finally:
        connection.close()


def get_session_summary(session_id: int) -> dict:
    """Get summary counts for a session."""
    attendance_list = get_session_attendance(session_id)
    total = len(attendance_list)
    present = sum(1 for a in attendance_list if a["status"] == "present")
    late = sum(1 for a in attendance_list if a["status"] == "late")
    absent = sum(1 for a in attendance_list if a["status"] == "absent")
    
    return {
        "total": total,
        "present": present,
        "late": late,
        "absent": absent,
    }


def process_recognition_result(session_id: int, matches: list[dict]) -> dict:
    """Process face recognition matches for an active session.
    
    Args:
        session_id: The active session ID.
        matches: List of dicts from recognition.py, each containing 'student_id' (str or None) and 'distance' (float).
        
    Returns:
        dict with keys: 'recorded', 'already_present', 'pending', 'unknown_count'
        
    Raises:
        NoActiveSessionError: if the session is not active.
    """
    setup_logging()
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT status FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise SessionNotFoundError(session_id)
        if row["status"] != "active":
            raise NoActiveSessionError()
            
        # Get already present students in this session
        present_students = {
            row["student_id"] 
            for row in connection.execute(
                "SELECT student_id FROM attendance WHERE session_id = ?", (session_id,)
            ).fetchall()
        }
    finally:
        connection.close()

    recorded = []
    already_present = []
    unknown_count = 0
    seen_in_frame = set()

    with _streak_lock:
        if session_id not in streak_trackers:
            streak_trackers[session_id] = {}
        tracker = streak_trackers[session_id]

        for match in matches:
            student_id = match.get("student_id")
            distance = match.get("distance")

            if student_id is None:
                unknown_count += 1
                logger.info("چهره ناشناس دیده شد (فاصله: %.3f)", distance)
                continue

            seen_in_frame.add(student_id)

            if student_id in present_students:
                already_present.append(student_id)
                continue

            # Increment streak
            tracker[student_id] = tracker.get(student_id, 0) + 1

            if tracker[student_id] >= config.REQUIRED_CONSECUTIVE_FRAMES:
                # Log attendance
                success = log_attendance(session_id, student_id, source="face", confidence=distance)
                if success:
                    recorded.append(student_id)
                    present_students.add(student_id)
                    del tracker[student_id]
                else:
                    # Should not happen due to present_students check, but just in case
                    already_present.append(student_id)
                    del tracker[student_id]

        # Reset streak for students not seen in this frame (delete to prevent memory leak)
        for student_id in list(tracker.keys()):
            if student_id not in seen_in_frame:
                del tracker[student_id]

        pending_copy = dict(tracker)

    return {
        "recorded": recorded,
        "already_present": already_present,
        "pending": pending_copy,
        "unknown_count": unknown_count,
    }
```

---

<a id="backend-report_service-py"></a>
## Excel Report Generator (`backend/report_service.py`)

```python
"""Report generation service for Excel exports.

Implemented in stage 7.
"""
from __future__ import annotations

from datetime import datetime
import logging
import re
from pathlib import Path

import jdatetime
import openpyxl
from openpyxl.styles import Alignment, Font

from backend import config, database
from backend.attendance_service import get_session_attendance, get_session_summary
from backend.errors import InvalidInputError, ReportEmptyError, SessionNotFoundError
from backend.session_manager import get_session
from backend.utils import parse_iso, setup_logging

logger = logging.getLogger(__name__)

STATUS_MAP = {
    "present": "حاضر",
    "late": "تأخیر",
    "absent": "غایب",
}

SOURCE_MAP = {
    "face": "چهره",
    "manual": "دستی",
}


def _get_course_title(course_id: int) -> str:
    """Get course title by ID."""
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT title FROM courses WHERE id = ?", (course_id,)
        ).fetchone()
        return row["title"] if row else f"درس {course_id}"
    finally:
        connection.close()


def _write_session_to_sheet(ws, session: dict, attendance: list[dict], summary: dict) -> None:
    """Write session attendance data to a worksheet."""
    ws.sheet_view.rightToLeft = True
    
    # Header info
    dt = parse_iso(session["started_at"])
    jalali = jdatetime.datetime.fromgregorian(datetime=dt)
    date_str = f"{jalali.year:04d}/{jalali.month:02d}/{jalali.day:02d}"
    time_str = f"{jalali.hour:02d}:{jalali.minute:02d}"
    
    course_title = _get_course_title(session["course_id"])
    
    ws["A1"] = f"گزارش حضور و غیاب: {course_title}"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = Alignment(horizontal="right", vertical="center")
    ws.merge_cells("A1:H1")

    ws["A2"] = f"تاریخ: {date_str} | ساعت شروع: {time_str}"
    ws["A2"].alignment = Alignment(horizontal="right", vertical="center")
    ws.merge_cells("A2:H2")

    ws["A3"] = f"آمار: حاضر: {summary['present']} | تأخیر: {summary['late']} | غایب: {summary['absent']} | کل: {summary['total']}"
    ws["A3"].alignment = Alignment(horizontal="right", vertical="center")
    ws.merge_cells("A3:H3")
    
    # Column headers
    headers = ["ردیف", "شماره دانشجویی", "نام و نام خانوادگی", "رشته", "ترم", "وضعیت", "ساعت ورود", "روش ثبت"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=6, column=col_num, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
        
    # Sort attendance
    is_all_numeric = all(str(a["student_id"]).isdigit() for a in attendance)
    sorted_attendance = sorted(
        attendance, 
        key=lambda x: int(x["student_id"]) if is_all_numeric else str(x["student_id"])
    )
    
    # Write rows
    for row_num, record in enumerate(sorted_attendance, 7):
        ws.cell(row=row_num, column=1, value=row_num - 6)
        ws.cell(row=row_num, column=2, value=record["student_id"])
        ws.cell(row=row_num, column=3, value=record["full_name"])
        ws.cell(row=row_num, column=4, value=record["major"])
        ws.cell(row=row_num, column=5, value=record["term"])
        ws.cell(row=row_num, column=6, value=STATUS_MAP.get(record["status"], record["status"]))
        
        if record["checked_at"]:
            checked_dt = parse_iso(record["checked_at"])
            ws.cell(row=row_num, column=7, value=checked_dt.strftime("%H:%M"))
        else:
            ws.cell(row=row_num, column=7, value="")
            
        if record["source"]:
            ws.cell(row=row_num, column=8, value=SOURCE_MAP.get(record["source"], record["source"]))
        else:
            ws.cell(row=row_num, column=8, value="")
            
    # Adjust column widths
    column_widths = [8, 15, 25, 15, 10, 10, 12, 10]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width


def export_session_report(session_id: int) -> Path:
    """Export attendance report for a specific session.
    
    Args:
        session_id: The ID of the session.
        
    Returns:
        Path to the generated Excel file.
        
    Raises:
        SessionNotFoundError: If the session does not exist.
    """
    setup_logging()
    session = get_session(session_id)
    attendance = get_session_attendance(session_id)
    summary = get_session_summary(session_id)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "گزارش جلسه"
    
    _write_session_to_sheet(ws, session, attendance, summary)
    
    # Generate filename
    dt = parse_iso(session["started_at"])
    jalali = jdatetime.datetime.fromgregorian(datetime=dt)
    date_str = f"{jalali.year:04d}-{jalali.month:02d}-{jalali.day:02d}"
    time_str = f"{jalali.hour:02d}{jalali.minute:02d}"
    filename = f"attendance_session{session_id}_{date_str}_{time_str}.xlsx"
    
    file_path = config.REPORTS_DIR / filename
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    wb.save(file_path)
    
    logger.info("Session report exported: %s", file_path)
    return file_path


def export_daily_report(date_iso: str) -> Path:
    """Export daily attendance report for all sessions on a given Gregorian date.
    
    Args:
        date_iso: The Gregorian date in YYYY-MM-DD format.
        
    Returns:
        Path to the generated Excel file.
        
    Raises:
        InvalidInputError: If date format is invalid, values are out of range, or a Shamsi date is passed.
        ReportEmptyError: If no sessions exist for the given date.
    """
    if not isinstance(date_iso, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", date_iso):
        raise InvalidInputError("فرمت تاریخ باید YYYY-MM-DD باشد.")
    
    try:
        parsed_date = datetime.strptime(date_iso, "%Y-%m-%d").date()
    except ValueError:
        raise InvalidInputError("تاریخ میلادی واردشده نامعتبر است.")
        
    if parsed_date.year < 1900:
        raise InvalidInputError("تاریخ باید به تقویم میلادی باشد؛ تاریخ شمسی پذیرفته نمی‌شود.")

    setup_logging()
    
    # Get all sessions and filter by Gregorian date (started_at[:10])
    connection = database.get_connection()
    try:
        rows = connection.execute("SELECT * FROM sessions ORDER BY started_at").fetchall()
    finally:
        connection.close()
        
    sessions = []
    for row in rows:
        started_at = row["started_at"]
        if started_at and started_at[:10] == date_iso:
            sessions.append(dict(row))
            
    if not sessions:
        raise ReportEmptyError()
        
    wb = openpyxl.Workbook()
    # Remove default sheet
    default_sheet = wb.active
    wb.remove(default_sheet)
    
    for session in sessions:
        attendance = get_session_attendance(session["id"])
        summary = get_session_summary(session["id"])
        
        course_title = _get_course_title(session["course_id"])
        # Clean sheet name: remove forbidden chars, limit to 31, ensure uniqueness with session ID
        clean_title = re.sub(r'[\\/:*?"\[\]]', '', f"{session['id']}_{course_title}")
        clean_title = clean_title[:31]
        
        ws = wb.create_sheet(title=clean_title)
        _write_session_to_sheet(ws, session, attendance, summary)
        
    filename = f"daily_report_{date_iso}.xlsx"
    file_path = config.REPORTS_DIR / filename
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    wb.save(file_path)
    
    logger.info("Daily report exported: %s", file_path)
    return file_path
```

---

<a id="backend-cli_format-py"></a>
## CLI Formatter (Boxes & Tables) (`backend/cli_format.py`)

```python
"""Terminal formatting utilities for CLI commands.

Provides ASCII box drawing and table formatting without external dependencies.
Safe for Windows PowerShell 5.1 and UTF-8 / ASCII consoles.
"""
from __future__ import annotations

import sys
from typing import Any, Sequence


def sanitize_text(text: Any, placeholder: str = "(Persian)") -> str:
    """Return placeholder if text contains non-ASCII characters, else ASCII text or '-'."""
    if text is None:
        return "-"
    s = str(text).strip()
    if not s:
        return "-"
    if any(ord(c) >= 128 for c in s):
        return placeholder
    return s


def print_box(
    title: str,
    items: list[tuple[str, Any]],
    min_width: int = 40,
    file=None,
) -> None:
    """Print an ASCII bordered box with key-value pairs aligned.

    Supports section dividers when key is '---' or None:
        - ('---', 'Section Title') creates an internal header '+-- Section Title ----+'
        - ('---', '') creates a simple horizontal line '+----------------------+'

    Example:
        +-- Session started ----------------+
        | Session ID   : 3                  |
        | Course ID    : 1                  |
        | Late after   : 10 min             |
        +-----------------------------------+
    """
    out = file if file is not None else sys.stdout

    if not items:
        content_width = max(min_width - 4, len(title) + 4)
        total_width = content_width + 4
        dash_count = max(0, total_width - len(title) - 6)
        top = f"+-- {title} " + ("-" * dash_count) + "+"
        bottom = "+" + ("-" * (total_width - 2)) + "+"
        print(top, file=out)
        print(bottom, file=out)
        return

    kv_items = [(str(k), str(v)) for k, v in items if k != "---" and k is not None]
    divider_titles = [str(v) for k, v in items if (k == "---" or k is None) and v]

    max_k = max((len(k) for k, _ in kv_items), default=0)
    max_v = max((len(v) for _, v in kv_items), default=0)
    max_div = max((len(t) for t in divider_titles), default=0)

    content_width = max(min_width - 4, len(title) + 4, max_k + max_v + 5, max_div + 4)
    total_width = content_width + 4

    dash_count = max(0, total_width - len(title) - 6)
    top = f"+-- {title} " + ("-" * dash_count) + "+"
    bottom = "+" + ("-" * (total_width - 2)) + "+"

    print(top, file=out)
    for k, v in items:
        if k == "---" or k is None:
            if v:
                sec_dash = max(0, total_width - len(str(v)) - 6)
                sec_line = f"+-- {v} " + ("-" * sec_dash) + "+"
                print(sec_line, file=out)
            else:
                sep_line = "+" + ("-" * (total_width - 2)) + "+"
                print(sep_line, file=out)
        else:
            line_content = f"{str(k):<{max_k}} : {str(v)}"
            padded = f"| {line_content:<{content_width}} |"
            print(padded, file=out)
    print(bottom, file=out)


def print_table(
    headers: list[str],
    rows: list[list[Any]],
    file=None,
) -> None:
    """Print a clean ASCII table with column headers and borders.

    Example:
        +------------+------------------+------+--------+-----------+
        | Student ID | Major            | Term | Photos | Embedding |
        +------------+------------------+------+--------+-----------+
        | S1001      | Computer Science | 4    | 4      | Yes       |
        +------------+------------------+------+--------+-----------+
    """
    out = file if file is not None else sys.stdout
    if not headers:
        return

    col_count = len(headers)
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for idx in range(min(col_count, len(row))):
            col_widths[idx] = max(col_widths[idx], len(str(row[idx])))

    border = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_line = "| " + " | ".join(f"{str(h):<{w}}" for h, w in zip(headers, col_widths)) + " |"

    print(border, file=out)
    print(header_line, file=out)
    print(border, file=out)
    for row in rows:
        padded_row = list(row) + [""] * (col_count - len(row))
        row_line = "| " + " | ".join(f"{str(cell):<{w}}" for cell, w in zip(padded_row, col_widths)) + " |"
        print(row_line, file=out)
    print(border, file=out)
```

---

<a id="backend-api-schemas-py"></a>
## FastAPI Pydantic Schemas (`backend/api/schemas.py`)

```python
"""Pydantic request and response schemas for the API."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str = "ok"


class StudentCreate(BaseModel):
    student_id: str
    full_name: str
    major: str = ""
    term: str = ""


class StudentUpdate(BaseModel):
    full_name: str | None = None
    major: str | None = None
    term: str | None = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: str
    full_name: str
    major: str = ""
    term: str = ""
    embedding_path: str | None = None
    photo_count: int = 0
    created_at: str
    has_embedding: bool = False


class ProcessPhotosResponse(BaseModel):
    accepted: int
    rejected: list[dict]
    warnings: list[dict]
    embedding_saved: bool


class CourseResponse(BaseModel):
    id: int
    title: str
    teacher: str = ""
    room: str = ""


class SessionStartRequest(BaseModel):
    course_id: int = 1
    late_after_minutes: int | None = None


class SessionCloseRequest(BaseModel):
    session_id: int | None = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    started_at: str
    ended_at: str | None = None
    late_after_minutes: int
    status: str


class AttendanceItem(BaseModel):
    student_id: str
    full_name: str
    major: str = ""
    term: str = ""
    status: str
    checked_at: str | None = None
    source: str | None = None


class SessionSummary(BaseModel):
    total: int
    present: int
    late: int
    absent: int


class SessionAttendanceResponse(BaseModel):
    attendance: list[AttendanceItem]
    summary: SessionSummary


class FaceItem(BaseModel):
    box: tuple[float, float, float, float]
    student_id: str | None = None
    distance: float


class RecognitionResponse(BaseModel):
    recorded: list[str]
    already_present: list[str]
    pending: dict[str, int]
    unknown_count: int
    faces: list[FaceItem]


class ErrorResponse(BaseModel):
    error: str
    message: str
```

---

<a id="backend-api-app-py"></a>
## FastAPI App Endpoints (`backend/api/app.py`)

```python
"""FastAPI application shell (routes only, no business logic).

Implemented in stage 8.
"""
from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import Body, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from backend import (
    attendance_service,
    config,
    database,
    enrollment,
    recognition,
    report_service,
    session_manager,
)
from backend.api.schemas import (
    CourseResponse,
    HealthResponse,
    ProcessPhotosResponse,
    RecognitionResponse,
    SessionAttendanceResponse,
    SessionCloseRequest,
    SessionResponse,
    SessionStartRequest,
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)
from backend.errors import (
    AppError,
    InvalidInputError,
    MultipleFacesError,
    NoActiveSessionError,
    NoFaceError,
    NotEnoughPhotosError,
    PayloadTooLargeError,
    ReportEmptyError,
    SessionAlreadyActiveError,
    SessionClosedError,
    SessionNotFoundError,
    StudentExistsError,
    StudentHasAttendanceError,
    StudentNotFoundError,
)
from backend.utils import normalize_digits, setup_logging

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

ERROR_STATUS_MAP: dict[type[AppError], int] = {
    StudentNotFoundError: 404,
    SessionNotFoundError: 404,
    ReportEmptyError: 404,
    StudentExistsError: 409,
    SessionAlreadyActiveError: 409,
    StudentHasAttendanceError: 409,
    SessionClosedError: 409,
    NoActiveSessionError: 409,
    InvalidInputError: 422,
    NotEnoughPhotosError: 422,
    NoFaceError: 422,
    MultipleFacesError: 422,
    PayloadTooLargeError: 413,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    database.init_db()
    yield


app = FastAPI(
    title="Smart Attendance API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError):
    status_code = 400
    for err_cls, code in ERROR_STATUS_MAP.items():
        if isinstance(exc, err_cls):
            status_code = code
            break
    return JSONResponse(
        status_code=status_code,
        content={"error": exc.code, "message": exc.message_fa},
    )


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "invalid_input", "message": "ورودی نامعتبر است."},
    )


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": str(exc.detail)},
    )


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #
@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
# Students
# --------------------------------------------------------------------------- #
@app.get("/students", response_model=list[StudentResponse])
def get_students():
    return enrollment.list_students()


@app.post("/students", response_model=StudentResponse)
def create_student(payload: StudentCreate):
    return enrollment.add_student(
        student_id=payload.student_id,
        full_name=payload.full_name,
        major=payload.major,
        term=payload.term,
    )


@app.put("/students/{id}", response_model=StudentResponse)
def update_student(id: str, payload: StudentUpdate):
    cleaned_id = normalize_digits(id)
    return enrollment.update_student(
        student_id=cleaned_id,
        full_name=payload.full_name,
        major=payload.major,
        term=payload.term,
    )


@app.delete("/students/{id}")
def delete_student(id: str, force: bool = False):
    cleaned_id = normalize_digits(id)
    success = enrollment.delete_student(student_id=cleaned_id, force=force)
    return {"success": success, "student_id": cleaned_id}


@app.post("/students/{id}/process-photos", response_model=ProcessPhotosResponse)
def process_photos(id: str):
    cleaned_id = normalize_digits(id)
    return enrollment.process_photos(student_id=cleaned_id)


# --------------------------------------------------------------------------- #
# Courses
# --------------------------------------------------------------------------- #
@app.get("/courses", response_model=list[CourseResponse])
def get_courses():
    return session_manager.list_courses()


# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #
@app.post("/sessions/start", response_model=SessionResponse)
def start_session(payload: SessionStartRequest | None = None):
    body = payload or SessionStartRequest()
    return session_manager.start_session(
        course_id=body.course_id,
        late_after_minutes=body.late_after_minutes,
    )


@app.post("/sessions/close", response_model=SessionResponse)
def close_session(payload: SessionCloseRequest | None = None):
    target_id = payload.session_id if payload is not None else None
    return session_manager.close_session(session_id=target_id)


@app.get("/sessions/active", response_model=SessionResponse | None)
def get_active_session():
    return session_manager.get_active_session()


@app.get("/sessions", response_model=list[SessionResponse])
def get_sessions(limit: int = 50):
    return session_manager.list_sessions(limit=limit)


# --------------------------------------------------------------------------- #
# Attendance & Recognition
# --------------------------------------------------------------------------- #
@app.get("/sessions/{id}/attendance", response_model=SessionAttendanceResponse)
def get_session_attendance(id: int):
    attendance = attendance_service.get_session_attendance(id)
    summary = attendance_service.get_session_summary(id)
    return {
        "attendance": attendance,
        "summary": summary,
    }


@app.post("/sessions/{id}/recognize", response_model=RecognitionResponse)
def recognize(id: int, file: UploadFile = File(...)):
    # Verify session exists and is active before doing heavy image processing
    session = session_manager.get_session(id)
    if session["status"] != "active":
        raise NoActiveSessionError()

    contents = file.file.read()
    if not contents:
        raise InvalidInputError("فایل تصویر خالی است.")
    if len(contents) > MAX_IMAGE_SIZE:
        raise PayloadTooLargeError()

    nparr = np.frombuffer(contents, np.uint8)
    bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise InvalidInputError("فایل ارسالی تصویر معتبری نیست.")

    matches = recognition.recognize_frame(bgr)
    result = attendance_service.process_recognition_result(
        session_id=id, matches=matches
    )
    result["faces"] = [
        {
            "box": match["box"],
            "student_id": match["student_id"],
            "distance": match["distance"],
        }
        for match in matches
    ]
    return result


@app.put("/sessions/{id}/attendance/{student_id}")
def log_manual_attendance(id: int, student_id: str):
    cleaned_id = normalize_digits(student_id)
    success = attendance_service.log_attendance(
        session_id=id,
        student_id=cleaned_id,
        source="manual",
    )
    result = {"success": success, "session_id": id, "student_id": cleaned_id}
    if not success:
        result["reason"] = "already_present"
    return result


@app.delete("/sessions/{id}/attendance/{student_id}")
def remove_manual_attendance(id: int, student_id: str):
    cleaned_id = normalize_digits(student_id)
    success = attendance_service.remove_attendance(
        session_id=id,
        student_id=cleaned_id,
    )
    return {"success": success, "session_id": id, "student_id": cleaned_id}


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #
@app.get("/sessions/{id}/report")
def export_session_report(id: int):
    file_path = report_service.export_session_report(session_id=id)
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/reports/daily")
def export_daily_report(date: str = Query(...)):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise InvalidInputError("فرمت تاریخ باید YYYY-MM-DD باشد.")
    file_path = report_service.export_daily_report(date_iso=date)
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
```

---

<a id="manage-py"></a>
## Management CLI Tool (`manage.py`)

```python
"""Non-interactive CLI commands (argparse).

Stage 9. Provides administrative CLI commands for initializing the database,
managing students, processing photos, controlling sessions, generating reports,
and running the API server.

Supports clean ASCII box/table formatting, UTF-8 output on Windows PowerShell 5.1,
zero Persian text in default English mode, and an explicit --lang flag ('en' by default, or 'fa').
"""
from __future__ import annotations

import argparse
import sys
from typing import Any

import jdatetime

from backend import attendance_service, config, database, enrollment, report_service, session_manager
from backend.cli_format import print_box, print_table, sanitize_text
from backend.errors import (
    AppError,
    InvalidInputError,
    NotEnoughPhotosError,
    ReportEmptyError,
    SessionNotFoundError,
    StudentExistsError,
    StudentNotFoundError,
)

# Configure output streams for clean UTF-8 on Windows PowerShell
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


ERROR_MESSAGES_EN: dict[str, str] = {
    "student_exists": "Student already exists.",
    "student_not_found": "Student not found.",
    "student_has_attendance": "Student has attendance records and cannot be deleted without --force.",
    "no_face": "No face found in image.",
    "multiple_faces": "Multiple faces found in image.",
    "not_enough_photos": "Not enough valid photos (minimum 3 required).",
    "session_already_active": "Another session is already active.",
    "no_active_session": "No active session found.",
    "session_not_found": "Session not found.",
    "session_closed": "Session is already closed.",
    "invalid_input": "Invalid input provided.",
    "report_empty": "No attendance records found for the requested report.",
    "payload_too_large": "Image payload is too large (maximum 10 MB).",
}


def _format_error(err: AppError, lang: str = "en") -> str:
    """Format AppError with stable code and language-specific text."""
    if lang == "fa":
        return f"خطا [{err.code}]: {err.message_fa}"

    msg = ERROR_MESSAGES_EN.get(err.code, f"An error occurred ({err.code}).")
    return f"Error [{err.code}]: {msg}"


def _format_bidi_name(name: str) -> str:
    """Shape Persian name for RTL display if arabic_reshaper/bidi are available."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return get_display(arabic_reshaper.reshape(name))
    except Exception:
        return name


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description="Smart Attendance System - Administrative CLI",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "fa"],
        default="en",
        help="Output language (default: en)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # 1. init-db
    subparsers.add_parser("init-db", help="Initialize database schema and default course")

    # 2. add-student
    p_add = subparsers.add_parser("add-student", help="Register student metadata")
    p_add.add_argument("--id", required=True, help="Unique student ID")
    p_add.add_argument("--name", required=True, help="Full name")
    p_add.add_argument("--major", default="", help="Academic major (optional)")
    p_add.add_argument("--term", default="", help="Academic term (optional)")

    # 3. delete-student
    p_del = subparsers.add_parser("delete-student", help="Delete a student record")
    p_del.add_argument("--id", required=True, help="Student ID to delete")
    p_del.add_argument(
        "--force",
        action="store_true",
        help="Force deletion even if student has attendance records",
    )

    # 4. process-photos
    p_photos = subparsers.add_parser("process-photos", help="Process photos and compute mean embedding")
    p_photos.add_argument("--id", required=True, help="Student ID")

    # 5. list-students
    p_list = subparsers.add_parser("list-students", help="List all registered students")
    p_list.add_argument(
        "--compact",
        action="store_true",
        help="Display compact table instead of individual cards",
    )
    p_list.add_argument(
        "--show-names",
        action="store_true",
        help="Print Persian full names in a separate section below the output",
    )

    # 6. start-session
    p_start = subparsers.add_parser("start-session", help="Start a new attendance session")
    p_start.add_argument("--course-id", type=int, default=1, help="Course ID (default: 1)")
    p_start.add_argument(
        "--late-after",
        type=int,
        default=None,
        help="Late threshold in minutes (default: 10)",
    )

    # 7. close-session
    p_close = subparsers.add_parser("close-session", help="Close an attendance session")
    p_close.add_argument(
        "--id",
        type=int,
        default=None,
        help="Session ID to close (defaults to currently active session)",
    )

    # 8. session-summary
    p_sum = subparsers.add_parser("session-summary", help="Display attendance summary for a specific session")
    p_sum.add_argument("--id", type=int, required=True, help="Session ID to inspect")

    # 9. status
    subparsers.add_parser("status", help="Display overall system summary and statistics")

    # 10. report
    p_report = subparsers.add_parser("report", help="Export Excel attendance report")
    r_group = p_report.add_mutually_exclusive_group(required=True)
    r_group.add_argument("--session-id", type=int, help="Single session ID to export")
    r_group.add_argument(
        "--daily",
        action="store_true",
        help="Export all sessions for a given date into a multi-sheet Excel file",
    )
    p_report.add_argument(
        "--date",
        default=None,
        help="Shamsi date for daily report (format: 1403-08-11 or 1403/08/11; default: today)",
    )

    # 11. run
    p_run = subparsers.add_parser("run", help="Run FastAPI server via uvicorn")
    p_run.add_argument("--host", default=None, help="Server host (default: 127.0.0.1)")
    p_run.add_argument("--port", type=int, default=None, help="Server port (default: 8000)")

    return parser


def _handle_init_db(lang: str) -> int:
    database.init_db()
    if lang == "fa":
        print_box(
            "مقداردهی اولیه پایگاه داده",
            [
                ("وضعیت", "موفقیت‌آمیز"),
                ("---", "جزئیات"),
                ("درس پیش‌فرض", "درس شماره ۱ ایجاد شد"),
                ("---", "گام بعدی"),
                ("گام بعدی", "ثبت دانشجو با 'manage.py add-student --id <id> --name <name>'"),
            ],
        )
    else:
        print_box(
            "Database Initialized",
            [
                ("Status", "Success"),
                ("---", "Details"),
                ("Default item", "Course #1 ready"),
                ("---", "Next Step"),
                ("Next step", "Register students with 'manage.py add-student --id <id> --name <name>'"),
            ],
        )
    return 0


def _handle_add_student(args: argparse.Namespace) -> int:
    try:
        student = enrollment.add_student(
            student_id=args.id,
            full_name=args.name,
            major=args.major,
            term=args.term,
        )
        if args.lang == "fa":
            print_box(
                "ثبت دانشجو",
                [
                    ("وضعیت", "موفقیت‌آمیز"),
                    ("---", "جزئیات"),
                    ("شماره دانشجویی", student["student_id"]),
                    ("نام و نام خانوادگی", _format_bidi_name(student["full_name"])),
                    ("رشته", student["major"] or "-"),
                    ("ترم", student["term"] or "-"),
                    ("---", "گام بعدی"),
                    ("گام بعدی", f"قرار دادن ۳ تا ۵ تصویر در known_faces/{student['student_id']}/ و سپس اجرای process-photos"),
                ],
            )
        else:
            print_box(
                "Student Registered",
                [
                    ("Status", "Success"),
                    ("---", "Details"),
                    ("Student ID", student["student_id"]),
                    ("Full Name", sanitize_text(student["full_name"], "(Persian name)")),
                    ("Major", sanitize_text(student["major"], "(Persian)")),
                    ("Term", sanitize_text(student["term"], "-")),
                    ("---", "Next Step"),
                    ("Next step", f"Put 3-5 photos in known_faces/{student['student_id']}/ then run process-photos"),
                ],
            )
        return 0
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_delete_student(args: argparse.Namespace) -> int:
    try:
        enrollment.delete_student(student_id=args.id, force=args.force)
        if args.lang == "fa":
            print_box(
                "حذف دانشجو",
                [
                    ("وضعیت", "با موفقیت حذف شد"),
                    ("---", "جزئیات"),
                    ("شماره دانشجویی", args.id),
                    ("اجباری (Force)", "بله" if args.force else "خیر"),
                    ("---", "گام بعدی"),
                    ("گام بعدی", "بررسی دانشجویان باقی‌مانده با 'manage.py list-students'"),
                ],
            )
        else:
            print_box(
                "Student Deleted",
                [
                    ("Status", "Successfully removed"),
                    ("---", "Details"),
                    ("Student ID", args.id),
                    ("Force", str(args.force)),
                    ("---", "Next Step"),
                    ("Next step", "Check remaining students with 'manage.py list-students'"),
                ],
            )
        return 0
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_process_photos(args: argparse.Namespace) -> int:
    try:
        res = enrollment.process_photos(student_id=args.id)
        saved = "Saved" if res.get("embedding_saved") else "Failed"
        saved_fa = "ذخیره شد" if res.get("embedding_saved") else "ناموفق"
        if args.lang == "fa":
            print_box(
                "پردازش تصاویر",
                [
                    ("وضعیت", "موفقیت‌آمیز"),
                    ("---", "جزئیات"),
                    ("شماره دانشجویی", args.id),
                    ("پذیرفته‌شده", res["accepted"]),
                    ("ردشده", len(res["rejected"])),
                    ("امبدینگ", saved_fa),
                    ("---", "گام بعدی"),
                    ("گام بعدی", "شروع جلسه حضور و غیاب با 'manage.py start-session'"),
                ],
            )
        else:
            print_box(
                "Photos Processed",
                [
                    ("Status", "Success"),
                    ("---", "Details"),
                    ("Student ID", args.id),
                    ("Accepted", res["accepted"]),
                    ("Rejected", len(res["rejected"])),
                    ("Embedding", saved),
                    ("---", "Next Step"),
                    ("Next step", "Start an attendance session with 'manage.py start-session'"),
                ],
            )
        return 0
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_list_students(args: argparse.Namespace) -> int:
    students = enrollment.list_students()
    if not students:
        if args.lang == "fa":
            print("هیچ دانشجویی در سیستم ثبت نشده است.")
        else:
            print("No students found in the database.")
        return 0

    total = len(students)
    with_emb = sum(1 for s in students if s.get("has_embedding"))
    without_emb = total - with_emb

    if args.compact:
        if args.lang == "fa":
            headers = ["شناسه", "رشته", "ترم", "عکس‌ها", "امبدینگ"]
            rows = [
                [
                    s["student_id"],
                    s.get("major") or "-",
                    s.get("term") or "-",
                    s.get("photo_count", 0),
                    "دارد" if s.get("has_embedding") else "ندارد",
                ]
                for s in students
            ]
            print_table(headers, rows)
            print(f"مجموع دانشجویان: {total} | دارای امبدینگ: {with_emb} | فاقد امبدینگ: {without_emb}")
        else:
            headers = ["Student ID", "Major", "Term", "Photos", "Embedding"]
            rows = [
                [
                    s["student_id"],
                    sanitize_text(s.get("major"), "(Persian)"),
                    s.get("term") or "-",
                    s.get("photo_count", 0),
                    "Yes" if s.get("has_embedding") else "No",
                ]
                for s in students
            ]
            print_table(headers, rows)
            print(f"Total students: {total} | With embedding: {with_emb} | Without: {without_emb}")
    else:
        for idx, s in enumerate(students, 1):
            if args.lang == "fa":
                title = f"دانشجو {idx} از {total}"
                items = [
                    ("شماره دانشجویی", s["student_id"]),
                    ("ترم", s.get("term") or "-"),
                    ("عکس‌ها", s.get("photo_count", 0)),
                    ("امبدینگ", "دارد" if s.get("has_embedding") else "ندارد"),
                ]
            else:
                title = f"Student {idx} of {total}"
                items = [
                    ("Student ID", s["student_id"]),
                    ("Term", s.get("term") or "-"),
                    ("Photos", s.get("photo_count", 0)),
                    ("Embedding", "Yes" if s.get("has_embedding") else "No"),
                ]
            print_box(title, items)

        if args.lang == "fa":
            print(f"مجموع دانشجویان: {total} | دارای امبدینگ: {with_emb} | فاقد امبدینگ: {without_emb}")
        else:
            print(f"Total students: {total} | With embedding: {with_emb} | Without: {without_emb}")

    if args.show_names:
        if args.lang == "fa":
            print("\nاسامی دانشجویان:")
            for s in students:
                print(f"  {s['student_id']}: {_format_bidi_name(s['full_name'])}")
        else:
            print("\nNames (Persian):")
            for s in students:
                print(f"  {s['student_id']}: {_format_bidi_name(s['full_name'])}")

    return 0


def _handle_start_session(args: argparse.Namespace) -> int:
    try:
        session = session_manager.start_session(
            course_id=args.course_id,
            late_after_minutes=args.late_after,
        )
        if args.lang == "fa":
            print_box(
                "شروع جلسه",
                [
                    ("وضعیت", "فعال"),
                    ("---", "جزئیات"),
                    ("شناسه جلسه", session["id"]),
                    ("شناسه درس", session["course_id"]),
                    ("حد تأخیر", f"{session['late_after_minutes']} دقیقه"),
                    ("زمان شروع", session["started_at"]),
                    ("---", "گام بعدی"),
                    ("گام بعدی", f"اجرای 'python main_test.py --session-id {session['id']}' جهت ثبت حضور"),
                ],
            )
        else:
            print_box(
                "Session Started",
                [
                    ("Status", "Active"),
                    ("---", "Details"),
                    ("Session ID", session["id"]),
                    ("Course ID", session["course_id"]),
                    ("Late after", f"{session['late_after_minutes']} min"),
                    ("Started at", session["started_at"]),
                    ("---", "Next Step"),
                    ("Next step", f"Run 'python main_test.py --session-id {session['id']}' to take attendance"),
                ],
            )
        return 0
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_close_session(args: argparse.Namespace) -> int:
    try:
        session = session_manager.close_session(session_id=args.id)
        if args.lang == "fa":
            print_box(
                "پایان جلسه",
                [
                    ("وضعیت", "بسته شد"),
                    ("---", "جزئیات"),
                    ("شناسه جلسه", session["id"]),
                    ("زمان شروع", session["started_at"]),
                    ("زمان پایان", session["ended_at"] or "-"),
                    ("---", "گام بعدی"),
                    ("گام بعدی", f"صدور گزارش اکسل با 'manage.py report --session-id {session['id']}'"),
                ],
            )
        else:
            print_box(
                "Session Closed",
                [
                    ("Status", "Closed"),
                    ("---", "Details"),
                    ("Session ID", session["id"]),
                    ("Started at", session["started_at"]),
                    ("Ended at", session["ended_at"] or "-"),
                    ("---", "Next Step"),
                    ("Next step", f"Export report with 'manage.py report --session-id {session['id']}'"),
                ],
            )
        return 0
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_session_summary(args: argparse.Namespace) -> int:
    try:
        session = session_manager.get_session(args.id)
        summary = attendance_service.get_session_summary(args.id)
        roster = attendance_service.get_session_attendance(args.id)

        if args.lang == "fa":
            items: list[tuple[str, Any]] = [
                ("وضعیت", session["status"]),
                ("زمان شروع", session["started_at"]),
                ("زمان پایان", session["ended_at"] or "-"),
                ("حد تأخیر", f"{session['late_after_minutes']} دقیقه"),
                ("---", "آمار حضور و غیاب"),
                ("حاضر", summary["present"]),
                ("تأخیر", summary["late"]),
                ("غایب", summary["absent"]),
                ("مجموع کلاس", summary["total"]),
                ("---", "فهرست وضعیت دانشجویان"),
            ]
            if roster:
                for r in roster:
                    src = " (چهره)" if r.get("source") == "face" else (" (دستی)" if r.get("source") == "manual" else "")
                    items.append((r["student_id"], f"{r['status']}{src}"))
            else:
                items.append(("فهرست", "هیچ دانشجویی ثبت نشده است"))
            print_box(f"خلاصه جلسه شماره {args.id}", items)
        else:
            items = [
                ("Status", session["status"]),
                ("Started at", session["started_at"]),
                ("Ended at", session["ended_at"] or "-"),
                ("Late threshold", f"{session['late_after_minutes']} min"),
                ("---", "Attendance Stats"),
                ("Present", summary["present"]),
                ("Late", summary["late"]),
                ("Absent", summary["absent"]),
                ("Total roster", summary["total"]),
                ("---", "Student Records"),
            ]
            if roster:
                for r in roster:
                    src = f" ({r['source']})" if r.get("source") else ""
                    items.append((r["student_id"], f"{r['status']}{src}"))
            else:
                items.append(("Roster", "No students registered"))
            print_box(f"Session #{args.id} Summary", items)
        return 0
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_status(lang: str) -> int:
    students = enrollment.list_students()
    total_students = len(students)
    with_emb = sum(1 for s in students if s.get("has_embedding"))
    without_emb = total_students - with_emb

    active_session = session_manager.get_active_session()
    if active_session:
        active_desc = f"Session #{active_session['id']} (started {active_session['started_at']})"
        active_desc_fa = f"جلسه شماره {active_session['id']} (شروع در {active_session['started_at']})"
    else:
        active_desc = "None"
        active_desc_fa = "ندارد"

    sessions = session_manager.list_sessions(limit=500)
    total_sessions = len(sessions)

    report_files = list(config.REPORTS_DIR.glob("*.xlsx")) if config.REPORTS_DIR.exists() else []
    total_reports = len(report_files)

    if lang == "fa":
        items = [
            ("وضعیت", "عملیاتی"),
            ("---", "دانشجویان"),
            ("کل دانشجویان", total_students),
            ("دارای امبدینگ", with_emb),
            ("فاقد امبدینگ", without_emb),
            ("---", "جلسات"),
            ("جلسه فعال", active_desc_fa),
            ("کل جلسات", total_sessions),
            ("---", "گزارش‌ها"),
            ("گزارش‌های اکسل", f"{total_reports} فایل در reports/"),
        ]
        print_box("وضعیت سامانه", items)
    else:
        items = [
            ("Status", "Operational"),
            ("---", "Students"),
            ("Total students", total_students),
            ("With embedding", with_emb),
            ("Without embedding", without_emb),
            ("---", "Sessions"),
            ("Active session", active_desc),
            ("Total sessions", total_sessions),
            ("---", "Reports"),
            ("Excel reports", f"{total_reports} files in reports/"),
        ]
        print_box("System Status", items)
    return 0


def _handle_report(args: argparse.Namespace) -> int:
    try:
        if args.session_id is not None:
            path = report_service.export_session_report(session_id=args.session_id)
            if args.lang == "fa":
                print_box(
                    "صدور گزارش جلسه",
                    [
                        ("وضعیت", "موفقیت‌آمیز"),
                        ("---", "جزئیات"),
                        ("شناسه جلسه", args.session_id),
                        ("مسیر فایل", str(path)),
                        ("---", "گام بعدی"),
                        ("گام بعدی", "باز کردن فایل گزارش در پوشه reports/"),
                    ],
                )
            else:
                print_box(
                    "Session Report Exported",
                    [
                        ("Status", "Success"),
                        ("---", "Details"),
                        ("Session ID", args.session_id),
                        ("File path", str(path)),
                        ("---", "Next Step"),
                        ("Next step", "Open Excel report file in reports/ directory"),
                    ],
                )
            return 0

        # args.daily
        if args.date:
            cleaned = args.date.strip().replace("/", "-")
            parts = cleaned.split("-")
            if len(parts) != 3 or not all(p.isdigit() for p in parts):
                err_msg = (
                    "خطا: فرمت تاریخ شمسی نامعتبر است. نمونه: 1403-08-11"
                    if args.lang == "fa"
                    else "Error [invalid_input]: Invalid Shamsi date format. Example: 1403-08-11"
                )
                print(err_msg, file=sys.stderr)
                return 1
            try:
                jy, jm, jd = int(parts[0]), int(parts[1]), int(parts[2])
                j_date = jdatetime.date(jy, jm, jd)
                g_date_iso = j_date.togregorian().isoformat()
            except Exception:
                err_msg = (
                    "خطا: تاریخ شمسی واردشده نامعتبر است."
                    if args.lang == "fa"
                    else "Error [invalid_input]: Invalid Shamsi calendar date."
                )
                print(err_msg, file=sys.stderr)
                return 1
        else:
            j_today = jdatetime.date.today()
            g_date_iso = j_today.togregorian().isoformat()

        path = report_service.export_daily_report(date_iso=g_date_iso)
        if args.lang == "fa":
            print_box(
                "صدور گزارش روزانه",
                [
                    ("وضعیت", "موفقیت‌آمیز"),
                    ("---", "جزئیات"),
                    ("تاریخ میلادی", g_date_iso),
                    ("مسیر فایل", str(path)),
                    ("---", "گام بعدی"),
                    ("گام بعدی", "باز کردن فایل گزارش روزانه در پوشه reports/"),
                ],
            )
        else:
            print_box(
                "Daily Report Exported",
                [
                    ("Status", "Success"),
                    ("---", "Details"),
                    ("Date", g_date_iso),
                    ("File path", str(path)),
                    ("---", "Next Step"),
                    ("Next step", "Open Excel report file in reports/ directory"),
                ],
            )
        return 0
    except ReportEmptyError:
        err_msg = (
            "خطا [report_empty]: هیچ جلسه‌ای برای صدور گزارش در این تاریخ یافت نشد."
            if args.lang == "fa"
            else "Error [report_empty]: No sessions found for the requested date."
        )
        print(err_msg, file=sys.stderr)
        return 1
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_run(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:  # pragma: no cover
        err_msg = (
            "خطا: ماژول uvicorn نصب نیست."
            if args.lang == "fa"
            else "Error: uvicorn module is not installed."
        )
        print(err_msg, file=sys.stderr)
        return 1

    host = args.host or config.API_HOST
    port = args.port or config.API_PORT
    uvicorn.run("backend.api.app:app", host=host, port=port, workers=1, reload=False)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    if getattr(args, "lang", "en") == "fa":
        print(
            "Warning: Windows PowerShell console may not render bidirectional Persian text correctly.\n",
            file=sys.stderr,
        )

    handlers = {
        "init-db": lambda: _handle_init_db(args.lang),
        "add-student": lambda: _handle_add_student(args),
        "delete-student": lambda: _handle_delete_student(args),
        "process-photos": lambda: _handle_process_photos(args),
        "list-students": lambda: _handle_list_students(args),
        "start-session": lambda: _handle_start_session(args),
        "close-session": lambda: _handle_close_session(args),
        "session-summary": lambda: _handle_session_summary(args),
        "status": lambda: _handle_status(args.lang),
        "report": lambda: _handle_report(args),
        "run": lambda: _handle_run(args),
    }

    handler = handlers.get(args.subcommand)
    if handler:
        return handler()
    return 1  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
```

---

<a id="main_test-py"></a>
## Live Camera & Video Recognition Test (`main_test.py`)

```python
"""Camera smoke test and live recognition loop.

Stage 9. Provides live video inspection:
- Default: Preview mode (detects and identifies faces, displays bounding boxes
  and Persian student names, does NOT record anything to database).
- Recording mode: When --session-id <id> is explicitly provided, verifies the
  session is active, processes frames every PROCESS_EVERY_N_FRAMES, and calls
  attendance_service.process_recognition_result.
- Connectivity test: --camera-test-only checks frame acquisition and exits.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any

import numpy as np

from backend import config

# Configure output streams for UTF-8
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger(__name__)

_FONT_CACHE: dict[int, Any] = {}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main_test.py",
        description="سامانه آزمون دوربین و حلقه زنده تشخیص چهره",
    )
    parser.add_argument(
        "--camera-source",
        default=None,
        help="منبع دوربین (اندیس وب‌کم یا آدرس RTSP/HTTP؛ پیش‌فرض از config خوانده می‌شود)",
    )
    parser.add_argument(
        "--camera-test-only",
        action="store_true",
        help="صرفاً تست اتصال به دوربین و دریافت فریم اولیه، بدون ورود به حلقه تشخیص",
    )
    parser.add_argument(
        "--session-id",
        type=int,
        default=None,
        help="شناسه جلسه فعال جهت ثبت خودکار حضور (در صورت عدم ارسال، برنامه در حالت پیش‌نمایش اجرا می‌شود)",
    )
    return parser


def _parse_camera_source(raw_source: Any) -> int | str:
    if raw_source is None:
        raw_source = config.CAMERA_SOURCE
    if isinstance(raw_source, str) and raw_source.isdigit():
        return int(raw_source)
    return raw_source


def _get_font(font_size: int = 20) -> Any:
    """Load and cache a TrueType font supporting Persian (Tahoma/Segoe UI)."""
    if font_size in _FONT_CACHE:
        return _FONT_CACHE[font_size]

    from PIL import ImageFont

    candidate_paths = [
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    font = None
    for path in candidate_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except Exception:
                continue

    if font is None:
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

    _FONT_CACHE[font_size] = font
    return font


def draw_label(
    frame: np.ndarray,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int] = (0, 255, 0),
    font_size: int = 20,
    fallback_ascii: str = "",
) -> np.ndarray:
    """Draw a Persian/RTL or ASCII text label onto a BGR OpenCV frame.

    Uses Pillow + arabic_reshaper + bidi for correct Persian letter shaping and RTL display.
    Falls back to cv2.putText with fallback_ascii (or text) if shaping or fonts fail.

    Args:
        frame: BGR numpy ndarray (OpenCV frame).
        text: Label string (Persian or ASCII).
        position: (x, y) coordinates for the top-left of the text.
        color: BGR tuple (e.g. (0, 255, 0) for green, (0, 0, 255) for red).
        font_size: Font size in points.
        fallback_ascii: ASCII string to use if Persian rendering fails.

    Returns:
        The modified frame (updated in-place when possible).
    """
    import cv2
    x, y = position

    try:
        from PIL import Image, ImageDraw
        import arabic_reshaper
        from bidi.algorithm import get_display

        font = _get_font(font_size)
        if font is None:
            raise RuntimeError("No suitable font available for Pillow rendering")

        # Reshape and reorder for Persian RTL display
        reshaped = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped)

        # Convert BGR to RGB for Pillow
        rgb_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(rgb_img)

        # Color in Pillow is RGB
        rgb_color = (color[2], color[1], color[0])
        draw.text((x, y), bidi_text, font=font, fill=rgb_color)

        # Convert back to BGR and update in-place
        bgr_result = cv2.cvtColor(np.asarray(rgb_img), cv2.COLOR_RGB2BGR)
        frame[:] = bgr_result
        return frame
    except Exception as exc:
        logger.warning("رسم متن فارسی با مشکل مواجه شد (%s)؛ استفاده از متن ASCII جایگزین.", exc)
        alt = fallback_ascii or text
        alt_ascii = "".join(c for c in alt if ord(c) < 128) or "Face"
        cv2.putText(
            frame,
            alt_ascii,
            (x, max(y + font_size, 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )
        return frame


def load_student_names() -> dict[str, str]:
    """Load mapping of student_id -> full_name once at startup."""
    try:
        from backend import database
        connection = database.get_connection()
        try:
            rows = connection.execute("SELECT student_id, full_name FROM students").fetchall()
            return {row["student_id"]: row["full_name"] for row in rows}
        finally:
            connection.close()
    except Exception as exc:
        logger.warning("خواندن نام دانشجویان از دیتابیس ناموفق بود: %s", exc)
        return {}


def run_camera_test(source: int | str, cap_override: Any = None) -> int:
    """Smoke test camera connectivity: grab 1 frame and print properties."""
    import cv2

    print(f"Connecting to camera: {source} ...")
    cap = cap_override if cap_override is not None else cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Error: Failed to open camera source '{source}'.", file=sys.stderr)
        return 1

    try:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Error: Failed to read frame from camera.", file=sys.stderr)
            return 1

        height, width = frame.shape[:2]
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        print("Camera connected successfully:")
        print(f"- Resolution: {width}x{height}")
        print(f"- Nominal FPS: {fps:.1f}")
        return 0
    finally:
        cap.release()


def run_live_loop(
    source: int | str,
    session_id: int | None = None,
    cap_override: Any = None,
    max_frames: int | None = None,
) -> int:
    """Run the video recognition loop.

    - If session_id is None: Preview mode (no database writes).
    - If session_id is provided: Attendance recording mode on the active session.
    """
    import cv2
    from backend import attendance_service, recognition, session_manager
    from backend.errors import AppError

    # Verify session if recording mode is requested
    if session_id is not None:
        try:
            session = session_manager.get_session(session_id)
            if session.get("status") != "active":
                print(
                    f"Error: Session {session_id} is not active (current status: {session.get('status')}).",
                    file=sys.stderr,
                )
                return 1
        except AppError as err:
            print(f"Error checking session: [{err.code}]", file=sys.stderr)
            return 1
        print(f"Recording mode active for session {session_id}. Press 'q' to exit.")
        window_title = f"Attendance System - Session {session_id} (Press Q to exit)"
    else:
        print("Preview mode active (no database writes). Press 'q' to exit.")
        window_title = "Attendance System - Preview Mode (Press Q to exit)"

    # Load student names ONCE at startup (not every frame)
    student_names = load_student_names()

    cap = cap_override if cap_override is not None else cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Error: Failed to open camera source '{source}'.", file=sys.stderr)
        return 1

    frame_count = 0
    last_faces: list[dict] = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Camera stream ended.")
                break

            frame_count += 1

            # Only process every N frames
            if frame_count % config.PROCESS_EVERY_N_FRAMES == 0:
                # Top-level face recognition function
                faces = recognition.recognize_frame(frame)

                if session_id is not None:
                    # Pass full matches structure directly to process_recognition_result
                    res = attendance_service.process_recognition_result(session_id, faces)
                    if res.get("recorded"):
                        for sid in res["recorded"]:
                            print(f"Attendance recorded: {sid}")

                last_faces = faces

            # Annotate frame
            h, w = frame.shape[:2]
            for face in last_faces:
                top_rel, right_rel, bottom_rel, left_rel = face["box"]
                top = max(0, int(top_rel * h))
                right = min(w, int(right_rel * w))
                bottom = min(h, int(bottom_rel * h))
                left = max(0, int(left_rel * w))

                student_id = face.get("student_id")

                if student_id is not None:
                    color = (0, 255, 0)  # Green for recognized
                    label = student_names.get(student_id, student_id)
                    fallback_ascii = student_id
                else:
                    color = (0, 0, 255)  # Red for unknown
                    label = "ناشناس"
                    fallback_ascii = "Unknown"

                # Draw bounding box
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                # Draw Persian label using Pillow
                label_pos = (left, max(top - 24, 4))
                draw_label(
                    frame=frame,
                    text=label,
                    position=label_pos,
                    color=color,
                    font_size=18,
                    fallback_ascii=fallback_ascii,
                )

            # Display window
            cv2.imshow(window_title, frame)

            if max_frames and frame_count >= max_frames:
                break

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # 'q' or ESC
                print("Exiting on user request.")
                break

        return 0
    finally:
        cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:  # pragma: no cover
            pass


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    source = _parse_camera_source(args.camera_source)

    if args.camera_test_only:
        return run_camera_test(source)

    return run_live_loop(source=source, session_id=args.session_id)


if __name__ == "__main__":
    sys.exit(main())
```

---

<a id="requirements-txt"></a>
## Requirements (`requirements.txt`)

```text
# Locked with pip freeze on Windows, Python 3.11.9 (64-bit).
#
# face_recognition is installed separately so pip never tries to build dlib
# from source (dlib-bin already provides the compiled dlib module):
#
#   pip install -r requirements.txt
#   pip install face_recognition==1.3.0 --no-deps

annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.15.1
certifi==2026.10.23
click==8.5.0
colorama==0.4.6
dlib-bin==20.0.1.post1
et_xmlfile==2.0.0
face_recognition_models==0.3.0
fastapi==0.162.0
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.20
iniconfig==2.3.1
jalali_core==1.0.0
jdatetime==6.1.1
numpy==1.26.4
opencv-python==4.11.0.86
openpyxl==3.1.5
opentelemetry-api==1.45.1
packaging==26.3
pillow==13.0.0
pluggy==1.7.0
pydantic==2.14.1
pydantic_core==2.50.1
Pygments==2.21.0
pytest==9.1.1
python-multipart==0.0.32
starlette==1.10.0
typing-inspection==0.4.4
typing_extensions==4.16.0
tzdata==2026.5
uvicorn==0.54.0
```

---

<a id="pytest-ini"></a>
## Pytest Configuration (`pytest.ini`)

```ini
[pytest]
testpaths = tests
addopts = --basetemp=.pytest_tmp
filterwarnings =
    ignore:.*Using `httpx` with `starlette\.testclient` is deprecated.*:Warning
```

---

<a id="-gitignore"></a>
## Git Ignore Configuration (`.gitignore`)

```text
venv/
__pycache__/
*.pyc
.env
known_faces/
embeddings/
data/
reports/
logs/
tests/data/
.claude/
.pytest_cache/
.pytest_tmp/
*_output.txt

.vscode/
```

---
