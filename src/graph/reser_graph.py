from src.db.neo4j_connection import get_neo4j_driver

def resetear_grafo():
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run("MATCH (n) DETACH DELETE n")
        print("🧨 Todos los nodos y relaciones han sido eliminados.")

if __name__ == "__main__":
    resetear_grafo()