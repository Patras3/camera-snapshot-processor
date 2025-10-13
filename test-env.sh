#!/bin/bash
# Helper script for managing the Home Assistant test environment

set -e

CONTAINER_NAME="camera-snap-tune-test"

show_help() {
    cat << EOF
Usage: ./test-env.sh [COMMAND]

Commands:
  start       Start the Home Assistant test environment
  stop        Stop the Home Assistant test environment
  restart     Restart the Home Assistant container
  logs        Show logs from the container (use -f to follow)
  status      Show container status
  url         Show the URL to access Home Assistant
  shell       Open a shell inside the container
  help        Show this help message

Examples:
  ./test-env.sh start
  ./test-env.sh logs -f
  ./test-env.sh restart
EOF
}

get_wsl_ip() {
    # Get WSL IP address for accessing from Windows
    hostname -I | awk '{print $1}'
}

case "${1:-help}" in
    start)
        echo "Starting Home Assistant test environment..."
        docker compose up -d
        echo ""
        echo "Home Assistant is starting up..."
        echo "This may take a few minutes on first start."
        echo ""
        echo "Access URLs:"
        echo "  From WSL:     http://localhost:8123"
        echo "  From Windows: http://$(get_wsl_ip):8123"
        echo ""
        echo "Use './test-env.sh logs -f' to follow the logs"
        ;;

    stop)
        echo "Stopping Home Assistant test environment..."
        docker compose down
        echo "Environment stopped."
        ;;

    restart)
        echo "Restarting Home Assistant container..."
        docker restart $CONTAINER_NAME
        echo "Container restarted."
        ;;

    logs)
        shift
        docker logs $CONTAINER_NAME "$@"
        ;;

    status)
        if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
            echo "Status: Running"
            docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        else
            echo "Status: Not running"
        fi
        ;;

    url)
        if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
            echo "Access URLs:"
            echo "  From WSL:     http://localhost:8123"
            echo "  From Windows: http://$(get_wsl_ip):8123"
        else
            echo "Container is not running. Start it with: ./test-env.sh start"
        fi
        ;;

    shell)
        docker exec -it $CONTAINER_NAME /bin/bash
        ;;

    help|--help|-h)
        show_help
        ;;

    *)
        echo "Error: Unknown command '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac
