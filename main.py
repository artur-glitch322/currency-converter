import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

# Файл для истории конвертаций
HISTORY_FILE = "conversion_history.json"

# Настройка API
API_KEY = "75ee88933fba607e9c75f0d8"  # Личный ключ
BASE_URL = "https://v6.exchangerate-api.com/v6"

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("620x520")
        self.root.resizable(False, False)

        self.history = []
        self.currencies = ["Загрузка..."]

        self.create_widgets()

        self.load_history()
        self.fetch_currencies()

    # Получить и установить список валют
    def fetch_currencies(self):
        try:
            url = f"{BASE_URL}/{API_KEY}/latest/USD"
            response = requests.get(url)
            data = response.json()

            if data.get("result") == "success":
                self.currencies = sorted(data["conversion_rates"].keys())
                self.currencies.insert(0, "USD")
            else:
                raise Exception("Ошибка API: " + data.get("error-type", "Unknown"))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить курсы:\n{e}\nИспользуем базовые валюты.")
            self.currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "KZT", "CAD", "AUD"]

        self.from_currency.config(values=self.currencies)
        self.to_currency.config(values=self.currencies)

    # Создать поля интерфейса
    def create_widgets(self):
        title = tk.Label(self.root, text="Конвертер валют", font=("Arial", 16, "bold"))
        title.pack(pady=10)

        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Из валюты:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.from_currency = ttk.Combobox(input_frame, values=self.currencies, state="readonly", width=12)
        self.from_currency.set("USD")
        self.from_currency.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="В валюту:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.to_currency = ttk.Combobox(input_frame, values=self.currencies, state="readonly", width=12)
        self.to_currency.set("RUB")
        self.to_currency.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Сумма:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.amount_entry = tk.Entry(input_frame, width=15)
        self.amount_entry.grid(row=2, column=1, padx=5, pady=5)

        convert_btn = tk.Button(
            self.root,
            text="🔄 Конвертировать",
            command=self.convert,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        )
        convert_btn.pack(pady=10)

        self.result_label = tk.Label(self.root, text="", font=("Arial", 12), fg="darkblue")
        self.result_label.pack(pady=5)

        tk.Label(self.root, text="История конверсий", font=("Arial", 12, "bold")).pack(pady=8)

        columns = ("#1", "#2", "#3", "#4", "#5")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=8)
        self.tree.heading("#1", text="№")
        self.tree.heading("#2", text="Дата и время")
        self.tree.heading("#3", text="Сумма")
        self.tree.heading("#4", text="Направление")
        self.tree.heading("#5", text="Результат")

        self.tree.column("#1", width=40, anchor="center")
        self.tree.column("#2", width=130, anchor="center")
        self.tree.column("#3", width=90, anchor="center")
        self.tree.column("#4", width=110, anchor="center")
        self.tree.column("#5", width=110, anchor="center")

        self.tree.pack(padx=20, pady=5, fill="both", expand=True)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="🗑 Очистить", command=self.clear_history, bg="#f44336", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="🔄 Обновить валюты", command=self.refresh_rates, bg="#2196F3", fg="white").pack(side="left", padx=5)

        self.update_history_table()

    # Получить новый список валют
    def refresh_rates(self):
        self.currencies = ["Обновление..."]
        self.from_currency.config(values=self.currencies)
        self.to_currency.config(values=self.currencies)
        self.root.after(100, self.fetch_currencies)

    # Конвертация
    def convert(self):
        amount_str = self.amount_entry.get().strip()
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()

        if not amount_str:
            messagebox.showwarning("Ошибка", "Введите сумму!")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Ошибка", "Сумма должна быть положительным числом!")
            return

        try:
            url = f"{BASE_URL}/{API_KEY}/pair/{from_curr}/{to_curr}"
            response = requests.get(url)
            data = response.json()

            if data.get("result") != "success":
                raise Exception(data.get("error-type", "Ошибка API"))

            rate = data["conversion_rate"]
            result = round(amount * rate, 2)

            self.result_label.config(text=f"✅ {amount} {from_curr} = {result} {to_curr}")

            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "from": from_curr,
                "to": to_curr,
                "rate": rate,
                "result": result
            }
            self.history.append(entry)
            self.save_history()
            self.update_history_table()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось конвертировать:\n{e}")

    # Добавить записи конвертации
    def update_history_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, entry in enumerate(reversed(self.history[-10:]), 1):  # последние 10
            self.tree.insert("", "end", values=(
                i,
                entry["timestamp"],
                f"{entry['amount']:.2f}",
                f"{entry['from']}→{entry['to']}",
                f"{entry['result']:.2f}"
            ))

    # Сохранить истории в файл
    def save_history(self):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=4)

    # Загрузить историю из файла
    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить историю:\n{e}")
                self.history = []
        else:
            self.history = []

    # Очистить историю
    def clear_history(self):
        if messagebox.askyesno("Подтверждение", "Очистить всю историю?"):
            self.history.clear()
            self.save_history()
            self.update_history_table()
            self.result_label.config(text="")


if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()