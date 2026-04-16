# OpenPrinterAgent

**OpenPrinterAgent** es una aplicación de código abierto para controlar impresoras térmicas ESC/POS desde tu escritorio o mediante una API REST.

## Características

- **GUI de Escritorio**: Interfaz moderna con CustomTkinter para gestionar impresoras y trabajos de impresión
- **API REST**: Endpoints completos para integrar con otros sistemas
- **Soporte USB y Serial**: Conexión directa a impresoras térmicas via USB o puerto serial
- **Comandos ESC/POS**: Implementación completa del protocolo ESC/POS para texto, códigos de barras, códigos QR e imágenes
- **Multi-plataforma**: Funciona en Windows, Linux y macOS

## Requisitos

- Python 3.10+
- Impresora térmica ESC/POS compatible
- libusb (para conexión USB en Linux)
- Puerto COM disponible (para conexión Serial en Windows)

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/yourusername/OpenPrinterAgent.git
cd OpenPrinterAgent
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate   # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar

Copia el archivo de ejemplo de configuración:

```bash
cp .env.example .env
```

Edita `.env` según tu configuración:

```env
API_HOST=127.0.0.1
API_PORT=5000
API_KEY=tu-clave-api-secreta
FLASK_DEBUG=1
```

## Uso

### Modo GUI (Escritorio)

```bash
python -m src.main gui
```

### Modo API (Servidor REST)

```bash
python -m src.main api
```

### Construcción de Executable

```bash
chmod +x scripts/build_exe.sh
./scripts/build_exe.sh
```

El executable se generará en `dist/OpenPrinterAgent/`.

## API REST

La API está protegida con autenticación por API Key. Incluye las siguientes rutas:

### Endpoints Públicos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/status` | Estado del sistema |

### Endpoints de Impresoras

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/printers` | Listar impresoras |
| POST | `/api/printers` | Crear impresora |
| GET | `/api/printers/<id>` | Obtener impresora |
| DELETE | `/api/printers/<id>` | Eliminar impresora |
| POST | `/api/printers/<id>/connect` | Conectar impresora |
| POST | `/api/printers/<id>/disconnect` | Desconectar impresora |

### Endpoints de Impresión

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/print` | Enviar trabajo de impresión |
| GET | `/api/jobs` | Listar trabajos |
| GET | `/api/jobs/<id>` | Obtener trabajo |
| DELETE | `/api/jobs/<id>` | Cancelar trabajo |

### Autenticación

Todas las rutas (excepto `/api/status`) requieren el header:

```
X-API-Key: tu-clave-api
```

### Ejemplo de uso

```bash
# Crear una impresora USB
curl -X POST http://localhost:5000/api/printers \
  -H "X-API-Key: tu-clave-api" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Impresora",
    "connection_type": "usb",
    "vendor_id": 1208,
    "product_id": 514
  }'

# Imprimir texto
curl -X POST http://localhost:5000/api/print \
  -H "X-API-Key: tu-clave-api" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "text",
    "printer_id": "uuid-de-impresora",
    "text": "Hola Mundo!"
  }'

# Imprimir código de barras
curl -X POST http://localhost:5000/api/print \
  -H "X-API-Key: tu-clave-api" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "barcode",
    "printer_id": "uuid-de-impresora",
    "data": "123456789",
    "barcode_type": "CODE128"
  }'
```

## Desarrollo

### Ejecutar Tests

```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

### Linting

```bash
ruff check src/
ruff format src/
```

## Estructura del Proyecto

```
OpenPrinterAgent/
├── src/
│   ├── api/              # API REST (Flask)
│   ├── core/            # Entidades y excepciones
│   ├── drivers/         # Drivers USB/Serial
│   ├── gui/             # Aplicación de escritorio
│   ├── models/          # Modelos de datos
│   ├── services/         # Lógica de negocio
│   └── utils/           # Configuración y logging
├── tests/               # Tests unitarios e integración
├── scripts/             # Scripts de utilidad
├── docs/                # Documentación
└── requirements.txt      # Dependencias
```

## Licencia

MIT License - ver archivo [LICENSE](LICENSE) para más detalles.

## Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-feature`)
3. Commit tus cambios (`git commit -am 'Agrega nueva feature'`)
4. Push a la rama (`git push origin feature/nueva-feature`)
5. Crea un Pull Request

## Recursos

- [Documentación ESC/POS](https://reference.epson-biz.com/modules/ref_escpos/index.php)
- [CustomTkinter Documentation](https://customtkinter.tomschimansky.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
