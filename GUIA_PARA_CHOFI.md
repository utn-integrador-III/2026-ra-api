# Guía para correr PathAR (backend + frontend) — para Chofi

Esta guía te deja el backend y el frontend corriendo en tu compu, con un usuario
admin para que puedas cargar destinos y aceras y probar la app de verdad.
Seguí los pasos en orden, no te saltes ninguno.

---

## Parte 1 — Instalar WSL con Ubuntu

El backend corre en Linux, así que primero necesitás "Linux dentro de Windows"
(se llama WSL). Si ya lo tenés instalado, saltate a la Parte 2.

1. Abrí **PowerShell como administrador** (clic derecho → "Ejecutar como administrador").
2. Corré:
   ```
   wsl --install -d Ubuntu-24.04
   ```
3. Te va a pedir reiniciar la compu. Reiniciá.
4. Al reiniciar, se abre solo una ventana de Ubuntu pidiéndote crear un
   usuario y contraseña — ponele lo que quieras, es solo para vos, dentro de
   esa Ubuntu (no tiene que ver con tu contraseña de Windows). **Anotala**,
   la vas a necesitar seguido.

Desde ahora, cada vez que esta guía diga "en Ubuntu" o "en WSL", abrí el
menú de Windows, escribí "Ubuntu" y abrí esa terminal.

---

## Parte 2 — Bajar y preparar el backend

Todo esto es **dentro de la ventana de Ubuntu**, no en PowerShell.

1. Cloná el repo (poné tu propia carpeta si querés, esto es un ejemplo):
   ```
   cd ~
   git clone https://github.com/utn-integrador-III/2026-ra-api.git
   cd 2026-ra-api
   ```
2. Corré el script que instala todo (Python, PostgreSQL, dependencias):
   ```
   bash setup.sh
   ```
   Te va a pedir tu contraseña de Ubuntu un par de veces (es normal, es para
   instalar cosas). Cuando termina, dice "✅ Setup completo."

3. Creá tu archivo de configuración:
   ```
   cp .env.example .env
   ```
   Con eso ya queda funcionando para la base de datos y el login normal
   (usuario/contraseña). **No hace falta que edites nada de `.env` para
   arrancar** — los valores de ejemplo ya coinciden con lo que crea `setup.sh`.

4. **El login con Google no va a funcionar todavía** — para eso hace falta un
   archivo con credenciales que no se sube a GitHub por seguridad
   (`firebase-service-account.json`). Pedile ese archivo por privado (Discord,
   WhatsApp, lo que sea — **nunca lo subas a GitHub**) a algún compañero, y
   ponelo en la raíz del proyecto, junto al `.env`:
   ```
   ~/2026-ra-api/firebase-service-account.json
   ```
   Si todavía no lo tenés, no pasa nada — podés probar toda la app igual con
   el login normal (correo y contraseña), y agregás Google después.

---

## Parte 3 — Arrancar el backend

1. En Ubuntu, dentro de la carpeta del proyecto:
   ```
   cd ~/2026-ra-api
   source .venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Deberías ver algo como:
   ```
   ✓ Tablas creadas/verificadas en la BD
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```
   **Dejá esta ventana abierta** — mientras la tengas abierta así, el backend
   está corriendo. Si la cerrás, se apaga.
3. Probá que funciona: abrí un navegador (en Windows, normal) y entrá a
   `http://localhost:8000/docs` — si ves una página con la lista de todos los
   endpoints de la API, está funcionando.

---

## Parte 4 — Crear tu usuario admin

Sin esto no vas a poder cargar destinos ni aceras. Se hace en dos pasos:
registrarte como usuario normal, y después "ascenderte" a admin directo en
la base de datos (no hay botón para esto, es a propósito, por seguridad).

1. Registrate como usuario normal desde el navegador, en
   `http://localhost:8000/docs`:
   - Buscá **POST /api/auth/register**, hacé clic, "Try it out".
   - Completá con tus datos, por ejemplo:
     ```json
     {
       "name": "Chofi",
       "email": "chofi@pathar.com",
       "password": "unaContraseñaCualquiera123"
     }
     ```
   - "Execute". Si te devuelve un `access_token`, ya quedaste registrada.

2. Ahora convertí ese usuario en admin. **Abrí otra ventana de Ubuntu**
   (dejá la del backend corriendo) y entrá a la base de datos:
   ```
   psql -U pathar_user -d pathar_db -h localhost -p 5432
   ```
   Te pide contraseña: `pathar_password` (la que puso `setup.sh` por defecto).

3. Ya adentro de `psql`, corré (con el MISMO correo que usaste al registrarte):
   ```sql
   UPDATE users SET role = 'admin' WHERE email = 'chofi@pathar.com';
   ```
   Debería decir `UPDATE 1`. Salí con `\q`.

Listo, ese correo/contraseña ya es admin.

---

## Parte 5 — Cargar datos con el panel de administración

Esto es lo más importante de todo: **sin esto, la app no va a poder calcular
ninguna ruta**, por más que todo lo demás esté bien. La app no "inventa"
caminos — necesita que vos le enseñes primero por dónde se puede caminar.

1. En el navegador, andá a `http://localhost:8000/admin/`
2. Iniciá sesión con el correo/contraseña que acabás de convertir en admin.
3. Vas a ver un mapa con dos pestañas en el costado:

   **📍 Ubicaciones** — son los destinos que la gente va a poder buscar en la
   app (aulas, laboratorios, cafetería, etc.). Tocá "➕ Nueva", completá
   nombre y coordenadas (o hacé clic en el mapa para tomar la posición), y
   guardá.

   **🚶 Aceras** — esto es el "camino caminable" que usa la app para trazar
   rutas. Tiene 3 modos (botones arriba del mapa):
   - **➕ Agregar nodo**: hacé clic en el mapa en cada esquina/punto por
     donde se puede caminar (como poner "postes" a lo largo de las aceras
     reales del campus).
   - **🔗 Conectar dos nodos**: hacé clic en un nodo y después en otro para
     unirlos con un tramo caminable (así el sistema sabe que esos dos puntos
     están conectados por una acera real).
   - **🖱️ Ver / eliminar**: para revisar o borrar lo que ya pusiste.

   Tenés que armar una **red conectada** de nodos y tramos que cubra
   más o menos el campus (o al menos la zona donde vayas a probar). Con
   poner una ruta de prueba (unos 5-10 nodos conectados en fila cerca de
   donde vayas a caminar) alcanza para probar la app.

Si intentás navegar a un lugar y te dice "No hay un camino caminable entre
origen y destino" o "No hay aceras registradas todavía", es porque falta esto.

---

## Parte 6 — Bajar y correr el frontend

1. Instalá Flutter si no lo tenés: https://docs.flutter.dev/get-started/install
2. Cloná el repo del frontend (en Windows, no en Ubuntu):
   ```
   git clone https://github.com/utn-integrador-III/2026-ra-fe.git
   cd 2026-ra-fe
   flutter pub get
   ```
3. Abrí el archivo `.env` (en la raíz del proyecto) y cambiá la IP para que
   apunte a tu backend. Tenés dos caminos, elegí el más fácil para vos:

   **Opción A — con un emulador de Android (la más fácil, recomendada)**

   Si tenés Android Studio con un emulador, no hay que configurar nada de
   red. Dejá el `.env` así:
   ```
   API_URL=http://10.0.2.2:8000
   ```
   `10.0.2.2` es una dirección especial que el emulador usa automáticamente
   para "tu propia compu" — como WSL reenvía el puerto 8000 solo, esto
   funciona directo, sin tocar nada más.

   **Opción B — con tu celular real (más delicada)**

   Necesitás la IP de tu compu en la red WiFi, y que el celular esté en
   **la misma red y banda de WiFi** que la compu (si el router separa 2.4GHz
   y 5GHz en dos redes distintas, tenés que estar en la misma). Buscá tu IP:
   ```
   ipconfig
   ```
   (mirá la de "Wi-Fi", algo como `192.168.x.x`) y poné en `.env`:
   ```
   API_URL=http://192.168.x.x:8000
   ```
   Si aun así el celular no conecta, puede ser que el router tenga activado
   "aislamiento de clientes" (bloquea que los dispositivos de la misma red
   se vean entre sí) — avisale a Ahian si te pasa esto, ya lo debatimos y
   tiene solución pero depende de la configuración de tu router.

4. Corré la app:
   ```
   flutter run
   ```
   Elegí el emulador o el celular conectado cuando te pregunte.

---

## Resumen — cada vez que quieras probar la app

1. Abrí Ubuntu → `cd ~/2026-ra-api && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
2. Dejá esa ventana abierta.
3. En Windows → `cd 2026-ra-fe && flutter run`

Con eso ya tenés todo funcionando: backend, base de datos, panel de admin
para cargar destinos/aceras, y la app corriendo contra tu propio backend.
