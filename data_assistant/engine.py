from dataclasses import dataclass
import pandas as pd
from .schema import AnalysisPlan


@dataclass
class AnalysisResult:
    table: pd.DataFrame
    filtered_rows: int
    full_result_rows: int
    notes: list[str]


def validate_plan(df, plan):
    # Re-validate even if the object was constructed outside Pydantic validation.
    p = AnalysisPlan.model_validate(plan.model_dump() if isinstance(plan, AnalysisPlan) else plan)
    if p.operation == "unsupported":
        raise ValueError("Bu soru desteklenen işlemlerle yanıtlanamıyor: " + p.explanation)
    required = p.group_by + p.columns + [f.column for f in p.filters]
    if p.metric is not None:
        required.append(p.metric)
    if any(c not in df.columns for c in required):
        raise ValueError("Plan, veride olmayan bir sütun kullanıyor.")
    if len(p.group_by) != len(set(p.group_by)) or len(p.columns) != len(set(p.columns)):
        raise ValueError("Plan aynı sütunu birden fazla kullanıyor.")
    if p.operation == "aggregate":
        if p.aggregation is None or (p.metric is None and p.aggregation != "count"):
            raise ValueError("Toplulaştırma için bir ölçüm ve işlem seçilmeli; satır sayımında ölçüm boş olabilir.")
        if p.columns:
            raise ValueError("Toplulaştırmada columns boş olmalı.")
        if p.aggregation in ("sum", "mean", "min", "max"):
            if not pd.api.types.is_numeric_dtype(df[p.metric]) or pd.api.types.is_bool_dtype(df[p.metric]):
                raise ValueError("Bu işlem için sayısal bir sütun gerekiyor; otomatik tip dönüşümü yapılmadı.")
        output_columns = p.group_by + ["__value__"]
    elif p.operation == "rows":
        if p.group_by or p.metric is not None or p.aggregation is not None:
            raise ValueError("Satır seçiminde toplulaştırma alanları boş olmalı.")
        output_columns = p.columns or list(df.columns)
    else:
        if p.group_by or p.columns or p.metric is not None or p.aggregation is not None or p.sort_by is not None or p.chart != "none":
            raise ValueError("Profil planında yalnızca filters ve limit kullanılabilir.")
        output_columns = []
    if p.sort_by is not None and p.sort_by not in output_columns:
        raise ValueError("Sıralama sütunu sonuç tablosunda bulunmuyor.")
    if p.chart != "none" and (p.operation != "aggregate" or len(p.group_by) != 1):
        raise ValueError("Grafik için tek gruplama sütunu ile toplulaştırma gerekiyor.")
    return p


def _filter(df, f):
    col = df[f.column]
    if f.op == "is_null":
        return col.isna()
    if f.op == "not_null":
        return col.notna()
    if f.value is None:
        raise ValueError("Bu filtrede değer gerekli; boşluk kontrolü için is_null kullan.")
    if f.op == "contains":
        if not isinstance(f.value, str):
            raise ValueError("contains için metin gerekiyor.")
        return col.astype("string").str.contains(f.value, regex=False, na=False)
    value = f.value
    if pd.api.types.is_numeric_dtype(col) and not pd.api.types.is_bool_dtype(col):
        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise ValueError("Sayısal filtreye sayı yazılmalı.")
    elif pd.api.types.is_datetime64_any_dtype(col):
        try:
            value = pd.Timestamp(value)
        except (ValueError, TypeError) as e:
            raise ValueError("Tarih filtresi geçersiz.") from e
    methods = {"eq": "eq", "ne": "ne", "gt": "gt", "ge": "ge", "lt": "lt", "le": "le"}
    try:
        return getattr(col, methods[f.op])(value).fillna(False) & col.notna()
    except (TypeError, ValueError) as e:
        raise ValueError("Filtre değeri sütun türüyle uyumlu değil.") from e


def execute(df, plan):
    p = validate_plan(df, plan)
    data = df.copy()
    for f in p.filters:
        data = data.loc[_filter(data, f)]
    notes = ["Kaynak veri değiştirilmedi. Filtreler AND ile birleştirildi."]
    if p.operation == "profile":
        rows = []
        for c in data.columns:
            s = data[c]
            numeric = pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)
            rows.append({"column": c, "dtype": str(s.dtype), "non_null": int(s.notna().sum()),
                         "missing": int(s.isna().sum()), "unique_non_null": int(s.nunique()),
                         "mean": s.mean() if numeric else None,
                         "min": s.min() if numeric else None, "max": s.max() if numeric else None})
        table = pd.DataFrame(rows)
    elif p.operation == "rows":
        table = data.loc[:, p.columns or list(data.columns)].copy()
    else:
        if p.group_by:
            grouped = data.groupby(p.group_by, dropna=False, observed=True, sort=True)
            if p.metric is None:
                values = grouped.size()
            elif p.aggregation == "sum":
                values = grouped[p.metric].sum(min_count=1)
            else:
                values = getattr(grouped[p.metric], p.aggregation)()
            table = values.rename("__value__").reset_index()
        else:
            if p.metric is None:
                value = len(data)
            elif p.aggregation == "sum":
                value = data[p.metric].sum(min_count=1)
            else:
                value = getattr(data[p.metric], p.aggregation)()
            table = pd.DataFrame({"__value__": [value]})
        notes.append(f"İşlem: {p.aggregation}; ölçüm: {p.metric or 'satır sayısı'}; boş grup anahtarları dahil.")
        notes.append("count: boş olmayan değer sayısı; ölçüm boşsa tüm satırlar. nunique: boş hariç farklı değer sayısı.")
        notes.append("sum/mean/min/max boş ölçümleri atlar; tümü boşsa sonuç boştur.")
    if p.sort_by:
        table = table.sort_values(p.sort_by, ascending=not p.descending, kind="stable", na_position="last")
    total = len(table)
    table = table.head(p.limit).reset_index(drop=True)
    if total > p.limit:
        notes.append(f"Sonuç {total} satır; yalnızca ilk {p.limit} satır gösteriliyor ve dışa aktarılıyor.")
    if data.empty:
        notes.append("Filtre sonrasında eşleşen kaynak satır bulunamadı.")
    return AnalysisResult(table, len(data), total, notes)
