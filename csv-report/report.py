"""Generate a self-contained HTML profile for a CSV file."""

from __future__ import annotations

import argparse
import csv
import html
import statistics
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    filled: int
    missing: int
    unique: int
    kind: str
    minimum: str = "—"
    maximum: str = "—"
    average: str = "—"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    raw = path.read_bytes()
    text = None
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("Не удалось определить кодировку CSV")
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(text.splitlines(), dialect=dialect)
    headers = reader.fieldnames or []
    if not headers:
        raise ValueError("В CSV нет строки заголовков")
    return headers, [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def profile_column(name: str, rows: list[dict[str, str]]) -> ColumnProfile:
    values = [row.get(name, "").strip() for row in rows]
    present = [value for value in values if value]
    numbers: list[float] = []
    numeric = bool(present)
    for value in present:
        try:
            numbers.append(float(value.replace(" ", "").replace(",", ".")))
        except ValueError:
            numeric = False
            break
    if numeric:
        return ColumnProfile(
            name=name,
            filled=len(present),
            missing=len(values) - len(present),
            unique=len(set(present)),
            kind="Число",
            minimum=f"{min(numbers):g}",
            maximum=f"{max(numbers):g}",
            average=f"{statistics.fmean(numbers):.2f}",
        )
    return ColumnProfile(name, len(present), len(values) - len(present), len(set(present)), "Текст")


def make_report(source: Path) -> str:
    headers, rows = read_csv(source)
    profiles = [profile_column(name, rows) for name in headers]
    profile_rows = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in (
            item.name, item.kind, item.filled, item.missing, item.unique, item.minimum, item.maximum, item.average
        )) + "</tr>"
        for item in profiles
    )
    preview = "".join(
        "<tr>" + "".join(f"<td>{html.escape(row.get(name, ''))}</td>" for name in headers) + "</tr>"
        for row in rows[:10]
    )
    header_cells = "".join(f"<th>{html.escape(name)}</th>" for name in headers)
    return f"""<!doctype html>
<html lang=\"ru\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\">
<title>Отчёт: {html.escape(source.name)}</title>
<style>
body{{font:16px system-ui;background:#f1f5f9;color:#0f172a;margin:0;padding:32px}}main{{max-width:1100px;margin:auto}}
h1{{margin-bottom:6px}}.cards{{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}}.card{{background:white;padding:18px;border-radius:12px;min-width:180px;box-shadow:0 2px 8px #0001}}
.number{{font-size:28px;font-weight:700;color:#2563eb}}.table{{overflow:auto;background:white;border-radius:12px;margin:16px 0}}table{{border-collapse:collapse;width:100%}}th,td{{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left;white-space:nowrap}}th{{background:#1e293b;color:white}}
</style><main><h1>CSV Data Report</h1><p>Источник: <b>{html.escape(source.name)}</b></p>
<section class=\"cards\"><div class=\"card\"><div class=\"number\">{len(rows)}</div>строк данных</div><div class=\"card\"><div class=\"number\">{len(headers)}</div>столбцов</div></section>
<h2>Профиль столбцов</h2><div class=\"table\"><table><thead><tr><th>Столбец</th><th>Тип</th><th>Заполнено</th><th>Пропуски</th><th>Уникальных</th><th>Мин.</th><th>Макс.</th><th>Среднее</th></tr></thead><tbody>{profile_rows}</tbody></table></div>
<h2>Первые 10 строк</h2><div class=\"table\"><table><thead><tr>{header_cells}</tr></thead><tbody>{preview}</tbody></table></div></main></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Создать HTML-отчёт по CSV-файлу")
    parser.add_argument("source", type=Path, help="Путь к CSV")
    parser.add_argument("--output", type=Path, default=Path("report.html"), help="Итоговый HTML")
    args = parser.parse_args()
    try:
        args.output.write_text(make_report(args.source), encoding="utf-8")
        print(f"Готово: {args.output.resolve()}")
        return 0
    except (OSError, ValueError, csv.Error) as error:
        print(f"Ошибка: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

