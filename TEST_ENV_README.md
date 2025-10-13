# Home Assistant Test Environment

This directory contains a Docker-based test environment for the camera-snap-tune custom component.

## Quick Start

1. Start the test environment:
   ```bash
   ./test-env.sh start
   ```

2. Access Home Assistant:
   - From WSL: http://localhost:8123
   - From Windows: Use the IP shown in the terminal output (typically http://172.x.x.x:8123)

3. On first start, create an account and complete the onboarding process

4. Add your test cameras to `test_config/configuration.yaml` (they will persist across restarts)

## Usage

The `test-env.sh` script provides all the commands you need:

```bash
./test-env.sh start      # Start the environment
./test-env.sh stop       # Stop the environment
./test-env.sh restart    # Restart the container
./test-env.sh logs       # View logs
./test-env.sh logs -f    # Follow logs in real-time
./test-env.sh status     # Check if container is running
./test-env.sh url        # Show access URLs
./test-env.sh shell      # Open a shell inside the container
```

## Automatic Restart on Commit

The test environment includes a git post-commit hook that automatically restarts the container when you commit changes. This means:

1. Make changes to the code
2. Commit them: `git add . && git commit -m "Your message"`
3. The container will automatically restart
4. Refresh the Home Assistant UI to see your changes

## Adding Test Cameras

Edit `test_config/configuration.yaml` and add your cameras. For example:

```yaml
camera:
  - platform: generic
    name: Test Camera 1
    still_image_url: https://example.com/camera1.jpg
    username: !secret camera_username
    password: !secret camera_password
```

Create `test_config/secrets.yaml` for sensitive data:

```yaml
camera_username: your_username
camera_password: your_password
```

## Directory Structure

- `docker-compose.yml` - Docker Compose configuration
- `test_config/` - Home Assistant configuration directory
  - `configuration.yaml` - Main configuration file (tracked in git)
  - Other files are auto-generated and ignored by git
- `test-env.sh` - Helper script for managing the environment
- `.git/hooks/post-commit` - Auto-restart hook

## Troubleshooting

### Cannot access from Windows
If you can't access Home Assistant from Windows, check:
1. Run `./test-env.sh url` to get the correct IP
2. Make sure Windows Firewall allows WSL connections
3. Try accessing from WSL first to verify it's running

### Container won't start
Check the logs:
```bash
./test-env.sh logs
```

### Changes not appearing
1. Make sure you committed your changes (this triggers the restart)
2. Clear your browser cache
3. Check logs for errors: `./test-env.sh logs -f`

### Post-commit hook not working
Make sure it's executable:
```bash
chmod +x .git/hooks/post-commit
```

## Cleaning Up

To completely remove the test environment and all data:

```bash
./test-env.sh stop
rm -rf test_config/*
docker volume prune
```

Note: This will delete all your test configuration and data!
