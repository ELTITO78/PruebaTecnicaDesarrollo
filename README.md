API en FastAPI que consume PokéAPI y expone modelos propios, más una interfaz en HTML y JavaScript.


Funciona Con Docker:

```bash
docker compose up --build
```

Y Sin Docker:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Interfaz: http://localhost:8000



```bash
cd backend
pytest
```


Rutas / Endpoints


| GET | `/api/pokemon?page=1&size=20&name=&type=` 
| GET | `/api/pokemon/{nombre o id}`  
| GET | `/api/types` 

Respuesta:

```json
{ "id": 25, "name": "pikachu", "image": "https://...", "types": ["electric"] }
```


Capas: `client` (HTTP + caché), `service` (reglas y mapeo a DTO), `main` (rutas y manejo de errores).

DTO: `to_pokemon` extrae solo id, nombre, imagen y tipos; nunca se reenvía la respuesta de PokéAPI

Errores: fallos de red o 5xx de PokéAPI: `503`= recurso inexistente  `404`= parámetros inválidos

Caché: TTL + LRU en memoria. Las peticiones concurrentes a la misma clave comparten una sola llamada y los errores no se cachean

Paralelismo controlado: los detalles se consultan con `asyncio.gather` limitados por un `Semaphore` (`POKEDEX_MAX_CONCURRENCY`)

Búsqueda: el índice de nombres se obtiene en una sola llamada y se cachea, así la búsqueda parcial y la paginación solo piden el detalle de los 20 resultados visibles.

Frontend: sin dependencias ni build; cancela peticiones obsoletas con `AbortController` y aplica debounce a la búsqueda


Variables con prefijo `POKEDEX_`: `POKEAPI_URL`, `REQUEST_TIMEOUT`, `MAX_CONCURRENCY`, `CACHE_TTL`, `CACHE_MAX_SIZE`, `CORS_ORIGINS`.
