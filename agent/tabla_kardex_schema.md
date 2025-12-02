# Esquema de la tabla Kardex en Airtable

## IMPORTANTE: Diferencias con Certificados

**Certificados** = Certificados de devolución/recolección emitidos por Campolimpio (documento oficial)
**Kardex** = Movimientos internos de material, registro de flujo de residuos (control operativo)

Los Certificados documentan entregas formales, mientras que Kardex registra movimientos operativos y disposición de materiales.

---

## Campos propios (datos directos en esta tabla)

### Identificación y control
- `idkardex` - ID único del movimiento
- `Pre-ID` - Pre-identificador
- `TipoMovimiento` - Tipo de movimiento (entrada, salida, transferencia, etc.)
- `fechakardex` - Fecha del movimiento/registro
- `MES` - Mes del movimiento
- `ANO` - Año del movimiento
- `FechaCreacion` - Fecha de creación del registro

### Materiales (campos numéricos - DIFERENTES a Certificados)
- `Reciclaje` - Peso/cantidad de material para reciclaje (kg)
- `Incineración` - Peso/cantidad de material para incineración (kg)
- `PlasticoContaminado` - Peso/cantidad de plástico contaminado (kg)
- `Flexibles` - Peso/cantidad de materiales flexibles (kg)
- `Lonas` - Peso/cantidad de lonas (kg)
- `Carton` - Peso/cantidad de cartón (kg)
- `Metal` - Peso/cantidad de metal (kg)
- `Total` - Total del movimiento (kg)
- `TotalKilos` - Total en kilos (campo alternativo/calculado)

### Control y observaciones
- `Observaciones` - Notas sobre el movimiento

## Campos de lookup/linked records (dependen de otras tablas)

### Coordinador (de tabla Coordinadores)
- `Coordinador` - Linked record a tabla de coordinadores
- `idcoordinador` - ID del coordinador
- `Name (from Coordinador)` - Lookup: nombre del coordinador

### Ubicación
- `MunicipioOrigen` - Municipio de origen del material
- `mundep (from MunicipioOrigen)` - Lookup: código o referencia del municipio

### Centro de Acopio
- `CentrodeAcopio` - Linked record a tabla de centros de acopio
- `NombreCentrodeAcopio` - Lookup: nombre del centro de acopio

### Gestor
- `gestor` - Linked record a tabla de gestores
- `nombregestor` - Lookup: nombre del gestor de residuos

---

## Diferencias clave con Certificados

| Aspecto | Certificados | Kardex |
|---------|--------------|--------|
| **Propósito** | Documento oficial de recolección | Control operativo de movimientos |
| **Fecha principal** | `fechadevolucion` | `fechakardex` |
| **Materiales** | rigidos, flexibles, metalicos, embalaje | Reciclaje, Incineración, PlasticoContaminado, Flexibles, Lonas, Carton, Metal |
| **Enfoque** | Recolección desde generadores | Movimientos y disposición de materiales |
| **Ubicación** | municipiogenerador, municipiodevolucion | MunicipioOrigen, CentrodeAcopio |
| **Actores** | Coordinador, Generador | Coordinador, CentrodeAcopio, Gestor |

---

## Campos clave para reportes de Kardex

### Para consolidado de movimientos por coordinador:
- `Name (from Coordinador)` - Agrupar por coordinador
- `Reciclaje`, `Incineración`, `PlasticoContaminado`, etc. - Sumar por tipo
- `Total` o `TotalKilos` - Totales
- `fechakardex` - Filtrar por período
- `TipoMovimiento` - Diferenciar tipos de movimiento
- `MunicipioOrigen` - Análisis geográfico

### Para análisis de disposición final:
- `Reciclaje` vs `Incineración` - Porcentajes de cada tipo
- `NombreCentrodeAcopio` - Por centro de acopio
- `nombregestor` - Por gestor autorizado
- `PlasticoContaminado` - Material que requiere tratamiento especial

### Filtros comunes:
- Por fecha: `fechakardex`
- Por mes/año: `MES`, `ANO`
- Por coordinador: `Name (from Coordinador)`
- Por tipo de movimiento: `TipoMovimiento`
- Por centro de acopio: `NombreCentrodeAcopio`
- Por gestor: `nombregestor`

---

## Notas importantes:

1. **Kardex es posterior a Certificados**: Primero se genera el Certificado (recolección), luego Kardex registra qué pasa con ese material
2. **Diferentes categorías de material**: Kardex usa clasificación por destino (Reciclaje, Incineración) vs Certificados por tipo físico (rígidos, flexibles)
3. **TipoMovimiento** es crítico para entender el flujo (entrada a bodega, salida a gestor, transferencia entre centros, etc.)
4. **Trazabilidad completa**: Centro de Acopio + Gestor permite seguir el material desde recolección hasta disposición final
5. **Material contaminado**: `PlasticoContaminado` requiere manejo especial y no puede reciclarse

---

## Preguntas típicas sobre Kardex:

- ¿Cuánto material se envió a reciclaje vs incineración este mes?
- ¿Qué centro de acopio tiene más material acumulado?
- ¿Qué coordinador reporta más movimientos?
- ¿Cuánto plástico contaminado se generó en X período?
- ¿Qué gestores están recibiendo más material?
- ¿Cuál es el flujo de material por tipo de movimiento?
