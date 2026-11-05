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
