"""Генерація канонічного набору резюме — єдине джерело даних для всіх трьох баз.

Запуск:  python generate_data.py   -> створює data.json і друкує статистику перетинів.
"""
import hashlib
import json
import os
import random
from collections import defaultdict
from datetime import date

from config import DATA_FILE, RESUME_COUNT, SEED

TODAY = date(2026, 10, 1)

# Невеликі довідники -> гарантовані перетини між резюме
CITIES = ["Київ", "Львів", "Харків", "Одеса", "Дніпро", "Вінниця", "Запоріжжя", "Івано-Франківськ"]
CITY_WEIGHTS = [10, 6, 5, 4, 4, 2, 2, 2]

HOBBIES = ["шахи", "біг", "фотографія", "читання", "велоспорт", "кулінарія", "подорожі",
           "гітара", "йога", "плавання", "настільні ігри", "малювання", "туризм",
           "програмування", "футбол"]

COMPANIES = ["EPAM", "SoftServe", "GlobalLogic", "Ciklum", "Monobank", "Rozetka",
             "Нова Пошта", "Київстар", "Grammarly", "MacPaw"]

POSITIONS = ["Junior Python Developer", "Python Developer", "QA Engineer", "Data Analyst",
             "Project Manager", "Business Analyst", "DevOps Engineer", "Frontend Developer",
             "HR Manager", "UI/UX Designer"]

MALE_NAMES = ["Іван", "Олександр", "Андрій", "Дмитро", "Максим", "Богдан", "Тарас", "Сергій", "Олег", "Юрій"]
FEMALE_NAMES = ["Олена", "Марія", "Анна", "Ірина", "Наталія", "Катерина", "Софія", "Юлія", "Оксана", "Дарина"]
LAST_NAMES = ["Коваленко", "Шевченко", "Бондаренко", "Ткаченко", "Кравченко", "Олійник", "Мельник",
              "Лисенко", "Савченко", "Руденко", "Мороз", "Поліщук", "Гончаренко", "Клименко", "Павленко"]

# ім'я батька -> (по батькові чол., по батькові жін.)
PATRONYMICS = {
    "Петро": ("Петрович", "Петрівна"), "Іван": ("Іванович", "Іванівна"),
    "Василь": ("Васильович", "Василівна"), "Микола": ("Миколайович", "Миколаївна"),
    "Олег": ("Олегович", "Олегівна"), "Сергій": ("Сергійович", "Сергіївна"),
    "Андрій": ("Андрійович", "Андріївна"), "Юрій": ("Юрійович", "Юріївна"),
}

ABOUT_TEMPLATES = ["Шукаю позицію {pos} у продуктовій компанії.",
                   "Маю досвід роботи {pos}, відкритий до нових проєктів.",
                   "Цікавлюся розвитком у напрямі {pos}."]

TRANSLIT = dict(zip("абвгґдеєжзиіїйклмнопрстуфхцчшщьюя",
                    ["a", "b", "v", "h", "g", "d", "e", "ie", "zh", "z", "y", "i", "i", "i", "k", "l", "m",
                     "n", "o", "p", "r", "s", "t", "u", "f", "kh", "ts", "ch", "sh", "shch", "", "iu", "ia"]))


def translit(text: str) -> str:
    return "".join(TRANSLIT.get(ch, ch) for ch in text.lower())


def hash_password(password: str, salt: str) -> str:
    return salt + "$" + hashlib.sha256((salt + password).encode()).hexdigest()


def add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    return date(d.year + y, m + 1, 1)


def make_experience(rnd: random.Random, birth: date) -> list[dict]:
    """1–3 послідовні місця роботи; останнє може тривати досі."""
    start = date(birth.year + rnd.randint(21, 23), rnd.choice([1, 3, 6, 9]), 1)
    jobs = []
    for company in rnd.sample(COMPANIES, rnd.randint(1, 3)):
        if start >= TODAY:
            break
        end = add_months(start, rnd.randint(8, 40))
        jobs.append({"company": company, "position": rnd.choice(POSITIONS),
                     "start_date": start, "end_date": end if end < TODAY else None})
        if end >= TODAY:
            break
        start = add_months(end, rnd.randint(0, 3))
    if jobs and jobs[-1]["end_date"] and rnd.random() < 0.5:
        jobs[-1]["end_date"] = None
    return jobs


def generate(n: int = RESUME_COUNT, seed: int = SEED) -> list[dict]:
    rnd = random.Random(seed)
    users, used_logins = [], set()
    for i in range(n):
        male = i % 2 == 0
        first = rnd.choice(MALE_NAMES if male else FEMALE_NAMES)
        last = rnd.choice(LAST_NAMES)
        patronymic = (PATRONYMICS[rnd.choice(list(PATRONYMICS))][0 if male else 1]
                      if rnd.random() < 0.8 else None)

        login = f"{translit(first)}_{translit(last)}"
        while login in used_logins:
            login += str(rnd.randint(0, 9))
        used_logins.add(login)

        birth = date(rnd.randint(1980, 2003), rnd.randint(1, 12), rnd.randint(1, 28))
        experience = make_experience(rnd, birth)
        about = (rnd.choice(ABOUT_TEMPLATES).format(pos=experience[-1]["position"])
                 if experience and rnd.random() < 0.8 else None)

        users.append({
            "login": login,
            "password_hash": hash_password(f"pass_{login}", salt=f"{i:04x}"),
            "resume": {
                "first_name": first,
                "last_name": last,
                "patronymic": patronymic,
                "birth_date": birth,
                "about": about,
                "city": rnd.choices(CITIES, weights=CITY_WEIGHTS)[0],
                "hobbies": rnd.sample(HOBBIES, rnd.randint(1, 4)),
                "experience": experience,
            },
        })
    return users


# ---------- JSON (дати зберігаються як ISO-рядки) ----------

def save_data(users: list[dict], path: str = DATA_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2, default=lambda d: d.isoformat())


def load_data(path: str = DATA_FILE) -> list[dict]:
    """Читає data.json (створює, якщо його немає) і повертає дати як date-об'єкти."""
    if not os.path.exists(path):
        save_data(generate(), path)
    with open(path, encoding="utf-8") as f:
        users = json.load(f)
    for u in users:
        r = u["resume"]
        r["birth_date"] = date.fromisoformat(r["birth_date"])
        for job in r["experience"]:
            job["start_date"] = date.fromisoformat(job["start_date"])
            job["end_date"] = date.fromisoformat(job["end_date"]) if job["end_date"] else None
    return users


def print_stats(users: list[dict]) -> None:
    by_city, by_hobby, by_company = defaultdict(set), defaultdict(set), defaultdict(set)
    for u in users:
        r = u["resume"]
        by_city[r["city"]].add(u["login"])
        for h in r["hobbies"]:
            by_hobby[h].add(u["login"])
        for job in r["experience"]:
            by_company[job["company"]].add(u["login"])

    print(f"Резюме: {len(users)}")
    print(f"Міст: {len(by_city)}, хобі: {len(by_hobby)}, закладів: {len(by_company)}")
    print("Мешканців по містах:", {c: len(s) for c, s in sorted(by_city.items(), key=lambda x: -len(x[1]))})
    print("Працівників по закладах:", {c: len(s) for c, s in sorted(by_company.items(), key=lambda x: -len(x[1]))})

    shared = sum(1 for s in by_company.values() if len(s) >= 2)
    assert shared >= 3, "Замало спільних закладів — запит №5 не матиме сенсу"
    assert sum(1 for s in by_city.values() if len(s) >= 2) >= 3, "Замало спільних міст"
    print(f"OK: закладів зі спільними працівниками — {shared}")


if __name__ == "__main__":
    data = generate()
    save_data(data)
    print_stats(data)
    print(f"Збережено у {DATA_FILE}")