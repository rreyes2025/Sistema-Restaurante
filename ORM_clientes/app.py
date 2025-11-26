import customtkinter as ctk
from tkinter import ttk, filedialog
from CTkMessagebox import CTkMessagebox
from fpdf import FPDF
import webbrowser
import os
import re
from datetime import datetime

# imports del sistema
from database import SessionLocal
import crud.ingrediente_crud as ing_crud
import crud.cliente_crud as cli_crud
import crud.menu_crud as men_crud
import crud.pedido_crud as ped_crud
import graficos

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# LOGICA PDF 
class PDFBoleta(FPDF):
    def __init__(self, fecha_manual=None):
        super().__init__()
        self.fecha_manual = fecha_manual

    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Boleta del Pedido", ln=True, align="C")
        self.set_font("Arial", "", 10)
        
        if self.fecha_manual:
            texto_fecha = f"Fecha de Emision: {self.fecha_manual}"
        else:
            texto_fecha = f"Emitida el: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
        self.cell(0, 10, texto_fecha, ln=True, align="C")
        self.ln(5)
        self.set_draw_color(150, 150, 150)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

    def agregar_datos_cliente(self, nombre_cliente):
        self.set_font("Arial", "", 12)
        self.cell(0, 10, f"Cliente: {nombre_cliente}", ln=True)
        self.ln(5)

    def agregar_tabla_pedido(self, pedido_orm):
        self.set_font("Arial", "B", 12)
        self.cell(90, 10, "Menu", border=1, align="C")
        self.cell(30, 10, "Cantidad", border=1, align="C")
        self.cell(30, 10, "Precio Unit.", border=1, align="C")
        self.cell(30, 10, "Subtotal", border=1, align="C")
        self.ln()

        self.set_font("Arial", "", 10)
        for det in pedido_orm.detalles:
            self.cell(90, 10, det.menu.nombre, border=1)
            self.cell(30, 10, str(det.cantidad), border=1, align="C")
            self.cell(30, 10, f"${det.menu.precio:,.0f}", border=1, align="R")
            self.cell(30, 10, f"${det.subtotal:,.0f}", border=1, align="R")
            self.ln()

        total_con_iva = pedido_orm.total
        subtotal = total_con_iva / 1.19
        iva = total_con_iva - subtotal

        self.ln(5)
        self.set_font("Arial", "B", 11)
        self.cell(150, 8, "Subtotal", border=1, align="R")
        self.cell(30, 8, f"${subtotal:,.0f}", border=1, align="R")
        self.ln()
        self.cell(150, 8, "IVA (19%)", border=1, align="R")
        self.cell(30, 8, f"${iva:,.0f}", border=1, align="R")
        self.ln()
        self.cell(150, 10, "TOTAL", border=1, align="R")
        self.cell(30, 10, f"${total_con_iva:,.0f}", border=1, align="R")
        self.ln(10)

class PDFMenu(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Carta del Dia", ln=True, align="C")
        self.set_font("Arial", "", 10)
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 10, f"Generado el: {fecha}", ln=True, align="C")
        self.ln(5)
        self.set_draw_color(150, 150, 150)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

    def agregar_tabla_menus(self, menus_disponibles):
        self.set_font("Arial", "B", 12)
        col_nombre = 60
        col_ingredientes = 90
        col_precio = 30

        self.cell(col_nombre, 10, "Menu", border=1, align="C")
        self.cell(col_ingredientes, 10, "Ingredientes", border=1, align="C")
        self.cell(col_precio, 10, "Precio", border=1, align="C")
        self.ln()

        self.set_font("Arial", "", 10)
        for menu in menus_disponibles:
            nombres = [assoc.ingrediente.nombre for assoc in menu.ingredientes_asociados]
            ingredientes_texto = ", ".join(nombres)

            altura_linea = 8
            x = self.get_x()
            y = self.get_y()

            self.multi_cell(col_nombre, altura_linea, menu.nombre, border=1)
            y2 = self.get_y()
            h = y2 - y

            self.set_xy(x + col_nombre, y)
            self.multi_cell(col_ingredientes, altura_linea, ingredientes_texto, border=1)
            y3 = self.get_y()
            h = max(h, y3 - y)

            self.set_xy(x + col_nombre + col_ingredientes, y)
            self.cell(col_precio, h, f"${menu.precio:,.0f}", border=1, align="R")

            self.set_y(max(y2, y3, y + h))

# APP PRINCIPAL
class RestauranteApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Restaurante")
        self.geometry("1150x750")
        self.db = SessionLocal()
        
        # estado
        self.carrito = [] 
        self.menu_generado = False 
        self.menus_disponibles_cache = []

        # pestañas
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_carga = self.tabs.add("Carga/Stock")
        self.tab_clientes = self.tabs.add("Gestion Clientes")
        self.tab_carta = self.tabs.add("Carta")
        self.tab_pedido = self.tabs.add("Pedido")
        self.tab_graficos = self.tabs.add("Estadisticas")
        
        self.setup_ui_carga()
        self.setup_ui_clientes()
        self.setup_ui_carta()
        self.setup_ui_pedido()
        self.setup_ui_graficos()

    def on_closing(self):
        self.db.close()
        self.destroy()

    # 1. PESTAÑA CARGA Y STOCK
    def setup_ui_carga(self):
        # frame carga CSV
        frm_csv = ctk.CTkFrame(self.tab_carga)
        frm_csv.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(frm_csv, text="Carga Masiva:").pack(side="left", padx=10)
        ctk.CTkButton(frm_csv, text="Seleccionar CSV", command=self.cargar_csv_action).pack(side="left", padx=10)
        
        # frame carga manual
        frm_man = ctk.CTkFrame(self.tab_carga)
        frm_man.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(frm_man, text="Ingreso Manual:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        
        self.ent_ing_nom = ctk.CTkEntry(frm_man, placeholder_text="Nombre Ingrediente")
        self.ent_ing_nom.pack(side="left", padx=5)
        
        ctk.CTkLabel(frm_man, text="Unidad:").pack(side="left", padx=(10, 2))
        self.combo_unidad = ctk.CTkComboBox(frm_man, values=["unidad", "kilo"], width=80, state="readonly")
        self.combo_unidad.pack(side="left", padx=2)
        self.combo_unidad.set("unidad")
        
        self.ent_ing_cant = ctk.CTkEntry(frm_man, placeholder_text="Cantidad", width=80)
        self.ent_ing_cant.pack(side="left", padx=5)
        
        ctk.CTkButton(frm_man, text="Agregar", command=self.agregar_manual_action, fg_color="green", width=80).pack(side="left", padx=10)
        ctk.CTkButton(frm_man, text="Eliminar", command=self.eliminar_ingrediente_action, fg_color="red", width=80).pack(side="right", padx=10)

        # tabla stock
        self.tree_ing = ttk.Treeview(self.tab_carga, columns=("ID", "Nom", "Uni", "Cant"), show="headings", height=15)
        self.tree_ing.heading("ID", text="ID")
        self.tree_ing.heading("Nom", text="Nombre")
        self.tree_ing.heading("Uni", text="Unidad")
        self.tree_ing.heading("Cant", text="Cantidad")
        self.tree_ing.column("ID", width=50)
        self.tree_ing.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.actualizar_tabla_stock()

    def cargar_csv_action(self):
        path = filedialog.askopenfilename()
        if path:
            try:
                n = ing_crud.cargar_csv(self.db, path)
                CTkMessagebox(message=f"Cargados {n} registros desde CSV")
                self.actualizar_tabla_stock()
                self.invalidar_menu()
            except Exception as e:
                CTkMessagebox(title="Error", message=str(e), icon="cancel")

    def agregar_manual_action(self):
        nom = self.ent_ing_nom.get()
        uni = self.combo_unidad.get()
        cant_str = self.ent_ing_cant.get()
        
        if not nom or not cant_str:
            CTkMessagebox(title="Error", message="Complete nombre y cantidad.", icon="warning")
            return
            
        if not re.match(r"^[a-zA-ZñÑáéíóúÁÉÍÓÚ\s]+$", nom):
            CTkMessagebox(title="Error", message="El nombre solo puede contener letras y espacios.", icon="warning")
            return
        
        try:
            cant = float(cant_str)
            ing_crud.crear_ingrediente(self.db, nom, uni, cant)
            self.actualizar_tabla_stock()
            self.invalidar_menu()
            self.ent_ing_nom.delete(0, 'end')
            self.ent_ing_cant.delete(0, 'end')
            CTkMessagebox(message=f"Ingrediente '{nom}' agregado/actualizado.")
        except Exception as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel")

    def eliminar_ingrediente_action(self):
        sel = self.tree_ing.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Seleccione un ingrediente para eliminar.", icon="warning")
            return
        
        item = self.tree_ing.item(sel[0])
        id_ing = item['values'][0]
        nombre_ing = item['values'][1]
        
        try:
            ing_crud.eliminar_ingrediente(self.db, id_ing)
            CTkMessagebox(message=f"Ingrediente '{nombre_ing}' eliminado.", icon="check")
            self.actualizar_tabla_stock()
            self.invalidar_menu()
        except ValueError as ve:
            CTkMessagebox(title="No se puede eliminar", message=str(ve), icon="cancel")
        except Exception as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel")

    def actualizar_tabla_stock(self):
        self.tree_ing.delete(*self.tree_ing.get_children())
        for i in ing_crud.leer_ingredientes(self.db):
            self.tree_ing.insert("", "end", values=(i.id, i.nombre, i.unidad, i.cantidad))

    def invalidar_menu(self):
        self.menu_generado = False
        self.menus_disponibles_cache = []
        self.render_botones_menu()

    # 2. PESTAÑA CLIENTES
    def setup_ui_clientes(self):
        frm = ctk.CTkFrame(self.tab_clientes)
        frm.pack(fill="x", padx=10, pady=10)
        
        self.ent_cli_nom = ctk.CTkEntry(frm, placeholder_text="Nombre Cliente")
        self.ent_cli_nom.pack(side="left", padx=5)
        self.ent_cli_mail = ctk.CTkEntry(frm, placeholder_text="Correo")
        self.ent_cli_mail.pack(side="left", padx=5)
        ctk.CTkButton(frm, text="Crear Cliente", command=self.crear_cliente_action).pack(side="left", padx=5)
        
        ctk.CTkButton(frm, text="Eliminar Seleccionado", command=self.eliminar_cliente_action, fg_color="red").pack(side="right", padx=5)
        
        self.combo_cli_ped = ctk.CTkComboBox(self.tab_pedido, values=[]) 
        
        self.tree_cli = ttk.Treeview(self.tab_clientes, columns=("ID", "Nombre", "Correo"), show="headings")
        self.tree_cli.heading("ID", text="ID")
        self.tree_cli.heading("Nombre", text="Nombre")
        self.tree_cli.heading("Correo", text="Correo")
        self.tree_cli.pack(fill="both", expand=True, padx=10)
        
        self.actualizar_tabla_clientes()

    def crear_cliente_action(self):
        nom = self.ent_cli_nom.get()
        correo = self.ent_cli_mail.get()
        
        if not re.match(r"^[a-zA-ZñÑáéíóúÁÉÍÓÚ\s]+$", nom):
            CTkMessagebox(title="Error", message="El nombre del cliente solo puede contener letras y espacios.", icon="warning")
            return

        try:
            cli_crud.crear_cliente(self.db, nom, correo)
            self.actualizar_tabla_clientes()
            self.ent_cli_nom.delete(0, 'end')
            self.ent_cli_mail.delete(0, 'end')
            CTkMessagebox(message="Cliente creado correctamente.")
        except Exception as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel")

    def eliminar_cliente_action(self):
        sel = self.tree_cli.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Seleccione un cliente para eliminar.", icon="warning")
            return
        
        item = self.tree_cli.item(sel[0])
        id_cli = item['values'][0]
        
        try:
            if cli_crud.eliminar_cliente(self.db, id_cli):
                self.actualizar_tabla_clientes()
                CTkMessagebox(message="Cliente eliminado correctamente.", icon="check")
        except ValueError as ve:
            CTkMessagebox(title="No se puede eliminar", message=str(ve), icon="cancel")
        except Exception as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel")

    def actualizar_tabla_clientes(self):
        self.tree_cli.delete(*self.tree_cli.get_children())
        clis = cli_crud.leer_clientes(self.db)
        for c in clis:
            self.tree_cli.insert("", "end", values=(c.id, c.nombre, c.correo))
        self.combo_cli_ped.configure(values=[f"{c.id}-{c.nombre}" for c in clis])

    # 3. PESTAÑA CARTA
    def setup_ui_carta(self):
        frm = ctk.CTkFrame(self.tab_carta)
        frm.pack(expand=True)
        ctk.CTkLabel(frm, text="Gestion de Carta Diaria", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkLabel(frm, text="Genera PDF con menus disponibles segun stock").pack(pady=10)
        ctk.CTkButton(frm, text="Generar Carta PDF", command=self.generar_carta_action, height=50, width=200).pack(pady=20)

    def generar_carta_action(self):
        todos = men_crud.leer_menus(self.db)
        # FILTER 
        disponibles = list(filter(lambda m: men_crud.verificar_stock_menu(m), todos))
        self.menus_disponibles_cache = disponibles
        self.menu_generado = True
        
        try:
            pdf = PDFMenu()
            pdf.alias_nb_pages()
            pdf.add_page()
            
            if not disponibles:
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, "No hay menus disponibles por falta de ingredientes.", ln=True, align="C")
            else:
                pdf.agregar_tabla_menus(disponibles)
            
            filename = "menu_disponible.pdf"
            pdf.output(filename)
            webbrowser.open(f"file://{os.path.abspath(filename)}")
            
            self.render_botones_menu()
            CTkMessagebox(message="Carta generada y pedidos habilitados.")
            
        except Exception as e:
            CTkMessagebox(title="Error PDF", message=str(e), icon="cancel")

    # 4. PESTAÑA PEDIDO 
    def setup_ui_pedido(self):
        frm_top = ctk.CTkFrame(self.tab_pedido)
        frm_top.pack(fill="x", padx=10, pady=5)
        
        # clientes
        ctk.CTkLabel(frm_top, text="Clientes:", font=("Arial", 14, "bold")).pack(side="left", padx=(10, 5))
        self.combo_cli_ped.pack(side="left", padx=5)

        # fecha manual
        ctk.CTkLabel(frm_top, text="Fecha (dd/mm/aaaa):").pack(side="left", padx=(20, 5))
        self.ent_fecha_ped = ctk.CTkEntry(frm_top, width=100)
        self.ent_fecha_ped.pack(side="left", padx=5)
        
        hoy = datetime.now().strftime("%d/%m/%Y")
        self.ent_fecha_ped.insert(0, hoy)

        # contenedor principal
        frm_main = ctk.CTkFrame(self.tab_pedido)
        frm_main.pack(fill="both", expand=True, padx=10, pady=5)

        self.scroll_menus = ctk.CTkScrollableFrame(frm_main, label_text="Menús de la Carta", width=350)
        self.scroll_menus.pack(side="left", fill="both", padx=5, pady=5)

        frm_der = ctk.CTkFrame(frm_main)
        frm_der.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(frm_der, text="Detalle del Pedido Actual").pack(pady=5)
        
        self.tree_carr = ttk.Treeview(frm_der, columns=("Menu", "Cant", "Precio"), show="headings")
        self.tree_carr.heading("Menu", text="Menú")
        self.tree_carr.heading("Cant", text="Cant")
        self.tree_carr.heading("Precio", text="Precio U.")
        self.tree_carr.pack(fill="both", expand=True, pady=5)
        
        frm_btns = ctk.CTkFrame(frm_der)
        frm_btns.pack(fill="x", pady=5)
        ctk.CTkButton(frm_btns, text="Quitar Seleccionado", command=self.quitar_item_carrito, fg_color="red").pack(side="left", padx=5)
        ctk.CTkButton(frm_btns, text="Limpiar Todo", command=self.limpiar_carrito, fg_color="orange").pack(side="left", padx=5)
        
        ctk.CTkButton(self.tab_pedido, text="CONFIRMAR PEDIDO Y GENERAR BOLETA", 
                      command=self.finalizar_pedido_action, fg_color="green", height=40).pack(fill="x", padx=20, pady=10)

        self.render_botones_menu()

    def render_botones_menu(self):
        for w in self.scroll_menus.winfo_children(): w.destroy()
        
        if not self.menu_generado:
            ctk.CTkLabel(self.scroll_menus, text="Genere la Carta PDF primero").pack(pady=20)
            return
        if not self.menus_disponibles_cache:
            ctk.CTkLabel(self.scroll_menus, text="Sin stock disponible").pack(pady=20)
            return
            
        for m in self.menus_disponibles_cache:
            btn = ctk.CTkButton(self.scroll_menus, text=f"{m.nombre}\n${m.precio:,.0f}", 
                                command=lambda x=m: self.agregar_al_carrito(x))
            btn.pack(fill="x", pady=2)

    def agregar_al_carrito(self, menu):
        self.carrito.append(menu)
        self.actualizar_tree_carrito()

    def quitar_item_carrito(self):
        sel = self.tree_carr.selection()
        if not sel: return
        
        item_vals = self.tree_carr.item(sel[0])['values']
        nombre_borrar = item_vals[0]
        
        for i, m in enumerate(self.carrito):
            if m.nombre == nombre_borrar:
                del self.carrito[i]
                break
        self.actualizar_tree_carrito()

    def limpiar_carrito(self):
        self.carrito = []
        self.actualizar_tree_carrito()

    def actualizar_tree_carrito(self):
        self.tree_carr.delete(*self.tree_carr.get_children())
        conteo = {}
        precios = {}
        for m in self.carrito:
            conteo[m.nombre] = conteo.get(m.nombre, 0) + 1
            precios[m.nombre] = m.precio
            
        for nombre, cant in conteo.items():
            self.tree_carr.insert("", "end", values=(nombre, cant, f"${precios[nombre]:,.0f}"))

    def finalizar_pedido_action(self):
        if not self.carrito:
            CTkMessagebox(title="Error", message="El pedido está vacio", icon="warning")
            return
        
        val_cli = self.combo_cli_ped.get()
        if not val_cli:
            CTkMessagebox(title="Error", message="Seleccione un cliente", icon="warning")
            return
        
        fecha_txt = self.ent_fecha_ped.get()
        if not fecha_txt:
            CTkMessagebox(title="Error", message="La fecha no puede estar vacia", icon="warning")
            return

        cli_id = int(val_cli.split("-")[0])
        
        items_procesar = []
        seen_ids = set()
        for m in self.carrito:
            if m.id not in seen_ids:
                cant = self.carrito.count(m)
                items_procesar.append({'menu_id': m.id, 'cantidad': cant})
                seen_ids.add(m.id)
                
        try:
            pedido = ped_crud.crear_pedido(self.db, cli_id, items_procesar, fecha_str=fecha_txt)
            
            # pasar fecha manual al PDF 
            fecha_pdf = pedido.fecha.strftime("%d/%m/%Y")
            pdf = PDFBoleta(fecha_manual=fecha_pdf)
            pdf.alias_nb_pages()
            pdf.add_page()
            
            pdf.agregar_datos_cliente(pedido.cliente.nombre)
            pdf.agregar_tabla_pedido(pedido)
            pdf.cell(0, 10, "Gracias por su compra!", ln=True, align="C")
            
            filename = f"boleta_{pedido.id}.pdf"
            pdf.output(filename)
            webbrowser.open(f"file://{os.path.abspath(filename)}")
            
            CTkMessagebox(message="Pedido procesado y boleta generada.")
            self.carrito = []
            self.actualizar_tree_carrito()
            self.actualizar_tabla_stock()
            self.invalidar_menu()
            
        except ValueError as ve:
             CTkMessagebox(title="Error de Formato", message=str(ve), icon="warning")
        except Exception as e:
            CTkMessagebox(title="Error en Pedido", message=str(e), icon="cancel")

    # 5. PESTAÑA GRÁFICOS
    def setup_ui_graficos(self):
        frm = ctk.CTkFrame(self.tab_graficos)
        frm.pack(expand=True)
        ctk.CTkButton(frm, text="Ver Ventas Diarias", command=lambda: graficos.ventas_diarias(self.db), width=250).pack(pady=20)
        ctk.CTkButton(frm, text="Ver Menus Mas Vendidos", command=lambda: graficos.menus_mas_vendidos(self.db), width=250).pack(pady=20)