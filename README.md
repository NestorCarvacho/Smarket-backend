# Grocery List API (Smarket Backend)

Backend REST en FastAPI para una app de lista de supermercado. Permite crear listas con productos y cantidades, y registrar la compra de cada producto indicando marca, precio y nombre, soportando que un mismo producto se compre en varias marcas distintas hasta cubrir la cantidad pedida.

## Arquitectura

Arquitectura en capas aplicando principios SOLID y los siguientes patrones de diseño:

- **Repository**: `app/repositories/` — abstrae el acceso a datos detrás de interfaces (`interfaces.py`), implementadas con SQLAlchemy.
- **Service Layer / Use Cases**: `app/services/` — contiene toda la logica de negocio, sin conocer HTTP ni SQL.
- **DTO**: `app/schemas/` — modelos Pydantic de entrada/salida, separados de los modelos ORM (`app/models/`).
- **Dependency Injection**: `app/api/deps.py` — construye e inyecta repositorios/services vía `Depends` de FastAPI (Dependency Inversion: los services dependen de interfaces, no de SQLAlchemy).
- **Unit of Work simplificado**: una sesión de SQLAlchemy por request (`app/db/session.py`), con commit/rollback automático.

```
app/
  core/         # config, seguridad JWT, excepciones de dominio
  db/           # engine y sesión async
  models/       # entidades SQLAlchemy (User, ShoppingList, ListItem, Purchase)
  schemas/      # DTOs Pydantic
  repositories/ # interfaces + implementaciones SQLAlchemy
  services/     # lógica de negocio
  api/v1/       # routers (auth, lists, items, purchases)
tests/          # pytest con SQLite en memoria
alembic/        # migraciones de base de datos
```

## Modelo de dominio

Un `ShoppingList` tiene varios `ListItem` (producto + cantidad pedida). Cada `ListItem` puede tener varias `Purchase` (una por marca comprada, con precio y cantidad). Cuando la suma de cantidades compradas alcanza la cantidad pedida, el item pasa a `completed`.

## Requisitos previos

- Python 3.10+
- MySQL (en produccion: el de PythonAnywhere) o SQLite para desarrollo local

## Deploy en la nube (PythonAnywhere, sin Docker)

Ver la guia completa: [`DEPLOY_PYTHONANYWHERE.md`](./DEPLOY_PYTHONANYWHERE.md).

Resumen: subis el repo, creas un virtualenv, configuras MySQL + `.env`, corres `alembic upgrade head`, y apuntas la Web App al `wsgi.py` (adapta FastAPI ASGI → WSGI con `a2wsgi`).

La API queda en `https://TU_USUARIO.pythonanywhere.com` y el frontend usa:

```env
EXPO_PUBLIC_API_URL=https://TU_USUARIO.pythonanywhere.com/api/v1
```

## Puesta en marcha local (Windows / PowerShell)

```powershell
# 1. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Copiar variables de entorno
Copy-Item .env.example .env
# Editá .env y poné un JWT_SECRET_KEY propio

# 4. Levantar MySQL con Docker
docker compose up -d

# 5. Aplicar migraciones (crea las tablas)
alembic revision --autogenerate -m "init"
alembic upgrade head

# 6. Correr el servidor de desarrollo
uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`. Documentación interactiva (Swagger) en `http://127.0.0.1:8000/docs`.

Si estás probando desde el celular con Expo Go, usá la IP de tu PC en la red local (ej. `http://192.168.0.10:8000`) en vez de `127.0.0.1`, y corré uvicorn con `--host 0.0.0.0`.

## Alternativa rápida sin Docker (SQLite)

Si todavía no tenés Docker instalado, podés arrancar el backend igual usando SQLite en vez de MySQL, sin cambiar nada del código:

```powershell
# .env con SQLite en vez de MySQL
@"
DATABASE_URL=sqlite+aiosqlite:///./smarket_dev.db
DATABASE_URL_SYNC=sqlite:///./smarket_dev.db
JWT_SECRET_KEY=<generá el tuyo con: python -c "import secrets; print(secrets.token_urlsafe(48))">
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
CORS_ORIGINS=*
"@ | Out-File -Encoding ascii .env

alembic revision --autogenerate -m "init"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

> Nota: si el puerto 8000 aparece "en uso" sin que haya ningún proceso Python corriendo, probá con otro puerto (ej. 8010) — es un tema conocido de reserva de puertos en Windows/Hyper-V, no del proyecto.

Cuando instales Docker, volvé a poner las URLs de MySQL en `.env` y seguí la sección de arriba.

## Tests

```powershell
pytest
```

Los tests usan SQLite en memoria (no requieren Docker ni MySQL corriendo) y cubren registro/login y el flujo completo de compra multi-marca.

## Endpoints principales

| Método | Ruta                                                    | Descripción                              |
|--------|----------------------------------------------------------|-------------------------------------------|
| POST   | `/api/v1/auth/register`                                  | Registrar usuario                         |
| POST   | `/api/v1/auth/login`                                      | Login, devuelve access + refresh token    |
| POST   | `/api/v1/auth/refresh`                                     | Renovar access token                      |
| GET/POST | `/api/v1/lists`                                          | Listar / crear listas del usuario         |
| GET/DELETE | `/api/v1/lists/{list_id}`                                | Detalle / eliminar lista                  |
| GET/POST | `/api/v1/lists/{list_id}/items`                          | Listar / agregar producto a la lista      |
| PATCH/DELETE | `/api/v1/lists/{list_id}/items/{item_id}`            | Editar / eliminar producto                |
| POST   | `/api/v1/lists/{list_id}/items/{item_id}/purchases`       | Registrar compra (marca, precio, cantidad)|
| DELETE | `/api/v1/lists/{list_id}/items/{item_id}/purchases/{id}` | Deshacer una compra                       |

Todas las rutas (excepto `/auth/*`) requieren el header `Authorization: Bearer <access_token>`.
