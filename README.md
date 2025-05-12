# 🎧 MusicGraph – Recomendador Musical Inteligente

**MusicGraph** es un sistema de descubrimiento musical que analiza tus hábitos de escucha en Spotify para construir un perfil musical único. Utiliza grafos y afinidades reales entre usuarios para ofrecerte recomendaciones personalizadas, exploración de nuevos géneros y una interfaz web inspirada en el estilo de Spotify.

---

## 🧠 Objetivo del Proyecto

Crear una plataforma que:
- Conecte con la cuenta de Spotify del usuario.
- Recolecte su historial musical (top tracks, playlists).
- Almacene la información en MongoDB.
- Construya un grafo en Neo4j con relaciones entre usuarios, artistas y géneros.
- Calcule afinidades musicales entre usuarios reales.
- Genere recomendaciones personalizadas basadas en el grafo.
- Clasifique al usuario según su perfil musical (mainstream, explorador...).

---

## ⚙️ Tecnologías utilizadas

- **Python 3.10**
- **Flask** – servidor web
- **MongoDB** – almacenamiento documental
- **Neo4j** – base de datos de grafos
- **Spotipy (Spotify API)** – recolección de datos musicales
- **AJAX + HTML/CSS** – frontend dinámico sin recarga
- **Docker Compose** – orquestación de MongoDB y Neo4j

---

## 🧱 Arquitectura del sistema

```
+--------------------------+        +--------------------+
|      Interfaz Web        | <----> |    Flask Backend   |
|  (HTML/CSS + JS + AJAX)  |        +--------------------+
+--------------------------+                 |
          ^                                   |
          | AJAX                              v
+--------------------------+        +--------------------+
|      Recomendaciones     |        |  Recolección de    |
|    Análisis de Perfil    |        |     datos Spotify  |
+--------------------------+        +--------------------+
          |                                   |
          v                                   v
+---------------------+          +----------------------+
|      MongoDB        | <------> |      Neo4j           |
| Historial de tracks |          |   Grafo musical:     |
|  Artistas, Géneros  |          | Users – Artists – Genres
+---------------------+          +----------------------+
```

---

## 📂 Estructura del Proyecto

```
musicgraph/
├── app.py                      # Arranque principal con Flask
├── admincli.py                 # CLI para tareas de administración
├── docker-compose.yml          # MongoDB y Neo4j
├── .env                        # Variables de entorno (IGNORADO por Git)
├── requirements.txt            # Dependencias Python
├── web/
│   └── templates/
│       ├── index.html          # Página principal con formulario y recomendaciones
│       └── perfil.html         # Visualización del perfil musical
├── src/
│   ├── api/                    # Blueprints de Flask
│   ├── db/                     # Conexiones a MongoDB y Neo4j
│   ├── graph/                  # Construcción y mantenimiento del grafo
│   ├── services/               # Recolección, perfil y recomendación
│   └── __init__.py
```

---

## 🚀 Instrucciones de ejecución

1. **Clona el repositorio:**
```bash
git clone https://github.com/tuusuario/musicgraph.git
cd musicgraph
```

2. **Crea el entorno virtual:**
```bash
python -m venv venv
source venv/bin/activate  # o .\venv\Scripts\activate en Windows
```

3. **Instala las dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configura el entorno:**
Crea un archivo `.env` con:

```ini
SPOTIFY_CLIENT_ID=tu_client_id
SPOTIFY_CLIENT_SECRET=tu_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback

MONGODB_URI=mongodb://admin:password@localhost:27017/musicgraph?authSource=admin
MONGODB_DATABASE=musicgraph

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

5. **Levanta los servicios:**
```bash
docker-compose up -d
```

6. **Ejecuta la app web:**
```bash
python app.py
```

---

## 🌐 Funcionalidades principales

- ✅ Autenticación segura con Spotify
- ✅ Análisis de perfil musical con clasificación personalizada
- ✅ Recomendaciones personalizadas basadas en afinidad de usuarios
- ✅ Modo explorador para salir de la burbuja musical
- ✅ Grafo musical dinámico en Neo4j
- ✅ Interfaz web moderna, sin recargas, estilo Spotify


---

## 🧭 Trabajo futuro

- Recomendaciones colaborativas + basadas en contenido
- Exportar playlists sugeridas directamente a Spotify
- Visualización interactiva del grafo (con Pyvis o Cytoscape)
- Segmentación de comunidades musicales (clustering)
- Sistema de feedback del usuario

---

## 👨‍💻 Autores

- Raúl Mendoza Peña  
- Yain Estrada Domínguez

> Proyecto desarrollado para la asignatura **Bases de Datos No Relacionales (BDNR)**  
> Grado en Ciencia e Ingeniería de Datos – **ULPGC**
