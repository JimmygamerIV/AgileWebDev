# UniMap Application Test Suite

Comprehensive pytest test suite for the UniMap web application.

## Quick Start

### 1. Install Testing Dependencies

```bash
pip install -r test-requirements.txt
```

### 2. Run All Tests

```bash
pytest
```

### 3. Run with Coverage Report

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```

### 4. Run Specific Test Categories

```bash
# Authentication tests
pytest test/test_auth.py -v

# Friends functionality
pytest test/test_friends.py -v

# Events and timetables
pytest test/test_events.py -v

# Database models
pytest test/test_models.py -v

# Database operations
pytest test/test_database.py -v

# Form validation
pytest test/test_forms.py -v
```

### 5. Run by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run authentication tests
pytest -m auth

# Run without slow tests
pytest -m "not slow"
```

## Test Structure

```
test/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_auth.py             # Authentication (signup, signin, logout)
├── test_friends.py          # Friends management
├── test_events.py           # Events and timetable import
├── test_models.py           # Database model tests
├── test_database.py         # Database operations and constraints
└── test_forms.py            # Form validation
```

## Test Coverage

### Authentication (test_auth.py)
- ✅ Signup with valid/invalid inputs
- ✅ Password validation rules (length, uppercase, lowercase, numbers)
- ✅ Email domain validation (UWA emails only)
- ✅ Duplicate username/email handling
- ✅ Signin with correct/incorrect credentials
- ✅ Session management
- ✅ User loading from session

### Friends (test_friends.py)
- ✅ Friend list management
- ✅ Favourite friend marking
- ✅ Friend requests (send, accept, reject)
- ✅ Friend discovery
- ✅ Friend list sorting and filtering
- ✅ Incoming and outgoing requests

### Events & Timetables (test_events.py)
- ✅ Event creation and deletion
- ✅ Event querying by user, day, date
- ✅ ICS file import
- ✅ Multiple event handling
- ✅ Event overwriting on import
- ✅ Missing field handling in imports

### Models (test_models.py)
- ✅ User model with all fields
- ✅ Friend relationships
- ✅ Friend requests with status validation
- ✅ Events and event scheduling
- ✅ Unique constraints (username, email)
- ✅ Composite primary keys

### Database (test_database.py)
- ✅ Database initialization
- ✅ Session management
- ✅ Transaction handling
- ✅ Constraint enforcement
- ✅ Query operations
- ✅ Edge cases (null values, special characters, unicode)

### Forms (test_forms.py)
- ✅ SignupForm validation
- ✅ SigninForm validation
- ✅ ImportTimetableForm validation
- ✅ AddFriendForm validation
- ✅ FriendActionForm handling
- ✅ Required and optional field validation

## Running Tests

### Basic Commands

```bash
# Run all tests with verbose output
pytest -v

# Run a single test file
pytest test/test_auth.py

# Run a specific test class
pytest test/test_auth.py::TestSignup

# Run a specific test function
pytest test/test_auth.py::TestSignup::test_signup_success

# Run tests matching a pattern
pytest -k "signup"

# Run tests and stop on first failure
pytest -x

# Run with detailed output
pytest -vv

# Show print statements
pytest -s

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=. --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=. --cov-report=html

# View coverage in terminal
pytest --cov=. --cov-report=term-missing:skip-covered
```

### Debugging Tests

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb

# Show local variables on failure
pytest -l

# Verbose with long tracebacks
pytest -vv --tb=long
```

## Fixtures

Common fixtures defined in `conftest.py`:

### Database Fixtures
- `db_session`: Database session for each test
- `temp_db`: Temporary test database
- `app`: Flask test application
- `client`: Flask test client
- `runner`: CLI test runner

### User Fixtures
- `sample_user`: Test user (username: testuser)
- `sample_user_2`: Second test user (username: testuser2)
- `sample_user_3`: Third test user (username: testuser3)
- `authenticated_client`: Test client with authenticated session

### Data Fixtures
- `sample_event`: Test event for sample_user

## Example Test

```python
def test_signup_success(self, client, db_session):
    """Test successful signup."""
    response = client.post('/signup', data={
        'username': 'newuser',
        'nickname': 'New User',
        'password': 'SecurePass123',
        'confirm_password': 'SecurePass123',
        'email': 'newuser@student.uwa.edu.au',
        'csrf_token': 'dummy'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    user = db_session.query(User).filter(User.username == 'newuser').first()
    assert user is not None
```

## Best Practices

1. **Use Fixtures**: Leverage pytest fixtures for common setup
2. **Group Related Tests**: Use test classes to organize related tests
3. **Clear Naming**: Use descriptive test names that explain what's being tested
4. **One Assertion Per Test**: Keep tests focused and isolated
5. **Mock External Dependencies**: Use pytest-mock for external services
6. **Test Edge Cases**: Include tests for boundary conditions and error cases
7. **Keep Tests Fast**: Avoid unnecessary database commits or file I/O
8. **Use Markers**: Organize tests with markers for selective execution

## Continuous Integration

For CI/CD pipelines, run:

```bash
pytest --cov=. --cov-report=xml --cov-report=term-missing --junitxml=junit.xml
```

This generates:
- `coverage.xml`: For coverage tracking
- `junit.xml`: For test reporting
- Terminal output: Coverage summary

## Troubleshooting

### Database Errors
- Ensure SQLite is available
- Check database file permissions
- Use `-s` flag to see database errors

### Import Errors
- Verify all dependencies in `test-requirements.txt` are installed
- Check `PYTHONPATH` includes the project root

### Fixture Errors
- Ensure `conftest.py` is in test directory
- Check fixture scope matches test requirements

### Test Failures
- Run with `-vv` for detailed output
- Use `--pdb` to debug interactively
- Check test isolation (parallel tests might fail)

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Add tests in appropriate test file
3. Run full test suite to ensure no regressions
4. Update this README if adding new test categories
5. Maintain >80% code coverage

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/testing/)
