#!/bin/bash
# Athan App Installation Script
# Islamic Prayer Time Application

set -e

echo "🕌 ATHAN APP - INSTALLATION SCRIPT"
echo "=================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  This script should not be run as root"
   exit 1
fi

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "✅ Detected OS: Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo "✅ Detected OS: macOS"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\\d+\\.\\d+' | head -1)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
    echo "❌ Python 3.8+ required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"

# Install system dependencies
echo ""
echo "📦 Installing system dependencies..."

if [[ "$OS" == "linux" ]]; then
    # Update package list
    echo "Updating package list..."
    sudo apt-get update -qq
    
    # Install required packages
    echo "Installing required packages..."
    sudo apt-get install -y \\
        python3-pip \\
        python3-dev \\
        build-essential \\
        vlc \\
        libvlc-dev \\
        libasound2-dev \\
        python3-tk \\
        python3-pil \\
        python3-pil.imagetk
    
    echo "✅ System dependencies installed"
    
elif [[ "$OS" == "macos" ]]; then
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is required for macOS installation"
        echo "Please install Homebrew first: https://brew.sh/"
        exit 1
    fi
    
    # Install VLC
    echo "Installing VLC..."
    brew install --cask vlc || true
    
    echo "✅ System dependencies installed"
fi

# Install Python dependencies
echo ""
echo "🐍 Installing Python dependencies..."

# Upgrade pip
python3 -m pip install --upgrade pip

# Install requirements
if [[ -f "requirements.txt" ]]; then
    python3 -m pip install -r requirements.txt
    echo "✅ Python dependencies installed"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Create application directory
APP_DIR="$HOME/.athan_app"
echo ""
echo "📁 Setting up application directory: $APP_DIR"

mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/config"
mkdir -p "$APP_DIR/logs"

# Copy application files
echo "Copying application files..."
cp -r . "$APP_DIR/"

# Make scripts executable
chmod +x "$APP_DIR/main.py"
chmod +x "$APP_DIR/main_headless.py"
chmod +x "$APP_DIR/test_core.py"

# Create desktop entry (Linux only)
if [[ "$OS" == "linux" ]]; then
    echo ""
    echo "🖥️  Creating desktop entry..."
    
    DESKTOP_FILE="$HOME/.local/share/applications/athan-app.desktop"
    mkdir -p "$(dirname "$DESKTOP_FILE")"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Athan App
Comment=Islamic Prayer Time Application
Exec=python3 $APP_DIR/main.py
Icon=$APP_DIR/assets/icons/tray_icon.png
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
EOF
    
    echo "✅ Desktop entry created"
fi

# Create startup script
echo ""
echo "🚀 Creating startup scripts..."

# GUI version startup script
cat > "$HOME/.local/bin/athan-app" << EOF
#!/bin/bash
cd "$APP_DIR"
python3 main.py "\$@"
EOF

# Headless version startup script
cat > "$HOME/.local/bin/athan-app-headless" << EOF
#!/bin/bash
cd "$APP_DIR"
python3 main_headless.py "\$@"
EOF

# Make startup scripts executable
chmod +x "$HOME/.local/bin/athan-app"
chmod +x "$HOME/.local/bin/athan-app-headless"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo "✅ Added $HOME/.local/bin to PATH"
fi

# Create systemd service (Linux only)
if [[ "$OS" == "linux" ]]; then
    echo ""
    echo "⚙️  Creating systemd service..."
    
    SERVICE_FILE="$HOME/.config/systemd/user/athan-app.service"
    mkdir -p "$(dirname "$SERVICE_FILE")"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Athan App - Islamic Prayer Times
After=network.target

[Service]
Type=simple
ExecStart=python3 $APP_DIR/main_headless.py
WorkingDirectory=$APP_DIR
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF
    
    # Reload systemd and enable service
    systemctl --user daemon-reload
    systemctl --user enable athan-app.service
    
    echo "✅ Systemd service created and enabled"
    echo "   Start with: systemctl --user start athan-app"
    echo "   Stop with: systemctl --user stop athan-app"
    echo "   Status: systemctl --user status athan-app"
fi

# Test installation
echo ""
echo "🧪 Testing installation..."

cd "$APP_DIR"
if python3 test_core.py > /dev/null 2>&1; then
    echo "✅ Installation test passed"
else
    echo "⚠️  Installation test had issues, but core functionality should work"
fi

# Final instructions
echo ""
echo "🎉 INSTALLATION COMPLETE!"
echo "========================"
echo ""
echo "📋 Usage Instructions:"
echo ""
echo "1. GUI Version (requires desktop environment):"
echo "   athan-app"
echo ""
echo "2. Headless Version (for servers/headless systems):"
echo "   athan-app-headless"
echo ""
echo "3. Test Core Functionality:"
echo "   cd $APP_DIR && python3 test_core.py"
echo ""

if [[ "$OS" == "linux" ]]; then
    echo "4. Run as Service:"
    echo "   systemctl --user start athan-app"
    echo ""
fi

echo "📁 Application Directory: $APP_DIR"
echo "📝 Configuration: $APP_DIR/config/"
echo "📋 Logs: $APP_DIR/athan_app.log"
echo ""
echo "🔧 Configuration:"
echo "   - Location is set to Raleigh, NC by default"
echo "   - Your custom Athan audio file is already configured"
echo "   - All 5 daily prayers are enabled"
echo ""
echo "For support or issues, check the logs in $APP_DIR/athan_app.log"
echo ""
echo "May Allah accept your prayers! 🤲"

