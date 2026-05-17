# Quick Test Setup and Execution Guide

## Installation

### 1. Install Test Dependencies

```bash
# From project root directory
pip install -r test-requirements.txt
```

This installs:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-flask` - Flask test utilities
- `selenium` - Browser automation
- `webdriver-manager` - Automatic WebDriver management

### 2. Verify Installation

```bash
pytest --version
```

## Running Tests

### All Tests
```bash
pytest test/ -v
```

### Unit Tests Only (Fast)
```bash
pytest test/ --ignore=test/test_selenium.py -v
```

### Selenium Tests Only (Requires Live Server)
```bash
pytest test/test_selenium.py -v
```

### Specific Test File
```bash
pytest test/test_auth.py -v
```

### Specific Test Class
```bash
pytest test/test_auth.py::TestSignup -v
```

### Specific Test
```bash
pytest test/test_auth.py::TestSignup::test_signup_success -v
```

## Test Runner Script

For easier test execution, use the provided `run_tests.py` script:

```bash
# Show all available commands
python run_tests.py

# Run unit tests
python run_tests.py unit

# Run Selenium tests
python run_tests.py selenium

# Run all tests
python run_tests.py all

# Run with coverage
python run_tests.py coverage

# Run specific category
python run_tests.py auth       # Authentication tests
python run_tests.py friends    # Friends tests
python run_tests.py events     # Events tests
python run_tests.py integration # Integration tests
```

## Coverage Report

### Generate Coverage Report
```bash
pytest test/ --cov=. --cov-report=html
```

### View Coverage Report
```bash
# Open in browser
open htmlcov/index.html          # macOS
start htmlcov/index.html         # Windows
xdg-open htmlcov/index.html      # Linux
```

## Troubleshooting

### Issue: Selenium Tests Timeout
**Solution**: Ensure port 5000 is not in use
```bash
# Check for processes using port 5000
lsof -i :5000              # macOS/Linux
netstat -ano | grep 5000   # Windows
```

### Issue: Chrome WebDriver Not Found
**Solution**: Update webdriver-manager
```bash
pip install --upgrade webdriver-manager
```

### Issue: Import Errors in Tests
**Solution**: Ensure you're in the project root
```bash
cd /path/to/AgileWebDev
pytest test/
```

### Issue: Database Lock Errors
**Solution**: Clean up temporary files
```bash
rm -f /tmp/pytest-*.db
```

## Test Statistics

| Category | Count |
|----------|-------|
| Total Unit Tests | 90+ |
| Total Selenium Tests | 10 |
| Test Files | 12 |
| Test Classes | 40+ |
| Estimated Coverage | 75%+ |

## Continuous Integration

For CI/CD pipelines:

```bash
# Run all tests with JUnit XML output
pytest test/ --junit-xml=test-results.xml -v

# Run with coverage XML (for codecov)
pytest test/ --cov=. --cov-report=xml test/

# Fail if coverage below threshold
pytest test/ --cov=. --cov-fail-under=75 test/
```

## Common Test Commands

```bash
# Run tests and stop at first failure
pytest test/ -x

# Run tests in reverse order
pytest test/ --reverse

# Run tests with specific keyword
pytest test/ -k "auth"
pytest test/ -k "not selenium"

# Run tests with markers
pytest test/ -m auth
pytest test/ -m "integration or friends"

# Verbose output with print statements
pytest test/ -v -s

# Quiet mode
pytest test/ -q

# Show test durations
pytest test/ --durations=5
```

## Routes Tested

The test suite validates all application routes:

| Route | Method | Authentication | Tested |
|-------|--------|-----------------|--------|
| `/signup` | GET/POST | No | ✅ |
| `/signin` | GET/POST | No | ✅ |
| `/logout` | POST | Yes | ✅ |
| `/` | GET | Yes | ✅ |
| `/add-event` | GET/POST | Yes | ✅ |
| `/timetable/restore` | POST | Yes | ✅ |
| `/settings` | GET/POST | Yes | ✅ |
| `/friends` | GET | Yes | ✅ |
| `/api/events/me` | GET | Yes | ✅ |
| `/api/events/<id>` | DELETE | Yes | ✅ |
| `/api/map/current-class` | GET | Yes | ✅ |
| `/api/friends/classes` | GET | Yes | ✅ |

## Test Markers

Run tests by category using markers:

```bash
# Authentication tests
pytest test/ -m auth

# Friends tests
pytest test/ -m friends

# Events tests
pytest test/ -m events

# Integration tests
pytest test/ -m integration

# Unit tests
pytest test/ -m unit

# Selenium tests
pytest test/ -m selenium

# Multiple markers
pytest test/ -m "auth or friends"
pytest test/ -m "not selenium"
```

## Performance Tips

```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest test/ -n auto

# Run only changed tests (requires pytest-testmon)
pip install pytest-testmon
pytest test/ --testmon

# Run tests in watch mode (requires pytest-watch)
pip install pytest-watch
ptw test/
```

## Documentation Files

- `TEST_SUITE.md` - Comprehensive test documentation
- `TEST_SUMMARY.md` - Test requirements verification
- `test/README.md` - Original test documentation
- `test/QUICKSTART.md` - Test quick start guide

---

For detailed information about specific tests, see [TEST_SUITE.md](TEST_SUITE.md)
