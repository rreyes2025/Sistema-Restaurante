from database import engine, Base, SessionLocal
from models import Menu
from app import RestauranteApp
import crud.menu_crud as men_crud

# lista de menus 
MENUS_POR_DEFECTO = [
    {
        "nombre": "Completo",
        "precio": 3500.0,
        "reqs": {"Pan de completo": 1, "Vienesa": 1, "Palta": 0.1, "Tomate": 0.1}
    },
    {
        "nombre": "Hamburguesa",
        "precio": 5500.0,
        "reqs": {"Pan de hamburguesa": 1, "Carne de vacuno": 0.15, "Lamina de queso": 1, "Lechuga": 1, "Tomate": 0.1, "Cebolla": 0.05}
    },
    {
        "nombre": "Churrasco",
        "precio": 5800.0,
        "reqs": {"Churrasco de carne": 1, "Palta": 0.1, "Tomate": 0.1, "Pan de completo": 1}
    },
    {
        "nombre": "Ensalada Mixta",
        "precio": 4200.0,
        "reqs": {"Lechuga": 1, "Tomate": 0.1, "Zanahoria rallada": 1, "Huevos": 1}
    },
    {
        "nombre": "Empanada de Pollo",
        "precio": 3000.0,
        "reqs": {"Masa de empanada": 1, "Presa de pollo": 0.5, "Porcion de aceite": 0.02}
    },
    {
        "nombre": "Papas Fritas",
        "precio": 2500.0,
        "reqs": {"Papas": 0.25, "Porcion de aceite": 0.05}
    },
    {
        "nombre": "Panqueques con Manjar",
        "precio": 3200.0,
        "reqs": {"Panqueques": 2, "Manjar": 1, "Azucar flor": 1}
    },
    {
        "nombre": "Bebida Coca Cola",
        "precio": 1500.0,
        "reqs": {"Coca cola": 1}
    },
    {
        "nombre": "Bebida Pepsi",
        "precio": 1500.0,
        "reqs": {"Pepsi": 1}
    }
]

def inicializar_datos():
    
    #verifica menu por menu. Si uno no existe, lo crea
    db = SessionLocal()
    print("Verificando integridad de menus...")
    
    for m_data in MENUS_POR_DEFECTO:
        # verificar si este menu especifico ya existe
        existe = db.query(Menu).filter(Menu.nombre == m_data['nombre']).first()
        
        if not existe:
            try:
                men_crud.crear_menu(db, m_data['nombre'], m_data['precio'], m_data['reqs'])
                print(f" [+] Menu agregado: {m_data['nombre']}")
            except Exception as e:
                print(f" [!] Error agregando {m_data['nombre']}: {e}")
        # si ya existe, no hacemos nada (para no duplicar)
        
    db.close()

if __name__ == "__main__":
    # 1. crear estructura de tablas
    Base.metadata.create_all(bind=engine)
    
    # 2. Cargar/Actualizar datos
    inicializar_datos()
    
    # 3. Iniciar App
    app = RestauranteApp()
    app.mainloop()