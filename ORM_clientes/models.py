from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# tabla intermedia entre menu e ingrediente con cantidad
class IngredienteMenu(Base):
    __tablename__ = 'ingrediente_menu'
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey('menus.id'))
    ingrediente_id = Column(Integer, ForeignKey('ingredientes.id'))
    cantidad_requerida = Column(Float, nullable=False)

    menu = relationship("Menu", back_populates="ingredientes_asociados")
    ingrediente = relationship("Ingrediente")

class Ingrediente(Base):
    __tablename__ = 'ingredientes'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False) # no duplicados 
    unidad = Column(String, nullable=False)
    cantidad = Column(Float, default=0.0) # stock

class Menu(Base):
    __tablename__ = 'menus'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    precio = Column(Float, nullable=False)
    # Relación inversa
    ingredientes_asociados = relationship("IngredienteMenu", back_populates="menu", cascade="all, delete-orphan")

class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False) # correo unico 
    pedidos = relationship("Pedido", back_populates="cliente")

class Pedido(Base):
    __tablename__ = 'pedidos'
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    fecha = Column(DateTime, default=datetime.now)
    total = Column(Float, default=0.0)

    cliente = relationship("Cliente", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")

class DetallePedido(Base):
    __tablename__ = 'detalle_pedidos'
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey('pedidos.id'))
    menu_id = Column(Integer, ForeignKey('menus.id'))
    cantidad = Column(Integer, default=1)
    subtotal = Column(Float, nullable=False)

    pedido = relationship("Pedido", back_populates="detalles")
    menu = relationship("Menu")