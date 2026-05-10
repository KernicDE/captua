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

# Fix Pillow bundled libs: linuxdeploy can't resolve deps when SONAMEs have hash suffixes
PILLOW_LIBS="${SITE_PACKAGES}/pillow.libs"
if [ -d "${PILLOW_LIBS}" ]; then
    echo "=== Creating symlinks for Pillow bundled libraries ==="
    cd "${PILLOW_LIBS}"
    for f in lib*.so*; do
        # e.g. libsharpyuv-0bacc318.so.0.1.2 -> create libsharpyuv.so.0, libsharpyuv.so.0.1, etc.
        if [[ "${f}" =~ ^(lib[a-zA-Z0-9]+)-[a-f0-9]+\.so(\.([0-9]+)(\.([0-9]+)(\.([0-9]+))?)?)?$ ]]; then
            base="${BASH_REMATCH[1]}"
            suffix="${BASH_REMATCH[2]}"
            if [ -n "${suffix}" ] && [ ! -e "${base}${suffix}" ]; then
                ln -sf "${f}" "${base}${suffix}"
            fi
        fi
    done
    cd "${BUILD_DIR}"
    export LD_LIBRARY_PATH="${PILLOW_LIBS}:${LD_LIBRARY_PATH}"
fi

# Remove unnecessary PySide6 modules and Qt tools to avoid linuxdeploy
# scanning ELF files with missing system dependencies (libpcsclite, libpulse, etc.)
echo "=== Removing unnecessary PySide6 modules ==="
PYSIDE6_DIR="${SITE_PACKAGES}/PySide6"
if [ -d "${PYSIDE6_DIR}" ]; then
    # Keep only essential .abi3.so files; QtNetwork/QtDBus are often needed indirectly
    for f in "${PYSIDE6_DIR}"/*.abi3.so; do
        [ -e "${f}" ] || continue
        basename=$(basename "${f}")
        case "${basename}" in
            QtCore.abi3.so|QtGui.abi3.so|QtWidgets.abi3.so|QtNetwork.abi3.so|QtDBus.abi3.so)
                ;;
            *)
                rm -f "${f}"
                ;;
        esac
    done

    # Remove Qt tools and extra executables that pull in many Qt libs
    for tool in designer linguist lrelease lupdate qml qmlcachegen qmlimportscanner \
                balsam qmllint qmleasing qmlprofiler qmltestrunner qt-cmake \
                qt-configure-module qtpaths qtplugininfo pixeltool; do
        rm -f "${PYSIDE6_DIR}/${tool}"
    done

    # Remove other .so files in PySide6 root except libpyside6
    for f in "${PYSIDE6_DIR}"/*.so*; do
        [ -e "${f}" ] || continue
        basename=$(basename "${f}")
        case "${basename}" in
            libpyside6*)
                ;;
            *)
                rm -f "${f}"
                ;;
        esac
    done

    # Remove Qt libexec tools
    rm -rf "${PYSIDE6_DIR}/Qt/libexec"

    # Remove Qt subdirectories we don't need
    rm -rf "${PYSIDE6_DIR}/Qt/qml"
    rm -rf "${PYSIDE6_DIR}/Qt/translations"
    rm -rf "${PYSIDE6_DIR}/Qt/resources"
    rm -rf "${PYSIDE6_DIR}/include"

    # Remove Qt plugin directories with missing system deps
    if [ -d "${PYSIDE6_DIR}/Qt/plugins" ]; then
        for plugin_dir in texttospeech gamepads geoservices mediaservice \
                          playlistformats printsupport sceneparsers \
                          sensorgestures sensors sqldrivers virtualkeyboard \
                          webview bearer audio position; do
            rm -rf "${PYSIDE6_DIR}/Qt/plugins/${plugin_dir}"
        done
    fi
fi

echo "=== Running linuxdeploy ==="
# AppImages need libfuse2 to run; if it's missing, extract and run
export APPIMAGE_EXTRACT_AND_RUN=1

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
