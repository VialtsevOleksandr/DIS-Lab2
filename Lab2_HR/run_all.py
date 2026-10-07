"""
  python run_all.py           # очистити бази, наповнити, виконати запити, зберегти results.txt
  python run_all.py seed      # лише очистити й наповнити бази
  python run_all.py queries   # лише виконати запити й зберегти results.txt
"""
import sys

import mongo_runner
import neo4j_runner
import postgres_runner
from config import RESULTS_FILE
from generate_data import load_data
from utils import format_results

RUNNERS = [("PostgreSQL", postgres_runner), ("MongoDB", mongo_runner), ("Neo4j", neo4j_runner)]


def seed_all():
    users = load_data()
    for name, runner in RUNNERS:
        runner.reset()
        runner.seed(users)
        print(f"[{name}] наповнено: {runner.counts()}")


def queries_all():
    text = "".join(format_results(name, runner.run_queries()) for name, runner in RUNNERS)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print(f"Збережено у {RESULTS_FILE}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("all", "seed"):
        seed_all()
    if mode in ("all", "queries"):
        queries_all()