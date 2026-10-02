from pathlib import Path
import hashlib
import json
import streamlit as st
from data_assistant.io import load_table, quality, csv_bytes
from data_assistant.planner import DEMO_QUESTIONS, demo_plan, llm_plan
from data_assistant.engine import execute, validate_plan
from data_assistant.report import html_report, plot_png

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="AI Veri Analizi Asistanı", page_icon="📊", layout="wide")
st.title("AI Veri Analizi Asistanı")
st.caption("Mert Nusret Sağlam · Python / Pandas / LangChain / Streamlit")

with st.sidebar:
    st.header("Veri ve çalışma modu")
    mode = st.radio("Mod", ["Demo (API gerektirmez)", "LLM (OpenAI API)"])
    use_sample = st.checkbox("Örnek satış verisini kullan", value=True)
    uploaded = None if use_sample else st.file_uploader("CSV veya Excel yükle", type=["csv", "xlsx"])
    separator = st.selectbox("CSV ayırıcı", [",", ";", "\t", "|"])
    decimal = st.selectbox("Ondalık işareti", [".", ","])
    encoding = st.selectbox("CSV karakter kodlaması", ["utf-8-sig", "cp1254", "latin1"])
    sheet = st.number_input("Excel sayfa numarası (0 = ilk)", min_value=0, value=0, step=1)
    st.caption("Sınırlar: 10 MB, 100.000 satır, 100 sütun. Excel formülleri için son kaydedilmiş değerler okunur.")

if use_sample:
    content = (ROOT / "sample_data" / "sales.csv").read_bytes()
    filename = "sales.csv"
    # The bundled example has fixed parsing settings.
    separator, decimal, encoding, sheet = ",", ".", "utf-8-sig", 0
elif uploaded is None:
    st.info("Soldan bir veri dosyası yükle veya örnek veriyi aç.")
    st.stop()
else:
    content, filename = uploaded.getvalue(), uploaded.name

try:
    df = load_table(content, filename, separator=separator, decimal=decimal, encoding=encoding, sheet=int(sheet))
except Exception as e:
    if isinstance(e, (ValueError, UnicodeError)):
        st.error("Dosya okunamadı: " + str(e))
    else:
        st.error("Dosya okunamadı. Biçim, başlıklar ve sayfa numarasını kontrol et.")
    st.stop()

fingerprint = hashlib.sha256(content + json.dumps([filename, separator, decimal, encoding, sheet, mode]).encode()).hexdigest()
if st.session_state.get("fingerprint") != fingerprint:
    st.session_state["fingerprint"] = fingerprint
    st.session_state.pop("pending", None)
    st.session_state.pop("result", None)

q = quality(df)
for col, (label, value) in zip(st.columns(4), [("Satır", q["rows"]), ("Sütun", q["columns"]),
                                               ("Boş hücre", q["missing_cells"]), ("Tekrarlanan satır", q["duplicate_rows"])]):
    col.metric(label, value)
with st.expander("Veriyi ve sütun türlerini incele", expanded=True):
    st.dataframe(df.head(20), hide_index=True)
    st.caption("Önizleme: ilk 20 satır. Sütun türleri otomatik okunur; yanlışsa dosyayı düzeltip yeniden yükle.")
    st.json({c: str(t) for c, t in df.dtypes.items()})

is_llm = mode.startswith("LLM")
if is_llm:
    st.info("LLM modunda sorunun metni, sütun adları ve veri türleri OpenAI API’ye gönderilir. Ham satırlar ve analiz sonuçları gönderilmez. Sorunun içine yazdığın değerler de soruyla birlikte gider. API kullanımı ücretli olabilir; anahtarını .env dosyasında tut.")
else:
    st.info("Demo altı hazır soruyu kullanır; dil modeli çalıştırmaz. Örnek satış verisiyle başla. Kendi verinde ilgili sütunlar yoksa plan reddedilir.")

with st.form("question_form"):
    question = st.text_area("Verine ne sormak istiyorsun?", value="Bölgelere göre toplam geliri grafikle göster", max_chars=2000) if is_llm else st.selectbox("Hazır demo sorusu", DEMO_QUESTIONS, index=2)
    consent = st.checkbox("Soru ve sütun şemasını API’ye gönder") if is_llm else True
    prepare = st.form_submit_button("Planı hazırla")

if prepare:
    st.session_state.pop("pending", None)
    st.session_state.pop("result", None)
    if not consent:
        st.warning("LLM planı için gönderim kutusunu işaretle.")
    else:
        try:
            with st.spinner("Analiz planı hazırlanıyor…"):
                plan = llm_plan(df, question) if is_llm else demo_plan(question)
                plan = validate_plan(df, plan)
            st.session_state["pending"] = (question, plan)
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Plan hazırlanamadı ({type(e).__name__}). API anahtarını, model erişimini, bakiyeyi ve internet bağlantısını kontrol et. Anahtarını paylaşma.")

pending = st.session_state.get("pending")
if pending:
    saved_question, plan = pending
    st.subheader("Analiz planı")
    st.write("Soru:", saved_question)
    st.write(plan.explanation)
    st.json(plan.model_dump())
    st.caption("Sütun, filtre, işlem ve sıralamanın soruna uygun olduğunu kontrol et. __value__ hesaplanan ölçüm sütunudur.")
    if st.button("Analizi çalıştır", type="primary"):
        try:
            with st.spinner("Hesaplama ve grafik hazırlanıyor…"):
                st.session_state["result"] = execute(df, plan)
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Analiz tamamlanamadı ({type(e).__name__}). Veri türlerini kontrol et.")
    result = st.session_state.get("result")
    if result is not None:
        st.subheader("Sonuç")
        st.dataframe(result.table, hide_index=True)
        for note in result.notes:
            st.caption(note)
        png = plot_png(plan, result)
        if png:
            st.image(png)
            st.caption("Grafikte en fazla ilk 50 sonuç satırı gösterilir; sıralama plana bağlıdır.")
        st.download_button("Sonuç CSV’sini indir", csv_bytes(result.table), "analysis_result.csv", "text/csv")
        st.download_button("HTML raporu indir", html_report(df, saved_question, plan, result, mode), "analysis_report.html", "text/html")
        st.download_button("Planı JSON olarak indir", json.dumps(plan.model_dump(), ensure_ascii=False, indent=2), "analysis_plan.json", "application/json")
        if png:
            st.download_button("Grafiği PNG olarak indir", png, "analysis_chart.png", "image/png")
        st.caption("HTML raporunu tarayıcıda açıp Yazdır → PDF olarak kaydet ile PDF’ye çevirebilirsin.")
