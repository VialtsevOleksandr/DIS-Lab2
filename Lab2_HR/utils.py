"""Спільне форматування результатів запитів для консолі та results.txt."""
import json
from datetime import date, datetime


def to_json(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()[:10]
    return str(o)


def format_results(db_name, results):
    out = ["=" * 80, f"  {db_name}", "=" * 80]
    for r in results:
        rows = r["rows"] or []
        out.append(f"\n--- {r['title']} ---")
        out.append("Запит:\n" + r["query"].strip())
        out.append(f"Результат ({len(rows)}):")
        out += ["  " + json.dumps(row, ensure_ascii=False, default=to_json) for row in rows]
    return "\n".join(out) + "\n"