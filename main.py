from ultralytics import YOLO
import cv2
import sys
import numpy as np
from pathlib import Path

# Fix for some Ubuntu/WSL environments with display issues
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')

MODEL_PATH = "best.pt"
CONF_THRESHOLD = 0.25
SAVE_OUTPUT = True

model = YOLO(MODEL_PATH)


def process_image(source):
    results = model.predict(source=source, conf=CONF_THRESHOLD, save=SAVE_OUTPUT, show=False)
    for r in results:
        print(f"\n--- {Path(source).name} ---")
        for box in r.boxes:
            cls_name = model.names[int(box.cls)]
            conf = float(box.conf)
            xyxy = box.xyxy[0].tolist()
            print(f"  {cls_name}: {conf:.2f}  bbox={[round(x) for x in xyxy]}")
        if SAVE_OUTPUT:
            print(f"  Saved → {r.save_dir}")


def process_video(source, output_path=None):
    """
    source: path to video file, or integer (0, 1...) for webcam, or RTSP URL string.
    output_path: optional path to save annotated video (e.g. "out.mp4")
    """
    # Open source — int for webcam, string for file/RTSP
    cap = cv2.VideoCapture(int(source) if str(source).isdigit() else source)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open source: {source}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] Stream opened — {width}x{height} @ {fps:.1f} fps")

    # Test read one frame to validate
    ret, test_frame = cap.read()
    if not ret or test_frame is None:
        print("[ERROR] Cannot read frames from source")
        cap.release()
        return
    print(f"[DEBUG] First frame OK: {test_frame.shape}")
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning for files

    # Create window explicitly BEFORE the loop (critical fix)
    window_name = "seadroneML — press Q to quit"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, width, height)
    cv2.startWindowThread()  # Helps on some Linux systems

    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        print(f"[INFO] Writing output → {output_path}")

    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[INFO] Stream ended.")
                break

            # Validate frame
            if frame is None or frame.size == 0:
                print(f"[WARN] Empty frame at {frame_count}, skipping")
                continue

            # Run inference on the raw BGR frame
            results = model.predict(source=frame, conf=CONF_THRESHOLD, save=False, show=False, verbose=False)
            r = results[0]

            # Draw boxes
            annotated = r.plot()  # returns BGR numpy array with boxes drawn

            # Fallback if plot returns None or empty
            if annotated is None or annotated.size == 0:
                print(f"[WARN] Empty annotation at frame {frame_count}, using original")
                annotated = frame.copy()
            
            # Ensure correct format for display
            if annotated.dtype != np.uint8:
                annotated = annotated.astype(np.uint8)

            # Print detections every 30 frames to avoid terminal spam
            if frame_count % 30 == 0:
                dets = [(model.names[int(b.cls)], float(b.conf)) for b in r.boxes]
                if dets:
                    print(f"  frame {frame_count}: " + ", ".join(f"{n} {c:.2f}" for n, c in dets))

            if writer:
                writer.write(annotated)

            # Show frame (critical: waitKey needed for window update)
            cv2.imshow(window_name, annotated)
            key = cv2.waitKey(1) & 0xFF  # 1ms delay allows window to render
            
            if key == ord("q"):
                print("[INFO] Quit by user.")
                break

            frame_count += 1

    except KeyboardInterrupt:
        print("[INFO] Interrupted by user (Ctrl+C)")
        
    finally:
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        # Extra cleanup for Linux
        cv2.waitKey(100)
        print(f"[INFO] Processed {frame_count} frames.")


# ── Entry point ────────────────────────────────────────────────────────────────
sources = sys.argv[1:] if len(sys.argv) > 1 else ["test.jpg"]

VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".ts"}

for source in sources:
    p = Path(source)
    is_webcam = source.isdigit()                        # "0", "1", …
    is_rtsp = source.startswith(("rtsp://", "http://", "https://"))
    is_video = p.suffix.lower() in VIDEO_EXTS

    if is_webcam or is_rtsp or is_video:
        out = str(p.with_stem(p.stem + "_annotated").with_suffix(".mp4")) if is_video else None
        process_video(source, output_path=out)
    else:
        process_image(source)
