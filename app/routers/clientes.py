from fastapi import APIRouter, HTTPException
from pymysql.err import IntegrityError

from app.database import conectar
from app.schemas import (
    ClienteActualizar,
    ClienteCrear,
    ClienteRespuesta,
    PedidoClienteResumen,
)

router = APIRouter(prefix='/clientes', tags=['Clientes'])


@router.get('', response_model=list[ClienteRespuesta])
def listar():
    """1. Lista todos los clientes."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT * FROM clientes ORDER BY id')
            return cur.fetchall()


@router.get('/{cliente_id}', response_model=ClienteRespuesta)
def obtener(cliente_id: int):
    """2. Obtiene un cliente por su id."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT * FROM clientes WHERE id=%s', (cliente_id,))
            cliente = cur.fetchone()
    if cliente is None:
        raise HTTPException(404, 'Cliente no encontrado')
    return cliente


@router.post('', response_model=ClienteRespuesta, status_code=201)
def crear(datos: ClienteCrear):
    """3. Crea un cliente. 409 si el correo ya existe."""
    try:
        with conectar() as db:
            with db.cursor() as cur:
                cur.execute(
                    'INSERT INTO clientes (nombre,correo) VALUES (%s,%s)',
                    (datos.nombre, str(datos.correo)),
                )
                nuevo_id = cur.lastrowid
                cur.execute('SELECT * FROM clientes WHERE id=%s', (nuevo_id,))
                return cur.fetchone()
    except IntegrityError as exc:
        raise HTTPException(409, 'Correo ya registrado') from exc


@router.put('/{cliente_id}', response_model=ClienteRespuesta)
def actualizar(cliente_id: int, datos: ClienteActualizar):
    """4. Reemplaza nombre y correo (Reto C). 404 si no existe, 409 si el correo es de otro cliente."""
    try:
        with conectar() as db:
            with db.cursor() as cur:
                cur.execute('SELECT id FROM clientes WHERE id=%s', (cliente_id,))
                if cur.fetchone() is None:
                    raise HTTPException(404, 'Cliente no encontrado')
                cur.execute(
                    'UPDATE clientes SET nombre=%s, correo=%s WHERE id=%s',
                    (datos.nombre, str(datos.correo), cliente_id),
                )
                cur.execute('SELECT * FROM clientes WHERE id=%s', (cliente_id,))
                return cur.fetchone()
    except IntegrityError as exc:
        raise HTTPException(409, 'Correo ya registrado por otro cliente') from exc


@router.delete('/{cliente_id}', status_code=204)
def eliminar(cliente_id: int):
    """5. Elimina un cliente (Reto C). 409 si tiene pedidos (respeta la clave foranea)."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT id FROM clientes WHERE id=%s', (cliente_id,))
            if cur.fetchone() is None:
                raise HTTPException(404, 'Cliente no encontrado')
            cur.execute('SELECT COUNT(*) AS n FROM pedidos WHERE cliente_id=%s', (cliente_id,))
            if cur.fetchone()['n'] > 0:
                raise HTTPException(409, 'No se puede eliminar: el cliente tiene pedidos')
            cur.execute('DELETE FROM clientes WHERE id=%s', (cliente_id,))


@router.get('/{cliente_id}/pedidos', response_model=list[PedidoClienteResumen])
def pedidos_del_cliente(cliente_id: int):
    """6. Pedidos de un cliente con JOIN, del mas reciente al mas antiguo (Reto A)."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT id FROM clientes WHERE id=%s', (cliente_id,))
            if cur.fetchone() is None:
                raise HTTPException(404, 'Cliente no encontrado')
            cur.execute(
                '''SELECT p.id, p.fecha, p.estado, p.total
                   FROM pedidos p JOIN clientes c ON c.id=p.cliente_id
                   WHERE c.id=%s ORDER BY p.fecha DESC, p.id DESC''',
                (cliente_id,),
            )
            return cur.fetchall()
