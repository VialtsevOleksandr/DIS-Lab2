import inspect
from datetime import datetime

from pymongo import ASCENDING, MongoClient

from config import MONGO_DB, MONGO_URI, QUERY_PARAMS
from utils import format_results


def get_db():
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)[MONGO_DB]


def q1(db, login):
    """1. Резюме конкретного користувача"""
    return list(db.users.find(
        {"login": login},
        {"_id": 0, "password_hash": 0}
    ))


def q2(db):
    """2. Усі унікальні хобі"""
    return db.users.distinct("resume.hobbies")


def q3(db):
    """3. Усі унікальні міста"""
    return db.users.distinct("resume.city")


def q4(db, city):
    """4. Хобі мешканців заданого міста"""
    return db.users.distinct("resume.hobbies", {"resume.city": city})


def q5(db):
    """5. Здобувачі зі спільним закладом роботи"""
    return list(db.users.aggregate([
        {"$unwind": "$resume.experience"},
        {"$group": {
            "_id": "$resume.experience.company",
            "colleagues": {
                "$addToSet": {"$concat": ["$login", " (", "$resume.last_name", " ", "$resume.first_name", ")"]}
            }
        }},
        {"$match": {"$expr": {"$gt": [{"$size": "$colleagues"}, 1]}}},
        {"$project": {"_id": 0, "company": "$_id", "colleagues": 1}},
        {"$sort": {"company": 1}}
    ]))


def to_datetime(d):
    return datetime(d.year, d.month, d.day) if d else None


def reset():
    db = get_db()
    db.users.drop()
    db.users.create_index([("login", ASCENDING)], unique=True)


def seed(users):
    docs = []
    for u in users:
        r = u["resume"]
        docs.append({
            "login": u["login"],
            "password_hash": u["password_hash"],
            "resume": {
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "patronymic": r["patronymic"],
                "birth_date": to_datetime(r["birth_date"]),
                "about": r["about"],
                "city": r["city"],
                "hobbies": r["hobbies"],
                "experience": [{"company": j["company"], "position": j["position"],
                                "start_date": to_datetime(j["start_date"]),
                                "end_date": to_datetime(j["end_date"])}
                               for j in r["experience"]],
            },
        })
    get_db().users.insert_many(docs)


def counts():
    return {"users": get_db().users.count_documents({})}


def run_queries():
    db = get_db()
    calls = [(q1, (QUERY_PARAMS["login"],)), (q2, ()), (q3, ()), (q4, (QUERY_PARAMS["city"],)), (q5, ())]
    return [{"title": fn.__doc__, "query": inspect.getsource(fn), "rows": fn(db, *args)}
            for fn, args in calls]


if __name__ == "__main__":
    print(format_results("MongoDB", run_queries()))