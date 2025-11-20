#!/bin/bash

# =============================================================================
# Songs Formatter - Comprehensive Setup Script
# =============================================================================
# This script automatically installs all dependencies and sets up the project
# for both developers and non-developers. It handles:
# - Operating system detection
# - Python installation
# - FFmpeg installation
# - Virtual environment setup
# - Python dependencies installation
# - Application startup
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            echo "ubuntu"
        elif command_exists yum; then
            echo "centos"
        elif command_exists pacman; then
            echo "arch"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to install Python on different systems
install_python() {
    local os_type=$1
    print_status "Installing Python..."
    
    case $os_type in
        "macos")
            if command_exists brew; then
                brew install python3
            else
                print_error "Homebrew not found. Please install Homebrew first:"
                print_error "Visit: https://brew.sh/"
                exit 1
            fi
            ;;
        "ubuntu")
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
            ;;
        "centos")
            sudo yum install -y python3 python3-pip
            ;;
        "arch")
            sudo pacman -S python python-pip
            ;;
        "windows")
            print_error "Please install Python manually from https://python.org"
            print_error "Make sure to check 'Add Python to PATH' during installation"
            exit 1
            ;;
        *)
            print_error "Unsupported operating system. Please install Python manually."
            exit 1
            ;;
    esac
}

# Function to install FFmpeg on different systems
install_ffmpeg() {
    local os_type=$1
    print_status "Installing FFmpeg..."
    
    case $os_type in
        "macos")
            if command_exists brew; then
                brew install ffmpeg
            else
                print_error "Homebrew not found. Please install Homebrew first:"
                print_error "Visit: https://brew.sh/"
                exit 1
            fi
            ;;
        "ubuntu")
            sudo apt-get update
            sudo apt-get install -y ffmpeg
            ;;
        "centos")
            # Enable EPEL repository for FFmpeg
            sudo yum install -y epel-release
            sudo yum install -y ffmpeg ffmpeg-devel
            ;;
        "arch")
            sudo pacman -S ffmpeg
            ;;
        "windows")
            print_error "Please install FFmpeg manually:"
            print_error "1. Download from: https://ffmpeg.org/download.html"
            print_error "2. Extract to a folder (e.g., C:\\ffmpeg)"
            print_error "3. Add C:\\ffmpeg\\bin to your PATH environment variable"
            exit 1
            ;;
        *)
            print_error "Unsupported operating system. Please install FFmpeg manually."
            exit 1
            ;;
    esac
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        local version=$(python3 --version 2>&1 | cut -d' ' -f2)
        local major=$(echo $version | cut -d'.' -f1)
        local minor=$(echo $version | cut -d'.' -f2)
        
        if [ "$major" -eq 3 ] && [ "$minor" -ge 7 ]; then
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

# Function to setup virtual environment
setup_virtual_environment() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created successfully"
    else
        print_status "Virtual environment already exists"
    fi
    
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    print_success "Virtual environment setup complete"
}

# Function to install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    pip install -r requirements.txt
    print_success "Python dependencies installed successfully"
}

# Function to verify installations
verify_installations() {
    print_header "Verifying Installations"
    
    # Check Python
    if check_python_version; then
        local version=$(python3 --version 2>&1)
        print_success "Python: $version"
    else
        print_error "Python 3.7+ is required but not found"
        return 1
    fi
    
    # Check FFmpeg
    if command_exists ffmpeg; then
        local version=$(ffmpeg -version 2>&1 | head -n1)
        print_success "FFmpeg: $version"
    else
        print_error "FFmpeg is required but not found"
        return 1
    fi
    
    # Check virtual environment
    if [ -d "venv" ]; then
        print_success "Virtual environment: Ready"
    else
        print_error "Virtual environment not found"
        return 1
    fi
    
    return 0
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    local dirs=("uploads" "outputs" "downloads" "temp")
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done
    
    print_success "All directories are ready"
}

# Function to start the application
start_application() {
    print_header "Starting Songs Formatter Application"
    
    # Activate virtual environment
    source venv/bin/activate
    
    print_status "Starting Flask server..."
    print_success "Application will be available at: http://127.0.0.1:5001"
    print_status "Note: Using port 5001 to avoid conflicts with macOS AirPlay Receiver"
    print_status "Press Ctrl+C to stop the server"
    echo
    
    # Start the Flask application
    python app.py
}

# Main execution
main() {
    print_header "Songs Formatter - Automatic Setup"
    print_status "This script will automatically install all dependencies and start the application"
    echo
    
    # Detect operating system
    OS_TYPE=$(detect_os)
    print_status "Detected operating system: $OS_TYPE"
    
    # Check if Python is installed and has correct version
    if ! check_python_version; then
        print_warning "Python 3.7+ not found or version too old"
        read -p "Do you want to install Python? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_python $OS_TYPE
        else
            print_error "Python 3.7+ is required. Please install it manually and run this script again."
            exit 1
        fi
    else
        print_success "Python version check passed"
    fi
    
    # Check if FFmpeg is installed
    if ! command_exists ffmpeg; then
        print_warning "FFmpeg not found"
        read -p "Do you want to install FFmpeg? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_ffmpeg $OS_TYPE
        else
            print_error "FFmpeg is required for audio processing. Please install it manually and run this script again."
            exit 1
        fi
    else
        print_success "FFmpeg is already installed"
    fi
    
    # Verify all installations
    if ! verify_installations; then
        print_error "Installation verification failed. Please check the errors above."
        exit 1
    fi
    
    # Setup virtual environment
    setup_virtual_environment
    
    # Install Python dependencies
    install_python_dependencies
    
    # Create necessary directories
    create_directories
    
    # Final verification
    print_header "Setup Complete"
    print_success "All dependencies have been installed successfully!"
    print_success "The Songs Formatter application is ready to run."
    echo
    
    # Ask user if they want to start the application now
    read -p "Do you want to start the application now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_application
    else
        print_status "You can start the application later by running: ./run.sh"
        print_status "Or manually with: source venv/bin/activate && python app.py"
    fi
}

# Handle script interruption
trap 'print_warning "\nScript interrupted by user"; exit 1' INT

# Run main function
main "$@"

