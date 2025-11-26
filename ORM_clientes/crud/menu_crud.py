from sqlalchemy.orm import Session
from models import Menu, Ingrediente, IngredienteMenu
from functools import reduce

def crear_menu(db: Session, nombre: str, precio: float, requerimientos: dict):
    # validacion: si el menu ya existe, no hacemos nada 
    if db.query(Menu).filter(Menu.nombre == nombre).first():
        return None 

    nuevo_menu = Menu(nombre=nombre, precio=precio)
    db.add(nuevo_menu)
    db.flush() # generamos el ID del menu

    for nom_ing, cant in requerimientos.items():
        # LIMPIEZA: quitamos espacios extra para asegurar coincidencia
        nombre_limpio = nom_ing.strip()
        
        # buscar ingrediente existente
        ing_db = db.query(Ingrediente).filter(Ingrediente.nombre == nombre_limpio).first()
        
        if not ing_db:
            # si no existe, se crea automaticamente con stock 0 
            # asi el menu existe, pero no estara disponible hasta que se cargue stock
            ing_db = Ingrediente(nombre=nombre_limpio, unidad="unid", cantidad=0)
            db.add(ing_db)
            db.flush() # Generar ID del ingrediente
        
        # crear la relación
        assoc = IngredienteMenu(menu_id=nuevo_menu.id, ingrediente_id=ing_db.id, cantidad_requerida=cant)
        db.add(assoc)

    db.commit()
    return nuevo_menu

def leer_menus(db: Session):
    return db.query(Menu).all()

def verificar_stock_menu(menu: Menu, cantidad: int = 1) -> bool:
    #valida si hay stock suficiente para preparar el menu
    
    if not menu.ingredientes_asociados:
        # si un menu no tiene ingredientes, se asume que no se puede preparar 
        return False
    
    # 1. MAP: genera una lista de booleanos 
    disponibilidad = list(map(
        lambda assoc: assoc.ingrediente.cantidad >= (assoc.cantidad_requerida * cantidad),
        menu.ingredientes_asociados
    ))
    
    # 2. REDUCE: verificar si todos son true 
    # el valor inicial true previene errores si la lista estuviera vacia
    resultado = reduce(lambda a, b: a and b, disponibilidad, True)
    
    return resultado