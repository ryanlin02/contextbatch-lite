import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
import contextbatch_lite as lite


class LiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_text_cli_and_preserved_input(self):
        source = self.root / "a.txt"
        raw = b"Aster Studio\r\nDelivery: 14 days\r\n"
        source.write_bytes(raw)
        out = self.root / "a.md"
        run = subprocess.run([sys.executable, str(Path(lite.__file__)), str(source), str(out)], capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(out.read_text(), "Aster Studio\nDelivery: 14 days\n")
        self.assertEqual(source.read_bytes(), raw)

    def test_existing_output_preserved(self):
        source = self.root / "a.txt"; source.write_text("new")
        out = self.root / "a.md"; out.write_text("keep")
        with self.assertRaisesRegex(ValueError, "already exists"):
            lite.convert_file(source, out)
        self.assertEqual(out.read_text(), "keep")

    def test_docx(self):
        source = self.root / "a.docx"
        with zipfile.ZipFile(source, "w") as z:
            z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
            z.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
            z.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Aster Studio delivery</w:t></w:r></w:p></w:body></w:document>')
        out = self.root / "a.md"; lite.convert_file(source, out)
        self.assertIn("Aster Studio delivery", out.read_text())

    def test_real_pdf(self):
        source = self.root / "a.pdf"
        stream = b"BT /F1 12 Tf 30 100 Td (Aster delivery 14 days) Tj ET"
        objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>", b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"]
        data = bytearray(b"%PDF-1.4\n"); offsets = [0]
        for i, obj in enumerate(objects, 1):
            offsets.append(len(data)); data.extend(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
        xref = len(data)
        data.extend(b"xref\n0 6\n0000000000 65535 f \n")
        for offset in offsets[1:]: data.extend(f"{offset:010} 00000 n \n".encode())
        data.extend(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
        source.write_bytes(data)
        out = self.root / "a.md"; lite.convert_file(source, out)
        self.assertIn("Aster delivery 14 days", out.read_text())

    def test_invalid_pdf_leaves_no_output(self):
        source = self.root / "a.pdf"; source.write_text("not a PDF")
        out = self.root / "a.md"
        with self.assertRaisesRegex(ValueError, "Invalid PDF"):
            lite.convert_file(source, out)
        self.assertFalse(out.exists())

    def test_symlink_rejected(self):
        source = self.root / "a.txt"; source.write_text("original")
        link = self.root / "link.txt"; link.symlink_to(source)
        with self.assertRaisesRegex(ValueError, "symlink"):
            lite.convert_file(link, self.root / "a.md")

    def test_socket_guard_in_subprocess(self):
        code = "import sys,socket;from contextbatch_lite import no_network;sys.addaudithook(no_network);socket.getaddrinfo('example.com',443)"
        run = subprocess.run([sys.executable, "-c", code], cwd=Path(lite.__file__).parent, capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("Network access is disabled", run.stderr)


if __name__ == "__main__": unittest.main()
