# Deploy en PythonAnywhere (sin Docker)

Guia paso a paso para hostear este backend en [PythonAnywhere](https://www.pythonanywhere.com).

## 1. Subir el codigo

Desde tu PC (Git):

```bash
# En PythonAnywhere: Consolas > Bash
git clone https://github.com/NestorCarvacho/Smarket-backend.git
cd Smarket-backend
```

O subi el zip por la pestana **Files**.

## 2. Crear virtualenv e instalar dependencias

En una consola Bash de PythonAnywhere:

```bash
cd ~/Smarket-backend
# Usa el Python que ofrezca PA (3.10+ recomendado)
mkvirtualenv --python=/usr/bin/python3.10 smarket
pip install -r requirements.txt
```

## 3. Crear la base MySQL

1. Pestana **Databases**
2. Create a new MySQL database (ej. nombre `smarket` → queda `tuusuario$smarket`)
3. Anota el password de MySQL (o setea uno)
4. El host suele ser: `tuusuario.mysql.pythonanywhere-services.com`

## 4. Configurar `.env`

En **Files**, crea `~/Smarket-backend/.env`:

```env
DATABASE_URL=mysql+aiomysql://nestorcarvacho:TU_PASSWORD@nestorcarvacho.mysql.pythonanywhere-services.com/nestorcarvacho%24smarket
DATABASE_URL_SYNC=mysql+pymysql://nestorcarvacho:TU_PASSWORD@nestorcarvacho.mysql.pythonanywhere-services.com/nestorcarvacho%24smarket
JWT_SECRET_KEY=PEGALE_UN_SECRETO_LARGO_AQUI
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
CORS_ORIGINS=*
```

Importante:
- Reemplaza `TU_PASSWORD` por el password de MySQL de PythonAnywhere.
- El `$` del nombre de DB va como `%24` en la URL.
- Genera el JWT con: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

## 5. Aplicar migraciones

```bash
cd ~/Smarket-backend
workon smarket
alembic upgrade head
```

Si falla por migraciones viejas / DB vacia, alternativa:

```bash
workon smarket
cd ~/Smarket-backend
python - <<'PY'
import asyncio
from app.db.base import Base
from app.db.session import engine
from app.models import ListItem, ListMember, Purchase, ShoppingList, User  # noqa: F401

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("OK tablas creadas")

asyncio.run(main())
PY
```

## 6. Configurar la Web App

1. Pestana **Web** → **Add a new web app**
2. Manual configuration → Python 3.10 (o el que usaste en el venv)
3. En **Virtualenv**: `/home/nestorcarvacho/.virtualenvs/smarket`
4. En **WSGI configuration file**, reemplaza TODO el contenido por:

```python
import sys
from pathlib import Path

project_home = "/home/nestorcarvacho/Smarket-backend"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from dotenv import load_dotenv
load_dotenv(Path(project_home) / ".env")

from a2wsgi import ASGIMiddleware
from app.main import app

application = ASGIMiddleware(app)
```

> Tambien podes apuntar el WSGI file a `~/Smarket-backend/wsgi.py` si preferis (editando la ruta en la config de Web).

5. **Reload** la web app (boton verde).

## 7. Probar

- Health: `https://nestorcarvacho.pythonanywhere.com/health`
- Docs: `https://nestorcarvacho.pythonanywhere.com/docs`
- API base: `https://nestorcarvacho.pythonanywhere.com/api/v1`

## 8. Apuntar el frontend

En `Smarket-frontend/.env`:

```env
EXPO_PUBLIC_API_URL=https://nestorcarvacho.pythonanywhere.com/api/v1
```

Reinicia Expo / recompila la app Android para que tome la URL.

## Troubleshooting

| Sintoma | Que revisar |
|---------|-------------|
| Error 500 al abrir /docs | Log en Web → Error log. Casi siempre path, venv o `.env`. |
| `Access denied` MySQL | Usuario/password/host; `%24` en el nombre de DB. |
| `ModuleNotFoundError: a2wsgi` | `workon smarket && pip install -r requirements.txt` y Reload. |
| App no ve cambios de codigo | Reload en la pestana Web. |
| CORS en el celular | Deja `CORS_ORIGINS=*` o agrega el origen de Expo. |

## Notas del plan free

- La URL publica es `https://usuario.pythonanywhere.com` (HTTPS incluido).
- Hay limite diario de CPU; para uso personal de la app alcanza.
- No hace falta Docker ni Nginx propio: PA ya sirve la app.
