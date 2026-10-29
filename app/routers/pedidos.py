from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.database import conectar
from app.schemas import (
    PedidoCrear,
    PedidoCreado,
    PedidoDetalle,
    PedidoEstado,
    PedidoEstadoRespuesta,
    PedidoResumen,
)

router = APIRouter(prefix='/pedidos', tags=['Pedidos'])


TRANSICIONES = {
    'pendiente': {'confirmado', 'cancelado'},
    'confirmado': {'cancelado'},
    'cancelado': set(),
}


def _cancelar(cur, pedido_id: int) -> PedidoEstadoRespuesta:
    """Cancela un pedido dentro de la transaccion abierta: devuelve el stock y cambia el estado."""
    cur.execute('SELECT id, estado FROM pedidos WHERE id=%s FOR UPDATE', (pedido_id,))
    pedido = cur.fetchone()
    if pedido is None:
        raise HTTPException(404, 'Pedido no encontrado')
    anterior = pedido['estado']
    if anterior == 'cancelado':
        raise HTTPException(409, 'El pedido ya esta cancelado')

    cur.execute(
        'SELECT producto_id, cantidad FROM detalle_pedidos WHERE pedido_id=%s ORDER BY producto_id',
        (pedido_id,),
    )
    for d in cur.fetchall():
        cur.execute(
            'UPDATE productos SET stock=stock+%s WHERE id=%s',
            (d['cantidad'], d['producto_id']),
        )
    cur.execute("UPDATE pedidos SET estado='cancelado' WHERE id=%s", (pedido_id,))
    return PedidoEstadoRespuesta(
        id=pedido_id,
        estado_anterior=anterior,
        estado='cancelado',
        mensaje='Pedido cancelado y stock devuelto',
    )


@router.post('', response_model=PedidoCreado, status_code=201)
def crear(datos: PedidoCrear):
    """14. Crea un pedido con sus detalles y descuenta el stock, todo en UNA transaccion."""
    
    if len({i.producto_id for i in datos.items}) != len(datos.items):
        raise HTTPException(422, 'No repita el mismo producto en un pedido')
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT id FROM clientes WHERE id=%s', (datos.cliente_id,))
            if cur.fetchone() is None:
                raise HTTPException(404, 'Cliente no encontrado')

            
            items = sorted(datos.items, key=lambda x: x.producto_id)
            detalles = []
            total = Decimal('0.00')
            for item in items:
                cur.execute(
                    'SELECT id,precio,stock FROM productos WHERE id=%s FOR UPDATE',
                    (item.producto_id,),
                )
                p = cur.fetchone()
                if p is None:
                    raise HTTPException(404, f'Producto {item.producto_id} no encontrado')
                if p['stock'] < item.cantidad:
                    raise HTTPException(409, f'Stock insuficiente del producto {item.producto_id}')
                subtotal = p['precio'] * item.cantidad
                total += subtotal
                detalles.append((item.producto_id, item.cantidad, p['precio'], subtotal))

            cur.execute(
                'INSERT INTO pedidos (cliente_id,estado,total) VALUES (%s,%s,%s)',
                (datos.cliente_id, datos.estado, total),
            )
            pedido_id = cur.lastrowid
            for producto_id, cantidad, precio, subtotal in detalles:
                cur.execute(
                    '''INSERT INTO detalle_pedidos
                       (pedido_id,producto_id,cantidad,precio_unitario,subtotal)
                       VALUES (%s,%s,%s,%s,%s)''',
                    (pedido_id, producto_id, cantidad, precio, subtotal),
                )
                cur.execute(
                    'UPDATE productos SET stock=stock-%s WHERE id=%s',
                    (cantidad, producto_id),
                )
            return PedidoCreado(
                id=pedido_id,
                cliente_id=datos.cliente_id,
                estado=datos.estado,
                total=total,
                items=len(detalles),
            )


@router.get('', response_model=list[PedidoResumen])
def listar(
    estado: Literal['pendiente', 'confirmado', 'cancelado'] | None = None,
    cliente_id: int | None = Query(None, gt=0),
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
):
    """15. Lista pedidos (JOIN con clientes). Filtros opcionales: estado y cliente_id."""
    sql = '''SELECT p.id, p.fecha, p.estado, p.total, c.nombre AS cliente
             FROM pedidos p JOIN clientes c ON c.id=p.cliente_id'''
    condiciones, params = [], []
    if estado:
        condiciones.append('p.estado=%s')
        params.append(estado)
    if cliente_id:
        condiciones.append('p.cliente_id=%s')
        params.append(cliente_id)
    if condiciones:
        sql += ' WHERE ' + ' AND '.join(condiciones)
    sql += ' ORDER BY p.id DESC LIMIT %s OFFSET %s'
    params.extend([limite, (pagina - 1) * limite])
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(sql, tuple(params))
            return cur.fetchall()


@router.get('/{pedido_id}', response_model=PedidoDetalle)
def detalle(pedido_id: int):
    """16. Encabezado del pedido y sus items (JOIN con clientes y productos)."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                '''SELECT p.id, p.fecha, p.estado, p.total, c.nombre AS cliente
                   FROM pedidos p JOIN clientes c ON c.id=p.cliente_id WHERE p.id=%s''',
                (pedido_id,),
            )
            pedido = cur.fetchone()
            if pedido is None:
                raise HTTPException(404, 'Pedido no encontrado')
            cur.execute(
                '''SELECT d.producto_id, pr.nombre AS producto, d.cantidad, d.precio_unitario, d.subtotal
                   FROM detalle_pedidos d JOIN productos pr ON pr.id=d.producto_id
                   WHERE d.pedido_id=%s ORDER BY d.id''',
                (pedido_id,),
            )
            pedido['items'] = cur.fetchall()
            return pedido


@router.patch('/{pedido_id}/estado', response_model=PedidoEstadoRespuesta)
def cambiar_estado(pedido_id: int, datos: PedidoEstado):
    """17. Cambia el estado respetando las transiciones validas (Reto B).

    pendiente -> confirmado | cancelado,  confirmado -> cancelado,  cancelado -> nada.
    Al pasar a 'cancelado' se devuelve el stock.
    """
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT estado FROM pedidos WHERE id=%s FOR UPDATE', (pedido_id,))
            pedido = cur.fetchone()
            if pedido is None:
                raise HTTPException(404, 'Pedido no encontrado')
            actual = pedido['estado']
            if datos.estado not in TRANSICIONES.get(actual, set()):
                raise HTTPException(409, f'Transicion no permitida: {actual} -> {datos.estado}')
            if datos.estado == 'cancelado':
                return _cancelar(cur, pedido_id)
            cur.execute('UPDATE pedidos SET estado=%s WHERE id=%s', (datos.estado, pedido_id))
            return PedidoEstadoRespuesta(
                id=pedido_id,
                estado_anterior=actual,
                estado=datos.estado,
                mensaje='Estado actualizado',
            )


@router.post('/{pedido_id}/cancelar', response_model=PedidoEstadoRespuesta)
def cancelar(pedido_id: int):
    """18. Cancela el pedido, devuelve el stock y evita la doble cancelacion (Reto D)."""
    with conectar() as db:
        with db.cursor() as cur:
            return _cancelar(cur, pedido_id)
