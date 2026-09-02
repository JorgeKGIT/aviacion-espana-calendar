# 📅 Calendario de eventos de Aviación España 

Script que extrae eventos de aviación desde **PreparaULM** y los publica en un archivo **ICS** de calendario, permitiendo suscribirse desde dispositivos móviles (iPhone, Android, Outlook, Google Calendar, etc.).

## 🎯 ¿Qué hace este proyecto?

Este proyecto automatiza la tarea de recopilar eventos de aviación en España desde el sitio web [PreparaULM](https://www.preparaulm.com) y convertirlos en un calendario estándar (formato ICS) que puedes suscribir en cualquier aplicación de calendario.

**Flujo del proceso:**
```
PreparaULM (sitio web)
    ↓
Web Scraping (BeautifulSoup)
    ↓
Parsing de datos (fechas, ubicación, descripción)
    ↓
Calendario ICS
    ↓
Archivo: docs/aviacion.ics
```

## 📦 Requisitos

- Python 3.7+
- Las dependencias en `requirements.txt`:
  - **requests**: Para descargar las páginas web de PreparaULM
  - **beautifulsoup4**: Para analizar el HTML y extraer información
  - **icalendar**: Para crear archivos de calendario en formato ICS

Instala las dependencias con:
```bash
pip install -r requirements.txt
```

## 🚀 Cómo usar

Ejecuta el script desde la línea de comandos:
```bash
python update_calendar.py
```

El script descargará automáticamente todos los eventos de aviación y generará el archivo `docs/aviacion.ics`.

## 📋 Estructura del código

### 1. **`parse_date_range(text)`**
Convierte fechas en formato de texto legible por humanos a objetos `date` de Python.

**Ejemplos que procesa:**
- `"4 - 6 septiembre de 2026"` → (2026-09-04, 2026-09-06)
- `"6 de septiembre de 2026"` → (2026-09-06, 2026-09-06)
- `"4 de enero de 2026"` → (2026-01-04, 2026-01-04)

**Tecnología:** Expresiones regulares para extraer día(s), mes y año.

---

### 2. **`clean_text(text)`**
Limpia el texto eliminando espacios en blanco duplicados y espacios al inicio/final.

```python
"Esto   es   un    texto" → "Esto es un texto"
```

---

### 3. **`event_uid(title, start)`**
Genera un identificador único y estable para cada evento usando SHA-256.

**¿Por qué es importante?** Si PreparaULM cambia la descripción del evento, Apple Calendar y otras aplicaciones seguirán reconociendo que es el mismo evento (no duplicados).

```python
event_uid("Congreso de Aviación", date(2026, 9, 4))
# → "a3b4c5d6e7f8g9h0i1j2@aviacion-espana-calendar"
```

---

### 4. **`extract_events(html)`** ⭐ Parte principal
Extrae todos los eventos de la página HTML de PreparaULM.

#### Proceso paso a paso:

**A) Encuentra enlaces a eventos:**
- Busca todos los `<a>` que contengan `/eventos-aeronauticos/` en la URL
- Evita duplicados

**B) Para cada evento, extrae:**

| Campo | Cómo lo obtiene |
|-------|-----------------|
| **Título** | Del `<h1>` de la página del evento |
| **Fecha** | Usando `parse_date_range()` en el texto de la página |
| **Ubicación** | El texto inmediatamente después de la fecha (filtrado para evitar basura) |
| **Descripción** | Busca la sección "Sobre el evento" (entre `<h2>` o `<h3>`) |
| **URL** | La URL de la página del evento |

#### Características de robustez:
- ✅ Manejo de errores de red (timeout de 30 segundos)
- ✅ Validación de datos (si falta título o fecha, salta el evento)
- ✅ Logs detallados de progreso: `[1/25] 2026-09-04 → 2026-09-06 | Congreso...`

---

### 5. **`create_calendar(events)`** ⭐ Generación del calendario
Convierte los eventos extraídos en un archivo de calendario ICS profesional.

#### Procesamiento:

1. **Crea un calendario base:**
   - Nombre: "Eventos de Aviación en España"
   - Zona horaria: Europe/Madrid
   - Versión: iCalendar 2.0

2. **Filtra eventos:**
   - Solo incluye eventos **futuros** (fecha >= hoy)
   - Elimina **duplicados** (mismo título, misma fecha)
   - Ordena **cronológicamente**

3. **Para cada evento, añade:**
   - **UID**: Identificador único y estable
   - **DTSTART/DTEND**: Fechas de inicio y fin
   - **SUMMARY**: Título del evento
   - **DESCRIPTION**: Descripción completa + URL de origen
   - **LOCATION**: Ubicación (si disponible)
   - **URL**: Enlace al evento en PreparaULM

#### Ejemplo de evento generado:
```
BEGIN:VEVENT
UID:a3b4c5d6@aviacion-espana-calendar
DTSTART:20260904
DTEND:20260907
SUMMARY:Congreso de Aviación 2026
DESCRIPTION:Evento obtenido de PreparaULM...
LOCATION:Madrid
URL:https://www.preparaulm.com/eventos-aeronauticos/123
END:VEVENT
```

---

### 6. **`main()`** - Orquestación
Coordina todo el proceso:

1. Descarga la página de eventos de PreparaULM
2. Extrae todos los eventos
3. Crea el calendario
4. Guarda el archivo `docs/aviacion.ics`

---

## 📁 Estructura del proyecto

```
aviacion-espana-calendar/
├── README.md                                # Este archivo
├── requirements.txt                         # Dependencias de Python
├── update_calendar.py                       # Script principal
├── .github/
│   └── workflows/
│       └── update.yml                       # Workflow de GitHub Actions (automatización)
└── docs/
    └── aviacion.ics                         # Archivo de calendario generado
```

## 📱 Cómo usar el calendario en tu móvil

### iPhone (Apple Calendar):
1. Comparte el archivo `docs/aviacion.ics` (ej: subiéndolo a un servidor web)
2. Abre el enlace desde tu iPhone
3. Toca "Add to Calendar"

### Android (Google Calendar):
1. Sube el archivo a Google Drive o un servidor web
2. Abre Google Calendar
3. Menú → Agregar calendario → Por URL → Pega el enlace

### Outlook:
1. Descarga el archivo `.ics`
2. Doble click para importar

### macOS/Linux:
```bash
# Ver el contenido del calendario
cat docs/aviacion.ics

# Importar en Thunderbird, Evolution, etc.
```

## ⚙️ Automatización con GitHub Actions

El proyecto incluye un workflow automático (`.github/workflows/update.yml`) que mantiene el calendario siempre actualizado.

### ¿Cómo funciona?

El workflow se ejecuta **automáticamente** 2 veces al día:
- 🌅 **06:00 UTC** - Actualización matutina
- 🌆 **18:00 UTC** - Actualización vespertina

También puedes ejecutarlo **manualmente** desde GitHub:
1. Ve a la pestaña "Actions" de tu repositorio
2. Selecciona "Actualizar calendario de aviación"
3. Haz click en "Run workflow"

### ¿Qué hace?

```yaml
1. Descarga el código del repositorio
2. Configura Python 3.12
3. Instala las dependencias (requests, beautifulsoup4, icalendar)
4. Ejecuta update_calendar.py
5. Detecta cambios en docs/aviacion.ics
6. Hace commit y push de los cambios automáticamente
```

### Permisos necesarios

El workflow necesita permisos para escribir en el repositorio:
```yaml
permissions:
  contents: write  # Permite hacer push de cambios
```

Si clonas este proyecto a tu propio repositorio, asegúrate de que GitHub Actions está habilitado en los ajustes del repositorio.

## 🔧 Configuración personalizada

En el archivo `update_calendar.py` puedes ajustar:

```python
BASE_URL = "https://www.preparaulm.com"  # URL base
EVENTS_URL = "..."  # URL de eventos (filtrados por "nacional" y "todos")
OUTPUT_FILE = "docs/aviacion.ics"        # Dónde guardar el calendario
```

## 📊 Información técnica

- **Web Scraping:** Beautiful Soup 4 (análisis HTML)
- **HTTP Requests:** Requests (con User-Agent personalizado)
- **Parsing de fechas:** Expresiones regulares con soporte para español
- **Formato de salida:** iCalendar (RFC 5545)
- **Zona horaria:** Europe/Madrid (UTC+1 / UTC+2 en verano)
- **CI/CD:** GitHub Actions (automatización en la nube)
- **Entorno de CI:** Ubuntu Latest con Python 3.12
- **Frecuencia de actualización:** 2 veces al día (6:00 y 18:00 UTC)

## ⚠️ Notas importantes

1. **Respeto a los términos de servicio:** Este script respeta la estructura de PreparaULM y solo extrae información pública. Incluye delays y User-Agent apropiados.

2. **Eventos futuros:** El calendario solo incluye eventos con fecha posterior a hoy.

3. **Duplicados:** El script detecta y elimina automáticamente eventos duplicados.

4. **Tiempos de ejecución:** Depende de la cantidad de eventos (típicamente 30-60 segundos).

## 🎓 Aprendizajes técnicos

Este proyecto demuestra:
- Web scraping con BeautifulSoup
- Parsing de texto en español con regex
- Generación de archivos ICS (calendarios)
- Manejo de excepciones y logging
- Extracción estructurada de datos HTML
- Trabajar con zonas horarias en Python

## 📝 Licencia

Libre para uso personal y educativo.
