from io import BytesIO
from pathlib import Path
import csv
import pandas as pd

MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 100_000
MAX_COLUMNS = 100


def load_table(content: bytes, filename: str, *, separator=",", decimal=".", encoding="utf-8-sig", sheet=0):
    if not content or len(content) > MAX_BYTES:
        raise ValueError("Dosya boş veya 10 MB sınırını aşıyor.")
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        if separator not in [",", ";", "\t", "|"] or decimal not in [".", ","]:
            raise ValueError("Geçersiz CSV ayarı.")
        header = next(csv.reader(content.decode(encoding).splitlines(), delimiter=separator), [])
        _check_headers(header)
        df = pd.read_csv(BytesIO(content), sep=separator, decimal=decimal, encoding=encoding, nrows=MAX_ROWS + 1)
    elif suffix == ".xlsx":
        from zipfile import ZipFile
        with ZipFile(BytesIO(content)) as archive:
            if len(archive.infolist()) > 1000 or sum(f.file_size for f in archive.infolist()) > 80 * 1024 * 1024:
                raise ValueError("Excel dosyasının açılmış içeriği sınırı aşıyor.")
        # Check the raw header before pandas can silently rename duplicate columns.
        with pd.ExcelFile(BytesIO(content), engine="openpyxl") as book:
            header = pd.read_excel(book, sheet_name=sheet, header=None, nrows=1)
            _check_headers([] if header.empty else header.iloc[0].tolist())
            df = pd.read_excel(book, sheet_name=sheet, nrows=MAX_ROWS + 1)
    else:
        raise ValueError("Yalnızca .csv ve .xlsx destekleniyor.")
    if df.empty or len(df) > MAX_ROWS or len(df.columns) > MAX_COLUMNS:
        raise ValueError("Veri boş veya 100.000 satır / 100 sütun sınırını aşıyor.")
    df.columns = [str(c).strip() for c in df.columns]
    # Missing values stay missing; invalid infinities are rejected rather than hidden.
    numeric = df.select_dtypes(include="number")
    import numpy as np
    if np.isinf(numeric.to_numpy(dtype=float)).any():
        raise ValueError("Sayısal veride sonsuz değer var; önce veriyi düzelt.")
    return df


def _check_headers(header):
    names = [str(c).strip() for c in header]
    if not names or any(pd.isna(c) or not str(c).strip() for c in header):
        raise ValueError("Her sütunun boş olmayan bir başlığı olmalı.")
    if len(names) != len(set(names)):
        raise ValueError("Tekrarlanan sütun adlarını düzelt.")
    if len(names) > MAX_COLUMNS or any(len(c) > 120 or c.startswith("__") for c in names):
        raise ValueError("En fazla 100 sütun; adlar en fazla 120 karakter, '__' ile başlamamalı.")


def table_schema(df):
    # Only names/types, never sample rows, category values or computed statistics.
    return [{"name": str(c), "dtype": str(df[c].dtype)} for c in df.columns]


def quality(df):
    return {"rows": len(df), "columns": len(df.columns),
            "missing_cells": int(df.isna().sum().sum()), "duplicate_rows": int(df.duplicated().sum())}


def csv_bytes(df):
    # Spreadsheet formula injection protection for textual values only.
    safe = df.copy()
    def escape(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
    for c in safe.columns:
        if safe[c].dtype == object or pd.api.types.is_string_dtype(safe[c]):
            safe[c] = safe[c].map(escape)
    safe.columns = [escape(str(c)) for c in safe.columns]
    return safe.to_csv(index=False).encode("utf-8-sig")
