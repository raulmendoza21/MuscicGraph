from neo4j import GraphDatabase
from src.db.neo4j_connection import get_neo4j_driver
from typing import Optional

def recomendar_artistas_para_usuario(user_spotify_id: str, top_n: int = 5, genero: Optional[str] = None):
    driver = get_neo4j_driver()

    query = """
    MATCH (:User {spotify_id: $user_id})-[:MUSICAL_AFFINITY]->(vecino:User)
    MATCH (vecino)-[:LISTENS_TO]->(artista:Artist)
    WHERE NOT EXISTS {
        MATCH (:User {spotify_id: $user_id})-[:LISTENS_TO]->(artista)
    }
    """

    # Si se filtra por género, añadimos ese MATCH
    if genero:
        query += """
        MATCH (artista)-[:BELONGS_TO]->(g:Genre)
        WHERE g.name = $genero
        """

    query += """
    RETURN artista.name AS nombre,
           artista.spotify_id AS id,
           artista.popularity AS popularidad,
           COUNT(*) AS coincidencias
    ORDER BY coincidencias DESC, popularidad DESC
    LIMIT $top_n
    """

    with driver.session() as session:
        result = session.run(query, user_id=user_spotify_id, genero=genero, top_n=top_n)
        recomendaciones = result.data()

    if not recomendaciones:
        print(f"⚠️ No se encontraron recomendaciones para el usuario {user_spotify_id}.")
    else:
        print(f"\n🎧 Recomendaciones para {user_spotify_id}" + (f" (género: {genero})" if genero else "") + ":")
        for i, reco in enumerate(recomendaciones, start=1):
            print(f"{i}. {reco['nombre']} (id: {reco['id']}) | Popularidad: {reco.get('popularidad', 'N/A')} | Escuchado por {reco['coincidencias']} usuarios similares")

    return recomendaciones
