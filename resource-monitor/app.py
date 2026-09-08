"""Lightweight Windows resource monitor with a Tkinter interface."""

from __future__ import annotations

import csv
import ctypes
import shutil
import sys
import time
import tkinter as tk
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


if sys.platform != "win32":
    raise SystemExit("Resource Monitor supports Windows only.")


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _filetime_value(value: wintypes.FILETIME) -> int:
    return (value.dwHighDateTime << 32) | value.dwLowDateTime


class CpuSampler:
    def __init__(self) -> None:
        self.previous = self._read_times()

    @staticmethod
    def _read_times() -> tuple[int, int, int]:
        idle = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(
            ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
        ):
            raise ctypes.WinError()
        return tuple(map(_filetime_value, (idle, kernel, user)))

    def percent(self) -> float:
        current = self._read_times()
        idle_delta = current[0] - self.previous[0]
        total_delta = (current[1] - self.previous[1]) + (current[2] - self.previous[2])
        self.previous = current
        if total_delta <= 0:
            return 0.0
        return max(0.0, min(100.0, 100.0 * (1.0 - idle_delta / total_delta)))


def memory_percent() -> float:
    status = MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError()
    return float(status.dwMemoryLoad)


def disk_percent(path: str = "C:\\") -> float:
    usage = shutil.disk_usage(path)
    return 100.0 * usage.used / usage.total


@dataclass(frozen=True)
class Snapshot:
    timestamp: str
    cpu: float
    memory: float
    disk: float


class MonitorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Windows Resource Monitor")
        self.geometry("520x330")
        self.minsize(460, 300)
        self.configure(bg="#111827")
        self.cpu_sampler = CpuSampler()
        self.history: list[Snapshot] = []
        self.running = True
        self.values: dict[str, tk.StringVar] = {}
        self.bars: dict[str, ttk.Progressbar] = {}
        self._build_ui()
        self.after(700, self.refresh)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Monitor.Horizontal.TProgressbar", troughcolor="#243047", background="#22c55e")

        tk.Label(
            self,
            text="Состояние компьютера",
            font=("Segoe UI", 18, "bold"),
            fg="#f8fafc",
            bg="#111827",
        ).pack(pady=(18, 10))

        panel = tk.Frame(self, bg="#111827")
        panel.pack(fill="both", expand=True, padx=28)
        for key, label in (("cpu", "Процессор"), ("memory", "Память"), ("disk", "Диск C:")):
            row = tk.Frame(panel, bg="#111827")
            row.pack(fill="x", pady=8)
            tk.Label(row, text=label, width=13, anchor="w", fg="#cbd5e1", bg="#111827").pack(side="left")
            bar = ttk.Progressbar(row, maximum=100, style="Monitor.Horizontal.TProgressbar")
            bar.pack(side="left", fill="x", expand=True, padx=8)
            value = tk.StringVar(value="0.0%")
            tk.Label(row, textvariable=value, width=8, anchor="e", fg="#f8fafc", bg="#111827").pack(side="right")
            self.bars[key] = bar
            self.values[key] = value

        controls = tk.Frame(self, bg="#111827")
        controls.pack(pady=16)
        self.toggle_button = ttk.Button(controls, text="Пауза", command=self.toggle)
        self.toggle_button.pack(side="left", padx=5)
        ttk.Button(controls, text="Сохранить CSV", command=self.save_csv).pack(side="left", padx=5)
        ttk.Button(controls, text="Закрыть", command=self.destroy).pack(side="left", padx=5)

        self.status = tk.StringVar(value="Мониторинг запущен")
        tk.Label(self, textvariable=self.status, fg="#94a3b8", bg="#111827").pack(pady=(0, 12))

    def refresh(self) -> None:
        if self.running:
            try:
                snapshot = Snapshot(
                    timestamp=datetime.now().isoformat(timespec="seconds"),
                    cpu=self.cpu_sampler.percent(),
                    memory=memory_percent(),
                    disk=disk_percent(),
                )
                self.history.append(snapshot)
                self.history = self.history[-3600:]
                for key in ("cpu", "memory", "disk"):
                    value = getattr(snapshot, key)
                    self.bars[key]["value"] = value
                    self.values[key].set(f"{value:.1f}%")
                self.status.set(f"Обновлено: {snapshot.timestamp.replace('T', ' ')}")
            except OSError as error:
                self.status.set(f"Ошибка чтения данных: {error}")
        self.after(1000, self.refresh)

    def toggle(self) -> None:
        self.running = not self.running
        self.toggle_button.configure(text="Пауза" if self.running else "Продолжить")
        self.status.set("Мониторинг запущен" if self.running else "Мониторинг приостановлен")

    def save_csv(self) -> None:
        if not self.history:
            messagebox.showinfo("Нет данных", "Сначала подождите несколько секунд.")
            return
        filename = filedialog.asksaveasfilename(
            title="Сохранить журнал",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"monitor-{time.strftime('%Y%m%d-%H%M')}.csv",
        )
        if not filename:
            return
        with Path(filename).open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "cpu_percent", "memory_percent", "disk_percent"])
            for item in self.history:
                writer.writerow([item.timestamp, f"{item.cpu:.1f}", f"{item.memory:.1f}", f"{item.disk:.1f}"])
        messagebox.showinfo("Готово", f"Журнал сохранён:\n{filename}")


if __name__ == "__main__":
    MonitorApp().mainloop()

