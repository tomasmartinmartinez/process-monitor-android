# Monitor de Procesos Android

App Android (Kotlin) que muestra en tiempo real los procesos que se están
ejecutando en el dispositivo, con su uso de CPU, RAM, hilos y estado.

## ✅ Compilar SIN Android Studio (lo más fácil)

### Opción recomendada: GitHub Actions (gratis, en la nube)

NO necesitas instalar NADA en tu PC. Solo un navegador y una cuenta de
GitHub (gratis).

**Pasos:**

1. Entra en https://github.com y crea cuenta (si no tienes).
2. Crea un **nuevo repositorio** → `New repository`:
   - Nombre: `process-monitor` (o el que quieras)
   - Público o privado (ambos funcionan)
   - **No** marques ninguna opción de README/gitignore
3. Sube los ficheros del proyecto:
   - En la página vacía del repo, arrastra **todos los ficheros** de la
     carpeta `ProcessMonitor/` (incluida la subcarpeta `.github/`).
   - GitHub te permite arrastrar varios a la vez.
   - Importante: la carpeta `.github` está oculta en algunos exploradores,
     asegúrate de incluirla (contiene el workflow que compila el APK).
   - Pulsa `Commit changes`.
4. Ve a la pestaña **`Actions`** del repositorio.
5. A la izquierda verás "Build APK" → haz clic.
6. Si no se ejecutó solo, pulsa el botón **`Run workflow`** (a la derecha).
7. Espera **5-10 minutos** a que termine (aparece un ✓ verde).
8. Haz clic en la ejecución completada.
9. En la parte inferior del resumen verás **`Artifacts`** → descarga
   `ProcessMonitor-APK` → descomprime el ZIP → ahí está tu `app-debug.apk`.
10. Transfiere el APK a tu móvil y ábrelo desde el gestor de archivos.

**¿Límites gratis?** GitHub Actions da 2.000 minutos/mes gratis para
repositorios públicos. Una compilación tarda ~7 minutos → puedes compilar
~280 APKs al mes sin coste.

---

## Otras opciones SIN Android Studio

### B) Línea de comandos en tu PC (Linux/Mac/WSL en Windows)

Requiere instalar JDK 17 + Android SDK command-line tools (~500 MB, menos
que Android Studio pero aún algo):

```bash
# 1. Instalar JDK 17
sudo apt install openjdk-17-jdk        # Ubuntu/Debian
# En Windows: https://adoptium.net (descarga el MSI)

# 2. Instalar Android command-line tools (no Android Studio completo)
#    https://developer.android.com/tools (apartado "Command line tools only")

# 3. Compilar:
cd ProcessMonitor
./gradlew assembleDebug
# APK en: app/build/outputs/apk/debug/app-debug.apk
```

### C) Usar un contenedor Docker

```bash
docker run --rm -v "$PWD":/home/gradle/project \
    -w /home/gradle/project \
    ghcr.io/cirruslabs/android:34 \
    ./gradlew assembleDebug
```

### D) Termux (compilar EN el propio móvil Android)

```bash
# En tu móvil con Termux instalado:
pkg install openjdk-17 git
git clone https://github.com/tu-usuario/process-monitor
cd process-monitor
chmod +x gradlew
./gradlew assembleDebug
# APK en: app/build/outputs/apk/debug/app-debug.apk
```

⚠ Termux no tiene Android SDK completo, así que esto puede requerir
ajustes. Solo recomendado si eres valiente.

---

## (Opcional) Ver TODOS los procesos del sistema

Sin root, Android limita la lectura de procesos ajenos. Para verlos,
concede el permiso `DUMP` vía ADB (depuración USB activada en el móvil):

```bash
adb shell pm grant com.example.processmonitor android.permission.DUMP
```

Después, la app podrá leer todos los procesos (`/proc/[pid]/` accesible).

## Cómo funciona el cálculo de % CPU

1. Lee `/proc/[pid]/stat` (campos 14 `utime` + 15 `stime` = tiempo total de CPU
   que ha usado ese proceso desde su arranque, en clock ticks).
2. Lee `/proc/stat` primera línea `cpu  user nice system idle ...` = tiempo
   total de CPU del sistema desde el arranque.
3. Calcula la **diferencia** entre la lectura actual y la anterior (2 s antes).
4. % CPU = (Δ tiempo proceso / Δ tiempo total) × 100 × núcleos

La primera lectura (sin dato anterior) muestra 0% — el cálculo real empieza
en la segunda iteración (2 s después).

## Estructura del proyecto

```
ProcessMonitor/
├── .github/workflows/
│   └── build-apk.yml                  ← workflow GitHub Actions
├── app/
│   ├── build.gradle.kts
│   ├── proguard-rules.pro
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/com/example/processmonitor/
│       │   ├── model/ProcessInfo.kt
│       │   ├── service/ProcessMonitor.kt    ← lectura /proc
│       │   └── ui/
│       │       ├── MainActivity.kt          ← pantalla + refresco
│       │       └── ProcessAdapter.kt        ← adapter RecyclerView
│       └── res/
│           ├── drawable/                    ← iconos vectoriales
│           ├── layout/                      ← activity_main, item_process
│           ├── menu/                        ← opciones de ordenación
│           ├── mipmap-anydpi-v26/           ← icono adaptativo
│           └── values/                      ← strings, colors, themes
├── build.gradle.kts
├── gradle.properties
├── gradle/wrapper/
│   ├── gradle-wrapper.jar
│   └── gradle-wrapper.properties
├── gradlew                              ← script Unix
├── gradlew.bat                          ← script Windows
└── settings.gradle.kts
```

## Permisos

- `INTERNET` — No se usa para conexión, pero Android lo requiere si alguna
  vez añades sincronización en nube. Puedes quitarlo.
- `DUMP` — Para ver procesos de sistema (concede vía ADB).
  Sin él, la app funciona igual pero solo ve procesos del usuario actual.

## Requisitos mínimos

- Android 8.0 (API 26) o superior
- ~5 MB de espacio

## Próximas mejoras posibles

- Gráfico histórico de CPU por proceso
- Detalle al hacer tap (memoria detallada, fds abiertos, etc.)
- Matar proceso (requiere root o permisos especiales)
- Exportar lista a CSV
- Widget de home screen con el top proceso
