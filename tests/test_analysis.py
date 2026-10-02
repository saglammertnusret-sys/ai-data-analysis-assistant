from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import unittest
from unittest.mock import patch
import pandas as pd
from pydantic import ValidationError
from data_assistant.engine import execute
from data_assistant.io import load_table, csv_bytes
from data_assistant.planner import base_plan, demo_plan, DEMO_QUESTIONS, llm_plan
from data_assistant.report import html_report, save_bundle

ROOT = Path(__file__).resolve().parents[1]


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.df = load_table((ROOT / "sample_data/sales.csv").read_bytes(), "sales.csv")

    def test_all_demo_plans_and_total(self):
        for question in DEMO_QUESTIONS:
            self.assertFalse(execute(self.df, demo_plan(question)).table.empty)
        self.assertEqual(execute(self.df, demo_plan(DEMO_QUESTIONS[1])).table.iloc[0, 0], 20800)
        filtered = execute(self.df, demo_plan(DEMO_QUESTIONS[4]))
        self.assertEqual(filtered.filtered_rows, 5)
        self.assertEqual(filtered.table.gelir.tolist(), [6000, 3000, 3000, 2000, 1500])

    def test_missing_groups_and_all_missing_sums(self):
        df = pd.DataFrame({"group":["a", "a", None], "x":[None, None, 2.0]})
        result = execute(df, base_plan(operation="aggregate", group_by=["group"], metric="x", aggregation="sum"))
        self.assertTrue(pd.isna(result.table.loc[result.table.group == "a", "__value__"].iloc[0]))
        self.assertEqual(result.table.loc[result.table.group.isna(), "__value__"].iloc[0], 2)

    def test_count_means_non_null_and_row_count_includes_missing(self):
        df = pd.DataFrame({"x":[1.0, None, 2.0]})
        self.assertEqual(execute(df, base_plan(operation="aggregate", metric="x", aggregation="count")).table.iloc[0,0], 2)
        self.assertEqual(execute(df, base_plan(operation="aggregate", aggregation="count")).table.iloc[0,0], 3)

    def test_filters_and_limit_and_source_unchanged(self):
        before = self.df.copy(deep=True)
        plan = base_plan(operation="rows", filters=[{"column":"bolge","op":"eq","value":"Ankara"},
            {"column":"gelir","op":"ge","value":1000}], sort_by="gelir", descending=True, limit=2)
        result = execute(self.df, plan)
        self.assertEqual(result.filtered_rows, 4)
        self.assertEqual(result.full_result_rows, 4)
        self.assertEqual(result.table.gelir.tolist(), [3000,1500])
        pd.testing.assert_frame_equal(before, self.df)

    def test_literal_contains_no_regex(self):
        df = pd.DataFrame({"s":["a.*b","abc",None]})
        result = execute(df, base_plan(operation="rows", filters=[{"column":"s","op":"contains","value":".*"}]))
        self.assertEqual(result.table.s.tolist(), ["a.*b"])

    def test_reject_unknown_column_and_invalid_aggregation(self):
        with self.assertRaises(ValueError):
            execute(self.df, base_plan(operation="aggregate", metric="missing", aggregation="sum"))
        with self.assertRaises(ValueError):
            execute(self.df, base_plan(operation="aggregate", metric="bolge", aggregation="sum"))
        with self.assertRaises(ValueError):
            execute(self.df, base_plan(operation="rows", columns=["bolge"], sort_by="gelir"))
        with self.assertRaises(ValueError):
            execute(self.df, base_plan(operation="rows", filters=[{"column":"gelir","op":"gt","value":"1000"}]))

    def test_code_and_extra_fields_rejected(self):
        payload = base_plan().model_dump()
        payload["code"] = "__import__('os').system('echo bad')"
        with self.assertRaises(ValidationError):
            execute(self.df, payload)
        payload.pop("code")
        payload["operation"] = "exec"
        with self.assertRaises(ValidationError):
            execute(self.df, payload)
        with self.assertRaises(ValueError):
            demo_plan("Rastgele serbest bir soru")

    def test_csv_header_validation_and_locale(self):
        with self.assertRaises(ValueError):
            load_table(b"x,x\n1,2\n", "d.csv")
        with self.assertRaises(ValueError):
            load_table(b"x,\n1,2\n", "d.csv")
        df = load_table("urun;gelir\nÇay;12,5\n".encode("cp1254"), "d.csv", separator=";", decimal=",", encoding="cp1254")
        self.assertEqual(df.gelir.iloc[0],12.5)
        self.assertEqual(df.urun.iloc[0], "Çay")

    def test_xlsx_sheet_selection_and_duplicate_header(self):
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            pd.DataFrame({"x":[1]}).to_excel(writer, sheet_name="a", index=False)
            pd.DataFrame({"y":[2]}).to_excel(writer, sheet_name="b", index=False)
        df = load_table(out.getvalue(), "d.xlsx", sheet=1)
        self.assertEqual(df.iloc[0,0],2)
        out = BytesIO()
        pd.DataFrame([[1,2]], columns=["same","same"]).to_excel(out, index=False)
        with self.assertRaises(ValueError):
            load_table(out.getvalue(), "d.xlsx")

    def test_report_escaping_formula_protection_no_overwrite(self):
        df = pd.DataFrame({"s":["<script>alert(1)</script>", "=1+1", "@SUM(A1)"]})
        plan = base_plan(operation="rows")
        result = execute(df, plan)
        report = html_report(df, "<img src=x onerror=alert(1)>", plan, result, "demo").decode()
        self.assertNotIn("<script>", report)
        self.assertNotIn("<img src=x", report)
        self.assertIn("&lt;script&gt;", report)
        exported = csv_bytes(df).decode("utf-8-sig")
        self.assertIn("'=1+1", exported)
        self.assertIn("'@SUM(A1)", exported)
        with TemporaryDirectory() as tmp:
            path = Path(tmp)/"result"
            save_bundle(path, df, "q", plan, result, "demo")
            before = (path/"report.html").read_bytes()
            with self.assertRaises(ValueError):
                save_bundle(path, df, "other", plan, result, "demo")
            self.assertEqual(before, (path/"report.html").read_bytes())

    def test_empty_filter_result(self):
        plan = base_plan(operation="aggregate", group_by=["bolge"], metric="gelir", aggregation="sum",
            filters=[{"column":"gelir","op":"gt","value":999999}], chart="bar")
        result = execute(self.df, plan)
        self.assertEqual(result.filtered_rows, 0)
        self.assertTrue(result.table.empty)
        self.assertIn("eşleşen", " ".join(result.notes))

    def test_real_langchain_pipeline_mock_http_no_rows_sent(self):
        import httpx
        from langchain_openai import ChatOpenAI
        plan = demo_plan(DEMO_QUESTIONS[2])
        requests = []
        def respond(request):
            body = json.loads(request.content)
            requests.append(body)
            return httpx.Response(200, json={"id":"offline-test", "object":"chat.completion", "created":0,
                "model":"gpt-4.1-mini", "choices":[{"index":0, "finish_reason":"tool_calls",
                "message":{"role":"assistant", "content":None, "tool_calls":[{"id":"call_test", "type":"function",
                "function":{"name":"AnalysisPlan", "arguments":plan.model_dump_json()}}]}}],
                "usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}})
        with httpx.Client(transport=httpx.MockTransport(respond)) as client:
            model = ChatOpenAI(model="gpt-4.1-mini", api_key="offline-test-key", base_url="https://offline.test/v1", http_client=client, max_retries=0)
            with patch.dict(os.environ, {"OPENAI_API_KEY":"offline-test-key"}), patch("langchain_openai.ChatOpenAI", return_value=model):
                parsed = llm_plan(self.df, DEMO_QUESTIONS[2])
        self.assertEqual(parsed, plan)
        self.assertEqual(len(requests),1)
        messages = json.dumps(requests[0]["messages"], ensure_ascii=False)
        self.assertIn("bolge", messages)
        self.assertNotIn("Istanbul", messages)
        self.assertNotIn("20800", messages)
        self.assertEqual(execute(self.df, parsed).table.__value__.sum(),20800)


if __name__ == "__main__":
    unittest.main()
