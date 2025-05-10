# 🎶 MusicGraph

**MusicGraph** es un sistema inteligente de descubrimiento musical que analiza hábitos de escucha de usuarios de Spotify, almacena sus datos en MongoDB y construye un grafo en Neo4j para descubrir afinidades musicales, colaboraciones entre artistas y ofrecer recomendaciones personalizadas.

---

## 🧠 Objetivo

Crear una plataforma que:
- Recoja datos reales de usuarios desde Spotify (top tracks)
- Almacene su historial musical en MongoDB
- Construya un grafo en Neo4j con relaciones entre usuarios, artistas y géneros
- Calcule la afinidad musical entre usuarios con teoría de grafos
- Genere recomendaciones personalizadas y modos de exploración musical

---

## ⚙️ Tecnologías usadas

- **Python 3.10**
- **Spotify API** (vía Spotipy)
- **MongoDB** – almacenamiento documental
- **Neo4j** – modelado de grafos
- **Flask** – interfaz web moderna
- **AJAX + HTML/CSS** – para experiencia dinámica sin recargas
- **dotenv / pymongo / neo4j / spotipy** – utilidades y conexiones

---

## 📂 Estructura del proyecto

```
musicgraph/
├── app.py                      # Arranque Flask
├── admincli.py                 # CLI para mantenimiento
├── main.py                     # Legacy script (opcional)
├── .env                        # Variables sensibles (NO subir)
├── docker-compose.yml          # Servicios MongoDB y Neo4j
├── requirements.txt
├── web/
│   └── templates/
│       ├── index.html          # Página principal y recomendaciones
│       └── perfil.html         # Análisis del perfil musical
├── src/
│   ├── api/                    # Rutas Flask (blueprints)
│   ├── config/                 # Carga de entorno
│   ├── db/                     # Conexión MongoDB / Neo4j
│   ├── graph/                  # Construcción de grafo
│   ├── services/               # Recomendaciones, recolección, perfil
│   └── __init__.py
```

---

## 🚀 Cómo ejecutar el proyecto

### 1. Clona el repositorio

```bash
git clone https://github.com/tuusuario/musicgraph.git
cd musicgraph
```

### 2. Crea tu entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # o .\venv\Scripts\activate en Windows
```

### 3. Instala dependencias

```bash
pip install -r requirements.txt
```

### 4. Configura el entorno

Crea un archivo `.env` en la raíz con el siguiente contenido:

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

### 5. Levanta servicios con Docker (MongoDB y Neo4j)

```bash
docker-compose up -d
```

### 6. Lanza la app web

```bash
python app.py
```

O usa el menú CLI:

```bash
python admincli.py
```

---

## 🌐 Funcionalidades disponibles

- Añadir usuario vía conexión con Spotify
- Analizar tu perfil musical y clasificarte: explorador, especialista, mainstream, etc.
- Obtener recomendaciones personalizadas con filtrado por género
- Modo explorador y descubrimiento para salir de tu zona de confort
- Grafo dinámico de usuarios, artistas y géneros
- Afinidad musical basada en coincidencias de artistas y géneros

---

## 📸 Captura de interfaz

> Inserta aquí una imagen de tu frontend o del grafo de Neo4j

---

## 🧭 Trabajo futuro

- Recomendaciones más profundas (colaborativas + contenido)
- Visualización interactiva del grafo (Pyvis / Cytoscape.js)
- Exportar playlists sugeridas directamente a Spotify
- Clustering de comunidades musicales
- Sugerencias cruzadas entre perfiles similares

---

## 👨‍💻 Autores

- Raúl Mendoza Peña
- Yain Estrada Domínguez

---

> Proyecto desarrollado para la asignatura **Bases de Datos No Relacionales (BDNR)**  
> Grado en Ciencia e Ingeniería de Datos – **ULPGC**
