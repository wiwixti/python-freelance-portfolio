"""Safely organize files by category with dry-run and undo support."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"},
    "Spreadsheets": {".csv", ".xls", ".xlsx", ".ods"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Audio": {".mp3", ".wav", ".flac", ".m4a", ".ogg"},
    "Video": {".mp4", ".mkv", ".avi", ".mov", ".webm"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml"},
}


@dataclass(frozen=True)
class Move:
    source: str
    destination: str


def category_for(path: Path) -> str:
    suffix = path.suffix.lower()
    for category, extensions in CATEGORIES.items():
        if suffix in extensions:
            return category
    return "Other"


def unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination
    counter = 1
    while True:
        candidate = destination.with_name(f"{destination.stem}_{counter}{destination.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def build_plan(folder: Path, manifest_name: str) -> list[Move]:
    if not folder.is_dir():
        raise ValueError(f"Папка не найдена: {folder}")
    plan: list[Move] = []
    for item in sorted(folder.iterdir(), key=lambda value: value.name.lower()):
        if not item.is_file() or item.name == manifest_name:
            continue
        destination = unique_destination(folder / category_for(item) / item.name)
        plan.append(Move(str(item.resolve()), str(destination.resolve())))
    return plan


def apply_plan(plan: list[Move], manifest: Path) -> None:
    completed: list[Move] = []
    try:
        for move in plan:
            source = Path(move.source)
            destination = Path(move.destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            completed.append(move)
    except OSError:
        for move in reversed(completed):
            destination = Path(move.destination)
            source = Path(move.source)
            source.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and not source.exists():
                shutil.move(str(destination), str(source))
        raise
    payload = {"created_at": datetime.now().isoformat(timespec="seconds"), "moves": [asdict(item) for item in completed]}
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def undo(manifest: Path) -> int:
    if not manifest.is_file():
        raise ValueError(f"Файл отмены не найден: {manifest}")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    restored = 0
    for raw in reversed(payload.get("moves", [])):
        source = Path(raw["source"])
        destination = Path(raw["destination"])
        if not destination.exists():
            continue
        if source.exists():
            raise FileExistsError(f"Нельзя восстановить, файл уже существует: {source}")
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(destination), str(source))
        restored += 1
    manifest.unlink(missing_ok=True)
    return restored


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Безопасная сортировка файлов по типам.")
    result.add_argument("folder", nargs="?", default=".", help="Папка для сортировки")
    result.add_argument("--apply", action="store_true", help="Выполнить показанный план")
    result.add_argument("--undo", action="store_true", help="Отменить последнюю сортировку")
    return result


def main() -> int:
    args = parser().parse_args()
    folder = Path(args.folder).expanduser().resolve()
    manifest = folder / "organizer_manifest.json"
    try:
        if args.undo:
            print(f"Восстановлено файлов: {undo(manifest)}")
            return 0
        plan = build_plan(folder, manifest.name)
        if not plan:
            print("Подходящих файлов нет.")
            return 0
        print("План сортировки:")
        for move in plan:
            print(f"  {Path(move.source).name} -> {Path(move.destination).parent.name}/")
        if not args.apply:
            print("\nПредпросмотр завершён. Для выполнения добавьте --apply")
            return 0
        apply_plan(plan, manifest)
        print(f"\nПеремещено файлов: {len(plan)}")
        print(f"Отмена: python organizer.py \"{folder}\" --undo")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Ошибка: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

