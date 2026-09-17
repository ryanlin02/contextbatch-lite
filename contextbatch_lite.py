#!/usr/bin/env python3
"""ContextBatch Lite 1.0: one local document to Markdown. MIT license."""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

SUPPORTED = {".txt", ".md", ".docx", ".pptx", ".xlsx", ".pdf"}
MAX_FILE = 20 * 1024 * 1024
MAX_TOTAL = 100 * 1024 * 1024
MAX_TEXT = 2_000_000

def no_network(event, args):
    if event in {"socket.connect", "socket.connect_ex", "socket.getaddrinfo", "socket.sendto"}:
        raise PermissionError("Network access is disabled during conversion")

def worker(path):
    """Run in a short-lived subprocess, with no configured LLMs or plugins."""
    sys.addaudithook(no_network)
    data = path.read_bytes()
    if path.suffix.lower() in {".txt", ".md"}:
        text = data.decode("utf-8-sig")
    else:
        import onnxruntime
        onnxruntime.disable_telemetry_events()
        from markitdown import MarkItDown
        from markitdown.converters import DocxConverter, PptxConverter, XlsxConverter, PdfConverter
        if path.suffix.lower() == ".pdf":
            # Prevent MarkItDown's permissive fallback from treating a renamed text file as a PDF.
            if not data.startswith(b"%PDF-"):
                raise ValueError("Invalid PDF header")
            import pdfplumber
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                if pdf.doc.encryption or not pdf.pages:
                    raise ValueError("Encrypted or empty PDFs are not supported")
        if path.suffix.lower() in {".docx", ".pptx", ".xlsx"}:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                infos = archive.infolist()
                if len(infos) > 2000 or sum(i.file_size for i in infos) > MAX_TOTAL:
                    raise ValueError("Office archive exceeds expanded-size or member limit")
                if any("vbaproject" in i.filename.lower() for i in infos):
                    raise ValueError("Macro content is not supported")
                expected = {".docx": "word/document.xml", ".pptx": "ppt/presentation.xml", ".xlsx": "xl/workbook.xml"}[path.suffix.lower()]
                if expected not in archive.namelist():
                    raise ValueError("Office file does not match its extension")
        # A byte stream cannot resolve a URL supplied as a path.
        converter = MarkItDown(enable_builtins=False, enable_plugins=False)
        converter.register_converter({".docx": DocxConverter, ".pptx": PptxConverter,
                                      ".xlsx": XlsxConverter, ".pdf": PdfConverter}[path.suffix.lower()]())
        result = converter.convert_stream(
            io.BytesIO(data), file_extension=path.suffix.lower()
        )
        text = result.text_content
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "").strip()
    if len(text) > MAX_TEXT:
        raise ValueError("Extracted text exceeds two million characters")
    return text + "\n" if text else ""

def convert(path, timeout):
    try:
        run = subprocess.run([sys.executable, str(Path(__file__).resolve()), "_worker", str(path)],
                             capture_output=True, timeout=timeout, text=True, encoding="utf-8")
    except subprocess.TimeoutExpired:
        return None, "Conversion timed out; original was not modified"
    try:
        response = json.loads(run.stdout)
        if response.get("ok") and run.returncode == 0:
            return response["text"], None
        return None, response.get("error", "Conversion failed")
    except (ValueError, KeyError):
        return None, "Converter process failed; check installation and input validity"

def convert_file(source, destination):
    source = source.expanduser()
    destination = destination.expanduser()
    if source.is_symlink() or not source.is_file():
        raise ValueError("Input must be a regular local file, not a symlink")
    source = source.resolve(strict=True)
    if source.suffix.lower() not in SUPPORTED:
        raise ValueError("Supported formats: TXT, MD, DOCX, PPTX, XLSX, text-based PDF")
    if source.stat().st_size > MAX_FILE:
        raise ValueError("Input exceeds 20 MB")
    if destination.suffix.lower() != ".md":
        raise ValueError("Choose a new output filename ending in .md")
    if destination.exists() or destination.is_symlink():
        raise ValueError("Output already exists; choose a new filename")
    if not destination.parent.is_dir():
        raise ValueError("Output parent folder must already exist")
    text, error = convert(source, timeout=60)
    if error:
        raise ValueError(error)
    if not text.strip():
        raise ValueError("No text extracted. Scanned PDFs need a separate OCR workflow")
    # Exclusive creation prevents overwriting even if a file appears during conversion.
    with destination.open("x", encoding="utf-8") as out:
        out.write(text)
    return len(text)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "_worker":
        try:
            path = Path(sys.argv[2])
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE:
                raise ValueError("Input must be a regular file of at most 20 MB")
            print(json.dumps({"ok": True, "text": worker(path)}))
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 1
        return 0
    parser = argparse.ArgumentParser(description="Convert one local document to Markdown without a model or API key.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, help="New .md file; parent folder must exist")
    args = parser.parse_args()
    try:
        count = convert_file(args.input, args.output)
    except (OSError, ValueError) as exc:
        print(f"Could not convert: {exc}", file=sys.stderr)
        return 1
    print(f"Created {args.output} ({count} characters). Review the extracted text before use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
