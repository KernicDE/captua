#!/bin/bash
set -euo pipefail

# Captua installer
# Detects your distro, installs system dependencies, creates a venv,
# and installs Captua into ~/.local/share/captua

INSTALL_DIR="${HOME}/.local/share/captua"
VENV_DIR="${INSTALL_DIR}/venv"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"

REPO_URL="https://github.com/KernicDE/captua"

echo "=== Captua Installer ==="
echo

# ---------------------------------------------------------------------------
# Detect distro
# ---------------------------------------------------------------------------
DISTRO="unknown"
PKG_MANAGER=""

if command -v pacman &>/dev/null; then
    DISTRO="arch"
    PKG_MANAGER="pacman"
elif command -v dnf &>/dev/null; then
    DISTRO="fedora"
    PKG_MANAGER="dnf"
elif command -v zypper &>/dev/null; then
    DISTRO="opensuse"
    PKG_MANAGER="zypper"
elif command -v apt-get &>/dev/null; then
    DISTRO="debian"
    PKG_MANAGER="apt-get"
fi

echo "Detected distro family: ${DISTRO}"
echo

# ---------------------------------------------------------------------------
# Check Python version
# ---------------------------------------------------------------------------
PYTHON_CMD=""
for cmd in python3.12 python3.11 python3; do
    if command -v "$cmd" &>/dev/null; then
        ver=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null <<<""; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "ERROR: Python 3.11+ is required but not found."
    echo "Please install Python 3.11 or newer and try again."
    exit 1
fi

echo "Using Python: $PYTHON_CMD ($($PYTHON_CMD --version))"
echo

# ---------------------------------------------------------------------------
# Install system dependencies
# ---------------------------------------------------------------------------
echo "=== Installing system dependencies ==="
echo "The following packages will be installed (if missing):"
echo "  grim slurp wl-clipboard"
echo

install_system_deps() {
    case "$DISTRO" in
        arch)
            if ! pacman -Q grim slurp wl-clipboard &>/dev/null; then
                echo "Running: sudo pacman -S --needed grim slurp wl-clipboard"
                sudo pacman -S --needed --noconfirm grim slurp wl-clipboard
            else
                echo "System dependencies already installed."
            fi
            ;;
        fedora)
            if ! rpm -q grim slurp wl-clipboard &>/dev/null 2>&1; then
                echo "Running: sudo dnf install -y grim slurp wl-clipboard"
                sudo dnf install -y grim slurp wl-clipboard
            else
                echo "System dependencies already installed."
            fi
            ;;
        opensuse)
            if ! rpm -q grim slurp wl-clipboard &>/dev/null 2>&1; then
                echo "Running: sudo zypper install -y grim slurp wl-clipboard"
                sudo zypper install -y grim slurp wl-clipboard
            else
                echo "System dependencies already installed."
            fi
            ;;
        debian)
            if ! dpkg -l grim slurp wl-clipboard &>/dev/null 2>&1; then
                echo "Running: sudo apt-get install -y grim slurp wl-clipboard"
                sudo apt-get update
                sudo apt-get install -y grim slurp wl-clipboard
            else
                echo "System dependencies already installed."
            fi
            ;;
        *)
            echo "WARNING: Could not detect your package manager."
            echo "Please manually install: grim, slurp, wl-clipboard"
            echo "Then press Enter to continue, or Ctrl+C to abort."
            read -r
            ;;
    esac
}

install_system_deps
echo

# ---------------------------------------------------------------------------
# Determine source directory
# ---------------------------------------------------------------------------
# If this script is inside a cloned repo, install from there.
# Otherwise, clone from GitHub.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${PROJECT_DIR}/pyproject.toml" ] && grep -q "name = \"captua\"" "${PROJECT_DIR}/pyproject.toml" 2>/dev/null; then
    SOURCE_DIR="${PROJECT_DIR}"
    echo "Installing from local source: ${SOURCE_DIR}"
else
    SOURCE_DIR="${INSTALL_DIR}/src"
    echo "Cloning from ${REPO_URL} ..."
    rm -rf "${SOURCE_DIR}"
    git clone --depth 1 "${REPO_URL}" "${SOURCE_DIR}"
fi
echo

# ---------------------------------------------------------------------------
# Create virtual environment and install
# ---------------------------------------------------------------------------
echo "=== Creating Python virtual environment ==="
mkdir -p "${INSTALL_DIR}"
rm -rf "${VENV_DIR}"
"${PYTHON_CMD}" -m venv "${VENV_DIR}"

echo "=== Installing Captua ==="
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install "${SOURCE_DIR}"
echo

# ---------------------------------------------------------------------------
# Create wrapper script
# ---------------------------------------------------------------------------
echo "=== Creating launcher ==="
mkdir -p "${BIN_DIR}"

cat > "${BIN_DIR}/captua" <<EOF
#!/bin/bash
# Captua launcher
exec "${VENV_DIR}/bin/captua" "\$@"
EOF
chmod +x "${BIN_DIR}/captua"

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo
    echo "WARNING: ${BIN_DIR} is not in your PATH."
    echo "Add this line to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo "  export PATH=\"${BIN_DIR}:\$PATH\""
    echo
fi

# ---------------------------------------------------------------------------
# Install .desktop entry
# ---------------------------------------------------------------------------
echo "=== Installing desktop entry ==="
mkdir -p "${DESKTOP_DIR}" "${ICON_DIR}"

if [ -f "${SOURCE_DIR}/captua-overlay.desktop" ]; then
    cp "${SOURCE_DIR}/captua-overlay.desktop" "${DESKTOP_DIR}/captua.desktop"
fi

# Generate a simple icon
if command -v python3 &>/dev/null; then
    python3 -c "
from PIL import Image
img = Image.new('RGB', (256, 256), '#FF5D62')
img.save('${ICON_DIR}/captua.png')
" 2>/dev/null || true
fi

# Refresh desktop database if available
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
fi

echo
# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo "========================================"
echo "  Captua installed successfully!"
echo "========================================"
echo
echo "Launcher: ${BIN_DIR}/captua"
echo "Venv:     ${VENV_DIR}"
if [ -f "${DESKTOP_DIR}/captua.desktop" ]; then
    echo "Desktop:  ${DESKTOP_DIR}/captua.desktop"
fi
echo
echo "Run Captua now:"
echo "  ${BIN_DIR}/captua"
echo
echo "Or add ${BIN_DIR} to your PATH and just run:"
echo "  captua"
echo
echo "To uninstall, simply remove:"
echo "  rm -rf ${INSTALL_DIR}"
echo "  rm -f  ${BIN_DIR}/captua"
echo "  rm -f  ${DESKTOP_DIR}/captua.desktop"
echo
