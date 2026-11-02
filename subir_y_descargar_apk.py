#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sube el proyecto a GitHub y descarga el APK compilado automáticamente.

Requisitos:
  - Python 3.8+
  - GitHub CLI (gh) — se instala automáticamente si no está
  - Git              — se instala automáticamente si no está (NEW v3)

Uso:
    python subir_y_descargar_apk.py
"""
import os
import sys
import time
import json
import shutil
import platform
import subprocess
import webbrowser

# ============================================================
# CONFIGURACIÓN
# ============================================================
REPO_NAME = "process-monitor-android"
REPO_DESC = "Monitor de procesos Android en tiempo real (CPU/RAM)"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
GITHUB_WORKFLOW_FILE = os.path.join(".github", "workflows", "build-apk.yml")
POLL_INTERVAL_SEC = 20
MAX_WAIT_MIN = 25
ARTIFACT_NAME = "ProcessMonitor-APK"

# Rutas típicas donde se instalan Git y gh en Windows (tras winget)
WINDOWS_GIT_PATHS = [
    r"C:\Program Files\Git\cmd",
    r"C:\Program Files\Git\bin",
    r"C:\Program Files (x86)\Git\cmd",
]
WINDOWS_GH_PATHS = [
    r"C:\Program Files\GitHub CLI",
    r"C:\Program Files (x86)\GitHub CLI",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\GitHub CLI"),
]


# ============================================================
# UTILIDADES
# ============================================================
def info(msg):
    print(f"\n  ℹ  {msg}")

def ok(msg):
    print(f"  ✅ {msg}")

def err(msg):
    print(f"  ❌ {msg}")

def warn(msg):
    print(f"  ⚠  {msg}")

def run(cmd, check=True, capture=False, cwd=None):
    """Ejecuta un comando. Si capture=True, devuelve stdout como string."""
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False
    try:
        result = subprocess.run(
            cmd, shell=shell, check=check,
            capture_output=capture, text=True, cwd=cwd
        )
        return result.stdout.strip() if capture else None
    except subprocess.CalledProcessError as e:
        if check:
            err(f"El comando falló: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
            if e.stderr:
                print(f"     stderr: {e.stderr.strip()}")
            raise
        return None


def check_command(name):
    """Devuelve True si el comando `name` está en el PATH."""
    return shutil.which(name) is not None


def refresh_windows_path():
    """Lee el PATH actual del registro de Windows y lo actualiza en este proceso."""
    if platform.system() != "Windows":
        return
    try:
        # Consultar el PATH actual del registro (Machine + User)
        import winreg
        machine_path = winreg.QueryValueEx(
            winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            "Path"
        )[0]
        user_path = winreg.QueryValueEx(
            winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment"),
            "Path"
        )[0]
        new_path = machine_path + ";" + user_path
        # Añadir rutas conocidas por si acaso
        for extra in WINDOWS_GIT_PATHS + WINDOWS_GH_PATHS:
            if extra not in new_path and os.path.isdir(extra):
                new_path = new_path + ";" + extra
        os.environ["PATH"] = new_path
    except Exception:
        # Fallback: añadir rutas conocidas a mano
        current = os.environ.get("PATH", "")
        for extra in WINDOWS_GIT_PATHS + WINDOWS_GH_PATHS:
            if extra not in current and os.path.isdir(extra):
                current = current + ";" + extra
        os.environ["PATH"] = current


# ============================================================
# INSTALACIÓN DE GIT (NEW v3)
# ============================================================
def install_git():
    """Instala Git automáticamente según el SO."""
    system = platform.system()
    info(f"Instalando Git para {system}...")

    if system == "Windows":
        # Probar winget (preinstalado en Win10/11)
        try:
            print("   → Usando winget (puede tardar 1-2 min)...")
            run("winget install --id Git.Git -e --silent "
                "--accept-source-agreements --accept-package-agreements",
                check=False)
            refresh_windows_path()
            if check_command("git"):
                return True
        except Exception as e:
            warn(f"winget falló: {e}")

        # Si winget no funcionó, dar instrucciones manuales
        err("No se pudo instalar Git automáticamente.")
        info("OPCIÓN RÁPIDA: descarga e instala Git desde:")
        print("     https://git-scm.com/download/win")
        info("Durante la instalación, deja todas las opciones por defecto.")
        info("Después CIERRA esta ventana y vuelve a ejecutar el .bat")
        return False

    elif system == "Darwin":  # macOS
        if check_command("brew"):
            run("brew install git")
            return check_command("git")
        warn("Necesitas Homebrew. Instálalo desde https://brew.sh")
        return False

    elif system == "Linux":
        if check_command("apt"):
            run("sudo apt update && sudo apt install -y git", check=False)
            return check_command("git")
        elif check_command("dnf"):
            run("sudo dnf install -y git")
            return check_command("git")
        elif check_command("pacman"):
            run("sudo pacman -S --noconfirm git")
            return check_command("git")
        return False

    return False


def ensure_git():
    """Comprueba que git está disponible; si no, intenta instalarlo."""
    if check_command("git"):
        version = run("git --version", capture=True)
        ok(f"Git encontrada: {version}")
        return True

    warn("Git NO está instalado. Intentando instalar automáticamente...")
    if install_git():
        version = run("git --version", capture=True)
        ok(f"Git instalado: {version}")
        return True
    return False


# ============================================================
# INSTALACIÓN DE GITHUB CLI
# ============================================================
def install_gh_cli():
    system = platform.system()
    info(f"Instalando GitHub CLI para {system}...")

    if system == "Windows":
        try:
            print("   → Usando winget (puede tardar 1-2 min)...")
            run("winget install --id GitHub.cli -e --silent "
                "--accept-source-agreements --accept-package-agreements",
                check=False)
            refresh_windows_path()
            if check_command("gh"):
                return True
        except Exception as e:
            warn(f"winget falló: {e}")
        info("Descarga manual desde: https://cli.github.com")
        return False

    elif system == "Darwin":
        if check_command("brew"):
            run("brew install gh")
            return check_command("gh")
        warn("Necesitas Homebrew. Instálalo desde https://brew.sh")
        return False

    elif system == "Linux":
        if check_command("apt"):
            run("sudo apt update && sudo apt install -y gh", check=False)
            return check_command("gh")
        elif check_command("dnf"):
            run("sudo dnf install -y gh")
            return check_command("gh")
        elif check_command("pacman"):
            run("sudo pacman -S --noconfirm github-cli")
            return check_command("gh")
        return False

    return False


def ensure_gh():
    if not check_command("gh"):
        if not install_gh_cli():
            err("No se pudo instalar GitHub CLI.")
            info("Instálalo manualmente desde https://cli.github.com")
            return False
        if platform.system() == "Windows":
            refresh_windows_path()
        if not check_command("gh"):
            err("GitHub CLI instalada pero no está en PATH.")
            info("Cierra y abre de nuevo esta terminal, o reinicia el script.")
            return False

    ok("GitHub CLI encontrada.")
    return True


# ============================================================
# AUTENTICACIÓN
# ============================================================
def ensure_gh_authed():
    auth_status = run("gh auth status", check=False, capture=True)
    if "Logged in to github.com" in (auth_status or ""):
        user = run("gh api user --jq .login", capture=True)
        ok(f"Ya autenticado como: {user}")
        return True

    print()
    print("  " + "=" * 60)
    print("  🔑 AUTENTICACIÓN EN GITHUB — LEE ESTO ANTES DE CONTINUAR")
    print("  " + "=" * 60)
    print()
    print("  En unos segundos vas a ver en esta ventana un texto como:")
    print()
    print("     ! First copy your one-time code: 1A2B-3C4D")
    print("     ! Press Enter to open github.com in your browser...")
    print()
    print("  ESE CÓDIGO (XXXX-XXXX) es el que tienes que pegar en la web")
    print("  'Authorize your device' que se abrirá sola.")
    print()
    print("  DESPUÉS de pegar el código en la web:")
    print("    1. Pulsa el botón verde 'Authorize github'")
    print("    2. Verás: 'Congratulations, you're all set!'")
    print("    3. Vuelve a ESTA ventana y pulsa ENTER cuando te lo pida")
    print()
    print("  ⚠  NO cierres esta ventana hasta ver 'Autenticado como:...'")
    print()
    input("  Pulsa ENTER cuando hayas leído esto para continuar...")
    print()

    subprocess.run("gh auth login --web --git-protocol https", shell=True)

    auth_status = run("gh auth status", check=False, capture=True)
    if "Logged in to github.com" not in (auth_status or ""):
        print()
        err("La autenticación falló o se interrumpió.")
        info("Si crees que sí te autenticaste, vuelve a ejecutar este script.")
        return False
    user = run("gh api user --jq .login", capture=True)
    print()
    ok(f"Autenticado como: {user}")
    return True


# ============================================================
# CREAR REPO Y SUBIR
# ============================================================
def write_gitignore():
    """Escribe el .gitignore (ampliado para no subir __pycache__)."""
    gitignore = """\
# Build outputs
build/
.gradle/
local.properties
*.iml
.idea/
captures/
.cxx/
apk_descargado/

# Python
__pycache__/
*.pyc
*.pyo

# macOS / Windows
.DS_Store
Thumbs.db
"""
    with open(os.path.join(PROJECT_DIR, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(gitignore)


def setup_git_local():
    """Inicializa git local + config user si no está configurado."""
    if not os.path.isdir(os.path.join(PROJECT_DIR, ".git")):
        info("Inicializando repositorio git local...")
        run("git init", cwd=PROJECT_DIR)
        # Renombrar rama a main (algunos Git viejos usan master)
        run("git branch -M main", cwd=PROJECT_DIR, check=False)
        # Configurar user/email si no están
        name = run("git config --global user.name", check=False, capture=True)
        if not name:
            run('git config --global user.name "Process Monitor"', check=False)
            run('git config --global user.email "process@monitor.local"',
                check=False)
        # Evitar avisos de LF->CRLF molestos en Windows
        run("git config core.autocrlf true", cwd=PROJECT_DIR, check=False)


def make_initial_commit():
    """Crea el commit inicial con todos los ficheros."""
    info("Haciendo commit de los ficheros...")
    # Borrar rastros de __pycache__ si se subieron antes (silencioso)
    run("git rm -r --cached __pycache__ --ignore-unmatch",
        cwd=PROJECT_DIR, check=False)
    run("git rm -r --cached .pytest_cache --ignore-unmatch",
        cwd=PROJECT_DIR, check=False)

    run("git add -A", cwd=PROJECT_DIR)

    # ¿Hay algo que commitear?
    has_changes = run("git diff --cached --quiet", check=False, capture=True)
    if has_changes is None:
        # Retorno None/"" -> ya estaba en quiet (no hay cambios)
        ok("Sin cambios nuevos que commitear.")
        return

    run('git commit -m "Subida inicial: Monitor de procesos Android"',
        cwd=PROJECT_DIR, check=False)
    ok("Commit creado.")


def create_or_reuse_remote():
    """
    Crea el repo en GitHub si no existe, o lo reutiliza.
    Devuelve la URL del repo y el usuario.
    """
    user = run("gh api user --jq .login", capture=True)
    if not user:
        err("No se pudo obtener el usuario de GitHub.")
        sys.exit(1)

    existing = run(f"gh repo view {user}/{REPO_NAME} --json name -q .name",
                   check=False, capture=True)
    repo_exists = existing == REPO_NAME

    if repo_exists:
        warn(f"El repo '{REPO_NAME}' ya existe en tu cuenta.")
        info("Se hará commit + push de los cambios (sin borrar el repo).")
        resp = input("  ¿Quieres BORRARLO y crearlo limpio? [s/N]: ").strip().lower()
        if resp in ("s", "si", "sí", "y", "yes"):
            info("Borrando repo existente...")
            run(f"gh repo delete {user}/{REPO_NAME} --yes", check=False)
            repo_exists = False

    if not repo_exists:
        info(f"Creando repositorio público '{REPO_NAME}' en GitHub...")
        # IMPORTANTE: NO usar --push aquí porque falla cuando todavía no hay commits.
        # Creamos el repo vacío, configuramos remote, hacemos commit, y luego push.
        run(f'gh repo create {user}/{REPO_NAME} --public --description "{REPO_DESC}"',
            check=False)
        ok("Repo creado (vacío).")

    # Asegurar remote configurado (siempre, por si ya existía)
    run("git remote remove origin", cwd=PROJECT_DIR, check=False)
    remote_url = f"https://github.com/{user}/{REPO_NAME}.git"
    run(f"git remote add origin {remote_url}", cwd=PROJECT_DIR, check=False)
    ok(f"Remote configurado: {remote_url}")

    return remote_url, user


def push_to_github():
    """Sube el código al remote origin."""
    info("Subiendo a GitHub (push)...")
    # Forzar autenticación vía gh (crea helper en git config)
    run("gh auth setup-git", check=False)

    for intento in range(1, 4):
        # Intentar push normal
        result = run("git push -u origin main",
                     cwd=PROJECT_DIR, check=False, capture=True)
        err_out = ""
        # Capturar stderr del push para análisis
        full_cmd = "git push -u origin main 2>&1"
        full_result = subprocess.run(full_cmd, shell=True, capture_output=True,
                                     text=True, cwd=PROJECT_DIR)
        combined = (full_result.stdout or "") + (full_result.stderr or "")

        if full_result.returncode == 0:
            ok("Código subido correctamente.")
            return True

        # Si es "rejected (fetch first)" -> hay cambios remotos, hacer pull
        if "rejected" in combined and "fetch first" in combined:
            warn("El repo remoto tiene commits previos. Haciendo pull y merge...")
            run("git pull origin main --no-rebase --allow-unrelated-histories -X theirs",
                cwd=PROJECT_DIR, check=False, capture=True)
            # Reintentar push
            continue

        # Si es "non-fast-forward" tras pull, forzar (nuestro commit es el bueno)
        if "non-fast-forward" in combined or "rejected" in combined:
            warn(f"Push intento {intento}/3 falló. Forzando push...")
            force_result = subprocess.run(
                "git push -u origin main --force-with-lease 2>&1",
                shell=True, capture_output=True, text=True, cwd=PROJECT_DIR
            )
            if force_result.returncode == 0:
                ok("Código subido correctamente (force push).")
                return True

        warn(f"Push intento {intento}/3 falló. Reintentando en 5s...")
        time.sleep(5)

    err("No se pudo hacer push tras 3 intentos.")
    info("Puedes hacer el push a mano con:")
    print("     git push -u origin main --force-with-lease")
    return False


def create_and_push_repo():
    """Flujo completo: init → commit → crear repo → push."""
    # 1. Configuración local
    setup_git_local()
    write_gitignore()

    # 2. Verificar workflow
    if not os.path.isfile(os.path.join(PROJECT_DIR, GITHUB_WORKFLOW_FILE)):
        err(f"No se encuentra el workflow: {GITHUB_WORKFLOW_FILE}")
        err("Asegúrate de ejecutar este script desde dentro de la carpeta ProcessMonitor.")
        sys.exit(1)
    ok("Workflow encontrado.")

    # 3. Commit PRIMERO (antes de gh repo create)
    make_initial_commit()

    # 4. Crear/reutilizar repo y configurar remote
    remote_url, user = create_or_reuse_remote()

    # 5. Push al repo
    push_to_github()

    ok(f"Repo público: {remote_url}")
    return remote_url


# ============================================================
# LANZAR Y ESPERAR
# ============================================================
def trigger_workflow():
    """Dispara el workflow manualmente. Tolerante a 404 (aún no indexado)."""
    info("Lanzando workflow de compilación...")
    # GitHub tarda unos segundos en indexar el workflow tras el push
    for intento in range(1, 6):
        time.sleep(5)
        result = run("gh workflow run build-apk.yml --ref main",
                     cwd=PROJECT_DIR, check=False, capture=True)
        if result is None or "404" in (result or "") or "not found" in (result or "").lower():
            warn(f"Workflow aún no indexado, reintentando ({intento}/5)...")
            continue
        ok("Workflow lanzado.")
        return True
    err("No se pudo lanzar el workflow tras 5 intentos.")
    info("Posiblemente el push no se completó. Verifica tu repo:")
    user = run("gh api user --jq .login", capture=True)
    print(f"     https://github.com/{user}/{REPO_NAME}")
    return False


def wait_for_completion():
    """Polling del workflow hasta terminar. Tolerante a 404 inicial."""
    info(f"Esperando a que termine la compilación (máx {MAX_WAIT_MIN} min)...")
    print()
    deadline = time.time() + MAX_WAIT_MIN * 60
    last_status = None
    errors_404 = 0

    while time.time() < deadline:
        # IMPORTANTE: check=False para que no reviente si GitHub devuelve 404
        run_json = run(
            f"gh run list --workflow=build-apk.yml --limit 1 --json status,conclusion,databaseId",
            check=False, capture=True, cwd=PROJECT_DIR
        )
        # Si la respuesta contiene "404" o está vacía, esperar y reintentar
        if not run_json or "404" in run_json or "not found" in run_json.lower():
            errors_404 += 1
            if errors_404 <= 6:
                warn("Workflow aún no aparece en GitHub, esperando 10s...")
                time.sleep(10)
                continue
            else:
                err("El workflow no aparece tras 60s. Revisa:")
                user = run("gh api user --jq .login", capture=True)
                print(f"     https://github.com/{user}/{REPO_NAME}/actions")
                sys.exit(1)

        try:
            data = json.loads(run_json)
        except Exception:
            time.sleep(POLL_INTERVAL_SEC)
            continue

        if not data:
            time.sleep(POLL_INTERVAL_SEC)
            continue

        run_data = data[0]
        status = run_data["status"]
        conclusion = run_data.get("conclusion")
        run_id = run_data["databaseId"]

        if status != last_status:
            print()
            if status == "queued":
                info("Compilación en cola...")
            elif status == "in_progress":
                info("Compilando APK en la nube de GitHub...")
            last_status = status

        if status == "completed":
            print()
            if conclusion == "success":
                ok("¡Compilación exitosa!")
                return run_id
            else:
                err(f"La compilación falló (conclusion: {conclusion})")
                info("Revisa los logs:")
                user = run("gh api user --jq .login", capture=True)
                print(f"     https://github.com/{user}/{REPO_NAME}/actions")
                sys.exit(1)

        print(".", end="", flush=True)
        time.sleep(POLL_INTERVAL_SEC)

    print()
    err("Se agotó el tiempo de espera.")
    user = run("gh api user --jq .login", capture=True)
    print(f"     https://github.com/{user}/{REPO_NAME}/actions")
    sys.exit(1)


def download_artifact(run_id):
    info(f"Descargando APK compilado (run {run_id})...")
    artifact_dir = os.path.join(PROJECT_DIR, "apk_descargado")
    if os.path.isdir(artifact_dir):
        shutil.rmtree(artifact_dir)
    os.makedirs(artifact_dir, exist_ok=True)

    run(f"gh run download {run_id} -n {ARTIFACT_NAME} -D {artifact_dir}",
        cwd=PROJECT_DIR)

    apk_path = None
    for root, dirs, files in os.walk(artifact_dir):
        for f in files:
            if f.endswith(".apk"):
                apk_path = os.path.join(root, f)
                break
        if apk_path:
            break

    if not apk_path:
        err("No se encontró ningún APK en el artifact descargado.")
        sys.exit(1)

    final_apk = os.path.join(PROJECT_DIR, "app-debug.apk")
    shutil.copy(apk_path, final_apk)
    ok(f"APK descargado: {final_apk}")

    size_mb = os.path.getsize(final_apk) / (1024 * 1024)
    print()
    print("  " + "=" * 60)
    print(f"  📱 APK LISTO: {os.path.basename(final_apk)}  ({size_mb:.1f} MB)")
    print("  " + "=" * 60)
    print(f"  Ruta completa: {final_apk}")
    print()
    print("  Siguientes pasos:")
    print("   1. Transfiere este archivo a tu móvil Android")
    print("   2. En el móvil activa 'Instalar apps desconocidas'")
    print("   3. Ábrelo desde el gestor de archivos → Instalar")
    print()
    return final_apk


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================
def main():
    print()
    print("  " + "=" * 60)
    print("  🚀 SUBIDA AUTOMÁTICA A GITHUB + DESCARGA APK (v3)")
    print("  " + "=" * 60)
    print()
    print(f"  Carpeta del proyecto: {PROJECT_DIR}")
    print(f"  Nombre del repo:      {REPO_NAME}")
    print()

    if not os.path.isfile(os.path.join(PROJECT_DIR, "settings.gradle.kts")):
        err("No estás en la carpeta del proyecto Android.")
        info("Ejecuta este script DESDE DENTRO de la carpeta 'ProcessMonitor/'.")
        sys.exit(1)

    # === PASO 1: Asegurar Git (NEW v3) ===
    print()
    print("  " + "-" * 60)
    print("  PASO 1/4: Comprobar Git")
    print("  " + "-" * 60)
    if not ensure_git():
        err("Git no está disponible y no se pudo instalar automáticamente.")
        info("Instálalo manualmente desde https://git-scm.com/download/win")
        info("y vuelve a ejecutar este script.")
        sys.exit(1)

    # === PASO 2: Asegurar GitHub CLI ===
    print()
    print("  " + "-" * 60)
    print("  PASO 2/4: Comprobar GitHub CLI")
    print("  " + "-" * 60)
    if not ensure_gh():
        sys.exit(1)

    # === PASO 3: Autenticar ===
    print()
    print("  " + "-" * 60)
    print("  PASO 3/4: Autenticación GitHub")
    print("  " + "-" * 60)
    if not ensure_gh_authed():
        sys.exit(1)

    # === PASO 4: Crear repo, subir, compilar, descargar ===
    print()
    print("  " + "-" * 60)
    print("  PASO 4/4: Subir y compilar")
    print("  " + "-" * 60)
    create_and_push_repo()
    trigger_workflow()
    run_id = wait_for_completion()
    download_artifact(run_id)

    print()
    print("  ¿Quieres abrir la página de Actions en el navegador? [s/N]: ", end="")
    resp = input().strip().lower()
    if resp in ("s", "si", "sí", "y", "yes"):
        user = run("gh api user --jq .login", capture=True)
        url = f"https://github.com/{user}/{REPO_NAME}/actions"
        try:
            webbrowser.open(url)
        except Exception:
            pass

    print()
    ok("¡Todo terminado! Disfruta tu app. 🎉")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⛔ Interrumpido por el usuario.")
        sys.exit(1)
