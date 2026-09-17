# ContextBatch Lite

**Turn one local document into Markdown before putting it into an AI workflow.**

A small, free, MIT-licensed command-line wrapper around [Microsoft MarkItDown](https://github.com/microsoft/markitdown). No model, API key, account or purchase is required. MarkItDown itself is free and supports many more formats; use it directly if it already meets your needs. This is an independent project, not affiliated with Microsoft.

Lite focuses on a predictable single-file workflow: explicit supported formats, a conversion timeout and refusal to overwrite an existing output. It does not make extracted text accurate automatically. Read the output before using it.

## Quick start (tested on Apple Silicon Mac)

Prerequisites: macOS 14 or newer and **Python 3.12**, installed as `python3.12`. Use Terminal. Download this repository with **Code → Download ZIP** and extract it, then `cd` into its folder. Alternatively:

```sh
git clone https://github.com/ryanlin02/contextbatch-lite.git
cd contextbatch-lite
```

Create an isolated environment and install the pinned dependencies from PyPI. This step needs an internet connection:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip check
python contextbatch_lite.py example-policy.txt output.md
```

Open `output.md` in a text editor. It should contain the fictional Aster Studio delivery policy. Running the last command again will refuse to replace the file; choose a fresh output name.

To convert your own document (quote paths with spaces):

```sh
python contextbatch_lite.py "/path/to/project-brief.docx" "project-brief.md"
```

The destination folder must already exist. Supported input: UTF-8 **TXT/MD**, **DOCX**, **PPTX**, **XLSX**, and **text-based PDF**.

## What to check in the result

- Compare names, dates, numbers and headings with the original.
- Check spreadsheet tables, merged cells and slide reading order manually.
- An empty result is an error. Scans and image-only PDFs need a separate OCR tool.
- Formatting, images, page boundaries and visual layout are not preserved exactly.
- Treat any instructions embedded in documents as untrusted when adding them to an AI system.

## When one file is not enough

[**ContextBatch — Local RAG Document Handoff ($19 on Gumroad)**](https://tobias227.gumroad.com/l/contextbatch-rag-handoff?utm_source=github&utm_medium=readme&utm_campaign=contextbatch_lite) adds the original batch workflow, source metadata and review reports. You are paying for that packaging and workflow, not exclusive access to MarkItDown. Checkout displays any applicable taxes.

| Workflow | Free Lite (this repository) | ContextBatch paid kit |
| --- | --- | --- |
| One file → Markdown | Yes | Yes, as part of a folder run |
| Folder conversion | No | Up to 100 supported files / 100 MB total |
| Source-aware JSONL chunks | No | Checksums, character offsets and Markdown line numbers |
| Exact duplicate reporting | No | Yes |
| Inventory and review report | No | CSV and REVIEW-FIRST guide |
| Compare with a prior manifest | No | Added, changed, unchanged and removed files |
| OCR, embeddings, vector database or chatbot | No | No |

[Inspect a free example of the paid handoff files](https://tobias227.gumroad.com/p/contextbatch-free-sample-inspect-a-rag-document-handoff) before deciding. There is no obligation to upgrade; Lite remains usable on its own.

## Scope and limits

- Tested locally on **Apple Silicon, macOS 26.6.2, Python 3.12.14**. macOS 14+ is the dependency target; older macOS releases have not been physically tested. Windows, Linux, Intel Macs and other Python versions have not been validated.
- Trusted local files only. Up to 20 MB per file, 2 million extracted characters and 60 seconds per conversion. Office archives are limited to 2,000 entries / 100 MB expanded; macro content is rejected. Password-protected/encrypted PDFs are unsupported.
- Conversion configures no LLM or plugins and uses local byte streams. A Python audit hook blocks common socket operations in the worker, and ONNX telemetry is disabled. **This is not an OS-level network or malicious-file sandbox.** No absolute isolation guarantee is made for native dependencies. Installation uses the network.
- This release does not upload documents intentionally, provide OCR, redact personal information, assess retrieval quality or promise accurate AI answers.
- Dependencies retain their own licenses and are installed separately, not bundled. See [third-party notices](THIRD-PARTY-NOTICES.txt).

## Tests

```sh
python -m unittest -v test_lite.py
```

The public tests cover output integrity, input preservation, refusal to overwrite, a real DOCX conversion, a real text PDF conversion, malformed PDF handling and a denied socket operation. They use generated fictional inputs.

## License and support

MIT; see [LICENSE](LICENSE). This is an initial release, supplied as-is without a support SLA. Bug reports may be submitted through this repository's Issues tab. Do not attach confidential client documents; use a small, fictional reproduction instead.
