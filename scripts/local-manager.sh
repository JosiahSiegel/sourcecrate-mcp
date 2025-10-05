#!/usr/bin/env bash

# Local Development Manager - Interactive CLI for local API and UI management
# Version: 1.0.0
# Manages: HTTP API and UI processes
# Note: MCP Server is managed by Claude Code, not this script
#
# HTTP API Start Methods (tried in order):
#   1. uvx --from .[http] sourcecrate-http    (recommended for development)
#   2. python -m sourcecrate_mcp.http_server  (direct Python execution)
#   3. sourcecrate-http                       (if installed with pip install -e .[http])
#
# The HTTP server provides REST API access to all SourceCrate functionality:
#   - Browse papers (metadata only)
#   - Download papers (full-text with PDF conversion)
#   - Convert PDFs to text/markdown
#   - View system status and configuration help
#   - OpenAPI docs at http://localhost:9000/docs

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="${LOG_FILE:-/tmp/local-manager.log}"
INTERACTIVE="${INTERACTIVE:-true}"

# Process management
PID_DIR="/tmp/sourcecrate-local-pids"
mkdir -p "$PID_DIR"

HTTP_PID_FILE="$PID_DIR/http.pid"
UI_PID_FILE="$PID_DIR/ui.pid"

# Default ports
HTTP_PORT="${HTTP_PORT:-9000}"
UI_PORT="${UI_PORT:-3001}"

# Helper functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}ℹ ${NC}$*" >&2 | tee -a "$LOG_FILE" >&2
}

success() {
    echo -e "${GREEN}✓${NC} $*" >&2 | tee -a "$LOG_FILE" >&2
}

warning() {
    echo -e "${YELLOW}⚠${NC} $*" >&2 | tee -a "$LOG_FILE" >&2
}

error() {
    echo -e "${RED}✗${NC} $*" >&2 | tee -a "$LOG_FILE" >&2
}

prompt() {
    if [[ "$INTERACTIVE" == "true" ]]; then
        echo -e "${CYAN}?${NC} $1" >&2
        read -r REPLY
        echo "$REPLY"
    else
        echo "${2:-}"
    fi
}

confirm() {
    if [[ "$INTERACTIVE" == "true" ]]; then
        echo -e "${YELLOW}⚠${NC} $1 [y/N]" >&2
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY]) return 0 ;;
            *) return 1 ;;
        esac
    else
        return 0
    fi
}

# ============================================================================
# PROCESS MANAGEMENT FUNCTIONS
# ============================================================================

is_running() {
    local pid_file="$1"
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

get_process_info() {
    local pid_file="$1"
    local service_name="$2"

    if is_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        echo -e "${GREEN}●${NC} ${BOLD}$service_name${NC} - ${GREEN}running${NC} (PID: $pid)"

        # Show port if process is listening
        if command -v lsof &> /dev/null; then
            local port=$(lsof -Pan -p "$pid" -i 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)
            if [[ -n "$port" ]]; then
                echo -e "  ${CYAN}Port:${NC} $port"
            fi
        fi
    else
        echo -e "${RED}○${NC} ${BOLD}$service_name${NC} - ${RED}stopped${NC}"
    fi
}

stop_service() {
    local pid_file="$1"
    local service_name="$2"

    if is_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        info "Stopping $service_name (PID: $pid)..."

        # Try graceful shutdown first
        kill -TERM "$pid" 2>/dev/null || true

        # Wait up to 5 seconds for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 "$pid" 2>/dev/null; then
                success "$service_name stopped gracefully"
                rm -f "$pid_file"
                return 0
            fi
            sleep 0.5
        done

        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            warning "Forcing $service_name to stop..."
            kill -KILL "$pid" 2>/dev/null || true
            sleep 1
        fi

        rm -f "$pid_file"
        success "$service_name stopped"
    else
        warning "$service_name is not running"
    fi
}

start_http_server() {
    if is_running "$HTTP_PID_FILE"; then
        warning "HTTP API is already running (PID: $(cat "$HTTP_PID_FILE"))"
        return 1
    fi

    info "Starting HTTP API on port $HTTP_PORT..."
    cd "$PROJECT_ROOT"

    # Determine start method (try in order of preference)
    local start_cmd=""
    local method=""

    # Method 1: uvx (recommended for development - always uses current code)
    if command -v uvx &> /dev/null; then
        # Note: uvx rebuilds from source each time with --from '.[http]'
        start_cmd="uvx --from '.[http]' sourcecrate-http --port $HTTP_PORT"
        method="uvx (from source)"
    # Method 2: Direct Python execution (fallback, requires manual dependency install)
    elif command -v python3 &> /dev/null && python3 -c "import fastapi" 2>/dev/null; then
        start_cmd="python3 -m sourcecrate_mcp.http_server --port $HTTP_PORT"
        method="Python module"
    elif command -v python &> /dev/null && python -c "import fastapi" 2>/dev/null; then
        start_cmd="python -m sourcecrate_mcp.http_server --port $HTTP_PORT"
        method="Python module"
    # Method 3: Installed package command (if someone manually installed it)
    elif command -v sourcecrate-http &> /dev/null; then
        start_cmd="sourcecrate-http --port $HTTP_PORT"
        method="installed package"
    else
        error "No suitable method to start HTTP server found"
        error "Recommended: Ensure uvx is available (comes with uv)"
        error "Or install dependencies: uv pip install -e .[http]"
        return 1
    fi

    info "Using: $method"
    info "Command: $start_cmd"

    # Run in background and save PID (use bash -c to handle quoted args)
    nohup bash -c "$start_cmd" > "$LOG_FILE.http" 2>&1 &
    echo $! > "$HTTP_PID_FILE"

    sleep 2

    if is_running "$HTTP_PID_FILE"; then
        success "HTTP API started (PID: $(cat "$HTTP_PID_FILE"))"
        info "Method: $method"
        info "URL: http://localhost:$HTTP_PORT"
        info "Docs: http://localhost:$HTTP_PORT/docs"
        info "Logs: $LOG_FILE.http"
        return 0
    else
        error "HTTP API failed to start. Check logs: $LOG_FILE.http"
        return 1
    fi
}

start_ui() {
    if is_running "$UI_PID_FILE"; then
        warning "UI is already running (PID: $(cat "$UI_PID_FILE"))"
        return 1
    fi

    # Check if browser-ui directory exists
    if [[ ! -d "$PROJECT_ROOT/browser-ui" ]]; then
        error "browser-ui directory not found at $PROJECT_ROOT/browser-ui"
        return 1
    fi

    info "Starting Browser UI on port $UI_PORT..."
    cd "$PROJECT_ROOT/browser-ui"

    # Create config.js with correct API URL
    info "Configuring API endpoint: http://localhost:$HTTP_PORT"
    cat > config.js <<EOF
// Auto-generated by local-manager.sh
// API URL for local development
window.PAPEREZ_API_URL = 'http://localhost:$HTTP_PORT';
EOF

    # Start simple HTTP server for the browser UI
    local start_cmd=""
    if command -v python3 &> /dev/null; then
        start_cmd="python3 -m http.server $UI_PORT"
    elif command -v python &> /dev/null; then
        start_cmd="python -m http.server $UI_PORT"
    else
        error "Python not found. Cannot start UI server."
        return 1
    fi

    info "Command: $start_cmd"

    # Run in background and save PID
    nohup $start_cmd > "$LOG_FILE.ui" 2>&1 &
    echo $! > "$UI_PID_FILE"

    sleep 1

    if is_running "$UI_PID_FILE"; then
        success "Browser UI started (PID: $(cat "$UI_PID_FILE"))"
        info "URL: http://localhost:$UI_PORT"
        info "Logs: $LOG_FILE.ui"
        echo ""
        warning "IMPORTANT: Browser UI expects API at http://localhost:$HTTP_PORT"
        if ! is_running "$HTTP_PID_FILE"; then
            warning "HTTP API is not running! Start it first with: http-start"
        else
            success "HTTP API is running on port $HTTP_PORT ✓"
        fi
        return 0
    else
        error "Browser UI failed to start. Check logs: $LOG_FILE.ui"
        return 1
    fi
}

restart_service() {
    local pid_file="$1"
    local service_name="$2"
    local start_func="$3"

    stop_service "$pid_file" "$service_name"
    sleep 1
    $start_func
}

view_logs() {
    local log_file="$1"
    local service_name="$2"
    local lines="${3:-50}"

    if [[ -f "$log_file" ]]; then
        info "Showing last $lines lines of $service_name logs:"
        echo ""
        tail -n "$lines" "$log_file"
    else
        warning "No logs found for $service_name at $log_file"
    fi
}

# ============================================================================
# STATUS FUNCTIONS
# ============================================================================

show_all_status() {
    echo -e "\n${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${CYAN}   📊 SERVICE STATUS${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    get_process_info "$HTTP_PID_FILE" "HTTP API"
    echo ""
    get_process_info "$UI_PID_FILE" "UI"
    echo ""
    echo -e "${BLUE}ℹ${NC}  ${BOLD}MCP Server${NC} - managed by Claude Code"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
}

# ============================================================================
# QUICK ACTIONS MENU (Most Common Tasks)
# ============================================================================

menu_quick_actions() {
    while true; do
        echo -e "\n${CYAN}═══════════════════════════════════════${NC}"
        echo -e "${CYAN}   ⚡ QUICK ACTIONS (Common Tasks)${NC}"
        echo -e "${CYAN}═══════════════════════════════════════${NC}"
        echo "1)  📊 View All Services Status"
        echo "2)  🚀 Start All Services"
        echo "3)  🛑 Stop All Services"
        echo "4)  🔄 Restart All Services"
        echo ""
        echo -e "${CYAN}HTTP API:${NC}"
        echo "5)  ▶️  Start HTTP API"
        echo "6)  ⏸️  Stop HTTP API"
        echo "7)  🔄 Restart HTTP API"
        echo "8)  🌐 Open API in Browser"
        echo ""
        echo -e "${CYAN}UI:${NC}"
        echo "9)  ▶️  Start UI"
        echo "10) ⏸️  Stop UI"
        echo "11) 🔄 Restart UI"
        echo "12) 🌐 Open UI in Browser"
        echo ""
        echo "13) 📝 View Logs"
        echo "0)  ← Back to main menu"
        echo -e "${CYAN}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) show_all_status ;;
            2)
                start_http_server
                start_ui
                ;;
            3)
                stop_service "$HTTP_PID_FILE" "HTTP API"
                stop_service "$UI_PID_FILE" "UI"
                ;;
            4)
                restart_service "$HTTP_PID_FILE" "HTTP API" "start_http_server"
                restart_service "$UI_PID_FILE" "UI" "start_ui"
                ;;
            5) start_http_server ;;
            6) stop_service "$HTTP_PID_FILE" "HTTP API" ;;
            7) restart_service "$HTTP_PID_FILE" "HTTP API" "start_http_server" ;;
            8)
                if command -v xdg-open &> /dev/null; then
                    xdg-open "http://localhost:$HTTP_PORT" 2>/dev/null || true
                elif command -v open &> /dev/null; then
                    open "http://localhost:$HTTP_PORT"
                else
                    info "Open in browser: http://localhost:$HTTP_PORT"
                fi
                ;;
            9) start_ui ;;
            10) stop_service "$UI_PID_FILE" "UI" ;;
            11) restart_service "$UI_PID_FILE" "UI" "start_ui" ;;
            12)
                if command -v xdg-open &> /dev/null; then
                    xdg-open "http://localhost:$UI_PORT" 2>/dev/null || true
                elif command -v open &> /dev/null; then
                    open "http://localhost:$UI_PORT"
                else
                    info "Open in browser: http://localhost:$UI_PORT"
                fi
                ;;
            13) menu_logs ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

# ============================================================================
# SERVICE-SPECIFIC MENUS
# ============================================================================

menu_http_api() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   🌐 HTTP API${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        get_process_info "$HTTP_PID_FILE" "HTTP API"
        echo ""
        echo -e "${BLUE}Start methods: uvx → python → pip${NC}"
        echo ""
        echo "1)  ▶️  Start HTTP API"
        echo "2)  ⏸️  Stop HTTP API"
        echo "3)  🔄 Restart HTTP API"
        echo "4)  📝 View Logs (last 50 lines)"
        echo "5)  📄 View Full Logs"
        echo "6)  🗑️  Clear Logs"
        echo "7)  🌐 Open in Browser"
        echo "8)  🔧 Change Port (current: $HTTP_PORT)"
        echo "0)  ← Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) start_http_server ;;
            2) stop_service "$HTTP_PID_FILE" "HTTP API" ;;
            3) restart_service "$HTTP_PID_FILE" "HTTP API" "start_http_server" ;;
            4) view_logs "$LOG_FILE.http" "HTTP API" 50 ;;
            5)
                if [[ -f "$LOG_FILE.http" ]]; then
                    less "$LOG_FILE.http"
                else
                    warning "No HTTP API logs found"
                fi
                ;;
            6)
                if confirm "Clear HTTP API logs?"; then
                    > "$LOG_FILE.http"
                    success "HTTP API logs cleared"
                fi
                ;;
            7)
                if command -v xdg-open &> /dev/null; then
                    xdg-open "http://localhost:$HTTP_PORT" 2>/dev/null || true
                elif command -v open &> /dev/null; then
                    open "http://localhost:$HTTP_PORT"
                else
                    info "Open in browser: http://localhost:$HTTP_PORT"
                fi
                ;;
            8)
                new_port=$(prompt "Enter new port:" "$HTTP_PORT")
                if [[ "$new_port" =~ ^[0-9]+$ ]] && [[ "$new_port" -ge 1024 ]] && [[ "$new_port" -le 65535 ]]; then
                    HTTP_PORT="$new_port"
                    success "Port changed to $HTTP_PORT. Restart HTTP API for changes to take effect."
                else
                    error "Invalid port. Must be between 1024 and 65535"
                fi
                ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

menu_ui() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   🎨 Browser UI${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        get_process_info "$UI_PID_FILE" "Browser UI"
        echo ""
        echo -e "${BLUE}Static HTML served with Python HTTP server${NC}"
        echo ""
        echo "1)  ▶️  Start Browser UI"
        echo "2)  ⏸️  Stop Browser UI"
        echo "3)  🔄 Restart Browser UI"
        echo "4)  📝 View Logs (last 50 lines)"
        echo "5)  📄 View Full Logs"
        echo "6)  🗑️  Clear Logs"
        echo "7)  🌐 Open in Browser"
        echo "0)  ← Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) start_ui ;;
            2) stop_service "$UI_PID_FILE" "UI" ;;
            3) restart_service "$UI_PID_FILE" "UI" "start_ui" ;;
            4) view_logs "$LOG_FILE.ui" "UI" 50 ;;
            5)
                if [[ -f "$LOG_FILE.ui" ]]; then
                    less "$LOG_FILE.ui"
                else
                    warning "No UI logs found"
                fi
                ;;
            6)
                if confirm "Clear UI logs?"; then
                    > "$LOG_FILE.ui"
                    success "UI logs cleared"
                fi
                ;;
            7)
                if command -v xdg-open &> /dev/null; then
                    xdg-open "http://localhost:$UI_PORT" 2>/dev/null || true
                elif command -v open &> /dev/null; then
                    open "http://localhost:$UI_PORT"
                else
                    info "Open in browser: http://localhost:$UI_PORT"
                fi
                ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

menu_logs() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   📊 LOGS & MONITORING${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo "1)  📝 View All Logs (last 50 lines)"
        echo "2)  📝 View HTTP API Logs"
        echo "3)  📝 View UI Logs"
        echo "4)  🔄 Follow HTTP Logs (real-time)"
        echo "5)  🔄 Follow UI Logs (real-time)"
        echo "6)  🗑️  Clear All Logs"
        echo "0)  ← Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1)
                view_logs "$LOG_FILE.http" "HTTP API" 50
                echo ""
                view_logs "$LOG_FILE.ui" "UI" 50
                ;;
            2) view_logs "$LOG_FILE.http" "HTTP API" 100 ;;
            3) view_logs "$LOG_FILE.ui" "UI" 100 ;;
            4)
                if [[ -f "$LOG_FILE.http" ]]; then
                    info "Following HTTP logs (Ctrl+C to exit)..."
                    tail -f "$LOG_FILE.http"
                else
                    warning "No HTTP logs found"
                fi
                ;;
            5)
                if [[ -f "$LOG_FILE.ui" ]]; then
                    info "Following UI logs (Ctrl+C to exit)..."
                    tail -f "$LOG_FILE.ui"
                else
                    warning "No UI logs found"
                fi
                ;;
            6)
                if confirm "Clear all logs?"; then
                    > "$LOG_FILE.http"
                    > "$LOG_FILE.ui"
                    success "All logs cleared"
                fi
                ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

# ============================================================================
# MAIN MENU
# ============================================================================

main_menu() {
    while true; do
        echo -e "\n${CYAN}╔═══════════════════════════════════════╗${NC}"
        echo -e "${CYAN}║   🚀 LOCAL DEVELOPMENT MANAGER       ║${NC}"
        echo -e "${CYAN}╚═══════════════════════════════════════╝${NC}"

        show_all_status

        echo ""
        echo -e "${MAGENTA}═══ Main Menu ═══${NC}"
        echo "1)  ⚡ Quick Actions (Most Common)"
        echo "2)  🌐 HTTP API Management"
        echo "3)  🎨 UI Management"
        echo "4)  📊 Logs & Monitoring"
        echo ""
        echo "0)  👋 Exit"
        echo -e "${CYAN}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) menu_quick_actions ;;
            2) menu_http_api ;;
            3) menu_ui ;;
            4) menu_logs ;;
            0)
                success "👋 Goodbye!"
                exit 0
                ;;
            *) warning "Invalid option" ;;
        esac
    done
}

# ============================================================================
# CLI MODE
# ============================================================================

cli_mode() {
    local command="$1"

    case "$command" in
        # Status
        status) show_all_status ;;

        # HTTP API
        http-start|api-start) start_http_server ;;
        http-stop|api-stop) stop_service "$HTTP_PID_FILE" "HTTP API" ;;
        http-restart|api-restart) restart_service "$HTTP_PID_FILE" "HTTP API" "start_http_server" ;;
        http-logs|api-logs) view_logs "$LOG_FILE.http" "HTTP API" 50 ;;

        # UI
        ui-start) start_ui ;;
        ui-stop) stop_service "$UI_PID_FILE" "UI" ;;
        ui-restart) restart_service "$UI_PID_FILE" "UI" "start_ui" ;;
        ui-logs) view_logs "$LOG_FILE.ui" "UI" 50 ;;

        # All services
        start-all)
            start_http_server
            start_ui
            ;;
        stop-all)
            stop_service "$HTTP_PID_FILE" "HTTP API"
            stop_service "$UI_PID_FILE" "UI"
            ;;
        restart-all)
            restart_service "$HTTP_PID_FILE" "HTTP API" "start_http_server"
            restart_service "$UI_PID_FILE" "UI" "start_ui"
            ;;

        # Logs
        logs)
            view_logs "$LOG_FILE.http" "HTTP API" 50
            view_logs "$LOG_FILE.ui" "UI" 50
            ;;

        # Help
        help|--help|-h)
            echo "Local Development Manager - CLI Mode"
            echo ""
            echo "Usage: $0 <command>"
            echo ""
            echo "Status:"
            echo "  status              Show all services status"
            echo ""
            echo "HTTP API:"
            echo "  http-start          Start HTTP API (tries uvx → python → installed)"
            echo "  http-stop           Stop HTTP API"
            echo "  http-restart        Restart HTTP API"
            echo "  http-logs           View HTTP API logs"
            echo ""
            echo "UI:"
            echo "  ui-start            Start UI"
            echo "  ui-stop             Stop UI"
            echo "  ui-restart          Restart UI"
            echo "  ui-logs             View UI logs"
            echo ""
            echo "All Services:"
            echo "  start-all           Start all services"
            echo "  stop-all            Stop all services"
            echo "  restart-all         Restart all services"
            echo ""
            echo "Logs:"
            echo "  logs                View all logs"
            echo ""
            echo "HTTP Server Start Methods (tried in order):"
            echo "  1. uvx --from .[http] sourcecrate-http    (recommended for development)"
            echo "  2. python -m sourcecrate_mcp.http_server  (direct Python execution)"
            echo "  3. sourcecrate-http                       (if installed with pip)"
            echo ""
            echo "Note: MCP Server is managed by Claude Code, not this script"
            echo ""
            echo "Run with no arguments for interactive mode"
            ;;

        *)
            error "Unknown command: $command"
            echo "Run '$0 help' for usage"
            exit 1
            ;;
    esac
}

# ============================================================================
# INITIALIZATION
# ============================================================================

check_dependencies() {
    # Clear screen for interactive mode
    if [[ "$INTERACTIVE" == "true" ]]; then
        clear
    fi

    # Check Python
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        error "Python not found. Please install Python 3.11+"
        exit 1
    fi

    success "Python found: $(python3 --version 2>&1 || python --version 2>&1)"

    # Check if in project directory
    if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        error "Not in sourcecrate-mcp project directory"
        exit 1
    fi

    success "Project directory: $PROJECT_ROOT"
}

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

main() {
    check_dependencies

    if [[ $# -eq 0 ]]; then
        # Interactive mode
        main_menu
    else
        # CLI mode
        INTERACTIVE=false
        cli_mode "$1"
    fi
}

# Run main function
main "$@"
