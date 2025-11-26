from sqlalchemy.orm import Session
from models import Cliente

def crear_cliente(db: Session, nombre: str, correo: str):
    if not nombre or "@" not in correo:
        raise ValueError("Datos invalidos")

    # MAP: formatear nombre
    nombre_fmt = " ".join(list(map(lambda x: x.capitalize(), nombre.split())))

    # FILTER: verificar si existe
    clientes = db.query(Cliente).all()
    duplicados = list(filter(lambda c: c.correo == correo, clientes))
    
    if duplicados:
        raise ValueError("El correo ya existe")

    cli = Cliente(nombre=nombre_fmt, correo=correo)
    db.add(cli)
    db.commit()
    return cli

def leer_clientes(db: Session):
    return db.query(Cliente).all()

def eliminar_cliente(db: Session, id_cliente: int):
    cli = db.query(Cliente).get(id_cliente)
    if cli:
        if cli.pedidos:
            raise ValueError("No se puede eliminar cliente con historial")
        db.delete(cli)
        db.commit()
        return True
    return False