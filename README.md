# Python Freelance Portfolio

Три прикладных проекта для автоматизации повседневных задач на Windows. Каждый проект запускается отдельно, содержит инструкцию, демонстрационные данные и проверки.

## Проекты

| Проект | Что решает | Технологии |
|---|---|---|
| [Resource Monitor](resource-monitor/) | Показывает загрузку процессора, памяти и диска в отдельном окне | Python, Tkinter, ctypes |
| [Safe File Organizer](file-organizer/) | Безопасно сортирует файлы по категориям и умеет отменять изменения | Python, pathlib, JSON, unittest |
| [CSV Report Generator](csv-report/) | Анализирует CSV и создаёт автономный HTML-отчёт | Python, csv, statistics, HTML, unittest |

## Быстрый запуск

Нужен Python 3.10 или новее. Сторонние библиотеки не требуются.

```powershell
git clone <адрес-репозитория>
cd python-freelance-portfolio
python resource-monitor/app.py
python file-organizer/organizer.py --help
python csv-report/report.py csv-report/demo/sales.csv --output report.html
```

## Что демонстрирует портфолио

- создание оконных приложений для Windows;
- безопасную автоматизацию файловых операций;
- обработку табличных данных и генерацию отчётов;
- обработку ошибок, журналирование и отмену операций;
- документацию и автоматические тесты.

## Проверка всех проектов

```powershell
python -m unittest discover -s file-organizer/tests -v
python -m unittest discover -s csv-report/tests -v
```

## Автор

Учебно-практическое портфолио начинающего Python-разработчика. Контакты и ссылки на профили будут добавлены перед публикацией.

