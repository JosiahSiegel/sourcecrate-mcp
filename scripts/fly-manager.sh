#!/usr/bin/env bash

# Fly.io Manager - Interactive CLI for all Fly.io operations
# Version: 1.0.0
# Compatible with: flyctl 0.2.0+

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
LOG_FILE="${LOG_FILE:-/tmp/fly-manager.log}"
INTERACTIVE="${INTERACTIVE:-true}"
APP_NAME="${FLY_APP_NAME:-}"

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
    echo -e "${RED}✗${NC} $*" >&2 | tee -a "$LOG_FILE"
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

check_flyctl() {
    if ! command -v fly &> /dev/null; then
        error "flyctl is not installed. Install it first:"
        echo "  macOS: brew install flyctl"
        echo "  Linux: curl -L https://fly.io/install.sh | sh"
        echo "  Windows: iwr https://fly.io/install.ps1 -useb | iex"
        exit 1
    fi
    success "flyctl found: $(fly version)"
}

check_auth() {
    if ! fly auth whoami &> /dev/null; then
        error "Not authenticated to Fly.io"
        info "Run: fly auth login"
        exit 1
    fi
    success "Authenticated as: $(fly auth whoami)"
}

select_app() {
    if [[ -n "$APP_NAME" ]]; then
        info "Using app: $APP_NAME"
        return 0
    fi

    # Get list of apps using JSON output
    local apps_json=$(fly apps list --json 2>/dev/null)

    # Try jq first, fallback to grep/cut if jq not available
    local apps_list
    if command -v jq &> /dev/null; then
        apps_list=$(echo "$apps_json" | jq -r '.[].Name' 2>/dev/null)
    else
        apps_list=$(echo "$apps_json" | grep -o '"Name": "[^"]*"' | cut -d'"' -f4)
    fi

    local app_count=$(echo "$apps_list" | wc -l)

    # Handle empty list
    if [[ -z "$apps_list" ]] || [[ "$apps_list" == "" ]]; then
        error "No apps found. Create one with: fly apps create"
        exit 1
    fi

    if [[ "$app_count" -eq 1 ]]; then
        # Only one app exists, auto-select it
        APP_NAME=$(echo "$apps_list" | head -1)
        info "Auto-selected only app: $APP_NAME"
        return 0
    else
        # Multiple apps, show list and prompt
        info "Available apps:"
        fly apps list

        APP_NAME=$(prompt "Enter app name:" "")
        if [[ -z "$APP_NAME" ]]; then
            error "App name is required"
            exit 1
        fi
    fi
}

# ============================================================================
# 1. APP MANAGEMENT
# ============================================================================

menu_apps() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   APP MANAGEMENT${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo "1)  List all apps"
        echo "2)  Create new app"
        echo "3)  Show app info"
        echo "4)  Open app dashboard"
        echo "5)  Destroy app (DELETE)"
        echo "6)  Restart app"
        echo "7)  View app config"
        echo "8)  View app releases"
        echo "0)  Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) fly apps list ;;
            2) cmd_apps_create ;;
            3) cmd_apps_info ;;
            4) cmd_apps_dashboard ;;
            5) cmd_apps_destroy ;;
            6) select_app && fly apps restart -a "$APP_NAME" ;;
            7) select_app && fly config show -a "$APP_NAME" ;;
            8) select_app && fly releases -a "$APP_NAME" ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

cmd_apps_create() {
    name=$(prompt "App name (leave empty for auto-generated):" "")
    org=$(prompt "Organization (leave empty for personal):" "")

    args=()
    [[ -n "$name" ]] && args+=(--name "$name")
    [[ -n "$org" ]] && args+=(--org "$org")

    if confirm "Create app now?"; then
        fly apps create "${args[@]}"
        success "App created successfully"
    fi
}

cmd_apps_info() {
    select_app
    info "App information:"
    fly status -a "$APP_NAME"
}

cmd_apps_dashboard() {
    select_app
    if command -v xdg-open &> /dev/null || command -v open &> /dev/null; then
        fly dashboard -a "$APP_NAME"
    else
        info "Dashboard URL: https://fly.io/apps/$APP_NAME"
        info "Open this URL in your browser (xdg-open not available in container)"
    fi
}

cmd_apps_destroy() {
    select_app
    warning "This will PERMANENTLY delete app: $APP_NAME"
    warning "This will delete all machines, volumes, IPs, secrets, and images"

    if confirm "Type app name to confirm deletion: $APP_NAME"; then
        read -r confirm_name
        if [[ "$confirm_name" == "$APP_NAME" ]]; then
            fly apps destroy "$APP_NAME" --yes
            success "App destroyed"
            APP_NAME=""
        else
            error "App name mismatch. Deletion cancelled."
        fi
    fi
}

# ============================================================================
# 2. DEPLOYMENT
# ============================================================================

menu_deploy() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   DEPLOYMENT${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo "1)  Launch new app (from current directory)"
        echo "2)  Deploy app"
        echo "3)  Deploy (with custom Dockerfile)"
        echo "4)  Deploy (from Docker image)"
        echo "5)  Deploy (build only, no deploy)"
        echo "6)  Deploy (with environment variables)"
        echo "7)  Deploy (with build secrets)"
        echo "8)  Redeploy previous release"
        echo "0)  Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) cmd_launch ;;
            2) select_app && fly deploy -a "$APP_NAME" ;;
            3) cmd_deploy_dockerfile ;;
            4) cmd_deploy_image ;;
            5) select_app && fly deploy -a "$APP_NAME" --build-only ;;
            6) cmd_deploy_env ;;
            7) cmd_deploy_secrets ;;
            8) cmd_redeploy ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

cmd_launch() {
    info "Launching app from current directory..."

    no_deploy=$(prompt "Skip initial deployment? [y/N]:" "n")

    if [[ "$no_deploy" =~ ^[yY]$ ]]; then
        fly launch --no-deploy
    else
        fly launch
    fi
}

cmd_deploy_dockerfile() {
    select_app
    dockerfile=$(prompt "Path to Dockerfile:" "Dockerfile")

    if [[ ! -f "$dockerfile" ]]; then
        error "Dockerfile not found: $dockerfile"
        return 1
    fi

    fly deploy -a "$APP_NAME" --dockerfile "$dockerfile"
}

cmd_deploy_image() {
    select_app
    image=$(prompt "Docker image (e.g., username/repo:tag):" "")

    if [[ -z "$image" ]]; then
        error "Image is required"
        return 1
    fi

    fly deploy -a "$APP_NAME" --image "$image"
}

cmd_deploy_env() {
    select_app
    info "Enter environment variables (format: KEY=VALUE, one per line, empty line to finish):"

    env_vars=()
    while true; do
        var=$(prompt "ENV var:" "")
        [[ -z "$var" ]] && break
        env_vars+=(-e "$var")
    done

    if [[ ${#env_vars[@]} -gt 0 ]]; then
        fly deploy -a "$APP_NAME" "${env_vars[@]}"
    else
        warning "No environment variables provided"
    fi
}

cmd_deploy_secrets() {
    select_app
    info "Enter build secrets (format: KEY=VALUE, one per line, empty line to finish):"

    secrets=()
    while true; do
        secret=$(prompt "Build secret:" "")
        [[ -z "$secret" ]] && break
        secrets+=(--build-secret "$secret")
    done

    if [[ ${#secrets[@]} -gt 0 ]]; then
        fly deploy -a "$APP_NAME" "${secrets[@]}"
    else
        warning "No build secrets provided"
    fi
}

cmd_redeploy() {
    select_app
    fly releases -a "$APP_NAME"

    version=$(prompt "Enter version to redeploy:" "")
    if [[ -n "$version" ]]; then
        if confirm "Redeploy version $version?"; then
            fly releases redeploy "$version" -a "$APP_NAME"
        fi
    fi
}

# ============================================================================
# 3. MACHINES
# ============================================================================

menu_machines() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   MACHINES${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo "1)  List machines"
        echo "2)  Create machine"
        echo "3)  Clone machine"
        echo "4)  Start machine"
        echo "5)  Stop machine"
        echo "6)  Suspend machine (faster restart)"
        echo "7)  Restart machine"
        echo "8)  Destroy machine"
        echo "9)  Update machine"
        echo "10) Run command on machine"
        echo "11) SSH into machine"
        echo "12) View machine logs"
        echo "0)  Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) select_app && fly machine list -a "$APP_NAME" ;;
            2) cmd_machine_create ;;
            3) cmd_machine_clone ;;
            4) cmd_machine_start ;;
            5) cmd_machine_stop ;;
            6) cmd_machine_suspend ;;
            7) cmd_machine_restart ;;
            8) cmd_machine_destroy ;;
            9) cmd_machine_update ;;
            10) cmd_machine_run ;;
            11) cmd_machine_ssh ;;
            12) cmd_machine_logs ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

cmd_machine_create() {
    select_app
    name=$(prompt "Machine name (optional):" "")
    region=$(prompt "Region (e.g., iad, lhr, syd):" "")

    args=(-a "$APP_NAME")
    [[ -n "$name" ]] && args+=(--name "$name")
    [[ -n "$region" ]] && args+=(--region "$region")

    fly machine run "${args[@]}" .
}

cmd_machine_clone() {
    select_app
    fly machine list -a "$APP_NAME"

    machine_id=$(prompt "Machine ID to clone:" "")
    region=$(prompt "Region (optional, leave empty for same region):" "")

    args=()
    [[ -n "$region" ]] && args+=(--region "$region")

    if [[ -n "$machine_id" ]]; then
        fly machine clone "$machine_id" -a "$APP_NAME" "${args[@]}"
    fi
}

cmd_machine_start() {
    select_app
    fly machine list -a "$APP_NAME"

    machine_id=$(prompt "Machine ID to start:" "")
    if [[ -n "$machine_id" ]]; then
        fly machine start "$machine_id" -a "$APP_NAME"
    fi
}

cmd_machine_stop() {
    select_app
    fly machine list -a "$APP_NAME"

    machine_id=$(prompt "Machine ID to stop:" "")
    if [[ -n "$machine_id" ]]; then
        fly machine stop "$machine_id" -a "$APP_NAME"
    fi
}

cmd_machine_suspend() {
    select_app
    fly machine list -a "$APP_NAME"

    machine_id=$(prompt "Machine ID to suspend:" "")
    if [[ -n "$machine_id" ]]; then
        info "Suspending machine (faster restart than stop)..."
        fly machine suspend "$machine_id" -a "$APP_NAME"
        success "Machine suspended. Use 'Start machine' to resume."
    fi
}

cmd_machine_restart() {
    select_app
    fly machine list -a "$APP_NAME"

    machine_id=$(prompt "Machine ID to restart:" "")
    if [[ -n "$machine_id" ]]; then
        fly machine restart "$machine_id" -a "$APP_NAME"
    fi
}

cmd_machine_destroy() {
    select_app
    fly machine list -a "$APP_NAME"

    machine_id=$(prompt "Machine ID to destroy:" "")
    if [[ -n "$machine_id" ]] && confirm "Destroy machine $machine_id?"; then
        fly machine destroy "$machine_id" -a "$APP_NAME" --force
    fi
}

cmd_machine_update() {
    select_app
    fly machine list -a "$APP_NAME"

    machine_id=$(prompt "Machine ID to update:" "")
    if [[ -n "$machine_id" ]]; then
        fly machine update "$machine_id" -a "$APP_NAME"
    fi
}

cmd_machine_run() {
    select_app
    command=$(prompt "Command to run:" "")

    if [[ -n "$command" ]]; then
        fly ssh console -a "$APP_NAME" -C "$command"
    fi
}

cmd_machine_ssh() {
    select_app
    fly ssh console -a "$APP_NAME"
}

cmd_machine_logs() {
    select_app
    fly machine list -a "$APP_NAME"

    machine_id=$(prompt "Machine ID (optional, leave empty for all):" "")

    if [[ -n "$machine_id" ]]; then
        fly logs -a "$APP_NAME" --instance "$machine_id"
    else
        fly logs -a "$APP_NAME"
    fi
}

# ============================================================================
# 4. SCALING
# ============================================================================

menu_scale() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   SCALING${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo "1)  Show current scale"
        echo "2)  Scale machine count"
        echo "3)  Scale machine count by region"
        echo "4)  Scale machine count by process group"
        echo "5)  Scale VM size (CPU/Memory)"
        echo "6)  Scale VM size by process group"
        echo "7)  Scale to zero (stop all)"
        echo "8)  Autoscale configuration"
        echo "0)  Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) select_app && fly scale show -a "$APP_NAME" ;;
            2) cmd_scale_count ;;
            3) cmd_scale_count_region ;;
            4) cmd_scale_count_group ;;
            5) cmd_scale_vm ;;
            6) cmd_scale_vm_group ;;
            7) cmd_scale_zero ;;
            8) cmd_autoscale ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

cmd_scale_count() {
    select_app
    fly scale show -a "$APP_NAME"

    count=$(prompt "Number of machines:" "")
    if [[ -n "$count" ]] && [[ "$count" =~ ^[0-9]+$ ]]; then
        fly scale count "$count" -a "$APP_NAME"
    else
        error "Invalid count"
    fi
}

cmd_scale_count_region() {
    select_app
    fly scale show -a "$APP_NAME"

    count=$(prompt "Number of machines:" "")
    region=$(prompt "Region (e.g., iad, lhr, syd):" "")

    if [[ -n "$count" ]] && [[ -n "$region" ]]; then
        fly scale count "$count" --region "$region" -a "$APP_NAME"
    fi
}

cmd_scale_count_group() {
    select_app
    fly scale show -a "$APP_NAME"

    group=$(prompt "Process group (e.g., web, worker):" "")
    count=$(prompt "Number of machines:" "")

    if [[ -n "$group" ]] && [[ -n "$count" ]]; then
        fly scale count "${group}=${count}" -a "$APP_NAME"
    fi
}

cmd_scale_vm() {
    select_app
    info "Available VM sizes:"
    echo "  - shared-cpu-1x (256MB)"
    echo "  - shared-cpu-2x (512MB)"
    echo "  - shared-cpu-4x (1GB)"
    echo "  - shared-cpu-8x (2GB)"
    echo "  - performance-1x (2GB)"
    echo "  - performance-2x (4GB)"
    echo "  - performance-4x (8GB)"
    echo "  - performance-8x (16GB)"

    size=$(prompt "VM size:" "")
    if [[ -n "$size" ]]; then
        fly scale vm "$size" -a "$APP_NAME"
    fi
}

cmd_scale_vm_group() {
    select_app
    fly scale show -a "$APP_NAME"

    group=$(prompt "Process group:" "")
    size=$(prompt "VM size:" "")

    if [[ -n "$group" ]] && [[ -n "$size" ]]; then
        fly scale vm "$size" --process-group "$group" -a "$APP_NAME"
    fi
}

cmd_scale_zero() {
    select_app
    warning "This will stop all machines"
    if confirm "Scale to zero?"; then
        fly scale count 0 -a "$APP_NAME"
    fi
}

cmd_autoscale() {
    select_app
    info "Autoscale configuration is set in fly.toml, not via flyctl commands"
    info ""
    info "To configure autoscaling, edit your fly.toml file:"
    info ""
    info "[[services]]"
    info "  [[services.concurrency]]"
    info "    type = \"requests\""
    info "    hard_limit = 25"
    info "    soft_limit = 20"
    info ""
    info "  [services.autoscaling]"
    info "    min_machines_running = 1"
    info "    max_machines_running = 10"
    info ""
    info "Then deploy with: fly deploy -a $APP_NAME"
    info ""
    info "Docs: https://fly.io/docs/reference/autoscaling/"
}

# ============================================================================
# 5. SECRETS
# ============================================================================

menu_secrets() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   SECRETS MANAGEMENT${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo "1)  List secrets"
        echo "2)  Set secret"
        echo "3)  Set multiple secrets"
        echo "4)  Set secret (staged, no deploy)"
        echo "5)  Deploy staged secrets"
        echo "6)  Unset secret"
        echo "7)  Import secrets from file"
        echo "0)  Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) select_app && fly secrets list -a "$APP_NAME" ;;
            2) cmd_secret_set ;;
            3) cmd_secret_set_multiple ;;
            4) cmd_secret_set_staged ;;
            5) select_app && fly secrets deploy -a "$APP_NAME" ;;
            6) cmd_secret_unset ;;
            7) cmd_secret_import ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

cmd_secret_set() {
    select_app
    key=$(prompt "Secret key:" "")
    value=$(prompt "Secret value:" "")

    if [[ -n "$key" ]] && [[ -n "$value" ]]; then
        fly secrets set "${key}=${value}" -a "$APP_NAME"
    fi
}

cmd_secret_set_multiple() {
    select_app
    info "Enter secrets (format: KEY=VALUE, one per line, empty line to finish):"

    secrets=()
    while true; do
        secret=$(prompt "Secret:" "")
        [[ -z "$secret" ]] && break
        secrets+=("$secret")
    done

    if [[ ${#secrets[@]} -gt 0 ]]; then
        fly secrets set "${secrets[@]}" -a "$APP_NAME"
    fi
}

cmd_secret_set_staged() {
    select_app
    key=$(prompt "Secret key:" "")
    value=$(prompt "Secret value:" "")

    if [[ -n "$key" ]] && [[ -n "$value" ]]; then
        fly secrets set "${key}=${value}" --stage -a "$APP_NAME"
        success "Secret staged. Run 'Deploy staged secrets' to apply."
    fi
}

cmd_secret_unset() {
    select_app
    fly secrets list -a "$APP_NAME"

    key=$(prompt "Secret key to unset:" "")
    if [[ -n "$key" ]] && confirm "Unset secret $key?"; then
        fly secrets unset "$key" -a "$APP_NAME"
    fi
}

cmd_secret_import() {
    select_app
    file=$(prompt "Path to secrets file (KEY=VALUE format):" "")

    if [[ -f "$file" ]]; then
        fly secrets import -a "$APP_NAME" < "$file"
    else
        error "File not found: $file"
    fi
}

# ============================================================================
# 6. VOLUMES
# ============================================================================

menu_volumes() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   VOLUME MANAGEMENT${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo "1)  List volumes"
        echo "2)  Create volume"
        echo "3)  Show volume details"
        echo "4)  Extend volume size"
        echo "5)  Fork volume"
        echo "6)  Destroy volume"
        echo "7)  List volume snapshots"
        echo "8)  Create volume snapshot"
        echo "9)  Restore from snapshot"
        echo "0)  Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) select_app && fly volumes list -a "$APP_NAME" ;;
            2) cmd_volume_create ;;
            3) cmd_volume_show ;;
            4) cmd_volume_extend ;;
            5) cmd_volume_fork ;;
            6) cmd_volume_destroy ;;
            7) cmd_volume_snapshots_list ;;
            8) cmd_volume_snapshot_create ;;
            9) cmd_volume_restore ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

cmd_volume_create() {
    select_app
    name=$(prompt "Volume name:" "")
    region=$(prompt "Region:" "")
    size=$(prompt "Size in GB:" "1")

    if [[ -n "$name" ]] && [[ -n "$region" ]]; then
        fly volumes create "$name" --region "$region" --size "$size" -a "$APP_NAME"
    fi
}

cmd_volume_show() {
    select_app
    fly volumes list -a "$APP_NAME"

    volume_id=$(prompt "Volume ID:" "")
    if [[ -n "$volume_id" ]]; then
        fly volumes show "$volume_id" -a "$APP_NAME"
    fi
}

cmd_volume_extend() {
    select_app
    fly volumes list -a "$APP_NAME"

    volume_id=$(prompt "Volume ID:" "")
    size=$(prompt "New size in GB:" "")

    if [[ -n "$volume_id" ]] && [[ -n "$size" ]]; then
        fly volumes extend "$volume_id" --size "$size" -a "$APP_NAME"
    fi
}

cmd_volume_fork() {
    select_app
    fly volumes list -a "$APP_NAME"

    volume_id=$(prompt "Volume ID to fork:" "")
    if [[ -n "$volume_id" ]]; then
        fly volumes fork "$volume_id" -a "$APP_NAME"
    fi
}

cmd_volume_destroy() {
    select_app
    fly volumes list -a "$APP_NAME"

    volume_id=$(prompt "Volume ID to destroy:" "")
    if [[ -n "$volume_id" ]] && confirm "Destroy volume $volume_id?"; then
        fly volumes destroy "$volume_id" -a "$APP_NAME" --yes
    fi
}

cmd_volume_snapshots_list() {
    select_app
    fly volumes list -a "$APP_NAME"

    volume_id=$(prompt "Volume ID:" "")
    if [[ -n "$volume_id" ]]; then
        fly volumes snapshots list "$volume_id" -a "$APP_NAME"
    fi
}

cmd_volume_snapshot_create() {
    select_app
    fly volumes list -a "$APP_NAME"

    volume_id=$(prompt "Volume ID:" "")
    if [[ -n "$volume_id" ]]; then
        fly volumes snapshots create "$volume_id" -a "$APP_NAME"
    fi
}

cmd_volume_restore() {
    select_app
    fly volumes list -a "$APP_NAME"

    volume_id=$(prompt "Volume ID:" "")
    if [[ -z "$volume_id" ]]; then
        return
    fi

    fly volumes snapshots list "$volume_id" -a "$APP_NAME"
    snapshot_id=$(prompt "Snapshot ID:" "")
    name=$(prompt "New volume name:" "")
    size=$(prompt "Size in GB:" "")

    if [[ -n "$snapshot_id" ]] && [[ -n "$name" ]]; then
        fly volumes create "$name" --snapshot-id "$snapshot_id" --size "$size" -a "$APP_NAME"
    fi
}

# ============================================================================
# 7. NETWORKING
# ============================================================================

menu_networking() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   NETWORKING${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo "1)  List IP addresses"
        echo "2)  Allocate IPv4 address"
        echo "3)  Allocate IPv6 address"
        echo "4)  Allocate private IPv6 (Flycast)"
        echo "5)  Release IP address"
        echo "6)  List private IPs"
        echo "7)  List certificates"
        echo "8)  Add certificate"
        echo "9)  Remove certificate"
        echo "10) Show services"
        echo "0)  Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) select_app && fly ips list -a "$APP_NAME" ;;
            2) cmd_ip_allocate_v4 ;;
            3) cmd_ip_allocate_v6 ;;
            4) cmd_ip_allocate_private ;;
            5) cmd_ip_release ;;
            6) select_app && fly ips private -a "$APP_NAME" ;;
            7) select_app && fly certs list -a "$APP_NAME" ;;
            8) cmd_cert_add ;;
            9) cmd_cert_remove ;;
            10) select_app && fly services list -a "$APP_NAME" ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

cmd_ip_allocate_v4() {
    select_app
    if confirm "Allocate IPv4 address? (costs $2/month)"; then
        fly ips allocate-v4 -a "$APP_NAME"
    fi
}

cmd_ip_allocate_v6() {
    select_app
    fly ips allocate-v6 -a "$APP_NAME"
}

cmd_ip_allocate_private() {
    select_app
    info "Allocating private IPv6 (Flycast)..."
    fly ips allocate-v6 --private -a "$APP_NAME"
}

cmd_ip_release() {
    select_app
    fly ips list -a "$APP_NAME"

    ip=$(prompt "IP address to release:" "")
    if [[ -n "$ip" ]] && confirm "Release IP $ip?"; then
        fly ips release "$ip" -a "$APP_NAME"
    fi
}

cmd_cert_add() {
    select_app
    hostname=$(prompt "Hostname (e.g., example.com):" "")

    if [[ -n "$hostname" ]]; then
        fly certs add "$hostname" -a "$APP_NAME"
    fi
}

cmd_cert_remove() {
    select_app
    fly certs list -a "$APP_NAME"

    hostname=$(prompt "Hostname to remove:" "")
    if [[ -n "$hostname" ]] && confirm "Remove certificate for $hostname?"; then
        fly certs remove "$hostname" -a "$APP_NAME"
    fi
}

# ============================================================================
# 8. MONITORING
# ============================================================================

menu_monitoring() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   MONITORING & LOGS${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo "1)  View app status"
        echo "2)  View real-time logs"
        echo "3)  View logs (last 100 lines)"
        echo "4)  View logs (specific machine)"
        echo "5)  View health checks"
        echo "6)  Ping app"
        echo "7)  Open monitoring dashboard"
        echo "8)  View app releases"
        echo "0)  Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) select_app && fly status -a "$APP_NAME" ;;
            2) select_app && fly logs -a "$APP_NAME" ;;
            3) select_app && fly logs -a "$APP_NAME" --lines 100 ;;
            4) cmd_logs_machine ;;
            5) select_app && fly checks list -a "$APP_NAME" ;;
            6) select_app && fly ping -a "$APP_NAME" ;;
            7) cmd_apps_dashboard ;;
            8) select_app && fly releases -a "$APP_NAME" ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

cmd_logs_machine() {
    select_app
    fly machine list -a "$APP_NAME"

    machine_id=$(prompt "Machine ID:" "")
    if [[ -n "$machine_id" ]]; then
        fly logs -a "$APP_NAME" --instance "$machine_id"
    fi
}

# ============================================================================
# 9. ADVANCED
# ============================================================================

menu_advanced() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   ADVANCED OPERATIONS${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo "1)  Create auth token"
        echo "2)  Create deploy token"
        echo "3)  WireGuard setup"
        echo "4)  Proxy connection"
        echo "5)  SFTP access"
        echo "6)  Platform info"
        echo "7)  Platform regions"
        echo "8)  Platform VM sizes"
        echo "9)  View fly.toml config"
        echo "10) Validate fly.toml"
        echo "0)  Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) fly auth token ;;
            2) cmd_token_deploy ;;
            3) cmd_wireguard ;;
            4) cmd_proxy ;;
            5) cmd_sftp ;;
            6) fly platform ;;
            7) fly platform regions ;;
            8) fly platform vm-sizes ;;
            9) select_app && fly config show -a "$APP_NAME" ;;
            10) fly config validate ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

cmd_token_deploy() {
    select_app
    fly tokens create deploy -a "$APP_NAME"
}

cmd_wireguard() {
    info "WireGuard VPN management"
    echo "1) Create WireGuard peer"
    echo "2) List WireGuard peers"
    echo "3) Remove WireGuard peer"

    choice=$(prompt "Choose option:" "0")
    case $choice in
        1) fly wireguard create ;;
        2) fly wireguard list ;;
        3)
            fly wireguard list
            peer=$(prompt "Peer name to remove:" "")
            [[ -n "$peer" ]] && fly wireguard remove "$peer"
            ;;
    esac
}

cmd_proxy() {
    select_app
    port=$(prompt "Local port:" "8080")
    remote_port=$(prompt "Remote port:" "8080")

    info "Proxying localhost:$port -> app:$remote_port"
    fly proxy "$port:$remote_port" -a "$APP_NAME"
}

cmd_sftp() {
    select_app
    operation=$(prompt "Operation (get/put):" "get")

    if [[ "$operation" == "get" ]]; then
        remote=$(prompt "Remote path:" "")
        local=$(prompt "Local path:" ".")
        fly ssh sftp get "$remote" "$local" -a "$APP_NAME"
    elif [[ "$operation" == "put" ]]; then
        local=$(prompt "Local path:" "")
        remote=$(prompt "Remote path:" "")
        fly ssh sftp put "$local" "$remote" -a "$APP_NAME"
    fi
}

# ============================================================================
# QUICK ACTIONS MENU (Most Common Tasks)
# ============================================================================

menu_quick_actions() {
    while true; do
        echo -e "\n${CYAN}═══════════════════════════════════════${NC}"
        echo -e "${CYAN}   ⚡ QUICK ACTIONS (Common Tasks)${NC}"
        echo -e "${CYAN}═══════════════════════════════════════${NC}"
        echo "1)  📊 View App Status & Info"
        echo "2)  📝 View Logs (last 100 lines)"
        echo "3)  🚀 Deploy App"
        echo "4)  📈 Scale App (simple)"
        echo ""
        echo -e "${CYAN}Machine Control:${NC}"
        echo "5)  ⏸️  Stop/Suspend Machine"
        echo "6)  ▶️  Start/Resume Machine"
        echo "7)  🔄 Restart Machine"
        echo "8)  🛑 Stop All (scale to 0)"
        echo ""
        echo "9)  🔐 Manage Secrets"
        echo "10) 🌐 Open Dashboard"
        echo "0)  ← Back to main menu"
        echo -e "${CYAN}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1)
                select_app
                info "App Status:"
                fly status -a "$APP_NAME"
                ;;
            2)
                select_app
                info "Recent Logs (last 100 lines):"
                fly logs -a "$APP_NAME" --lines 100
                ;;
            3)
                select_app
                if confirm "Deploy $APP_NAME now?"; then
                    fly deploy -a "$APP_NAME"
                fi
                ;;
            4)
                select_app
                fly scale show -a "$APP_NAME"
                count=$(prompt "Enter new machine count (or 0 to return):" "")
                if [[ -n "$count" ]] && [[ "$count" -gt 0 ]]; then
                    fly scale count "$count" -a "$APP_NAME"
                    success "Scaled to $count machines"
                fi
                ;;
            5)
                select_app
                info "Showing machines:"
                fly machine list -a "$APP_NAME"
                echo ""
                echo "Choose action:"
                echo "  1) Stop machine (full shutdown)"
                echo "  2) Suspend machine (faster restart - recommended)"
                action=$(prompt "Choose (1-2):" "2")
                machine_id=$(prompt "Machine ID:" "")
                if [[ -n "$machine_id" ]]; then
                    if [[ "$action" == "1" ]]; then
                        fly machine stop "$machine_id" -a "$APP_NAME"
                        success "Machine stopped (use option 6 to start)"
                    else
                        fly machine suspend "$machine_id" -a "$APP_NAME"
                        success "Machine suspended (use option 6 to resume)"
                    fi
                fi
                ;;
            6)
                select_app
                info "Showing machines:"
                fly machine list -a "$APP_NAME"
                echo ""
                machine_id=$(prompt "Machine ID to start/resume:" "")
                if [[ -n "$machine_id" ]]; then
                    fly machine start "$machine_id" -a "$APP_NAME"
                    success "Machine started"
                fi
                ;;
            7)
                select_app
                info "Showing machines:"
                fly machine list -a "$APP_NAME"
                echo ""
                machine_id=$(prompt "Machine ID to restart:" "")
                if [[ -n "$machine_id" ]]; then
                    fly machine restart "$machine_id" -a "$APP_NAME"
                    success "Machine restarted"
                fi
                ;;
            8)
                select_app
                if confirm "Stop ALL machines (scale to 0)?"; then
                    fly scale count 0 -a "$APP_NAME"
                    success "All machines stopped. Use 'Scale App' to restart."
                fi
                ;;
            9) menu_secrets ;;
            10) cmd_apps_dashboard ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

# ============================================================================
# COMBINED MENUS (Simplified Organization)
# ============================================================================

menu_apps_deploy() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   📦 APP & DEPLOYMENT${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${CYAN}App Management:${NC}"
        echo "1)  List all apps"
        echo "2)  Create new app"
        echo "3)  Show app info"
        echo "4)  Restart app"
        echo "5)  Destroy app (DELETE)"
        echo ""
        echo -e "${CYAN}Deployment:${NC}"
        echo "6)  Deploy app (simple)"
        echo "7)  Launch new app from current directory"
        echo "8)  Deploy with custom Dockerfile"
        echo "9)  Redeploy previous release"
        echo "10) View releases"
        echo "0)  ← Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) fly apps list ;;
            2) cmd_apps_create ;;
            3) cmd_apps_info ;;
            4) select_app && fly apps restart -a "$APP_NAME" ;;
            5) cmd_apps_destroy ;;
            6) select_app && fly deploy -a "$APP_NAME" ;;
            7) cmd_launch ;;
            8) cmd_deploy_dockerfile ;;
            9) cmd_redeploy ;;
            10) select_app && fly releases -a "$APP_NAME" ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

menu_machines_scale() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   🖥️  MACHINES & SCALING${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${CYAN}Machine Control:${NC}"
        echo "1)  📋 List machines"
        echo "2)  ▶️  Start machine"
        echo "3)  ⏸️  Stop machine"
        echo "4)  💤 Suspend machine (faster restart)"
        echo "5)  🔄 Restart machine"
        echo "6)  💻 SSH into machine"
        echo ""
        echo -e "${CYAN}Scaling:${NC}"
        echo "7)  📊 Show current scale"
        echo "8)  📈 Scale machine count (simple)"
        echo "9)  🌍 Scale by region"
        echo "10) 🔀 Scale by process group (frontend/backend)"
        echo "11) 🚀 Scale VM size (CPU/Memory)"
        echo "12) 🛑 Scale to zero (stop all)"
        echo "13) ⚙️  Autoscale info"
        echo "0)  ← Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) select_app && fly machine list -a "$APP_NAME" ;;
            2) cmd_machine_start ;;
            3) cmd_machine_stop ;;
            4) cmd_machine_suspend ;;
            5) cmd_machine_restart ;;
            6) cmd_machine_ssh ;;
            7) select_app && fly scale show -a "$APP_NAME" ;;
            8) cmd_scale_count ;;
            9) cmd_scale_count_region ;;
            10) cmd_scale_count_group ;;
            11) cmd_scale_vm ;;
            12) cmd_scale_zero ;;
            13) cmd_autoscale ;;
            0) return ;;
            *) warning "Invalid option" ;;
        esac
    done
}

menu_configuration() {
    while true; do
        echo -e "\n${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${MAGENTA}   ⚙️  CONFIGURATION${NC}"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
        echo -e "${CYAN}Secrets:${NC}"
        echo "1)  List secrets"
        echo "2)  Set secret"
        echo "3)  Unset secret"
        echo "4)  Import secrets from file"
        echo ""
        echo -e "${CYAN}Volumes:${NC}"
        echo "5)  List volumes"
        echo "6)  Create volume"
        echo "7)  Extend volume"
        echo "8)  Destroy volume"
        echo ""
        echo -e "${CYAN}Networking:${NC}"
        echo "9)  List IP addresses"
        echo "10) Allocate IPv4/IPv6"
        echo "11) List certificates"
        echo "12) Add certificate"
        echo "0)  ← Back to main menu"
        echo -e "${MAGENTA}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            # Secrets
            1) select_app && fly secrets list -a "$APP_NAME" ;;
            2) cmd_secret_set ;;
            3) cmd_secret_unset ;;
            4) cmd_secret_import ;;
            # Volumes
            5) select_app && fly volumes list -a "$APP_NAME" ;;
            6) cmd_volume_create ;;
            7) cmd_volume_extend ;;
            8) cmd_volume_destroy ;;
            # Networking
            9) select_app && fly ips list -a "$APP_NAME" ;;
            10)
                echo "  1) Allocate IPv4"
                echo "  2) Allocate IPv6"
                echo "  3) Allocate Private IPv6"
                ip_choice=$(prompt "Choose:" "1")
                case $ip_choice in
                    1) cmd_ip_allocate_v4 ;;
                    2) cmd_ip_allocate_v6 ;;
                    3) cmd_ip_allocate_private ;;
                esac
                ;;
            11) select_app && fly certs list -a "$APP_NAME" ;;
            12) cmd_cert_add ;;
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
        # Show app status if selected
        echo -e "\n${CYAN}╔═══════════════════════════════════════╗${NC}"
        echo -e "${CYAN}║   🚀 FLY.IO MANAGER v1.0.0            ║${NC}"
        echo -e "${CYAN}╚═══════════════════════════════════════╝${NC}"

        if [[ -n "$APP_NAME" ]]; then
            echo -e "${GREEN}📱 Current App: ${NC}${BOLD}$APP_NAME${NC}"
            # Show quick status if possible
            status_output=$(fly status -a "$APP_NAME" 2>/dev/null | grep -E "State|Machines" | head -2)
            if [[ -n "$status_output" ]]; then
                echo -e "${BLUE}$status_output${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  No app selected${NC}"
        fi

        echo ""
        echo -e "${MAGENTA}═══ Main Menu ═══${NC}"
        echo "1)  ⚡ Quick Actions (Most Common)"
        echo "2)  📦 App & Deployment"
        echo "3)  🖥️  Machines & Scaling"
        echo "4)  ⚙️  Configuration (Secrets, Volumes, Network)"
        echo "5)  📊 Monitoring & Logs"
        echo "6)  🔧 Advanced Operations"
        echo ""
        echo "9)  🔄 Select/Change App"
        echo "0)  👋 Exit"
        echo -e "${CYAN}═══════════════════════════════════════${NC}"

        choice=$(prompt "Choose option:" "0")

        case $choice in
            1) menu_quick_actions ;;
            2) menu_apps_deploy ;;
            3) menu_machines_scale ;;
            4) menu_configuration ;;
            5) menu_monitoring ;;
            6) menu_advanced ;;
            9) APP_NAME=""; select_app ;;
            0)
                success "👋 Goodbye!"
                exit 0
                ;;
            *) warning "Invalid option. Please choose 0-6 or 9." ;;
        esac
    done
}

# ============================================================================
# CLI MODE (Non-interactive)
# ============================================================================

cli_mode() {
    local command="$1"
    shift

    case "$command" in
        # App Management
        apps-list) fly apps list "$@" ;;
        apps-create) cmd_apps_create ;;
        apps-info) select_app && fly status -a "$APP_NAME" ;;
        apps-dashboard) cmd_apps_dashboard ;;
        apps-destroy) select_app && fly apps destroy "$APP_NAME" --yes ;;
        apps-restart) select_app && fly apps restart -a "$APP_NAME" ;;
        apps-config) select_app && fly config show -a "$APP_NAME" ;;
        apps-releases) select_app && fly releases -a "$APP_NAME" ;;

        # Deployment
        launch) cmd_launch ;;
        deploy) select_app && fly deploy -a "$APP_NAME" "$@" ;;
        deploy-dockerfile) cmd_deploy_dockerfile ;;
        deploy-image) cmd_deploy_image ;;
        deploy-build-only) select_app && fly deploy -a "$APP_NAME" --build-only ;;
        deploy-env) cmd_deploy_env ;;
        deploy-secrets) cmd_deploy_secrets ;;
        deploy-redeploy) cmd_redeploy ;;

        # Machines
        machines-list) select_app && fly machine list -a "$APP_NAME" ;;
        machines-create) cmd_machine_create ;;
        machines-clone) cmd_machine_clone ;;
        machines-start) cmd_machine_start ;;
        machines-stop) cmd_machine_stop ;;
        machines-suspend) cmd_machine_suspend ;;
        machines-restart) cmd_machine_restart ;;
        machines-destroy) cmd_machine_destroy ;;
        machines-update) cmd_machine_update ;;
        machines-run) cmd_machine_run ;;
        machines-ssh) cmd_machine_ssh ;;
        machines-logs) cmd_machine_logs ;;

        # Scaling
        scale-show) select_app && fly scale show -a "$APP_NAME" ;;
        scale-count) cmd_scale_count ;;
        scale-count-region) cmd_scale_count_region ;;
        scale-count-group) cmd_scale_count_group ;;
        scale-vm) cmd_scale_vm ;;
        scale-vm-group) cmd_scale_vm_group ;;
        scale-zero) cmd_scale_zero ;;
        scale-autoscale) cmd_autoscale ;;

        # Secrets
        secrets-list) select_app && fly secrets list -a "$APP_NAME" ;;
        secrets-set) cmd_secret_set ;;
        secrets-set-multiple) cmd_secret_set_multiple ;;
        secrets-set-staged) cmd_secret_set_staged ;;
        secrets-deploy) select_app && fly secrets deploy -a "$APP_NAME" ;;
        secrets-unset) cmd_secret_unset ;;
        secrets-import) cmd_secret_import ;;

        # Volumes
        volumes-list) select_app && fly volumes list -a "$APP_NAME" ;;
        volumes-create) cmd_volume_create ;;
        volumes-show) cmd_volume_show ;;
        volumes-extend) cmd_volume_extend ;;
        volumes-fork) cmd_volume_fork ;;
        volumes-destroy) cmd_volume_destroy ;;
        volumes-snapshots-list) cmd_volume_snapshots_list ;;
        volumes-snapshot-create) cmd_volume_snapshot_create ;;
        volumes-restore) cmd_volume_restore ;;

        # Networking
        ips-list) select_app && fly ips list -a "$APP_NAME" ;;
        ips-allocate-v4) cmd_ip_allocate_v4 ;;
        ips-allocate-v6) cmd_ip_allocate_v6 ;;
        ips-allocate-private) cmd_ip_allocate_private ;;
        ips-release) cmd_ip_release ;;
        ips-private) select_app && fly ips private -a "$APP_NAME" ;;
        certs-list) select_app && fly certs list -a "$APP_NAME" ;;
        certs-add) cmd_cert_add ;;
        certs-remove) cmd_cert_remove ;;
        services-list) select_app && fly services list -a "$APP_NAME" ;;

        # Monitoring & Logs
        status) select_app && fly status -a "$APP_NAME" ;;
        logs) select_app && fly logs -a "$APP_NAME" "$@" ;;
        logs-100) select_app && fly logs -a "$APP_NAME" --lines 100 ;;
        logs-machine) cmd_logs_machine ;;
        checks) select_app && fly checks list -a "$APP_NAME" ;;
        ping) select_app && fly ping -a "$APP_NAME" ;;
        dashboard) cmd_apps_dashboard ;;
        releases) select_app && fly releases -a "$APP_NAME" ;;

        # Advanced Operations
        auth-token) fly auth token ;;
        token-deploy) cmd_token_deploy ;;
        wireguard) cmd_wireguard ;;
        proxy) cmd_proxy ;;
        sftp) cmd_sftp ;;
        platform) fly platform ;;
        platform-regions) fly platform regions ;;
        platform-vm-sizes) fly platform vm-sizes ;;
        config-show) select_app && fly config show -a "$APP_NAME" ;;
        config-validate) fly config validate ;;

        # Help
        help|--help|-h)
            echo "Fly.io Manager - CLI Mode"
            echo ""
            echo "Usage: $0 <command> [args]"
            echo ""
            echo "App Management:"
            echo "  apps-list           List all apps"
            echo "  apps-info           Show app information"
            echo "  apps-dashboard      Open app dashboard"
            echo "  apps-restart        Restart app"
            echo "  apps-config         Show app config"
            echo "  apps-releases       Show app releases"
            echo ""
            echo "Deployment:"
            echo "  launch              Launch new app"
            echo "  deploy              Deploy app"
            echo "  deploy-build-only   Build without deploying"
            echo ""
            echo "Machines:"
            echo "  machines-list       List machines"
            echo "  machines-start      Start a machine"
            echo "  machines-stop       Stop a machine"
            echo "  machines-suspend    Suspend a machine (faster restart)"
            echo "  machines-ssh        SSH into machine"
            echo "  machines-logs       View machine logs"
            echo ""
            echo "Scaling:"
            echo "  scale-show          Show current scale"
            echo "  scale-count         Scale machine count"
            echo "  scale-vm            Scale VM size"
            echo "  scale-autoscale     Show autoscale config info"
            echo ""
            echo "Secrets:"
            echo "  secrets-list        List secrets"
            echo "  secrets-set         Set a secret"
            echo ""
            echo "Volumes:"
            echo "  volumes-list        List volumes"
            echo "  volumes-create      Create volume"
            echo ""
            echo "Networking:"
            echo "  ips-list            List IP addresses"
            echo "  ips-allocate-v4     Allocate IPv4"
            echo "  ips-allocate-v6     Allocate IPv6"
            echo "  certs-list          List certificates"
            echo ""
            echo "Monitoring:"
            echo "  status              Show app status"
            echo "  logs                View logs"
            echo "  checks              List health checks"
            echo "  dashboard           Open dashboard"
            echo ""
            echo "Advanced:"
            echo "  platform-regions    List regions"
            echo "  platform-vm-sizes   List VM sizes"
            echo "  config-show         Show fly.toml"
            echo ""
            echo "Run with no arguments for interactive mode"
            ;;

        *)
            error "Unknown command: $command"
            echo "Run '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Clear screen for interactive mode
    [[ "$INTERACTIVE" == "true" ]] && clear

    # Check prerequisites
    check_flyctl
    check_auth

    # CLI mode or interactive?
    if [[ $# -gt 0 ]]; then
        INTERACTIVE=false
        cli_mode "$@"
    else
        INTERACTIVE=true
        main_menu
    fi
}

# Run main if not sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
