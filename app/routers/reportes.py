from fastapi import APIRouter, Query

from app.database import conectar
from app.schemas import ProductoVendido, ResumenGeneral, VentasCliente

router = APIRouter(prefix='/reportes', tags=['Reportes'])
# Los reportes solo hacen SELECT: no modifican ningun registro.
# Los pedidos cancelados NO cuentan como venta.


@router.get('/ventas-por-cliente', response_model=list[VentasCliente])
def ventas_por_cliente():
    """19. Por cliente: cantidad de pedidos y total vendido (COUNT, SUM y JOIN) (Reto E)."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                '''SELECT c.id AS cliente_id, c.nombre AS cliente,
                          COUNT(p.id) AS total_pedidos,
                          COALESCE(SUM(p.total), 0) AS total_vendido
                   FROM clientes c
                   LEFT JOIN pedidos p ON p.cliente_id=c.id AND p.estado <> 'cancelado'
                   GROUP BY c.id, c.nombre
                   ORDER BY total_vendido DESC, c.id'''
            )
            return cur.fetchall()


@router.get('/productos-mas-vendidos', response_model=list[ProductoVendido])
def productos_mas_vendidos(limite: int = Query(5, ge=1, le=50)):
    """20. Ranking de productos por unidades vendidas."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                '''SELECT pr.id AS producto_id, pr.nombre AS producto,
                          SUM(d.cantidad) AS unidades_vendidas,
                          SUM(d.subtotal) AS total_vendido
                   FROM detalle_pedidos d
                   JOIN pedidos p ON p.id=d.pedido_id AND p.estado <> 'cancelado'
                   JOIN productos pr ON pr.id=d.producto_id
                   GROUP BY pr.id, pr.nombre
                   ORDER BY unidades_vendidas DESC, pr.id
                   LIMIT %s''',
                (limite,),
            )
            return cur.fetchall()


@router.get('/resumen', response_model=ResumenGeneral)
def resumen():
    """21. Totales generales de la tienda."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT COUNT(*) AS n FROM clientes')
            clientes = cur.fetchone()['n']
            cur.execute('SELECT COUNT(*) AS n FROM productos')
            productos = cur.fetchone()['n']
            cur.execute(
                '''SELECT
                     COALESCE(SUM(estado='pendiente'), 0)  AS pendientes,
                     COALESCE(SUM(estado='confirmado'), 0) AS confirmados,
                     COALESCE(SUM(estado='cancelado'), 0)  AS cancelados,
                     COALESCE(SUM(CASE WHEN estado <> 'cancelado' THEN total END), 0) AS ventas
                   FROM pedidos'''
            )
            r = cur.fetchone()
            return ResumenGeneral(
                clientes=clientes,
                productos=productos,
                pedidos_pendientes=int(r['pendientes']),
                pedidos_confirmados=int(r['confirmados']),
                pedidos_cancelados=int(r['cancelados']),
                ventas_totales=r['ventas'],
            )
