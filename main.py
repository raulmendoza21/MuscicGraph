from src.config.settings import load_env
from src.data.spotify_data_collector import MultiUserSpotifyDataCollector
from src.db.mongodb_connection import get_mongo_database
from src.db.neo4j_connection import get_neo4j_driver
from src.graph.graph_builder import construir_grafo
from src.graph.mongodb_to_neo4j import create_advanced_relationships
from src.graph.reser_graph import resetear_grafo

def conectar_mongodb():
    try:
        db = get_mongo_database()
        print(f"✅ Conectado a MongoDB. Colecciones: {db.list_collection_names()}")
    except Exception as e:
        print(f"❌ Error al conectar a MongoDB: {e}")

def conectar_neo4j():
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            result = session.run("RETURN 1 AS ok")
            print("✅ Conectado a Neo4j:", result.single()["ok"])
    except Exception as e:
        print(f"❌ Error al conectar a Neo4j: {e}")

def recolectar_datos():
    try:
        recolector = MultiUserSpotifyDataCollector()
        recolector.add_multiple_users(1)
    except Exception as e:
        print(f"❌ Error durante la recolección de datos: {e}")

def menu():
    while True:
        print("\n🎛️  Menu de opciones:")
        print("1. Conectar a MongoDB")
        print("2. Conectar a Neo4j")
        print("3. Recolectar datos de Spotify")
        print("4. Resetear grafo en Neo4j")
        print("5. Construir grafo inicial")
        print("6. Crear relaciones avanzadas (géneros, afinidad, colaboraciones)")
        print("7. Ejecutar TODO el flujo")
        print("0. Salir")

        choice = input("Selecciona una opción: ")

        if choice == "1":
            conectar_mongodb()
        elif choice == "2":
            conectar_neo4j()
        elif choice == "3":
            recolectar_datos()
        elif choice == "4":
            resetear_grafo()
        elif choice == "5":
            construir_grafo()
        elif choice == "6":
            create_advanced_relationships()
        elif choice == "7":
            conectar_mongodb()
            conectar_neo4j()
            recolectar_datos()
            resetear_grafo()
            construir_grafo()
            create_advanced_relationships()
        elif choice == "0":
            print("👋 Saliendo.")
            break
        else:
            print("❌ Opción no válida. Intenta de nuevo.")

def main():
    print("🚀 Iniciando MusicGraph...")
    load_env()
    menu()

if __name__ == "__main__":
    main()
