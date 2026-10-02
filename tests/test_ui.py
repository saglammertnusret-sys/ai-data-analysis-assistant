from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class UITests(unittest.TestCase):
    def test_demo_plan_execution_and_mode_change_clears_result(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[0].value,"12")
        next(b for b in app.button if b.label == "Planı hazırla").click().run()
        self.assertEqual(len(app.exception),0)
        next(b for b in app.button if b.label == "Analizi çalıştır").click().run()
        self.assertEqual(len(app.exception),0)
        result = app.dataframe[-1].value
        self.assertEqual(dict(zip(result.bolge, result.__value__)), {"Istanbul":8000,"Ankara":6500,"Izmir":6300})
        self.assertIn("result",app.session_state)
        app.radio[0].set_value("LLM (OpenAI API)").run()
        self.assertEqual(len(app.exception),0)
        self.assertNotIn("result",app.session_state)


if __name__ == "__main__":
    unittest.main()
