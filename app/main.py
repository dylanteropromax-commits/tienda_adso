from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.database import conectar
from app.routers import clientes, productos, pedidos, reportes

app = FastAPI(
    title='Taller 3 ADSO - Tienda',
    version='3.0',
    description='API relacional: clientes, productos, pedidos y detalles',
)

app.include_router(clientes.router)
app.include_router(productos.router)
app.include_router(pedidos.router)
app.include_router(reportes.router)

app.mount('/web', StaticFiles(directory=Path(__file__).parent / 'static', html=True), name='web')


@app.get('/', tags=['Inicio'])
def inicio():
    return {'mensaje': 'API tienda ADSO', 'documentacion': '/docs', 'interfaz': '/web'}


@app.get('/salud', tags=['Inicio'])
def salud():
    """Comprueba que la API puede hablar con la base de datos."""
    try:
        with conectar() as db:
            with db.cursor() as cur:
                cur.execute('SELECT 1 AS ok')
                cur.fetchone()
    except Exception as exc:
        raise HTTPException(503, f'Sin conexion a la base de datos: {exc}') from exc
    return {'api': 'ok', 'base_de_datos': 'ok'}
