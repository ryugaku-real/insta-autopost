"""アップロードされた PDF / Word / txt から本文を取り出す。"""
import io

MAX_BYTES = 10 * 1024 * 1024


def extract(filename: str, data: bytes) -> str:
    if len(data) > MAX_BYTES:
        raise ValueError("ファイルは10MBまでです")
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
        if not text.strip():
            raise ValueError("文字を取り出せませんでした(スキャン画像のPDFは非対応です)")
        return text
    if name.endswith(".docx"):
        from docx import Document

        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    if name.endswith((".txt", ".md")):
        for enc in ("utf-8", "cp932"):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                pass
        raise ValueError("文字コードを判別できませんでした")
    raise ValueError("対応形式は PDF / .docx / .txt です(古い .doc は非対応)")
