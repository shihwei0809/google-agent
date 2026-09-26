from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader


def extract_pdf(pdf_path: Path, output_dir: Path) -> Path:
    reader = PdfReader(str(pdf_path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    output_path = output_dir / f"{pdf_path.stem}.txt"
    output_path.write_text(text, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract PDF text to UTF-8 .txt files.")
    parser.add_argument("--input-dir", default=".", help="Directory containing PDF files.")
    parser.add_argument("--pattern", default="*.pdf", help="Glob pattern for PDFs.")
    parser.add_argument("--output-dir", default=".", help="Directory for text outputs.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    matched = sorted(input_dir.glob(args.pattern))
    if not matched:
        raise SystemExit(f"No PDFs matched pattern {args.pattern!r} in {input_dir}")

    for pdf_path in matched:
        out = extract_pdf(pdf_path, output_dir)
        print(f"{pdf_path.name} -> {out.name}")


if __name__ == "__main__":
    main()
