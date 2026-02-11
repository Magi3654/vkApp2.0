# 🏢 Kinessia Hub

**Sistema de Gestión de Viajes** — Plataforma interna para la administración integral de operaciones de agencia de viajes corporativa.

![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Proprietary-red)

---

## 📋 Descripción

Kinessia Hub es un sistema web multi-sucursal desarrollado para **Viajes Kinessia** (Ensenada / Mexicali, B.C., México) que centraliza y automatiza los procesos administrativos de una agencia de viajes corporativa especializada en boletos aéreos para empresas gubernamentales y privadas.

El sistema maneja el flujo completo de una venta: desde el cálculo del desglose de tarifas por empresa, la emisión de papeletas de cargo a tarjetas corporativas, el control de facturación, hasta la entrega de cortes de caja y la conciliación de expedientes.

---

## ✨ Módulos

### Operación de Ventas
| Módulo | Descripción |
|--------|-------------|
| **Calculadora de Desglose** | Calcula automáticamente tarifas base, IVA, cargos ocultos/visibles, bonificaciones y Q's según el esquema de facturación de cada empresa (IMSS, ISSSTE, CFE, estándar, etc.) |
| **Papeletas** | Registro de ventas de boletos vinculadas a tarjetas corporativas con control de folios, impresión de tickets térmicos y adjunto de documentos PDF |
| **Reportes de Ventas** | Consolidación de papeletas en reportes por periodo y agente |
| **Entregas / Cortes de Caja** | Control de entregas de efectivo del agente al gerente con vales y seguimiento de depósitos bancarios |

### Facturación
| Módulo | Descripción |
|--------|-------------|
| **Registro de Facturas** | Los agentes registran número de factura y monto contra papeletas |
| **Revisión de Facturas** | Flujo de aprobación/rechazo por parte de gerencia con comparación automática de montos |

### Administración
| Módulo | Descripción |
|--------|-------------|
| **Empresas** | CRUD de empresas cliente con configuración de esquemas de facturación, cargos de servicio, bonificaciones y descuentos |
| **Tarjetas Corporativas** | Gestión de tarjetas de crédito por sucursal con control de asignación a usuarios |
| **Autorizaciones** | Sistema de solicitud y aprobación para uso de tarjetas entre sucursales |
| **Usuarios** | Gestión de cuentas con roles, sucursales y asignación de tarjetas |

### Control y Seguimiento
| Módulo | Descripción |
|--------|-------------|
| **Expedientes** | Vista consolidada por clave de reservación que agrupa desgloses, papeletas y facturas |
| **Control de Papeletas** | Dashboard de validación y auditoría para gerencia |

---

## 🔐 Roles del Sistema

| Rol | Alcance |
|-----|---------|
| **Agente** | Crear desgloses y papeletas (propias), usar calculadora, generar reportes de ventas |
| **Facturación** | Registrar números de factura contra papeletas |
| **Gerente** | Todo lo anterior + revisión de facturas, expedientes globales, recepción de entregas |
| **Director / Admin** | Acceso total, aprobación de autorizaciones, gestión de usuarios y configuración |

---

## 🛠️ Stack Tecnológico

```
Backend:        Python 3.11+ / Flask 3.0
Base de Datos:  PostgreSQL 16
ORM:            SQLAlchemy + Flask-SQLAlchemy
Autenticación:  Flask-Login + Werkzeug (password hashing)
Frontend:       HTML5 / CSS3 / JavaScript (Vanilla)
Templates:      Jinja2
Tipografía:     Google Fonts (Noto Sans Display)
Iconos:         Font Awesome 6
Dates:          Flatpickr
Impresión:      Tickets térmicos (formato 80mm)
Email:          SMTP (Google Workspace)
```

---

## 📁 Estructura del Proyecto

```
vkApp2.0/
├── app/
│   ├── __init__.py              # Factory de la app Flask
│   ├── models.py                # Modelos SQLAlchemy
│   ├── routes.py                # Rutas principales (Blueprint main)
│   ├── auth.py                  # Blueprint de autenticación
│   ├── services/
│   │   └── notificaciones.py    # Servicio de email + notificaciones
│   ├── static/
│   │   ├── css/
│   │   │   ├── styles.css                    # Sistema de diseño maestro
│   │   │   ├── styleslogin.css               # Login
│   │   │   ├── stylesdash.css                # Dashboard
│   │   │   ├── stylespapeletas.css           # Formulario de papeletas
│   │   │   ├── stylesconsultapapeletas.css   # Consulta de papeletas
│   │   │   └── ...
│   │   ├── img/
│   │   │   └── logo_kinessia.png
│   │   └── uploads/                          # PDFs adjuntos
│   └── templates/
│       ├── base.html
│       ├── login.html
│       ├── dashboard.html
│       ├── papeletas.html
│       ├── consulta_papeletas.html
│       ├── calculadora_desglose.html
│       ├── empresas.html
│       ├── facturacion.html
│       ├── revision_facturas.html
│       ├── usuarios.html
│       ├── tarjetas.html
│       ├── autorizaciones.html
│       ├── reportes_ventas.html
│       ├── entregas.html
│       ├── expedientes.html
│       ├── control_papeletas.html
│       └── ...
├── .env                         # Variables de entorno (no en repo)
├── .gitignore
├── config.py
├── run.py                       # Entry point
└── requirements.txt
```

---

## ⚙️ Instalación

### Prerrequisitos

- Python 3.11+
- PostgreSQL 16+
- Git

### Setup

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/kinessia-hub.git
cd kinessia-hub

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=tu-clave-secreta

# Base de Datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/kinessia_hub

# Email (Google Workspace SMTP)
EMAIL_SENDER=correo@tudominio.com
EMAIL_PASSWORD=contraseña-de-app
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Base de Datos

```bash
# Crear la base de datos
createdb kinessia_hub

# Importar schema
psql -d kinessia_hub -f vkapp.sql
```

### Ejecutar

```bash
python run.py
```

La aplicación estará disponible en `http://127.0.0.1:5000`

---

## 🎨 Sistema de Diseño

El proyecto utiliza un sistema de diseño propio basado en la identidad visual de Kinessia:

| Token | Color | Uso |
|-------|-------|-----|
| `--kn-oxblood` | `#990100` | Primario, headers, botones principales |
| `--kn-ember` | `#b90504` | Gradientes, hover states |
| `--kn-graphite` | `#333333` | Texto principal |
| `--kn-snow` | `#f6f6f6` | Fondo de la aplicación |
| `--kn-alabaster` | `#e8e8e8` | Bordes, separadores |
| `--kn-white` | `#ffffff` | Cards, superficies |

El archivo `styles.css` contiene el sistema maestro con variables CSS, componentes base (botones, cards, tablas, modales, badges, formularios) y utilidades. Los módulos específicos extienden el sistema con archivos CSS dedicados.

---

## 📊 Flujo Principal de una Venta

```
  Agente                    Facturación              Gerente / Director
    │                            │                          │
    ├─ 1. Calcula desglose       │                          │
    │     (por empresa)          │                          │
    │                            │                          │
    ├─ 2. Crea papeleta          │                          │
    │     (cargo a tarjeta)      │                          │
    │                            │                          │
    │                       3. Registra ──────────────►     │
    │                          factura                      │
    │                            │                     4. Aprueba /
    │                            │                       Rechaza
    │                            │                          │
    ├─ 5. Crea reporte           │                          │
    │     de ventas              │                          │
    │                            │                          │
    ├─ 6. Genera entrega         │                          │
    │     (corte de caja)        │                          │
    │                            │                          │
    │                            │                     7. Recibe y
    │                            │                       deposita
    │                            │                          │
    └────────────────────────────┴──────────────────────────┘
```

---

## 📦 Dependencias Principales

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
Werkzeug==3.0.1
openpyxl==3.1.2
email-validator==2.1.0
```

---

## 🚀 Roadmap

- [ ] Migración a Supabase (PostgreSQL cloud + Auth + RLS)
- [ ] Módulo de Grupos y Cruceros
- [ ] Integración con GDS (Amadeus/Sabre)
- [ ] Dashboard ejecutivo con gráficas
- [ ] Notificaciones en tiempo real
- [ ] App móvil (PWA)

---

## 👩‍💻 Autora

**Ilse Machado** — Desarrolladora & Administradora de Sistemas  
Viajes Kinessia · Ensenada, B.C., México

---

## 📄 Licencia

Este es un proyecto privado desarrollado para uso interno de Viajes Kinessia.  
Todos los derechos reservados © 2025 Kinessia Trip.
