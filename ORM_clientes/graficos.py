import matplotlib.pyplot as plt
from sqlalchemy.orm import Session
from models import Pedido, DetallePedido
import pandas as pd

def ventas_diarias(db: Session):
    pedidos = db.query(Pedido).all()
    if not pedidos: return
    
    data = [{"Fecha": p.fecha.date(), "Total": p.total} for p in pedidos]
    df = pd.DataFrame(data)
    
    if df.empty: return
    df_g = df.groupby("Fecha")["Total"].sum()
    
    plt.figure(figsize=(8,5))
    df_g.plot(kind='bar', color='skyblue')
    plt.title("Ventas por Dia")
    plt.ylabel("CLP")
    plt.tight_layout()
    plt.show()

def menus_mas_vendidos(db: Session):
    detalles = db.query(DetallePedido).all()
    if not detalles: return

    data = [{"Menu": d.menu.nombre, "Cantidad": d.cantidad} for d in detalles]
    df = pd.DataFrame(data)
    
    if df.empty: return
    df_g = df.groupby("Menu")["Cantidad"].sum()
    
    plt.figure(figsize=(6,6))
    df_g.plot(kind='pie', autopct='%1.1f%%')
    plt.title("Distribucion de Menus")
    plt.ylabel("")
    plt.show()