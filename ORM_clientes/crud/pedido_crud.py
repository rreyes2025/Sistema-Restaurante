from sqlalchemy.orm import Session
from models import Pedido, DetallePedido, Menu, Ingrediente
from functools import reduce
from datetime import datetime

def crear_pedido(db: Session, cliente_id: int, lista_items: list, fecha_str: str = None):
    
    #crea un pedido 
    if not lista_items:
        raise ValueError("El pedido no puede estar vacio")

    # 1. REDUCE: calcular total de ingredientes necesarios
    def sumar_reqs(acumulado, item):
        menu = db.query(Menu).get(item['menu_id'])
        if not menu: return acumulado
        for assoc in menu.ingredientes_asociados:
            cant_necesaria = assoc.cantidad_requerida * item['cantidad']
            acumulado[assoc.ingrediente_id] = acumulado.get(assoc.ingrediente_id, 0) + cant_necesaria
        return acumulado

    total_reqs = reduce(sumar_reqs, lista_items, {})

    # validacion de stock
    for ing_id, necesario in total_reqs.items():
        ing = db.query(Ingrediente).get(ing_id)
        if ing.cantidad < necesario:
            raise ValueError(f"Stock insuficiente de {ing.nombre}")

    try:
        # descontar stock
        for ing_id, necesario in total_reqs.items():
            ing = db.query(Ingrediente).get(ing_id)
            ing.cantidad -= necesario

        # determinar fecha
        fecha_obj = datetime.now()
        if fecha_str:
            try:
                # convertir string dd/mm/yyyy a datetime
                fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
            except ValueError:
                raise ValueError("Formato de fecha invalido. Use dd/mm/yyyy")

        # crear pedido
        pedido = Pedido(cliente_id=cliente_id, fecha=fecha_obj)
        db.add(pedido)
        db.flush()

        # 2. MAP: crear objetos DetallePedido
        def crear_detalle(item):
            menu = db.query(Menu).get(item['menu_id'])
            subt = menu.precio * item['cantidad']
            return DetallePedido(
                pedido_id=pedido.id,
                menu_id=menu.id,
                cantidad=item['cantidad'],
                subtotal=subt
            )

        detalles_objs = list(map(crear_detalle, lista_items))
        db.add_all(detalles_objs)

        # 3. REDUCE: calcular total 
        suma_subtotales = reduce(lambda acc, det: acc + det.subtotal, detalles_objs, 0.0)
        
        pedido.total = suma_subtotales * 1.19 # IVA
        db.commit()
        db.refresh(pedido)
        return pedido
        
    except Exception as e:
        db.rollback()
        raise e