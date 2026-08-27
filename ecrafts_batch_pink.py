from pathlib import Path
import argparse
import sys

import cv2
import numpy as np


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

INPUT_DIR = Path(r"C:\Users\orlyn\Desktop\אני\Ecrafts\קטלוג\מוצרים")
OUTPUT_DIR = Path(r"C:\Users\orlyn\Desktop\אני\Ecrafts\קטלוג\מוצרים_ערוכים")

TARGET_RGB = np.array([250, 236, 239], dtype=np.float32)
PINK_STRENGTH = 0.72
HIGHLIGHT_REDUCTION = 0.18

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".tif",
    ".tiff",
}


def read_image(path):
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def save_image(path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    extension = path.suffix.lower()

    if extension in {".jpg", ".jpeg"}:
        success, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    elif extension == ".png":
        success, encoded = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    elif extension == ".webp":
        success, encoded = cv2.imencode(".webp", image, [cv2.IMWRITE_WEBP_QUALITY, 95])
    elif extension in {".tif", ".tiff"}:
        success, encoded = cv2.imencode(".tiff", image)
    else:
        return False

    if not success:
        return False

    encoded.tofile(str(path))
    return True


def create_background_mask(image_bgr):
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    saturation = hsv[..., 1] / 255.0
    value = hsv[..., 2] / 255.0

    neutral = np.clip((0.48 - saturation) / 0.48, 0, 1)
    bright = np.clip((value - 0.35) / 0.50, 0, 1)
    mask = neutral * bright

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    dark_protection = np.clip((gray - 0.25) / 0.35, 0, 1)
    mask *= dark_protection

    mask = cv2.GaussianBlur(mask, (0, 0), 3.0)
    return np.clip(mask, 0, 1)


def make_soft_pink(image_bgr):
    mask = create_background_mask(image_bgr)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

    luminance = 0.76 + 0.34 * gray
    pink_layer = TARGET_RGB[None, None, :] * luminance[..., None]
    pink_layer = np.clip(pink_layer, 0, 255)

    alpha = (mask * PINK_STRENGTH)[..., None]
    result = image_rgb * (1 - alpha) + pink_layer * alpha
    result = np.clip(result, 0, 255).astype(np.uint8)

    return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)


def reduce_highlights(image_bgr):
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    lightness = lab[..., 0] / 255.0

    highlight_mask = np.clip((lightness - 0.87) / 0.13, 0, 1)
    highlight_mask = cv2.GaussianBlur(highlight_mask, (0, 0), 2.0)

    lab[..., 0] *= 1.0 - HIGHLIGHT_REDUCTION * highlight_mask
    lab[..., 0] = np.clip(lab[..., 0], 0, 255)

    return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)


def edit_image(image):
    return reduce_highlights(make_soft_pink(image))


def collect_files(input_dir):
    return [
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def parse_args():
    parser = argparse.ArgumentParser(description="Ecrafts batch photo editor")
    parser.add_argument("--input", type=Path, default=INPUT_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--limit", type=int, default=0, help="Edit only the first N images for testing.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-edit all images, including outputs that are already up to date.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_dir = args.input
    output_dir = args.output

    if not input_dir.exists():
        print("לא מצאתי את תיקיית המוצרים:")
        print(input_dir)
        return 1

    files = collect_files(input_dir)
    if args.limit > 0:
        files = files[: args.limit]

    print()
    print("==============================")
    print(" Ecrafts batch photo editor")
    print("==============================")
    print()
    print(f"נמצאו לעריכה: {len(files)} תמונות.")
    print()

    if not files:
        print("לא נמצאו תמונות.")
        return 0

    successful = 0
    skipped = 0
    failed = 0

    for index, source_path in enumerate(files, start=1):
        relative_path = source_path.relative_to(input_dir)
        output_path = output_dir / relative_path
        print(f"[{index}/{len(files)}] {relative_path}")

        if not args.force and output_path.exists() and output_path.stat().st_mtime >= source_path.stat().st_mtime:
            print("   ללא שינוי - דילוג")
            skipped += 1
            continue

        image = read_image(source_path)
        if image is None:
            print("   לא הצלחתי לקרוא את התמונה")
            failed += 1
            continue

        try:
            edited = edit_image(image)
            if save_image(output_path, edited):
                successful += 1
            else:
                print("   שגיאה בשמירה")
                failed += 1
        except Exception as error:
            print(f"   שגיאה: {error}")
            failed += 1

    print()
    print("==============================")
    print("סיימתי!")
    print("==============================")
    print()
    print(f"נערכו בהצלחה: {successful}")
    print(f"דולגו ללא שינוי: {skipped}")
    print(f"שגיאות: {failed}")
    print()
    print("המקוריות נשארו כאן:")
    print(input_dir)
    print()
    print("התמונות הערוכות נמצאות כאן:")
    print(output_dir)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
