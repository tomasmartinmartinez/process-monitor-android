#!/usr/bin/env bash
# ============================================================
#   Un solo comando para: subir a GitHub + descargar APK
#   Uso:   ./_1CLICK_subir_y_descargar.sh
# ============================================================
set -e

cd "$(dirname "$0")"

echo
echo "============================================================"
echo "  🚀 SUBIDA AUTOMÁTICA A GITHUB + DESCARGA APK (v3)"
echo "============================================================"
echo
echo "Carpeta: $(pwd)"
echo

if ! command -v python3 >/dev/null 2>&1; then
    if ! command -v python >/dev/null 2>&1; then
        echo "❌ No se encuentra Python."
        echo "   Instálalo con: sudo apt install python3   (Linux)"
        echo "   o: brew install python                    (macOS)"
        exit 1
    fi
    PY=python
else
    PY=python3
fi

$PY subir_y_descargar_apk.py

echo
echo "============================================================"
echo "  Fin del proceso. Pulsa ENTER para cerrar."
echo "============================================================"
read
