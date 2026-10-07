"""Параметри підключення до трьох баз."""
import os

# --- PostgreSQL ---
PG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5432)),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
    "dbname": os.getenv("PG_DB", "hr_task"),  # створюється автоматично, якщо немає
}

# --- MongoDB ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "hr_task")

# --- Neo4j ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# --- Дані ---
BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE_DIR, "data.json")
RESULTS_FILE = os.path.join(BASE_DIR, "results.txt")
SEED = 42
RESUME_COUNT = 50

# --- Параметри запитів 1 і 4 ---
QUERY_PARAMS = {
    "login": "oleksandr_kovalenko",
    "city": "Київ",
}