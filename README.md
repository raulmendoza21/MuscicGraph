# 🎶 MusicGraph

**MusicGraph** es un sistema de análisis musical que recolecta hábitos de escucha de usuarios de Spotify, los almacena en MongoDB y construye un grafo relacional en Neo4j para visualizar afinidades musicales, colaboraciones entre artistas y generar futuras recomendaciones personalizadas.

---

## 🧠 Objetivo

Crear un sistema que:
- Recoja datos reales de usuarios desde Spotify
- Almacene su historial musical y playlists
- Construya un grafo en Neo4j con relaciones entre usuarios, artistas y géneros
- Calcule afinidades musicales entre usuarios
- Permita futuras recomendaciones personalizadas

---

## ⚙️ Tecnologías usadas

- **Python 3.10**
- **Spotify API** – para obtener datos reales
- **MongoDB** – para almacenamiento documental
- **Neo4j** – para modelar relaciones complejas como grafos
- **Spotipy** – wrapper de la API de Spotify
- **dotenv / logging / pymongo / neo4j** – utilidades y conexiones

---

## 📂 Estructura del proyecto

```
MusicGraph/
├── main.py                        # Menú interactivo para ejecutar todo
├── .env                           # Variables sensibles (NO subir)
├── requirements.txt               # Librerías necesarias
├── src/
│   ├── config/                    # Configuración de entorno
│   ├── data/                      # Recolección de datos Spotify
│   ├── db/                        # Conexiones MongoDB y Neo4j
│   ├── graph/                     # Construcción y limpieza del grafo
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

### 4. Configura tu `.env`

Crea un archivo `.env` en la raíz con este contenido:

```
SPOTIFY_CLIENT_ID=tu_id
SPOTIFY_CLIENT_SECRET=tu_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback

MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=musicgraph

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

### 5. Ejecuta el menú interactivo

```bash
python main.py
```

Desde el menú podrás:
- Conectar a MongoDB y Neo4j
- Recolectar datos de usuarios
- Generar y limpiar el grafo
- Crear relaciones avanzadas

---

## 📸 Ejemplo del grafo

*Puedes insertar una captura aquí desde Neo4j Browser o una visualización en Python.*

---

## 📚 Trabajo futuro

- Sistema de recomendaciones por afinidad musical
- Visualización con NetworkX o Pyvis
- Dashboard de artistas más escuchados por comunidad
- Exportación de playlists sugeridas

---

## 👨‍💻 Autores

- Raúl Mendoza Peña
- Yain Estrada Domínguez

---

> Proyecto para la asignatura de **Bases de Datos No Relacionales (BDNR)** - Grado en Ciencia e Ingeniería de Datos - ULPGC
