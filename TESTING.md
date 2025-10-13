# Testing and Pre-Commit Guide

## Overview

This project includes comprehensive tests and pre-commit hooks to ensure code quality and functionality before commits.

## Quick Setup

```bash
./setup-pre-commit.sh
```

This will:
1. Create/activate virtual environment
2. Install all dependencies
3. Install pre-commit hooks
4. Run initial test suite

## Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install homeassistant aiohttp voluptuous pillow numpy pre-commit

# Install pre-commit hooks
pre-commit install
```

## Test Suites

### 1. Integration Tests (`test_integration.py`)
Tests the core structure and compatibility with Home Assistant:
- Module imports
- Config flow structure
- API view registration
- Constants validation
- File existence

**Run manually:**
```bash
./venv/bin/python test_integration.py
```

### 2. API Flow Tests (`test_api_flow.py`)
Tests all API endpoints with mock requests:
- Config GET/POST
- Preview generation
- Source image retrieval
- Entity listing
- Error handling

**Run manually:**
```bash
./venv/bin/python test_api_flow.py
```

### 3. Frontend Validation (`test_frontend.py`)
Validates frontend code structure:
- HTML structure and IDs
- JavaScript functions and API calls
- CSS rules and styling
- Cross-reference consistency
- Common issues check

**Run manually:**
```bash
./venv/bin/python test_frontend.py
```

## Pre-Commit Hooks

When you commit, the following checks run automatically:

### Code Quality
- **Black**: Auto-formats Python code
- **isort**: Sorts Python imports
- **flake8**: Lints Python code

### File Checks
- Removes trailing whitespace
- Fixes end-of-file
- Validates JSON/YAML
- Checks file sizes

### Integration Tests
- Integration structure tests
- API flow tests
- Frontend validation
- Manifest validation
- API endpoint consistency

## Running Tests

### Run all pre-commit hooks
```bash
pre-commit run --all-files
```

### Run specific hook
```bash
pre-commit run integration-tests
pre-commit run api-flow-tests
pre-commit run frontend-validation
```

### Run only on changed files
```bash
pre-commit run
```

## Skipping Hooks

**Not recommended**, but if needed:
```bash
git commit --no-verify
```

## Test Results

All test results are documented in `TEST_RESULTS.md`.

Current status: **25/25 tests passing** ✅

## CI/CD Integration

The pre-commit config can also be used in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run pre-commit
  uses: pre-commit/action@v3.0.0
```

## Troubleshooting

### Hook fails to run
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Dependencies missing
```bash
# Reinstall venv
rm -rf venv
./setup-pre-commit.sh
```

### Tests fail
1. Check `TEST_RESULTS.md` for expected behavior
2. Run tests individually to isolate issues
3. Verify Home Assistant dependencies are installed

## Development Workflow

1. Make changes to code
2. Stage changes: `git add .`
3. Commit: `git commit -m "message"`
4. Pre-commit hooks run automatically
5. If tests fail, fix issues and commit again
6. If tests pass, commit proceeds

## Adding New Tests

To add a new test hook:

1. Create test script (e.g., `test_new_feature.py`)
2. Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: new-test
      name: New Feature Test
      entry: ./venv/bin/python test_new_feature.py
      language: system
      pass_filenames: false
      always_run: true
```

## Performance

All tests complete in < 5 seconds on average:
- Integration tests: ~1s
- API flow tests: ~2s
- Frontend validation: ~1s
- Pre-commit hooks: ~1s

Total pre-commit time: **~5 seconds**

## Best Practices

1. **Always run tests before committing**
   - Pre-commit handles this automatically

2. **Don't skip hooks**
   - They catch issues early

3. **Keep tests fast**
   - Current suite is well-optimized

4. **Update tests when adding features**
   - Add corresponding test coverage

5. **Review test failures carefully**
   - They prevent broken code from being committed

## Support

If tests fail unexpectedly:
1. Check `TEST_RESULTS.md` for expected behavior
2. Review recent changes
3. Run tests individually for details
4. Check Home Assistant compatibility

---

**Remember:** These tests ensure your integration works correctly with Home Assistant before you even deploy it! 🚀
