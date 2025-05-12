from src.services.spotify_data_collector import MultiUserSpotifyDataCollector
from src.db.mongodb_connection import get_mongo_database
from src.db.neo4j_connection import get_neo4j_driver
from src.graph.graph_builder_full import construir_grafo_completo, resetear_grafo
from src.services.recommendation_service import recomendar_artistas_para_usuario
from collections import Counter

def mostrar_resumen_musical(top_n=10):
    db = get_mongo_database()
    artistas_counter = Counter()
    canciones_counter = Counter()

    for track in db["top_tracks"].find():
        canciones_counter[track["name"]] += 1
        for artista in track.get("artists", []):
            artistas_counter[artista["name"]] += 1

    print(f"\n🎧 Top {top_n} artistas más escuchados:")
    for nombre, count in artistas_counter.most_common(top_n):
        print(f"  - {nombre} ({count} apariciones)")

    print(f"\n🎵 Top {top_n} canciones más frecuentes:")
    for nombre, count in canciones_counter.most_common(top_n):
        print(f"  - {nombre} ({count} veces)")

def mostrar_usuarios():
    db = get_mongo_database()
    usuarios = list(db["users"].find({}, {"display_name": 1, "spotify_id": 1}))
    if not usuarios:
        print("⚠️ No hay usuarios en la base de datos.")
        return
    print(f"\n👥 Usuarios registrados ({len(usuarios)}):")
    for u in usuarios:
        print(f"- {u.get('display_name', 'Desconocido')} ({u['spotify_id']})")

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
        print("📦 Conexiones:")
        print("1. Conectar a MongoDB")
        print("2. Conectar a Neo4j")
        print("\n🎧 Datos:")
        print("3. Recolectar datos de Spotify")
        print("6. Ver resumen musical global (MongoDB)")
        print("9. Ver usuarios registrados (MongoDB)")
        print("\n🧠 Grafo:")
        print("4. Resetear grafo en Neo4j")
        print("5. Construir grafo completo")
        print("\n🚀 Automatización:")
        print("7. Ejecutar TODO el flujo")
        print("8. Recomendar artistas")
        print("\n0. Salir")

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
            construir_grafo_completo()
        elif choice == "6":
            mostrar_resumen_musical()
        elif choice == "7":
            conectar_mongodb()
            conectar_neo4j()
            recolectar_datos()
            resetear_grafo()
            construir_grafo_completo()
        elif choice == "8":
            user_id = input("🎧 Ingresa tu Spotify ID: ").strip()
            recomendaciones = recomendar_artistas_para_usuario(user_id,None)
            print("\n🎯 Recomendaciones:")
            for r in recomendaciones:
                print(f"- {r['nombre']} ({', '.join(r['generos'])}) - Popularidad: {r['popularidad']}")
        elif choice == "9":
            mostrar_usuarios()
        elif choice == "0":
            print("👋 Saliendo.")
            break
        else:
            print("❌ Opción no válida. Intenta de nuevo.")

def main():
    print("🚀 Iniciando MusicGraph...")
    menu()

if __name__ == "__main__":
    main()
