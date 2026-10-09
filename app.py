import json
import gspread
from google.oauth2.service_account import Credentials
from google import genai
from PIL import Image
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestión de Inventario y Facturas", layout="wide"
)

# Conexión a Google Sheets usando los Secrets configurados en Streamlit Cloud
@st.cache_resource
def conectar_sheets():
  scope = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive",
  ]
  creds_dict = dict(st.secrets["gcp_service_account"])
  creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
  client = gspread.authorize(creds)
  sheet = client.open_by_url(st.secrets["sheets"]["spreadsheet_url"]).sheet1
  return sheet


st.title("🛒 Control de Inventario y Precios - Abarrotes")

# API Key de Gemini
api_key = st.sidebar.text_input("Ingresa tu API Key de Gemini:", type="password")

if not api_key:
  st.info(
      "👈 Por favor ingresa tu API Key de Gemini en la barra lateral para"
      " continuar."
  )
  st.stop()

client = genai.Client(api_key=api_key)

# Sección de carga de facturas
st.subheader("📸 Cargar Nota o Factura de Proveedor")
uploaded_file = st.file_uploader(
    "Selecciona una foto o imagen de la factura", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
  image = Image.open(uploaded_file)
  st.image(image, caption="Factura cargada", use_column_width=True)

  col1, col2 = st.columns(2)
  with col1:
    margen = st.slider(
        "Margen de ganancia objetivo (%)",
        min_value=20,
        max_value=50,
        value=30,
        step=5,
    )
  with col2:
    proveedor_manual = st.text_input(
        "Proveedor (Opcional si no es claro en la foto):", value=""
    )

  if st.button("🔍 Procesar y Guardar en Google Sheets"):
    with st.spinner("Analizando factura con Gemini y guardando en Google Sheets..."):
      try:
        prompt = f"""
                Analiza esta factura o nota de compra de abarrotes/farmacia.
                Extrae la información y responde ÚNICAMENTE con un arreglo JSON válido (sin texto adicional ni formato markdown triple backticks), con la siguiente estructura por cada producto detectado:
                [
                  {{
                    "fecha": "YYYY-MM-DD",
                    "proveedor": "{proveedor_manual if proveedor_manual else 'Nombre del proveedor detectado'}",
                    "producto": "Nombre exacto del producto",
                    "categoria": "Abarrotes o Farmacia",
                    "costo_neto": 0.00,
                    "margen": {margen},
                    "precio_venta": 0.00,
                    "diferencia": "N/A"
                  }}
                ]
                Nota: 'costo_neto' debe ser el precio unitario neto tras aplicar impuestos (IVA/IEPS) o descuentos.
                'precio_venta' debe calcularse con el {margen}% de margen sobre el costo_neto, redondeado a los $0.50 más cercanos.
                """

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=[prompt, image]
        )

        # Limpiar respuesta para parsear JSON
        texto_respuesta = (
            response.text.strip().replace("```json", "").replace("```", "")
        )
        productos = json.loads(texto_respuesta)

        # Enlazar con la hoja de Google Sheets
        sheet = conectar_sheets()

        # Preparar filas para insertar
        filas_a_insertar = []
        for p in productos:
          filas_a_insertar.append([
              p.get("fecha", ""),
              p.get("proveedor", ""),
              p.get("producto", ""),
              p.get("categoria", ""),
              p.get("costo_neto", 0.0),
              f"{p.get('margen', margen)}%",
              p.get("precio_venta", 0.0),
              p.get("diferencia", "N/A"),
          ])

        # Agregar filas al final de la hoja
        sheet.append_rows(filas_a_insertar)

        st.success(
            "¡Factura procesada con éxito! Se guardaron"
            f" {len(filas_a_insertar)} productos en Google Sheets."
        )

        # Mostrar tabla previa en la pantalla
        df = pd.DataFrame(productos)
        st.dataframe(df)

      except Exception as e:
        st.error(f"Error al procesar la imagen o guardar datos: {e}")
