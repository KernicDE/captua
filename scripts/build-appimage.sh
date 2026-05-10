#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${PROJECT_DIR}/build-appimage"
APPDIR="${BUILD_DIR}/AppDir"

LINUXDEPLOY_URL="https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
LINUXDEPLOY_QT_URL="https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-x86_64.AppImage"
PYTHON_BUILD_URL="https://github.com/indygreg/python-build-standalone/releases/download/20241016/cpython-3.12.7+20241016-x86_64-unknown-linux-gnu-install_only.tar.gz"

echo "=== Cleaning build directory ==="
rm -rf "${BUILD_DIR}"
mkdir -p "${APPDIR}/usr/bin" "${APPDIR}/usr/share/applications" "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

echo "=== Downloading portable Python ==="
cd "${BUILD_DIR}"
wget -q -O python.tar.gz "${PYTHON_BUILD_URL}"
tar -xzf python.tar.gz -C "${APPDIR}/usr" --strip-components=1
rm python.tar.gz

PYTHON="${APPDIR}/usr/bin/python3"
"${PYTHON}" -m ensurepip --upgrade
"${PYTHON}" -m pip install --upgrade pip

echo "=== Installing Python dependencies into AppDir ==="
"${PYTHON}" -m pip install \
    --prefix="${APPDIR}/usr" \
    --no-cache-dir \
    --ignore-installed \
    PySide6>=6.5.0 Pillow>=10.0.0

# Install the captua package itself
"${PYTHON}" -m pip install \
    --prefix="${APPDIR}/usr" \
    --no-cache-dir \
    --no-deps \
    "${PROJECT_DIR}"

echo "=== Locating site-packages ==="
SITE_PACKAGES=""
for sp in "${APPDIR}/usr/lib"/python*/site-packages "${APPDIR}/usr/local/lib"/python*/site-packages; do
    if [ -d "${sp}" ]; then
        SITE_PACKAGES="${sp}"
        break
    fi
done

if [ -z "${SITE_PACKAGES}" ]; then
    echo "ERROR: Could not find site-packages directory"
    find "${APPDIR}" -name "site-packages" -type d 2>/dev/null || true
    exit 1
fi

echo "Found site-packages: ${SITE_PACKAGES}"

echo "=== Creating AppRun ==="
cat > "${APPDIR}/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PYTHONPATH="${HERE}/usr/lib/python3.12/site-packages:${HERE}/usr/local/lib/python3.12/site-packages:${PYTHONPATH:-}"
export PATH="${HERE}/usr/bin:${PATH}"
export QT_QPA_PLATFORM=xcb
export QT_QPA_PLATFORMTHEME=gtk2
exec "${HERE}/usr/bin/python3" -m captua.main "$@"
EOF
chmod +x "${APPDIR}/AppRun"

echo "=== Copying desktop file ==="
cp "${PROJECT_DIR}/captua-overlay.desktop" "${APPDIR}/usr/share/applications/captua.desktop"
cp "${PROJECT_DIR}/captua-overlay.desktop" "${APPDIR}/captua.desktop"

echo "=== Creating placeholder icon ==="
touch "${APPDIR}/usr/share/icons/hicolor/256x256/apps/captua.png"

echo "=== Downloading linuxdeploy ==="
wget -q -O linuxdeploy "${LINUXDEPLOY_URL}"
wget -q -O linuxdeploy-plugin-qt "${LINUXDEPLOY_QT_URL}"
chmod +x linuxdeploy linuxdeploy-plugin-qt

echo "=== Setting up Qt paths for linuxdeploy-plugin-qt ==="
QMAKE_CANDIDATES=(
    "${SITE_PACKAGES}/PySide6/Qt6/bin/qmake"
    "${SITE_PACKAGES}/PySide6/Qt6/bin/qmake6"
)
QMAKE_PATH=""
for q in "${QMAKE_CANDIDATES[@]}"; do
    if [ -x "${q}" ]; then
        QMAKE_PATH="${q}"
        break
    fi
done

if [ -n "${QMAKE_PATH}" ]; then
    echo "Found qmake: ${QMAKE_PATH}"
    export QMAKE="${QMAKE_PATH}"
else
    echo "WARNING: qmake not found in PySide6; linuxdeploy-plugin-qt may not bundle all Qt libs"
fi

export LD_LIBRARY_PATH="${SITE_PACKAGES}/PySide6/Qt6/lib:${LD_LIBRARY_PATH:-}"

echo "=== Running linuxdeploy ==="
set +e
./linuxdeploy \
    --appdir="${APPDIR}" \
    --plugin=qt \
    --desktop-file="${APPDIR}/usr/share/applications/captua.desktop" \
    --executable="${APPDIR}/usr/bin/python3" \
    --icon-file="${APPDIR}/usr/share/icons/hicolor/256x256/apps/captua.png" \
    --output=appimage

LINUXDEPLOY_STATUS=$?
set -e

if [ ${LINUXDEPLOY_STATUS} -ne 0 ]; then
    echo "linuxdeploy with qt plugin failed; trying without qt plugin..."
    ./linuxdeploy \
        --appdir="${APPDIR}" \
        --desktop-file="${APPDIR}/usr/share/applications/captua.desktop" \
        --executable="${APPDIR}/usr/bin/python3" \
        --icon-file="${APPDIR}/usr/share/icons/hicolor/256x256/apps/captua.png" \
        --output=appimage
fi

echo "=== Moving AppImage to project root ==="
mv Captua-x86_64.AppImage "${PROJECT_DIR}/"

echo "=== Build complete: ${PROJECT_DIR}/Captua-x86_64.AppImage ==="
ls -lh "${PROJECT_DIR}/Captua-x86_64.AppImage"
