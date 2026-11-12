# Tareas API: ejecución reproducible con Docker

API REST de ejemplo para administrar tareas. La aplicación implementa operaciones CRUD con Flask y PostgreSQL; Docker Compose construye y ejecuta ambos servicios en una red privada.

Repositorio: <https://github.com/benitocr7/S2-Trabajo-Aut-nomo_Nube>

## Requisitos

- Git.
- Docker Desktop (Windows/macOS) o Docker Engine y el complemento Docker Compose v2 (Linux).
- Docker en ejecución y conexión a Internet la primera vez, para descargar las imágenes base y dependencias.
- PowerShell 5.1 o superior para copiar el archivo de entorno con los comandos de esta guía.

No es necesario instalar Python ni PostgreSQL en el equipo anfitrión.

## Estructura del proyecto

```text
.
├── app.py                 # API REST y acceso a PostgreSQL
├── compose.yaml           # Servicios API y base de datos
├── Dockerfile             # Imagen de la API
├── .env.example           # Variables de ejemplo, sin credenciales reales
├── .gitignore
├── requirements.txt       # Dependencias de Python fijadas
└── db/
    └── init.sql           # Esquema inicial de la base de datos
```

## Preparar el entorno

Clona el repositorio y entra en su carpeta:

```powershell
git clone https://github.com/benitocr7/S2-Trabajo-Aut-nomo_Nube.git
Set-Location S2-Trabajo-Aut-nomo_Nube
```

Crea tu configuración local a partir de la plantilla:

```powershell
Copy-Item .env.example .env
```

Revisa `.env` y cambia `POSTGRES_PASSWORD` por un valor propio antes de compartir el equipo con otras personas. El archivo `.env` está excluido de Git; no publiques contraseñas reales. `API_PORT` es el puerto local de la API.

## Construir e iniciar

Desde la raíz del proyecto:

```powershell
docker compose up --build -d
docker compose ps
```

Compose construye la imagen de la API, inicia PostgreSQL y espera a que la base de datos esté saludable antes de iniciar la API. Comprueba el estado:

```powershell
Invoke-RestMethod http://localhost:5000/health
```

La respuesta esperada es similar a:

```json
{"database":"connected","status":"ok"}
```

Si cambiaste `API_PORT` en `.env`, sustituye `5000` por ese puerto en las solicitudes. Para consultar los mensajes de los servicios:

```powershell
docker compose logs -f
```

Presiona `Ctrl+C` para salir del seguimiento de logs; esto no detiene los servicios.

## Base de datos

`db/init.sql` crea la tabla `tasks` automáticamente cuando PostgreSQL inicializa por primera vez el volumen de datos. No hay que ejecutar una migración manual para el primer inicio.

El script de inicialización solo se ejecuta con un volumen vacío. Para borrar todos los datos y volver a inicializar la base (acción irreversible), ejecuta:

```powershell
docker compose down -v
docker compose up --build -d
```

No uses `-v` si necesitas conservar las tareas guardadas.

## Solicitudes CRUD

La API escucha en `http://localhost:5000`. Los ejemplos usan PowerShell y no requieren instalar `curl`.

**Crear una tarea**

```powershell
$task = Invoke-RestMethod -Method Post `
  -Uri http://localhost:5000/api/tasks `
  -ContentType 'application/json' `
  -Body '{"title":"Preparar entrega","description":"Probar la API","done":false}'
$task
```

La respuesta es `201 Created` e incluye el identificador de la tarea. Guarda el identificador para las siguientes solicitudes:

```powershell
$id = $task.id
```

**Consultar todas las tareas o una por ID**

```powershell
Invoke-RestMethod http://localhost:5000/api/tasks
Invoke-RestMethod "http://localhost:5000/api/tasks/$id"
```

**Actualizar parcialmente una tarea**

```powershell
Invoke-RestMethod -Method Patch `
  -Uri "http://localhost:5000/api/tasks/$id" `
  -ContentType 'application/json' `
  -Body '{"done":true}'
```

Los campos editables son `title`, `description` y `done`. `title` no puede estar vacío; `done` debe ser booleano.

**Eliminar una tarea**

```powershell
Invoke-RestMethod -Method Delete -Uri "http://localhost:5000/api/tasks/$id"
```

La eliminación correcta devuelve `204 No Content`. Una tarea inexistente devuelve `404 Not Found`; un JSON inválido o campos no válidos devuelven `400 Bad Request`.

## Detener y reiniciar

Detén y elimina los contenedores, conservando el volumen de PostgreSQL:

```powershell
docker compose down
```

Para volver a iniciar los servicios después:

```powershell
docker compose up -d
```

## Errores frecuentes

1. **`docker` no se reconoce o el daemon no está disponible.** Docker Desktop no está instalado/iniciado, o el servicio Docker de Linux está detenido. Inicia Docker Desktop (o el servicio Docker) y comprueba `docker info` antes de usar Compose.
2. **El puerto `5000` ya está ocupado.** Otra aplicación usa el puerto configurado para la API. Cambia `API_PORT` en `.env` (por ejemplo, `5001`), recrea los servicios con `docker compose up --build -d` y usa el puerto nuevo en las solicitudes.
3. **La API no se conecta a PostgreSQL o Compose informa de variables faltantes.** `.env` no existe, alguna variable requerida está vacía o la base de datos aún está inicializándose. Confirma que copiaste `.env.example` a `.env`, revisa `docker compose ps` y los mensajes con `docker compose logs db api`. Compose espera a la comprobación de salud de la base; vuelve a consultar `/health` cuando ambos servicios estén activos.
4. **Cambios a `db/init.sql` no aparecen en una base ya iniciada.** PostgreSQL ejecuta los scripts de `db/init.sql` solo al crear un volumen nuevo. Conserva los datos y aplica un cambio de esquema mediante una migración; para una práctica desechable, reinicializa con `docker compose down -v` y vuelve a iniciar (esto elimina los datos).
5. **La API responde `404` para una tarea.** El ID no existe o ya fue eliminado. Lista las tareas con `GET /api/tasks` y utiliza un ID existente.

## Informe de ejecución

El informe con el enlace al repositorio, comandos ejecutados, resultados y evidencias se entrega en [`informe_ejecucion.pdf`](informe_ejecucion.pdf).
