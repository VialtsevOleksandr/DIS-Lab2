from neo4j import GraphDatabase

from config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER, QUERY_PARAMS
from utils import format_results

CONSTRAINTS = [
    "CREATE CONSTRAINT user_login IF NOT EXISTS FOR (u:User) REQUIRE u.login IS UNIQUE",
    "CREATE CONSTRAINT city_name IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT hobby_name IF NOT EXISTS FOR (h:Hobby) REQUIRE h.name IS UNIQUE",
    "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
]

SEED_QUERY = """
UNWIND $users AS u
CREATE (usr:User {login: u.login, password_hash: u.password_hash})
CREATE (usr)-[:HAS_RESUME]->(r:Resume {
  first_name: u.resume.first_name, last_name: u.resume.last_name,
  patronymic: u.resume.patronymic, birth_date: u.resume.birth_date,
  about: u.resume.about
})
MERGE (c:City {name: u.resume.city})
CREATE (r)-[:LIVES_IN]->(c)
FOREACH (h IN u.resume.hobbies |
  MERGE (hb:Hobby {name: h})
  CREATE (r)-[:HAS_HOBBY]->(hb))
FOREACH (j IN u.resume.experience |
  MERGE (co:Company {name: j.company})
  CREATE (r)-[:WORKED_AT {position: j.position, start_date: j.start_date, end_date: j.end_date}]->(co))
"""

QUERIES = [
    ("1. Резюме конкретного користувача", """
MATCH (u:User {login: $login})-[:HAS_RESUME]->(r:Resume)
OPTIONAL MATCH (r)-[:LIVES_IN]->(c:City)
OPTIONAL MATCH (r)-[:HAS_HOBBY]->(h:Hobby)
OPTIONAL MATCH (r)-[w:WORKED_AT]->(co:Company)
RETURN u.login, r, c.name AS city,
       collect(DISTINCT h.name) AS hobbies,
       collect(DISTINCT {company: co.name, position: w.position,
                         start_date: w.start_date, end_date: w.end_date}) AS experience
"""),
    ("2. Усі унікальні хобі", """
MATCH (:Resume)-[:HAS_HOBBY]->(h:Hobby)
RETURN DISTINCT h.name AS hobby
ORDER BY hobby
"""),
    ("3. Усі унікальні міста", """
MATCH (:Resume)-[:LIVES_IN]->(c:City)
RETURN DISTINCT c.name AS city
ORDER BY city
"""),
    ("4. Хобі мешканців заданого міста", """
MATCH (r:Resume)-[:HAS_HOBBY]->(h:Hobby)
MATCH (r)-[:LIVES_IN]->(c:City {name: $city})
RETURN DISTINCT h.name AS hobby
ORDER BY hobby
"""),
    ("5. Здобувачі зі спільним закладом роботи", """
MATCH (u:User)-[:HAS_RESUME]->(r:Resume)-[:WORKED_AT]->(c:Company)
WITH c, collect(DISTINCT u.login + ' (' + r.last_name + ' ' + r.first_name + ')') AS colleagues
WHERE size(colleagues) > 1
RETURN c.name AS company, colleagues
ORDER BY company
"""),
]


def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def reset():
    with get_driver() as driver:
        driver.execute_query("MATCH (n) DETACH DELETE n")
        for c in CONSTRAINTS:
            driver.execute_query(c)


def seed(users):
    with get_driver() as driver:
        driver.execute_query(SEED_QUERY, users=users)


def counts():
    with get_driver() as driver:
        nodes, _, _ = driver.execute_query(
            "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY label")
        rels, _, _ = driver.execute_query(
            "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS cnt ORDER BY type")
    return {**{r["label"]: r["cnt"] for r in nodes}, **{r["type"]: r["cnt"] for r in rels}}


def run_queries():
    results = []
    with get_driver() as driver:
        for title, query in QUERIES:
            records, _, _ = driver.execute_query(query, QUERY_PARAMS)
            results.append({"title": title, "query": query, "rows": [r.data() for r in records]})
    return results


if __name__ == "__main__":
    print(format_results("Neo4j", run_queries()))