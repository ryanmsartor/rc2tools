#!/usr/bin/env bash
set -euo pipefail

rc2t_print_help_message() {
    echo ""
}




rc2t() {
    case "$1" in
        dump)
            :
            ;;
    
        *)
            rc2t_print_help_message
            ;;
    esac
}