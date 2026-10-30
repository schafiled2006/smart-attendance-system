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
