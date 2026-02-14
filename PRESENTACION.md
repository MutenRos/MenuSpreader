# MenuSpreader — Automatización de Menús por WhatsApp

![MenuSpreader Hero](docs/index.html)

## Introducción

MenuSpreader es una herramienta completa diseñada para bares y restaurantes que necesitan enviar su menú del día a decenas o cientos de clientes de forma automática a través de WhatsApp. El proyecto combina una app de escritorio con interfaz gráfica en Python/Tkinter, un panel web moderno con Next.js y React, y un servidor bot con Node.js que se conecta a WhatsApp Web. Todo funciona de forma local, sin necesidad de servicios de terceros ni cuotas mensuales — el único requisito es una sesión de WhatsApp del negocio.

---

## Desarrollo de las partes

### 1. Esquema de base de datos con Prisma ORM

El modelo de datos se define con Prisma sobre SQLite, lo que permite un despliegue sin dependencias externas. El archivo `prisma/schema.prisma` (líneas 1-48) define cuatro entidades principales:

- **Bar**: almacena el nombre y email del establecimiento (línea 14-19). Es la entidad raíz a la que se vinculan menús y plantillas.
- **MessageTemplate**: plantillas de mensajes reutilizables con relación FK→Bar (línea 21-27).
- **Company**: los contactos/empresas destinatarios, con nombre, persona de contacto y teléfono (línea 29-34).
- **Menu**: registros de menús subidos, con imageUrl, fecha y campo `sentCount` para contar envíos (línea 36-44).

```prisma
model Menu {
  id        String   @id @default(cuid())
  barId     String
  bar       Bar      @relation(fields: [barId], references: [id])
  imageUrl  String
  date      DateTime @default(now())
  createdAt DateTime @default(now())
  sentCount Int      @default(0)
}
```

La conexión se inicializa en `src/lib/prisma.ts` (líneas 1-7) usando el patrón singleton recomendado por Next.js para evitar crear múltiples instancias en desarrollo por los hot reloads.

---

### 2. Server Actions de Next.js — actions.ts

El archivo `src/app/actions.ts` (183 líneas) contiene toda la lógica del servidor usando la directiva `'use server'`. Las funciones principales son:

- **uploadMenu** (líneas 9-72): recibe un FormData con la imagen, la guarda en `public/uploads/` con nombre sanitizado (timestamp + filtro regex), crea el registro Menu en Prisma y llama a `sendMenuviaWhatsApp()`.
- **createCompany** (líneas 110-131): crea un contacto con validación de teléfono (mínimo 9 dígitos, `trim()` en todos los campos).
- **sendMenuviaWhatsApp** (líneas 140-183): itera sobre todas las empresas registradas, personaliza el mensaje reemplazando `{nombre}` por el nombre del contacto, y envía un POST al bot-server en `localhost:3001/send-menu`.

```typescript
// Validar formato de teléfono (mínimo 9 dígitos)
const phoneDigits = contactPhone.replace(/\D/g, '')
if (phoneDigits.length < 9) {
  throw new Error('El teléfono debe tener al menos 9 dígitos')
}
```

El `revalidatePath('/')` tras cada mutación fuerza a Next.js a refetchear los datos del servidor.

---

### 3. Componente React — MenuAppClient.tsx

El componente principal `src/app/MenuAppClient.tsx` (270 líneas) es un Client Component (`'use client'`) que recibe los datos ya pre-cargados desde el Server Component `page.tsx`. Se estructura en:

- **Navbar** (líneas 78-100): barra superior sticky con nombre del bar editable inline mediante un `<form action={updateBarName}>`.
- **Zona principal** (líneas 102-170): área de subida de imagen con drag & drop visual (input file oculto + UI decorativa), textarea para el mensaje personalizado con botones de plantilla rápida, y botón de envío con gradiente indigo.
- **Sidebar** (líneas 200-270): gestión de plantillas (CRUD) y lista de difusión de empresas con formulario de alta.

```tsx
<textarea 
    name="messageText" 
    rows={4} 
    className="w-full border border-slate-200 rounded-xl p-4 ..."
    value={messageText}
    onChange={(e) => setMessageText(e.target.value)}
    placeholder="Escribe tu mensaje aquí..."
></textarea>
```

Los iconos están definidos como componentes SVG inline (`Icons.Send`, `Icons.Upload`, etc.) en líneas 35-45 para evitar dependencias externas.

---

### 4. Bot servidor de WhatsApp — bot-server.js

El archivo `bot-server.js` (110 líneas) implementa el puente entre la aplicación y WhatsApp Web usando la librería `whatsapp-web.js`:

- **Autenticación QR** (líneas 17-30): el `Client` de whatsapp-web.js con `LocalAuth` persiste la sesión entre reinicios. Cuando necesita autenticación, emite un evento `qr` que se almacena en la variable `currentQR`.
- **Endpoint /status** (línea 60): devuelve el estado del bot (`INITIALIZING`, `QR_READY`, `READY`) y el QR data para que la app de escritorio lo muestre.
- **Endpoint /send-menu** (líneas 64-95): recibe `phone`, `caption` e `imagePath`. Limpia el teléfono de caracteres no numéricos, construye el chatId con sufijo `@c.us`, carga la imagen con `MessageMedia.fromFilePath()` y envía el mensaje.
- **Endpoint /health** (nuevo): devuelve uptime, estado y timestamp para monitorización.

```javascript
// Limpieza básica del número (eliminar caracteres no numéricos)
const cleanPhone = phone.replace(/\D/g, ''); 
const chatId = cleanPhone + '@c.us'; 

if (media) {
     await client.sendMessage(chatId, media, { caption: caption });
}
```

---

### 5. App de escritorio — menu_app.py (Tkinter)

El archivo `menu_app.py` (795+ líneas) es una aplicación de escritorio completa con interfaz gráfica en Tkinter, dividida en tres pestañas:

- **Tab Enviar Menú** (líneas 330-390): selector de imagen, editor de mensaje con sistema de plantillas guardadas en SQLite (tabla `SavedMessages`, máximo 5), y botón de envío masivo con confirmación previa.
- **Tab Contactos** (líneas 480-560): Treeview estilizado con columnas Hora/Duración/Nombre/Teléfono, formulario de alta con prefijo telefónico internacional, validaciones de campo vacío y formato numérico.
- **Tab Ajustes** (líneas 570-590): configuración del nombre del bar guardado en SQLite.

```python
# Validar campos obligatorios antes de insertar
nombre = self.entry_comp_contact_name.get().strip()
raw_phone = self.entry_comp_phone.get().strip()

if not nombre:
    messagebox.showwarning("Campo vacío", "El nombre del contacto es obligatorio.")
    return
if not raw_phone or len(raw_phone) < 9:
    messagebox.showwarning("Teléfono inválido", "Introduce un número de teléfono válido (mín. 9 dígitos).")
    return
```

La clase `Colors` centraliza el esquema de colores (líneas 47-57) y la clase `MenuAppLocal` hereda de `tk.Tk` con inicio maximizado.

---

### 6. Sistema de auto-actualización

Las líneas 127-200 de `menu_app.py` implementan un sistema de auto-actualización silenciosa:

1. `check_for_updates()` (thread en background) consulta la API de GitHub Releases del repo.
2. `is_newer()` compara las versiones semánticas (1.0.5 < 1.0.6).
3. `perform_update()` descarga el ZIP del release, lo extrae, genera un script batch (`updater.bat`) que sobrescribe los archivos y relanza la aplicación.

```python
def is_newer(self, remote_tag, current_tag):
    try:
        r = [int(x) for x in remote_tag.lstrip('v').split('.')]
        c = [int(x) for x in current_tag.lstrip('v').split('.')]
        return r > c
    except:
        return False
```

Además el `installer.py` (144 líneas) empaqueta todo como instalador auto-extraíble que además descarga el VC++ Redistributable.

---

### 7. Frontend — Tailwind CSS y accesibilidad

El estilo de la aplicación web se define en `src/app/globals.css` (líneas 1-30) importando Tailwind CSS 4 y definiendo variables CSS para modo claro/oscuro:

```css
@import "tailwindcss";

:root {
  --background: #ffffff;
  --foreground: #171717;
}
```

Se añadieron mejoras de accesibilidad con `*:focus-visible` para indicadores de foco visibles (outline azul) y transiciones globales suaves en enlaces y botones. El componente React usa clases de Tailwind como `backdrop-blur-md`, `shadow-lg`, `rounded-2xl`, etc. para un diseño moderno y profesional.

---

### 8. Página de Server Component — page.tsx

El archivo `src/app/page.tsx` (32 líneas) es un React Server Component (`export const dynamic = 'force-dynamic'`) que ejecuta queries Prisma directamente en el servidor:

```tsx
export default async function Home() {
  const bar = await prisma.bar.findFirst()
  const templates = bar 
    ? await prisma.messageTemplate.findMany({ where: { barId: bar.id } }) 
    : []
  const menus = await prisma.menu.findMany({
    include: { bar: true },
    orderBy: { createdAt: 'desc' },
    take: 10
  })
  const companies = await prisma.company.findMany({
    orderBy: { name: 'asc' }
  })
  return <MenuAppClient initialBar={bar} ... />
}
```

Este patrón de Next.js permite que el data fetching se haga en el servidor sin exponer las queries al cliente, pasando los datos como props al Client Component para la interactividad.

---

## Presentación del proyecto

MenuSpreader nace de una necesidad real: muchos bares y restaurantes envían manualmente su menú del día por WhatsApp a decenas de clientes cada mañana. Este proyecto automatiza completamente ese proceso.

La aplicación combina dos interfaces complementarias. La **app de escritorio** en Python ofrece una GUI sencilla donde el dueño del bar selecciona la imagen del menú, elige o redacta un mensaje personalizado, y con un solo clic envía a toda su lista de contactos. Internamente, el envío pasa por un **servidor bot de WhatsApp** basado en Node.js que mantiene la sesión de WhatsApp Web abierta — solo hay que escanear el QR una vez.

Por otro lado, la **interfaz web** construida con Next.js 16 y React 19 ofrece la misma funcionalidad con un diseño más moderno y responsive, usando Tailwind CSS 4 y Server Actions para comunicarse con la base de datos SQLite a través de Prisma ORM.

El sistema de **plantillas de mensaje** permite guardar frases frecuentes con la variable `{nombre}` que se reemplaza automáticamente por el nombre de cada contacto, creando un trato personalizado sin esfuerzo. La **base de datos local** almacena los contactos, los menús enviados y la configuración del negocio.

La app de escritorio incluye además un **sistema de auto-actualización** que consulta las GitHub Releases y se actualiza sola cuando hay una nueva versión, y un **instalador** que configura todo automáticamente incluyendo las dependencias del sistema.

Todo funciona en local — los datos del negocio nunca salen de su ordenador. El proyecto está publicado como software open source en GitHub con una landing page profesional que permite descargar el instalador directamente.

---

## Conclusión

MenuSpreader es un proyecto full-stack que demuestra cómo resolver un problema real combinando múltiples tecnologías: Next.js con Server Actions y Prisma para el panel web, Python con Tkinter y SQLite para la app de escritorio, y Node.js con whatsapp-web.js para la integración con WhatsApp.

Los puntos fuertes del proyecto son su arquitectura local-first (sin dependencias en la nube), el sistema de auto-actualización automática desde GitHub Releases, la gestión de plantillas con variables personalizables, y las validaciones de entrada tanto en el frontend web como en la app de escritorio.

Es un proyecto que podría usarse en producción real por cualquier bar o restaurante, lo cual demuestra que las tecnologías aprendidas en el módulo de Bases de Datos (SQLite, Prisma ORM, esquemas relacionales) tienen aplicación directa en soluciones para negocios reales. Gracias por la atención.
