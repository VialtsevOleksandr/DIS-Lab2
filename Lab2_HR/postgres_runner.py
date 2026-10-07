import psycopg
from psycopg import sql

from config import PG, QUERY_PARAMS
from utils import format_results

DDL = """
DROP TABLE IF EXISTS work_experience, companies, resume_hobbies, hobbies,
                     resumes, cities, users CASCADE;

CREATE TABLE users (
  id            SERIAL PRIMARY KEY,
  login         VARCHAR(50) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL
);

CREATE TABLE cities (
  id   SERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE resumes (
  id          SERIAL PRIMARY KEY,
  user_id     INT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  first_name  VARCHAR(50) NOT NULL,
  last_name   VARCHAR(50) NOT NULL,
  patronymic  VARCHAR(50),
  birth_date  DATE NOT NULL,
  about       TEXT,
  city_id     INT NOT NULL REFERENCES cities(id)
);

CREATE TABLE hobbies (
  id   SERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE resume_hobbies (
  resume_id INT REFERENCES resumes(id) ON DELETE CASCADE,
  hobby_id  INT REFERENCES hobbies(id),
  PRIMARY KEY (resume_id, hobby_id)
);

CREATE TABLE companies (
  id   SERIAL PRIMARY KEY,
  name VARCHAR(150) UNIQUE NOT NULL
);

CREATE TABLE work_experience (
  id         SERIAL PRIMARY KEY,
  resume_id  INT NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
  company_id INT NOT NULL REFERENCES companies(id),
  position   VARCHAR(100) NOT NULL,
  start_date DATE NOT NULL,
  end_date   DATE
);
"""

QUERIES = [
    ("1. Резюме конкретного користувача", """
SELECT
    r.id,
    u.login,
    r.first_name,
    r.last_name,
    r.patronymic,
    r.birth_date,
    r.about,
    c.name AS city,
    (
        SELECT array_agg(h.name)
        FROM resume_hobbies rh
        JOIN hobbies h ON h.id = rh.hobby_id
        WHERE rh.resume_id = r.id
    ) AS hobbies,
    (
        SELECT json_agg(json_build_object(
            'company', comp.name,
            'position', we.position,
            'start_date', we.start_date,
            'end_date', we.end_date
        ))
        FROM work_experience we
        JOIN companies comp ON comp.id = we.company_id
        WHERE we.resume_id = r.id
    ) AS experience
FROM resumes r
JOIN users u ON u.id = r.user_id
JOIN cities c ON c.id = r.city_id
WHERE u.login = %(login)s;
"""),
    ("2. Усі унікальні хобі", """
SELECT DISTINCT h.name
FROM resume_hobbies rh
JOIN hobbies h ON h.id = rh.hobby_id
ORDER BY h.name;
"""),
    ("3. Усі унікальні міста", """
SELECT DISTINCT c.name FROM cities c
JOIN resumes r ON r.city_id = c.id
ORDER BY c.name;
"""),
    ("4. Хобі мешканців заданого міста", """
SELECT DISTINCT h.name
FROM resume_hobbies rh
JOIN hobbies h ON h.id = rh.hobby_id
JOIN resumes r ON r.id = rh.resume_id
JOIN cities c ON c.id = r.city_id
WHERE c.name = %(city)s
ORDER BY h.name;
"""),
    ("5. Здобувачі зі спільним закладом роботи", """
SELECT
    c.name AS company,
    array_agg(DISTINCT u.login || ' (' || r.last_name || ' ' || r.first_name || ')') AS colleagues
FROM companies c
JOIN work_experience we ON we.company_id = c.id
JOIN resumes r ON r.id = we.resume_id
JOIN users u ON u.id = r.user_id
GROUP BY c.name
HAVING count(DISTINCT r.id) > 1
ORDER BY c.name;
"""),
]


def connect():
    return psycopg.connect(**PG, connect_timeout=5)


def ensure_database():
    with psycopg.connect(**{**PG, "dbname": "postgres"}, autocommit=True, connect_timeout=5) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (PG["dbname"],)).fetchone()
        if not exists:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(PG["dbname"])))


def reset():
    ensure_database()
    with connect() as conn:
        conn.execute(DDL)


def insert_names(cur, table, names):
    ids = {}
    for name in sorted(set(names)):
        cur.execute(sql.SQL("INSERT INTO {} (name) VALUES (%s) RETURNING id").format(sql.Identifier(table)), (name,))
        ids[name] = cur.fetchone()[0]
    return ids


def seed(users):
    with connect() as conn, conn.cursor() as cur:
        resumes = [u["resume"] for u in users]
        city_ids = insert_names(cur, "cities", (r["city"] for r in resumes))
        hobby_ids = insert_names(cur, "hobbies", (h for r in resumes for h in r["hobbies"]))
        company_ids = insert_names(cur, "companies", (j["company"] for r in resumes for j in r["experience"]))

        for u in users:
            r = u["resume"]
            cur.execute("INSERT INTO users (login, password_hash) VALUES (%s, %s) RETURNING id",
                        (u["login"], u["password_hash"]))
            user_id = cur.fetchone()[0]

            cur.execute("""INSERT INTO resumes (user_id, first_name, last_name, patronymic, birth_date, about, city_id)
                           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                        (user_id, r["first_name"], r["last_name"], r["patronymic"],
                         r["birth_date"], r["about"], city_ids[r["city"]]))
            resume_id = cur.fetchone()[0]

            cur.executemany("INSERT INTO resume_hobbies (resume_id, hobby_id) VALUES (%s, %s)",
                            [(resume_id, hobby_ids[h]) for h in r["hobbies"]])
            cur.executemany("""INSERT INTO work_experience (resume_id, company_id, position, start_date, end_date)
                               VALUES (%s, %s, %s, %s, %s)""",
                            [(resume_id, company_ids[j["company"]], j["position"], j["start_date"], j["end_date"])
                             for j in r["experience"]])


def counts():
    tables = ["users", "resumes", "cities", "hobbies", "resume_hobbies", "companies", "work_experience"]
    with connect() as conn:
        return {t: conn.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(t))).fetchone()[0]
                for t in tables}


def run_queries():
    results = []
    with connect() as conn, conn.cursor() as cur:
        for title, query in QUERIES:
            cur.execute(query, QUERY_PARAMS)
            cols = [c.name for c in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            results.append({"title": title, "query": query, "rows": rows})
    return results


if __name__ == "__main__":
    print(format_results("PostgreSQL", run_queries()))