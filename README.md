# Taller 3 ADSO - Tienda

**Aprendiz:** Dilan Rodríguez Vargas
**Ficha:** 3409610

## ¿Qué hace?

Una aplicación para una tienda. Con ella se  puede:

- Guardar clientes.
- Guardar productos con su precio y cuántos hay.
- Hacer pedidos. Al hacer un pedido, los productos disponibles bajan solos.
- Cancelar un pedido. Los productos vuelven al inventario.

## ¿Cómo la uso?

1. En Workbench ejecutar *sql/01_esquema.sq* y luego  *sql/02_datos_prueba.sql* (una sola vez).
2. Copiar *.env.example*, llamarlo *.env* y escribir mi usuario y clave de MySQL.
3. En la terminal, dentro de la carpeta del proyecto:

   ***
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   fastapi dev app/main.py
   *****

4. Abrir en el navegador:
   - http://127.0.0.1:8000/web para usarla
   - http://127.0.0.1:8000/docs para probarla
   -http://127.0.0.1:8000/salud para comprobar la conexion con la base de datos

## Si algo falla

- **Access denied:** la clave del *.env* está mal.
- **Can't connect:** MySQL está apagado.
- **Unknown database:** falta ejecutar *01_esquema.sql*.

## Preguntas de la guía

**¿Para qué sirve detalle_pedidos?**
Para guardar qué productos y cuántos tiene cada pedido.

**¿Por qué se usan claves foráneas?**
Para unir las tablas y evitar errores, como un pedido de un cliente que no existe.

**¿Qué protege una transacción?**
Que el pedido se guarde completo o no se guarde nada.

**¿En qué archivos se separa la lógica?**
En *main.py, database.py, schemas.py, la carpeta routers y la carpeta sql.*