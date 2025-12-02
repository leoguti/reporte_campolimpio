# Esquema de la tabla Certificados en Airtable

## Campos propios (datos directos en esta tabla)

### Identificación y control
- `CreatedTime` - Fecha/hora de creación del registro
- `pre_consecutivo` - Número consecutivo del certificado
- `certificadopdf` - Archivo PDF del certificado
- `REGISTER_ID` - ID de registro
- `ano` - Año
- `Creada` - Fecha de creación
- `Creada 2` - Fecha de creación alternativa
- `reenviado` - Checkbox, indica si fue reenviado

### Fechas y ubicación
- `fechadevolucion` - Fecha en que se hizo la devolución
- `link_ubicación` - Enlace a ubicación
- `lugardevolucion` - Lugar de devolución
- `telefonousuario` - Teléfono del usuario

### Materiales (campos numéricos clave para reportes)
- `rigidos` - Peso/cantidad de materiales rígidos (kg)
- `flexibles` - Peso/cantidad de materiales flexibles (kg)
- `metalicos` - Peso/cantidad de materiales metálicos (kg)
- `embalaje` - Peso/cantidad de embalaje (kg)
- `total` - Total consolidado de todos los materiales (kg)

### Control de calidad
- `observaciones` - Observaciones o notas sobre el certificado
- `triplelavado` - Control de triple lavado

## Campos de lookup/linked records (dependen de otras tablas)

### Coordinador (de tabla Coordinadores)
- `coordinador` - Linked record a tabla de coordinadores
- `nombrecoordinador` - Lookup: nombre del coordinador
- `movilcoordinador` - Lookup: teléfono móvil del coordinador
- `emailcoordinador` - Lookup: email del coordinador

### Generador (de tabla Generadores)
- `nombregeherador` - Lookup: nombre del generador (agricultor/productor)
- `direcciongenerador` - Lookup: dirección del generador
- `cultivogenerador` - Lookup: tipo de cultivo del generador
- `municipiogenerador` - Lookup: municipio donde genera los residuos
- `cedulagenerador` - Lookup: cédula del generador
- `movilgenerador` - Lookup: teléfono del generador
- `emailgenerador` - Lookup: email del generador
- `tipogenerador` - Lookup: tipo de generador

### Ubicación
- `idmunicipodevolucion` - Linked record a tabla de municipios
- `municipiodevolucion` - Lookup: nombre del municipio de devolución
- `Departamento` - Lookup: departamento

## Campos clave para reportes

### Para consolidado por coordinador:
- `nombrecoordinador` - Agrupar por este campo
- `rigidos`, `flexibles`, `metalicos`, `embalaje`, `total` - Sumar estos valores
- `fechadevolucion` - Filtrar por período
- `municipiogenerador`, `municipiodevolucion` - Para análisis geográfico
- `pre_consecutivo` - Contar certificados
- `certificadopdf` - Enlace al certificado más reciente

### Para consolidado por tipo de material:
- `rigidos`, `flexibles`, `metalicos`, `embalaje` - Campos principales
- `nombrecoordinador` - Para desglose secundario
- `fechadevolucion` - Filtrar por período
- `municipiogenerador` - Para análisis territorial

### Filtros comunes:
- Por fecha: `fechadevolucion`
- Por coordinador: `nombrecoordinador`
- Por municipio generador: `municipiogenerador`
- Por municipio devolución: `municipiodevolucion`
- Por año: `ano`

## Notas importantes:
1. Los campos de lookup (≣) requieren que las tablas relacionadas estén correctamente vinculadas
2. El campo `total` debe ser la suma de rigidos + flexibles + metalicos + embalaje
3. Los campos numéricos están en kilogramos (kg)
4. `nombrecoordinador` puede venir como array/lista en algunos casos
