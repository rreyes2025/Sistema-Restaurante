from sqlalchemy.orm import Session
from models import Ingrediente, IngredienteMenu
import pandas as pd

def crear_ingrediente(db: Session, nombre: str, unidad: str, cantidad: float):
    
    #crea un ingrediente nuevo o actualiza el stock si ya existe 
    #validaciones 
    if not nombre or not nombre.strip():
        raise ValueError("El nombre del ingrediente no puede estar vacio")
    
    if cantidad < 0:
        raise ValueError("El stock no puede ser negativo")

    nombre_norm = nombre.strip() # normalizar nombre

    # verificar si existe para evitar duplicados y actualizar stock
    existente = db.query(Ingrediente).filter(Ingrediente.nombre == nombre_norm).first()
    
    if existente:
        # si existe, actualizamos el stock
        existente.cantidad += cantidad
        # actualizar unidad 
        if unidad:
            existente.unidad = unidad
        db.commit()
        db.refresh(existente)
        return existente

    # si no existe, crear nuevo
    nuevo = Ingrediente(nombre=nombre_norm, unidad=unidad, cantidad=cantidad)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def leer_ingredientes(db: Session):
    #retorna todos los ingredientes para visualizar
    return db.query(Ingrediente).all()

def eliminar_ingrediente(db: Session, ingrediente_id: int):
    
    #elimina un ingrediente, validando que no se use en ningun menu
    
    ing = db.query(Ingrediente).get(ingrediente_id)
    if not ing:
        raise ValueError("Ingrediente no encontrado")
    
    # no borrar si se usa en un menu 
    uso_menu = db.query(IngredienteMenu).filter(IngredienteMenu.ingrediente_id == ingrediente_id).first()
    if uso_menu:
        raise ValueError(f"No se puede eliminar '{ing.nombre}' porque es parte de una receta del Menu")

    db.delete(ing)
    db.commit()
    return True

def cargar_csv(db: Session, filepath: str):

    try:
        df = pd.read_csv(filepath)
        # normalizar columnas
        df.columns = [c.strip().lower() for c in df.columns]
        
        registros = df.to_dict('records')

        # 1. MAP: normalizar nombres y unidades
        registros_limpios = list(map(lambda r: {
            'nombre': str(r['nombre']).strip(),
            'unidad': str(r['unidad']).strip(),
            'cantidad': float(r['cantidad'])
        }, registros))

        # 2. FILTER: filtrar solo los que tienen cantidad positiva
        registros_validos = list(filter(lambda r: r['cantidad'] >= 0, registros_limpios))

        # procesar la insercion 
        contador = 0
        for row in registros_validos:
            try:
                # llamamos a la funcion interna sin importar el modulo completo para evitar conflictos
                # usamos la logica de crear/actualizar definida arriba
                nom = row['nombre']
                existe = db.query(Ingrediente).filter(Ingrediente.nombre == nom).first()
                if existe:
                    existe.cantidad += row['cantidad']
                else:
                    nuevo = Ingrediente(nombre=nom, unidad=row['unidad'], cantidad=row['cantidad'])
                    db.add(nuevo)
                contador += 1
            except Exception:
                continue
        
        db.commit()
        return contador
    except Exception as e:
        db.rollback()
        raise e