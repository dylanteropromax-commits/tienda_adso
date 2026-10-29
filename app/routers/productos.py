from fastapi import APIRouter, HTTPException, Query

from app.database import conectar
from app.schemas import ProductoActualizar, ProductoCrear, ProductoRespuesta

router = APIRouter(prefix='/productos', tags=['Productos'])


@router.get('', response_model=list[ProductoRespuesta])
def listar(
    buscar: str | None = None,
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=50),
):
    """7. Lista productos con busqueda por nombre y paginacion."""
    sql = 'SELECT * FROM productos'
    params = []
    if buscar:
        sql += ' WHERE nombre LIKE %s'
        params.append(f'%{buscar}%')
    sql += ' ORDER BY id LIMIT %s OFFSET %s'
    params.extend([limite, (pagina - 1) * limite])
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(sql, tuple(params))
            return cur.fetchall()


@router.get('/bajo-stock', response_model=list[ProductoRespuesta])
def bajo_stock(umbral: int = Query(5, ge=0)):
    """8. Productos con stock menor o igual al umbral (por defecto 5)."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT * FROM productos WHERE stock <= %s ORDER BY stock, id', (umbral,))
            return cur.fetchall()


@router.get('/{producto_id}', response_model=ProductoRespuesta)
def obtener(producto_id: int):
    """9. Obtiene un producto por su id."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT * FROM productos WHERE id=%s', (producto_id,))
            producto = cur.fetchone()
    if producto is None:
        raise HTTPException(404, 'Producto no encontrado')
    return producto


@router.post('', response_model=ProductoRespuesta, status_code=201)
def crear(datos: ProductoCrear):
    """10. Crea un producto. 422 si el precio es negativo o cero."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                'INSERT INTO productos (nombre,precio,stock) VALUES (%s,%s,%s)',
                (datos.nombre, datos.precio, datos.stock),
            )
            nuevo_id = cur.lastrowid
            cur.execute('SELECT * FROM productos WHERE id=%s', (nuevo_id,))
            return cur.fetchone()


@router.put('/{producto_id}', response_model=ProductoRespuesta)
def actualizar(producto_id: int, datos: ProductoActualizar):
    """11. Reemplaza nombre, precio y stock de un producto.

    Los pedidos ya hechos no cambian: guardan su propio precio_unitario.
    """
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                'UPDATE productos SET nombre=%s, precio=%s, stock=%s WHERE id=%s',
                (datos.nombre, datos.precio, datos.stock, producto_id),
            )
            cur.execute('SELECT * FROM productos WHERE id=%s', (producto_id,))
            producto = cur.fetchone()
            if producto is None:
                raise HTTPException(404, 'Producto no encontrado')
            return producto


@router.patch('/{producto_id}/stock', response_model=ProductoRespuesta)
def cambiar_stock(producto_id: int, stock: int = Query(ge=0)):
    """12. Cambia solo el stock: PATCH /productos/{id}/stock?stock=10"""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT id FROM productos WHERE id=%s', (producto_id,))
            if cur.fetchone() is None:
                raise HTTPException(404, 'Producto no encontrado')
            cur.execute('UPDATE productos SET stock=%s WHERE id=%s', (stock, producto_id))
            cur.execute('SELECT * FROM productos WHERE id=%s', (producto_id,))
            return cur.fetchone()


@router.delete('/{producto_id}', status_code=204)
def eliminar(producto_id: int):
    """13. Elimina un producto. 409 si ya aparece en algun pedido."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT id FROM productos WHERE id=%s', (producto_id,))
            if cur.fetchone() is None:
                raise HTTPException(404, 'Producto no encontrado')
            cur.execute('SELECT COUNT(*) AS n FROM detalle_pedidos WHERE producto_id=%s', (producto_id,))
            if cur.fetchone()['n'] > 0:
                raise HTTPException(409, 'No se puede eliminar: el producto aparece en pedidos')
            cur.execute('DELETE FROM productos WHERE id=%s', (producto_id,))
