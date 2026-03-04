"""Translate 1TV Russian news articles to English using Argos Translate.

Processes a CSV with 'title' and 'content' columns, adding 'title_en' and
'content_en' columns. Supports checkpoint/resume for long-running jobs.
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path


def setup_argos():
    """Install the Russian→English model if not already present."""
    import argostranslate.package
    import argostranslate.translate

    installed = argostranslate.translate.get_installed_languages()
    lang_codes = {lang.code for lang in installed}

    if "ru" not in lang_codes or "en" not in lang_codes:
        print("Downloading Russian→English model...")
        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        pkg = next(
            (p for p in available if p.from_code == "ru" and p.to_code == "en"),
            None,
        )
        if pkg is None:
            print("ERROR: ru→en package not found in Argos index.")
            sys.exit(1)
        argostranslate.package.install_from_path(pkg.download())
        print("Model installed.")

    installed = argostranslate.translate.get_installed_languages()
    ru = next(lang for lang in installed if lang.code == "ru")
    en = next(lang for lang in installed if lang.code == "en")
    translator = ru.get_translation(en)
    return translator


def translate_text(translator, text: str) -> str:
    """Translate a single text string, handling empty/null values."""
    if not text or not isinstance(text, str) or text.strip() == "":
        return ""
    try:
        return translator.translate(text)
    except Exception as e:
        print(f"  Translation error: {e}")
        return ""


def load_checkpoint(checkpoint_path: Path) -> int:
    """Return the number of rows already translated (0 if no checkpoint)."""
    if checkpoint_path.exists():
        with open(checkpoint_path) as f:
            return int(f.read().strip())
    return 0


def save_checkpoint(checkpoint_path: Path, n: int):
    """Save the number of rows translated so far."""
    with open(checkpoint_path, "w") as f:
        f.write(str(n))


def main():
    parser = argparse.ArgumentParser(
        description="Translate 1TV news CSV from Russian to English."
    )
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=500,
        help="Save checkpoint every N rows (default: 500)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    checkpoint_path = output_path.with_suffix(".checkpoint")

    # Load input
    print(f"Loading {input_path}...")
    rows = []
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    print(f"Loaded {len(rows)} rows.")

    # Output fieldnames
    out_fields = list(fieldnames) + ["title_en", "content_en"]

    # Check for existing progress
    completed = load_checkpoint(checkpoint_path)
    if completed > 0:
        print(f"Resuming from row {completed} (found checkpoint).")

    # Setup translator
    print("Loading Argos Translate model...")
    translator = setup_argos()
    print("Model loaded. Starting translation...\n")

    # Open output file in append mode if resuming, write mode if fresh
    mode = "a" if completed > 0 else "w"
    write_header = completed == 0

    start_time = time.time()

    with open(output_path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        if write_header:
            writer.writeheader()

        for i in range(completed, len(rows)):
            row = rows[i]
            title = row.get("title", "")
            content = row.get("content", "")

            row["title_en"] = translate_text(translator, title)
            row["content_en"] = translate_text(translator, content)

            writer.writerow(row)

            # Progress reporting
            done = i + 1
            if done % 100 == 0 or done == len(rows):
                elapsed = time.time() - start_time
                rows_done_this_session = done - completed
                rate = rows_done_this_session / elapsed if elapsed > 0 else 0
                remaining = (len(rows) - done) / rate if rate > 0 else 0
                print(
                    f"  [{done}/{len(rows)}] "
                    f"{rate:.1f} rows/sec | "
                    f"ETA: {remaining/3600:.1f}h",
                    flush=True,
                )

            # Checkpoint
            if done % args.checkpoint_interval == 0:
                f.flush()
                save_checkpoint(checkpoint_path, done)

    # Final checkpoint
    save_checkpoint(checkpoint_path, len(rows))

    total_time = time.time() - start_time
    print(f"\nDone! Translated {len(rows)} rows in {total_time/3600:.1f}h.")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
