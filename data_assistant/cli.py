import argparse
import json
from pathlib import Path
from .io import load_table, quality
from .planner import demo_plan, llm_plan, DEMO_QUESTIONS
from .engine import execute
from .report import save_bundle


def main():
    parser = argparse.ArgumentParser(description="AI veri analizi asistanı")
    parser.add_argument("--file", required=True)
    parser.add_argument("--mode", choices=["demo", "llm"], default="demo")
    parser.add_argument("--question", default=DEMO_QUESTIONS[2])
    parser.add_argument("--output", required=True)
    parser.add_argument("--separator", default=",")
    parser.add_argument("--decimal", default=".")
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--sheet", type=int, default=0)
    args = parser.parse_args()
    try:
        if Path(args.output).exists():
            raise ValueError("Çıktı klasörü zaten var; yeni bir --output seç.")
        source = Path(args.file)
        if source.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("Dosya 10 MB sınırını aşıyor.")
        df = load_table(source.read_bytes(), source.name, separator=args.separator, decimal=args.decimal,
                        encoding=args.encoding, sheet=args.sheet)
        print(json.dumps(quality(df), ensure_ascii=False))
        if args.mode == "llm":
            print("LLM: yalnızca soru ve sütun adları/türleri API'ye gönderiliyor.")
        plan = llm_plan(df, args.question) if args.mode == "llm" else demo_plan(args.question)
        print("Uygulanacak plan:", plan.model_dump_json(indent=2))
        result = execute(df, plan)
        target = save_bundle(args.output, df, args.question, plan, result, args.mode)
        print(result.table.to_string(index=False))
        print("Rapor hazır:", (target / "report.html").resolve())
    except (ValueError, OSError) as e:
        parser.exit(1, "Hata: " + str(e) + "\n")
    except KeyboardInterrupt:
        parser.exit(130, "\nİşlem durduruldu.\n")
    except Exception as e:
        parser.exit(1, f"İşlem tamamlanamadı ({type(e).__name__}). API ayarlarını veya veri dosyasını kontrol et.\n")


if __name__ == "__main__":
    main()
