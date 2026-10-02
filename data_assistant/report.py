from io import BytesIO
import base64
from html import escape
import json
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from .io import quality, csv_bytes


def plot_png(plan, result):
    if plan.chart == "none" or result.table.empty:
        return None
    table = result.table.head(50)
    fig = Figure(figsize=(9, 4.8), layout="constrained")
    ax = fig.subplots()
    labels = table[plan.group_by[0]].fillna("(boş)").astype(str).tolist()
    values = table["__value__"].to_numpy(dtype=float)
    if plan.chart == "bar":
        ax.bar(range(len(table)), values, color="#2463EB")
    else:
        ax.plot(range(len(table)), values, color="#2463EB", marker="o")
    ax.set_xticks(range(len(table)), labels, rotation=45, ha="right")
    ax.set_xlabel(plan.group_by[0])
    ax.set_ylabel(f"{plan.aggregation}({plan.metric or 'rows'})")
    ax.set_title("Analiz sonucu" + (" — ilk 50 satır" if len(result.table) > 50 else ""))
    ax.grid(axis="y", alpha=.2)
    output = BytesIO()
    fig.savefig(output, format="png", dpi=130)
    fig.clear()
    return output.getvalue()


def html_report(df, question, plan, result, mode):
    png = plot_png(plan, result)
    chart = '<img alt="Analiz grafiği" src="data:image/png;base64,' + base64.b64encode(png).decode() + '">' if png else ""
    q = quality(df)
    notes = "".join(f"<li>{escape(n)}</li>" for n in result.notes)
    plan_json = escape(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2))
    return f"""<!doctype html><html lang="tr"><meta charset="utf-8"><title>Veri analizi raporu</title>
<style>body{{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 24px;color:#172033}}
table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d7dee9;padding:8px;text-align:left}}
th{{background:#edf2fa}}img{{max-width:100%}}pre{{white-space:pre-wrap;background:#f2f5fa;padding:16px}}
@media print{{body{{margin:0}}}}</style>
<h1>AI Veri Analizi Asistanı</h1><p>Hazırlayan: Mert Nusret Sağlam · Mod: {escape(mode)}</p>
<h2>Soru</h2><p>{escape(question)}</p>
<h2>Veri özeti</h2><p>{q['rows']} satır · {q['columns']} sütun · {q['missing_cells']} boş hücre · {q['duplicate_rows']} tekrarlanan satır</p>
<p>Filtreye uyan kaynak satır: {result.filtered_rows}. Sonuç satırı: {result.full_result_rows}; aktarılan: {len(result.table)}.</p>
<h2>Sonuç</h2>{result.table.to_html(index=False, escape=True, na_rep='—')}{chart}
<h2>Hesaplama notları</h2><ul>{notes}</ul>
<p>Grafik en fazla 50 sonuç satırı içerir. Bulgular bu veri dosyası ve onaylanan planla sınırlıdır.
Demo hazır kuralları kullanır; LLM modunda yalnızca plan modelden gelir, sayılar Pandas ile hesaplanır.
Doğru hesaplama, modelin soruyu doğru yorumladığını tek başına kanıtlamaz.</p>
<h2>Uygulanan plan</h2><pre>{plan_json}</pre></html>""".encode("utf-8")


def save_bundle(directory, df, question, plan, result, mode):
    from pathlib import Path
    target = Path(directory)
    if target.exists():
        raise ValueError("Çıktı klasörü zaten var. Önceki çalışmayı korumak için yeni bir ad seç.")
    target.mkdir(parents=True)
    (target / "result.csv").write_bytes(csv_bytes(result.table))
    (target / "plan.json").write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    (target / "report.html").write_bytes(html_report(df, question, plan, result, mode))
    png = plot_png(plan, result)
    if png:
        (target / "chart.png").write_bytes(png)
    return target
