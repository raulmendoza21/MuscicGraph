from src.db.neo4j_connection import get_neo4j_driver

def verificar_afinidad_en_neo4j():
    driver = get_neo4j_driver()

    query = """
    MATCH (u1:User)-[r:MUSICAL_AFFINITY]->(u2:User)
    RETURN u1.spotify_id AS usuario1, u2.spotify_id AS usuario2, r.score AS afinidad
    ORDER BY afinidad DESC
    LIMIT 20
    """

    with driver.session() as session:
        print("🔍 Verificando relaciones MUSICAL_AFFINITY en Neo4j...")
        result = session.run(query)
        rows = list(result)
        if not rows:
            print("❌ No se encontraron relaciones MUSICAL_AFFINITY.")
        else:
            for row in rows:
                print(f"🎧 {row['usuario1']} ⇄ {row['usuario2']} → score: {row['afinidad']:.2f}")
