import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def get_neo4j_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        raise ValueError("❌ Faltan variables de entorno para Neo4j (URI, USERNAME o PASSWORD).")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver
