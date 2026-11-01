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

