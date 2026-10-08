prompt = """
Analiza la imagen de esta nota/factura (puede ser impresa o escrita a mano).
Extrae en JSON:
{
  "proveedor": "Nombre del proveedor (si no se ve, pon 'Proveedor Remisión')",
  "fecha": "YYYY-MM-DD (si no hay fecha, usa la fecha de hoy)",
  "productos": [
    {
      "descripcion": "Nombre claro del producto",
      "cantidad": 1.0,
      "unidad": "pieza / kg / bulto / caja",
      "costo_unitario": 0.0
    }
  ]
}
Si es bulto o caja, divide el importe total entre los kilos o piezas para obtener el costo unitario por kg/pieza.
"""
