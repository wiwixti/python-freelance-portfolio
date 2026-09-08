# Safe File Organizer

Консольная утилита сортирует файлы в выбранной папке по категориям. По умолчанию она только показывает план — данные не меняются, пока пользователь не добавит `--apply`.

## Примеры

```powershell
# Только посмотреть план
python organizer.py "$env:USERPROFILE\Downloads"

# Выполнить сортировку
python organizer.py "$env:USERPROFILE\Downloads" --apply

# Отменить последнюю сортировку
python organizer.py "$env:USERPROFILE\Downloads" --undo
```

При совпадении имён существующий файл не перезаписывается: к новому имени добавляется номер.

