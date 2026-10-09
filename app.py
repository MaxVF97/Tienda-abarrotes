import streamlit as st
import pandas as pd
from PIL import Image
import os
from google import genai

st.set_page_config(page_title="Gestión de Inventario y Facturas", layout="wide")

st.title("🛒 Control de Inventario y Precios - Abarrotes")

# Barra lateral para credenciales
st.sidebar.header("Configuración")
api_key = st.sidebar.text_input("Ingresa tu API Key de Gemini:", type="password")

if not api_key:
    st.info("👈 Por favor ingresa tu API Key de Gemini en la barra lateral para continuar.")
    st.stop()

# Cliente de Gemini
client = genai.Client(api_key=api_key)

# Cargar imagen de factura
st.subheader("📸 Cargar Nota o Factura de Proveedor")
uploaded_file = st.file_uploader("Selecciona una foto o imagen de la factura", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Factura cargada", use_column_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        margen = st.slider("Margen de ganancia objetivo (%)", min_value=20, max_value=50, value=30, step=5)
    with col2:
        redondeo = st.radio("Criterio de redondeo:", ["A los $0.50 más cercanos", "Entero superior ($1.00)"])
    
    if st.button("🔍 Procesar Factura con Gemini Vision"):
        with st.spinner("Analizando productos, IVA, IEPS y precios..."):
            try:
                prompt = f"""
                Analiza esta factura o nota de venta de abarrotes/farmacia.
                Extrae los productos listados en formato JSON estructurado con los siguientes campos por ítem:
                - producto: Nombre del producto
                - cantidad: Cantidad comprada
                - precio_unitario: Precio unitario sin impuestos
                - importe_total: Importe total de esa línea
                Calcula el precio neto unitario considerando IVA e IEPS si aplican.
                Aplica un margen de ganancia del {margen}%.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[prompt, image]
                )
                
                st.success("¡Factura procesada con éxito!")
                st.markdown("### Resultado del Análisis")
                st.write(response.text)
            except Exception as e:
                st.error(f"Error al procesar la imagen: {e}")
