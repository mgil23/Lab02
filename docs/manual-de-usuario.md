# Manual de Usuario — OpenIDP SaaS

**Versión 1.0 · Español**

Este manual está pensado para cualquier persona que use OpenIDP en su trabajo diario: revisores de documentos, personal de cuentas por pagar, analistas o gerentes. No necesitas conocimientos técnicos para seguirlo.

---

## Contenido

1. [¿Qué es OpenIDP?](#1-qué-es-openidp)
2. [Primeros pasos](#2-primeros-pasos)
3. [Panel de control](#3-panel-de-control)
4. [Cargar documentos](#4-cargar-documentos)
5. [Bandeja de documentos](#5-bandeja-de-documentos)
6. [Espacio de revisión](#6-espacio-de-revisión)
7. [Guía de colores e iconos](#7-guía-de-colores-e-iconos)
8. [Tipos de documento (administradores)](#8-tipos-de-documento-administradores)
9. [Área de pruebas](#9-área-de-pruebas)
10. [Claves de acceso para integraciones](#10-claves-de-acceso-para-integraciones)
11. [Facturación y plan](#11-facturación-y-plan)
12. [Referencia de estados](#12-referencia-de-estados)
13. [Preguntas frecuentes](#13-preguntas-frecuentes)

---

## 1 ¿Qué es OpenIDP?

OpenIDP es una plataforma de **procesamiento inteligente de documentos**. Su propósito es simple: subes un PDF — una factura, una orden de compra, un contrato, un expediente médico — y la plataforma lee el documento, identifica automáticamente la información relevante y te la presenta organizada en una tabla lista para revisar o exportar.

En lugar de leer manualmente cada página y copiar datos a una hoja de cálculo, con OpenIDP:

- Subes el PDF.
- La plataforma extrae los datos clave en segundos.
- Revisas los resultados, corriges lo que sea necesario y continúas.

**¿Qué tipo de información extrae?**
Depende de los esquemas que tu equipo configure. Ejemplos habituales:

| Documento | Campos típicos extraídos |
|-----------|--------------------------|
| Factura | Número de factura, proveedor, fecha, importe total, IVA |
| Orden de compra | Número de OC, productos, cantidades, precios, fecha |
| Contrato | Partes, fecha de inicio, fecha de vencimiento, cláusulas clave |
| Expediente médico | Nombre del paciente, fecha, diagnóstico, medicamentos |

**¿Qué pasa si el PDF contiene varios documentos juntos?**
OpenIDP los detecta automáticamente y los separa. Si subes un PDF de 15 páginas que en realidad contiene tres facturas consecutivas, la plataforma las identifica y trata cada una por separado.

---

## 2 Primeros pasos

### 2.1 Crear una cuenta

Si tu empresa aún no tiene cuenta en OpenIDP, sigue estos pasos:

1. Abre tu navegador y ve a la dirección que te haya dado tu administrador (por ejemplo, `https://app.tuempresa.com`).
2. Haz clic en **Crear cuenta** o ve directamente a `/register`.
3. Rellena el formulario:
   - **Nombre de la organización** — el nombre de tu empresa o equipo (mínimo 2 caracteres).
   - **Correo electrónico** — el tuyo personal de trabajo.
   - **Contraseña** — mínimo 8 caracteres.
4. Haz clic en **Crear cuenta**.
5. Serás redirigido automáticamente al **Panel de control**.

> **Nota:** El nombre de organización se convierte en el identificador de tu espacio de trabajo. Aparecerá en la barra de direcciones de todas las páginas.

### 2.2 Iniciar sesión

Si ya tienes cuenta:

1. Ve a la dirección de la aplicación.
2. Escribe tu **correo electrónico** y **contraseña**.
3. Haz clic en **Iniciar sesión**.

Si olvidaste tu contraseña, contacta con el administrador de tu organización.

### 2.3 La barra lateral de navegación

Tras iniciar sesión verás una barra lateral a la izquierda con todos los accesos:

| Icono | Sección | Para qué sirve |
|-------|---------|----------------|
| 🏠 | **Panel de control** | Resumen de actividad y estadísticas |
| 📄 | **Documentos** | Ver todos los documentos subidos |
| ⬆️ | **Subir** | Cargar nuevos PDFs |
| ⚙️ | **Tipos de documento** | Configurar esquemas de extracción (administradores) |
| 🧪 | **Área de pruebas** | Probar esquemas con texto libre |
| 🔧 | **Configuración** | Claves de acceso para integraciones |
| 💳 | **Facturación** | Plan, uso mensual y suscripción |

La barra lateral se puede **contraer** haciendo clic en el botón de flecha para ganar más espacio en pantalla. En modo contraído sólo se ven los iconos; al pasar el ratón por encima aparece el nombre de cada sección.

El botón **Cerrar sesión** está en la parte inferior de la barra.

---

## 3 Panel de control

El **Panel de control** es la primera pantalla que ves al iniciar sesión. Te da una visión general instantánea de lo que está ocurriendo con tus documentos.

### 3.1 Tarjetas de resumen

En la parte superior hay cuatro tarjetas que se actualizan automáticamente cada 30 segundos:

| Tarjeta | Qué muestra |
|---------|------------|
| **Total de documentos** | Todos los PDFs que has subido hasta hoy |
| **Procesando** | Documentos que el sistema está analizando ahora mismo |
| **Páginas procesadas hoy** | Cuántas páginas ha procesado tu equipo en el día de hoy |
| **Pendientes de revisión** | Documentos donde la IA no estaba segura y necesitan tu atención |

El número de **Completados** aparece como subtexto dentro de la tarjeta de Procesando, y el tiempo promedio de procesamiento aparece dentro de la tarjeta de Pendientes de revisión.

### 3.2 Gráfico de actividad

Debajo de las tarjetas hay un gráfico de barras con la actividad de los últimos 7 días:

- **Barras azules** — documentos completados correctamente ese día.
- **Barras rojas** — documentos que fallaron o tuvieron errores.

El gráfico se actualiza automáticamente cada minuto.

### 3.3 Documentos recientes

A la derecha del gráfico verás los **6 documentos más recientes** subidos por tu equipo, con:

- Nombre del archivo.
- Tamaño del archivo.
- Fecha y hora de subida.
- Estado actual (coloreado).

Haz clic en cualquier documento para abrirlo directamente en el **Espacio de revisión**.

El enlace **Ver todos** lleva a la bandeja completa de documentos.

---

## 4 Cargar documentos

### 4.1 Desde la página de carga

1. Haz clic en **Subir** en la barra lateral (o en el botón **Subir** de la bandeja de documentos).
2. Verás una zona de carga con el texto *"Arrastra PDFs aquí o haz clic para buscar"*.
3. Puedes:
   - **Arrastrar** uno o varios archivos PDF desde tu explorador de archivos directamente sobre esa zona.
   - **Hacer clic** en la zona para abrir el explorador de archivos y seleccionar archivos.
4. La zona se ilumina en azul cuando arrastras archivos encima para confirmar que puedes soltarlos.

**Restricciones:**
- Solo se aceptan archivos **PDF**.
- Tamaño máximo: **100 MB** por archivo.
- Puedes subir varios archivos a la vez.

### 4.2 Seguimiento del progreso

Una vez que sueltas o seleccionas los archivos, aparece una lista debajo de la zona de carga con el estado de cada archivo:

| Icono | Significado |
|-------|-------------|
| ⏳ (girando) | El archivo se está subiendo |
| ✅ (verde) | Subida completada |
| ❌ (rojo) | Error — revisa el mensaje que aparece debajo del nombre |

Cada archivo muestra también una barra de progreso en porcentaje mientras se sube.

### 4.3 Redirección automática

Cuando el último archivo termina de subirse, la aplicación te lleva automáticamente al **Espacio de revisión** del primer documento subido para que puedas empezar a revisar los resultados. Si subiste varios, los otros estarán disponibles en la bandeja de documentos.

> **Consejo:** Si subes un PDF que en realidad contiene varias facturas o contratos seguidos, no necesitas separarlos antes. OpenIDP detecta automáticamente dónde termina un documento y empieza otro.

---

## 5 Bandeja de documentos

La **Bandeja de documentos** (menú **Documentos**) muestra todos los PDFs que tu equipo ha subido.

### 5.1 Tabla de documentos

La tabla tiene las siguientes columnas:

| Columna | Descripción |
|---------|-------------|
| **Nombre** | Nombre del archivo PDF original |
| **Estado** | Estado actual del procesamiento (con color) |
| **Páginas** | Número de páginas del PDF (aparece tras la carga inicial) |
| **Tamaño** | Peso del archivo en KB o MB |
| **Subido** | Fecha y hora de subida |
| **Acciones** | Botones para abrir o eliminar el documento |

La tabla se actualiza automáticamente cada 10 segundos.

### 5.2 Filtrar por estado

Encima de la tabla hay botones de filtro:

**Todos · Pendiente · Procesando · Completado · Fallido · Revisión pendiente**

Haz clic en cualquiera para ver sólo los documentos en ese estado. Para volver a ver todos, haz clic en **Todos**.

### 5.3 Acciones por documento

En la columna **Acciones** de cada fila hay dos botones:

- **Abrir** (icono de enlace externo) — Abre el documento en el **Espacio de revisión**.
- **Eliminar** (icono de papelera) — Elimina permanentemente el documento y todos sus datos extraídos. Se pedirá confirmación antes de borrar.

> **Advertencia:** La eliminación es permanente. Una vez borrado, no se puede recuperar el documento ni los campos extraídos.

### 5.4 Paginación

Si tienes muchos documentos, la tabla muestra 20 por página. Usa los botones **Anterior** y **Siguiente** para navegar. El indicador central muestra en qué página estás y el total.

---

## 6 Espacio de revisión

El **Espacio de revisión** es el corazón de la plataforma. Aquí es donde lees el documento original, ves lo que la IA extrajo y corriges o apruebas cada campo.

Para acceder, haz clic en **Abrir** junto a cualquier documento en la bandeja, o haz clic en un documento reciente desde el panel de control.

La pantalla está dividida en tres zonas principales:

```
┌─ Barra de estado ─────────────────────────────────────────────────────┐
│ Progreso del procesamiento en tiempo real                              │
├─ Pestañas de sub-documentos ──────────────────────────────────────────┤
│ [ Doc 1 · factura · pp. 1-3 ]  [ Doc 2 · orden de compra · pp. 4-5 ] │
├─ Visor PDF (izquierda, 55%) ─────┬─ Panel de extracción (derecha) ────┤
│                                  │  [ Campos ]  [ Chat ]              │
│  Contenido del PDF               │                                    │
│  con zonas resaltadas            │  Tabla de campos extraídos         │
│                                  │  ── Panel de evidencia ──          │
│                                  │  Fuente y razonamiento de la IA    │
└──────────────────────────────────┴────────────────────────────────────┘
```

### 6.1 Barra de estado

La barra fina en la parte superior muestra qué está haciendo el sistema en tiempo real:

| Mensaje | Significado |
|---------|-------------|
| *Leyendo el documento…* | El sistema está procesando el archivo |
| *Analizando el diseño…* | Identificando bloques de texto, tablas e imágenes |
| *Clasificando y dividiendo…* | Detectando si hay varios documentos en el PDF |
| *Ejecutando OCR…* | Leyendo texto de páginas escaneadas o de imagen |
| *Extrayendo campos…* | La IA está identificando y extrayendo los datos |
| *Finalizando…* | Guardando los resultados |
| ✅ *Procesamiento completado* | Todo listo, puedes revisar los campos |
| ❌ *Error en el procesamiento* | Algo falló; el mensaje indica el detalle |

El indicador de conexión (icono wifi) muestra si la comunicación en tiempo real está activa. Si ves *Reconectando…* espera unos segundos; la conexión se restaura automáticamente.

### 6.2 Pestañas de sub-documentos

Si el PDF que subiste contiene **varios documentos concatenados**, verás una fila de pestañas, una por cada documento detectado:

```
[ Doc 1 · factura · pp. 1–3 ]   [ Doc 2 · oc · pp. 4–5 ]   [ Doc 3 · ...]
```

Cada pestaña indica:
- El número de documento dentro del PDF.
- El tipo de documento detectado (si se configuró un esquema).
- El rango de páginas que ocupa dentro del PDF original.

Haz clic en cualquier pestaña para cambiar el contexto: el visor PDF saltará a las páginas de ese sub-documento y la tabla de campos mostrará sólo los campos extraídos de él.

Si el PDF tiene un solo documento, las pestañas no aparecen.

### 6.3 Visor PDF

El lado izquierdo muestra el PDF original con controles de navegación en la parte inferior:

- **Flechas izquierda/derecha** — ir a la página anterior o siguiente.
- **Indicador de página** — muestra la página actual y el total (ej. *2 / 5*).
- **Zoom** — botones + y − para acercar o alejar.

#### Zonas resaltadas (bounding boxes)

Sobre el PDF verás **rectángulos de colores** superpuestos. Cada rectángulo señala exactamente la zona del documento de donde se extrajo un campo:

- **Azul claro** — zona de un campo extraído.
- **Amarillo** — zona del campo que tienes seleccionado en la tabla de la derecha.

**Interacción bidireccional:**

- Haz clic en un **rectángulo del PDF** → la fila correspondiente en la tabla se resalta automáticamente.
- Haz clic en una **fila de la tabla** → el PDF hace scroll hasta esa página y resalta el rectángulo correspondiente.

Esto te permite verificar con un solo clic que el valor extraído corresponde exactamente al texto que aparece en el documento.

### 6.4 Tabla de campos extraídos

El panel derecho muestra la tabla con todos los campos que la IA extrajo del sub-documento activo.

Las columnas son:

| Columna | Descripción |
|---------|-------------|
| **Campo** | Nombre del campo (ej. *Número de factura*, *Importe total*) |
| **Valor** | El texto extraído (editable) |
| **Estado** | Semáforo de confianza (✓ / ⚠ / ✗) |
| **Confianza** | Porcentaje de seguridad de la IA (0–100 %) |

#### Editar un valor

Si la IA extrajo un dato incorrecto o incompleto, puedes corregirlo directamente:

1. Haz clic en la celda de la columna **Valor** en la fila que quieres editar.
2. El campo se convierte en un cuadro de texto editable.
3. Escribe el valor correcto.
4. Pulsa **Enter** para guardar, o **Escape** para cancelar sin guardar.
5. La fila mostrará una marca verde (✓) indicando que fue revisada por un humano.

Los valores que tú corriges se guardan inmediatamente y quedan marcados como *revisados por humano*, lo que diferencia tu corrección de la extracción automática.

#### Semáforo de confianza

La columna **Estado** usa tres iconos:

| Icono | Color | Significado |
|-------|-------|-------------|
| ✓ | Verde | La IA está muy segura del valor (≥ 85 %) y pasó las validaciones |
| ⚠ | Amarillo | Seguridad media (65–84 %) o hay una advertencia de validación |
| ✗ | Rojo | Seguridad baja (< 65 %) o falló una regla de validación |
| ⏱ | Gris | Aún no se ha procesado este campo |

Los campos en **rojo** o **amarillo** son los que más necesitan tu atención.

### 6.5 Panel de evidencia

Debajo de la tabla hay una sección que se activa cuando seleccionas una fila: el **Panel de evidencia**.

Esta sección te muestra de dónde vino el valor extraído y por qué la IA tomó esa decisión:

| Elemento | Descripción |
|----------|-------------|
| **Método** | Cómo se extrajo: *IA* (modelo de lenguaje), *OCR* (reconocimiento óptico), o *Regla* (regla determinista configurada por el administrador) |
| **Confianza** | Porcentaje, coloreado según el semáforo |
| **Texto fuente** | El fragmento exacto del documento del que se tomó el valor, en cursiva |
| **Razonamiento de la IA** | La explicación paso a paso de por qué la IA eligió ese valor |
| **Errores de validación** | Si hay reglas que fallaron, aparecen aquí en rojo |

El panel de evidencia es especialmente útil para **auditorías**: puedes saber en todo momento de qué parte del documento viene cada dato sin tener que buscar manualmente.

Si no hay ningún campo seleccionado, el panel muestra *"Selecciona un campo para ver la evidencia"*.

### 6.6 Chat con el documento

Haz clic en la pestaña **Chat** (icono de burbuja de diálogo) en la parte superior del panel derecho para abrir el chat.

El chat te permite **hacer preguntas en lenguaje natural** sobre el contenido del documento activo. Útil cuando quieres encontrar información específica sin revisar el PDF página por página.

**Cómo usarlo:**

1. Escribe tu pregunta en el cuadro de texto de la parte inferior.
2. Pulsa **Enter** o haz clic en el botón de enviar (icono de flecha).
3. La respuesta aparece en segundos.

**Ejemplos de preguntas:**

> *¿Cuál es el nombre del proveedor?*
>
> *¿Hay algún descuento aplicado en esta factura?*
>
> *¿Cuándo vence este contrato?*
>
> *¿Cuál es la dirección de entrega?*

Las respuestas se basan en el texto extraído del documento. El historial de la conversación se mantiene mientras tengas la página abierta.

> **Nota:** La pestaña de Chat y la de Campos son independientes — puedes cambiar entre ellas sin perder los datos de ninguna.

---

## 7 Guía de colores e iconos

Esta sección es una referencia rápida para interpretar los indicadores visuales de la plataforma.

### Estados de documento (bandeja)

| Color del badge | Estado | Qué significa | Qué hacer |
|----------------|--------|---------------|-----------|
| ⚪ Gris | **Pendiente** | Subido, esperando procesamiento | Esperar |
| 🔵 Azul (pulsando) | **Procesando** | El sistema está trabajando | Esperar |
| 🟢 Verde | **Completado** | Extracción finalizada sin problemas | Revisar si lo deseas |
| 🟠 Naranja | **Revisión pendiente** | La IA encontró campos con baja confianza | **Abrir y revisar** |
| 🔴 Rojo | **Fallido** | Error durante el procesamiento | Contactar al administrador |

### Confianza de campos (espacio de revisión)

| Icono | Color | Rango | Acción recomendada |
|-------|-------|-------|-------------------|
| ✓ | Verde | 85–100 % | Ninguna, el valor es fiable |
| ⚠ | Amarillo | 65–84 % | Revisar visualmente el valor |
| ✗ | Rojo | 0–64 % | **Verificar y corregir manualmente** |

### Métodos de extracción

| Badge | Significado |
|-------|-------------|
| **IA** (morado) | Extraído por el modelo de inteligencia artificial |
| **OCR** (gris) | Extraído por reconocimiento óptico de caracteres (páginas escaneadas) |
| **Regla** (azul) | Extraído por una regla determinista configurada por el administrador |

### Indicadores de revisión humana

| Indicador | Significado |
|-----------|-------------|
| ✓ verde en la celda | El valor fue revisado y confirmado (o corregido) por una persona |
| Sin marca | El valor es directamente el que extrajo la IA |

---

## 8 Tipos de documento (administradores)

> **Nota para administradores:** Esta sección está dirigida a quienes configuran la plataforma. Los usuarios que sólo revisan documentos no necesitan tocar esta sección.

Los **Tipos de documento** definen qué campos debe extraer la IA de cada clase de documento. Sin un tipo de documento configurado, la plataforma no sabe qué información buscar.

### 8.1 Ver los tipos existentes

Ve al menú **Tipos de documento** (icono de capas en la barra lateral).

Verás una cuadrícula con todos los tipos configurados para tu organización. Cada tarjeta muestra el nombre, el identificador y una breve descripción.

Haz clic en cualquier tarjeta para editarla.

### 8.2 Crear un nuevo tipo de documento

1. Haz clic en el botón **Nuevo tipo** (esquina superior derecha).
2. Rellena el formulario:

**Información básica:**

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Nombre** | Nombre legible del tipo | *Factura de proveedor* |
| **Identificador** | Se genera automáticamente del nombre (no cambia después) | *factura-de-proveedor* |
| **Descripción** | Explicación breve para ayudar a la IA a clasificar correctamente | *Facturas emitidas por proveedores externos* |

3. Añade los campos que quieres extraer (ver sección siguiente).
4. Opcional: añade reglas de validación.
5. Haz clic en **Guardar**.

### 8.3 Añadir campos

En la sección **Campos** del formulario, haz clic en **+ Agregar campo** para cada dato que quieras extraer.

Cada campo requiere:

| Configuración | Descripción | Ejemplo |
|--------------|-------------|---------|
| **Nombre interno** | Identificador en minúsculas con guión bajo | `numero_factura` |
| **Etiqueta** | Nombre visible para el usuario | *Número de factura* |
| **Tipo** | Formato del dato (ver tabla abajo) | *Texto* |
| **Requerido** | ¿Marca el documento para revisión si falta este campo? | ✓ |

**Tipos de campo disponibles:**

| Tipo | Cuándo usarlo |
|------|--------------|
| **Texto** | Nombres, descripciones, referencias libres |
| **Número** | Cantidades, códigos numéricos |
| **Fecha** | Fechas de emisión, vencimiento, entrega |
| **Moneda** | Importes económicos (con símbolo de moneda) |
| **Verdadero/Falso** | Indicadores binarios (ej. ¿tiene IVA?) |
| **Tabla** | Líneas de detalle con varias columnas (ej. líneas de factura) |
| **Dirección** | Direcciones postales completas |
| **Correo electrónico** | Direcciones de email |
| **Teléfono** | Números de teléfono |

Puedes **reordenar los campos** arrastrándolos por el asa (icono de puntos a la izquierda de cada fila). El orden aquí es el orden en que aparecerán en la tabla del Espacio de revisión.

Para **eliminar un campo**, haz clic en el icono de papelera a la derecha de esa fila.

### 8.4 Reglas de validación (opcional)

Las reglas de validación comprueban automáticamente si un valor extraído es correcto. Si una regla falla, el campo aparece con ⚠ o ✗ para alertar al revisor.

Haz clic en **+ Agregar regla** en la sección de Reglas de validación.

**Tipos de regla disponibles:**

| Tipo | Para qué sirve | Ejemplo |
|------|---------------|---------|
| **Expresión regular** | Verificar que el valor sigue un formato | El número de factura debe empezar por "FAC-" |
| **Rango numérico** | Verificar que un número está dentro de límites | El importe debe ser entre 0 y 999.999 |
| **Campo requerido** | Verificar que el campo no está vacío | La fecha es obligatoria |
| **Campo cruzado** | Comparar dos campos entre sí | La fecha de vencimiento debe ser posterior a la fecha de emisión |
| **Validación semántica** | La IA verifica si el valor tiene sentido | "El nombre del proveedor debe ser una empresa real" |

### 8.5 Editar un tipo existente

Abre el tipo desde la cuadrícula y modifica lo que necesites. Puedes cambiar el nombre, la descripción, añadir o eliminar campos y modificar reglas.

> **Nota:** Los cambios sólo afectan a documentos procesados **después** de guardar. Los documentos ya procesados conservan los campos con los que fueron extraídos.

### 8.6 Desactivar un tipo

No existe un botón de *Eliminar* para los tipos de documento porque borrarlos podría afectar a documentos ya procesados. En su lugar, puedes **desactivarlos**: el tipo deja de aparecer en los menús pero todos sus datos históricos se conservan.

Para desactivar, abre el tipo y desmarca la casilla **Activo** al guardar.

---

## 9 Área de pruebas

El **Área de pruebas** (icono de matraz en la barra lateral) te permite comprobar cómo funciona un tipo de documento sin necesidad de subir un PDF.

Es útil cuando configuras un nuevo esquema y quieres verificar que los campos se extraen correctamente antes de ponerlo en producción.

### Cómo usar el área de pruebas

1. Ve al menú **Área de pruebas**.
2. En el desplegable **Tipo de documento**, selecciona el esquema que quieres probar.
3. En el cuadro **Texto del documento**, pega el texto de un documento de ejemplo (puedes copiarlo de un PDF abierto).
4. Haz clic en **Ejecutar extracción**.
5. El resultado aparece en el panel derecho mostrando cada campo, el valor encontrado y la confianza.

> **Consejo:** Si un campo no aparece o tiene baja confianza, revisa la **Descripción** del tipo de documento y asegúrate de que los nombres de los campos son descriptivos. Por ejemplo, usa *"numero_de_factura"* en lugar de *"campo1"*.

El área de pruebas no guarda ningún resultado ni crea registros en la bandeja de documentos. Es un entorno completamente seguro para experimentar.

---

## 10 Claves de acceso para integraciones

> **Nota:** Esta sección es relevante si tu equipo quiere conectar OpenIDP con otros sistemas (ERP, plataformas de automatización, scripts propios).

Las **Claves de acceso** (menú **Configuración**) permiten que aplicaciones externas interaccionen con OpenIDP sin necesitar tu contraseña personal.

### 10.1 Crear una clave

1. Ve a **Configuración** en la barra lateral.
2. En la pestaña **Claves de acceso**, escribe un nombre descriptivo para la clave (ej. *"Integración ERP Producción"*).
3. Haz clic en **Crear**.
4. **IMPORTANTE:** La clave completa aparece una única vez en un recuadro verde. **Cópiala ahora** haciendo clic en el icono de copiar.

Una vez que cierres o abandones esa pantalla, la clave completa no volverá a mostrarse. Si la pierdes, deberás eliminar esa clave y crear una nueva.

### 10.2 Identificar tus claves

En la tabla de claves verás:

| Columna | Descripción |
|---------|-------------|
| **Nombre** | El nombre que le diste al crear la clave |
| **Prefijo** | Los primeros caracteres de la clave (para identificarla sin exponer el secreto) |
| **Creada** | Fecha de creación |
| **Último uso** | Cuándo se usó por última vez (*Nunca* si no se ha usado aún) |

### 10.3 Eliminar una clave

Si sospechas que una clave está comprometida o ya no la necesitas:

1. Haz clic en el icono de papelera en la fila correspondiente.
2. Confirma la eliminación en el diálogo.

> **Advertencia:** Cualquier sistema que esté usando esa clave dejará de funcionar inmediatamente.

---

## 11 Facturación y plan

La página de **Facturación** (icono de tarjeta en la barra lateral) muestra tu suscripción actual y el consumo del mes.

### 11.1 Resumen de tu plan actual

En la parte superior verás:

- **Nombre del plan** (ej. *Plan Starter*).
- **Estado de la suscripción** (activo, cancelado, pago pendiente).
- **Páginas procesadas este mes** en formato *X de Y*, con una barra de progreso.
  - La barra se vuelve **amarilla** al superar el 70 % del límite.
  - Se vuelve **roja** al superar el 90 %.
- El botón **Gestionar suscripción** abre el portal de pagos donde puedes cambiar la forma de pago, ver facturas anteriores o cancelar.

### 11.2 Planes disponibles

| Plan | Precio | Páginas/mes | Usuarios | Para quién |
|------|--------|-------------|----------|-----------|
| **Starter** | $49/mes | 500 | 1 | Equipos pequeños o uso individual |
| **Professional** | $199/mes | 3.000 | 10 | Equipos medianos con volumen regular |
| **Enterprise** | A medida | Ilimitado | Ilimitado | Grandes organizaciones, SLA garantizado |

El plan Professional aparece resaltado como *Popular*.

### 11.3 Cambiar de plan

1. Haz clic en el botón **Actualizar** bajo el plan que deseas.
2. Si ya estás en ese plan, el botón dirá **Plan actual** y estará desactivado.
3. Se abrirá la página de pago en una nueva pestaña del navegador.
4. Completa el proceso de pago.
5. Al volver a la aplicación, tu nuevo plan estará activo en pocos minutos.

### 11.4 ¿Qué pasa si supero el límite de páginas?

Depende del plan:
- **Starter y Professional:** Las páginas adicionales tienen un coste por página.
- **Enterprise:** Sin límite.

Si te acercas al límite, el sistema te lo mostrará con la barra en rojo. Puedes actualizar a un plan superior en cualquier momento.

---

## 12 Referencia de estados

### Estados de documentos

| Estado | Color | Descripción | Qué hacer |
|--------|-------|-------------|-----------|
| **Pendiente** | Gris | El documento se subió correctamente y está en la cola de procesamiento | Esperar; normalmente pasa a *Procesando* en segundos |
| **Procesando** | Azul | El sistema está leyendo, dividiendo y extrayendo los datos | Esperar; el proceso completo toma menos de un minuto para la mayoría de PDFs |
| **Completado** | Verde | Extracción finalizada, todos los campos tienen confianza alta y pasaron las validaciones | Revisar si lo deseas; el documento está listo |
| **Revisión pendiente** | Naranja | Uno o más campos tienen confianza baja o fallaron una validación | **Abrir el documento y revisar los campos marcados con ⚠ o ✗** |
| **Fallido** | Rojo | El procesamiento encontró un error irrecuperable | Vuelve a subir el documento; si persiste, contacta al administrador |

### Estados de campos extraídos

| Estado | Icono | Descripción |
|--------|-------|-------------|
| **Válido** | ✓ verde | Extracción correcta y validaciones superadas |
| **Advertencia** | ⚠ amarillo | Confianza media o advertencia de validación no crítica |
| **Inválido** | ✗ rojo | Confianza muy baja o fallo de una regla de validación |
| **Revisado por humano** | ✓ verde oscuro | Un revisor confirmó o corrigió el valor manualmente |
| **Pendiente** | ⏱ gris | El campo aún no ha sido procesado |

---

## 13 Preguntas frecuentes

**¿Cuánto tiempo tarda en procesarse un documento?**

La mayoría de los documentos se procesan en menos de 60 segundos. Un PDF de 15 páginas con texto claro suele completarse en 30–45 segundos. Los documentos escaneados o con imágenes complejas pueden tardar un poco más porque requieren reconocimiento óptico de caracteres.

---

**¿Qué formatos de archivo puedo subir?**

Sólo se aceptan archivos en formato **PDF**. Si tienes documentos en Word, Excel o imagen (JPG, PNG), conviértelos a PDF antes de subirlos.

---

**¿Puedo subir un PDF que contiene varias facturas?**

Sí. OpenIDP detecta automáticamente las separaciones entre documentos y trata cada uno de forma independiente. Verás pestañas numeradas en el Espacio de revisión, una por cada documento detectado.

---

**¿Qué hago cuando un campo tiene el icono rojo (✗)?**

El campo tiene baja confianza o falló una regla de validación. Lo correcto es:
1. Hacer clic en la fila para ver la **evidencia** (fuente y razonamiento de la IA).
2. Revisar en el PDF el área resaltada en amarillo.
3. Si el valor es incorrecto, editarlo directamente en la celda.
4. Si el valor es correcto pero la IA marcó error, también puedes editarlo y guardarlo — esto lo marca como *revisado por humano*.

---

**¿Se puede recuperar un documento eliminado?**

No. La eliminación es permanente. Si necesitas mantener un registro histórico, evita eliminar documentos ya procesados.

---

**¿Qué pasa si mi empresa necesita más páginas de las incluidas en el plan?**

Las páginas adicionales se facturan automáticamente con una tarifa por página. Para evitar cargos extra, considera actualizar al plan siguiente si habitualmente superas el límite mensual.

---

**¿Es segura la información de mis documentos?**

Los documentos se almacenan con aislamiento por organización. Ningún otro cliente de OpenIDP puede acceder a tus datos. Antes de enviar cualquier texto al modelo de inteligencia artificial, la plataforma detecta y anonimiza automáticamente información sensible (nombres de personas, números de identificación, datos bancarios) para proteger la privacidad.

---

**¿Puedo usar OpenIDP desde el móvil?**

La interfaz está optimizada para pantallas de escritorio. En móvil es funcional pero la experiencia es mejor en un ordenador, especialmente en el Espacio de revisión donde la visualización del PDF y la tabla de campos requieren más espacio de pantalla.

---

**No veo el tipo de documento correcto en la lista al revisar. ¿Qué hago?**

El tipo de documento se asigna automáticamente durante el procesamiento. Si la clasificación no fue correcta, contacta con el administrador de tu organización para que revise los esquemas configurados y, si es necesario, vuelva a procesar el documento.

---

**¿Dónde puedo encontrar ayuda adicional?**

Contacta con el equipo de soporte de tu organización o con el administrador de OpenIDP. Si tu empresa tiene documentación interna sobre flujos de trabajo específicos, búscala en el portal de conocimiento interno.
