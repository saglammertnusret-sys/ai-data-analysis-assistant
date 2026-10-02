"""API-free calculation/report test; it does not measure LLM accuracy."""
from pathlib import Path
from tempfile import TemporaryDirectory
from data_assistant.io import load_table
from data_assistant.planner import DEMO_QUESTIONS, demo_plan
from data_assistant.engine import execute
from data_assistant.report import save_bundle


def main():
    root = Path(__file__).resolve().parent
    sample = root / "sample_data" / "sales.csv"
    df = load_table(sample.read_bytes(), sample.name)
    total = execute(df, demo_plan(DEMO_QUESTIONS[1]))
    assert total.table.iloc[0]["__value__"] == 20800
    plan = demo_plan(DEMO_QUESTIONS[2])
    result = execute(df, plan)
    assert dict(zip(result.table.bolge, result.table.__value__)) == {"Istanbul":8000,"Ankara":6500,"Izmir":6300}
    with TemporaryDirectory(prefix="ai-assistant-smoke-") as tmp:
        target = save_bundle(Path(tmp) / "report", df, DEMO_QUESTIONS[2], plan, result, "demo")
        assert (target / "chart.png").read_bytes().startswith(b"\x89PNG")
        assert (target / "report.html").stat().st_size > 1000
    print("SMOKE TEST PASSED")
    print("12 satır; toplam gelir: 20800; Istanbul: 8000; Ankara: 6500; Izmir: 6300.")
    print("Tablo, grafik ve HTML raporu üretildi. API çağrısı yapılmadı; LLM doğruluğu ölçülmedi.")


if __name__ == "__main__":
    main()
