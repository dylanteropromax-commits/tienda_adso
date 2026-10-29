from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, EmailStr



class ClienteCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    correo: EmailStr


class ClienteActualizar(ClienteCrear):
    """PUT reemplaza todos los campos, por eso es igual a ClienteCrear."""


class ClienteRespuesta(ClienteCrear):
    id: int


class ProductoCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    precio: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock: int = Field(ge=0)


class ProductoActualizar(ProductoCrear):
    """PUT reemplaza todos los campos, por eso es igual a ProductoCrear."""


class ProductoRespuesta(ProductoCrear):
    id: int


class ItemPedido(BaseModel):
    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0)


class PedidoCrear(BaseModel):
    cliente_id: int = Field(gt=0)
    items: list[ItemPedido] = Field(min_length=1)
    estado: Literal['pendiente', 'confirmado'] = 'confirmado'


class PedidoEstado(BaseModel):
    estado: Literal['confirmado', 'cancelado']


class PedidoCreado(BaseModel):
    id: int
    cliente_id: int
    estado: str
    total: Decimal
    items: int


class PedidoResumen(BaseModel):
    id: int
    fecha: datetime
    estado: str
    total: Decimal
    cliente: str


class PedidoClienteResumen(BaseModel):
    id: int
    fecha: datetime
    estado: str
    total: Decimal


class DetalleItem(BaseModel):
    producto_id: int
    producto: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class PedidoDetalle(PedidoResumen):
    items: list[DetalleItem]


class PedidoEstadoRespuesta(BaseModel):
    id: int
    estado_anterior: str
    estado: str
    mensaje: str


class VentasCliente(BaseModel):
    cliente_id: int
    cliente: str
    total_pedidos: int
    total_vendido: Decimal


class ProductoVendido(BaseModel):
    producto_id: int
    producto: str
    unidades_vendidas: int
    total_vendido: Decimal


class ResumenGeneral(BaseModel):
    clientes: int
    productos: int
    pedidos_pendientes: int
    pedidos_confirmados: int
    pedidos_cancelados: int
    ventas_totales: Decimal
