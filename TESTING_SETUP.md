# UniMap Project - Testing Suite Setup

## Summary

A comprehensive pytest testing suite has been created for the UniMap web application. The suite includes **300+ tests** covering all major components, security, performance, and edge cases.

## Files Created

### In `test/` Directory

| File | Purpose | Tests |
|------|---------|-------|
| `conftest.py` | Pytest fixtures and configuration | Setup |
| `test_auth.py` | Authentication tests | 30+ |
| `test_friends.py` | Friends management tests | 25+ |
| `test_events.py` | Events and timetables tests | 20+ |
| `test_models.py` | Database model tests | 25+ |
| `test_database.py` | Database operations tests | 35+ |
| `test_forms.py` | Form validation tests | 15+ |
| `test_integration.py` | Integration tests | 15+ |
| `test_security.py` | **NEW** Security tests (CSRF, XSS, SQL injection) | 40+ |
| `test_boundaries.py` | **NEW** Boundary condition tests | 60+ |
| `test_errors.py` | **NEW** Error handling & data consistency | 50+ |
| `test_performance.py` | **NEW** Performance & scalability tests | 30+ |
| `test_utils.py` | Testing utilities and helpers | - |
| `README.md` | Comprehensive testing documentation | - |
| `QUICKSTART.md` | Quick start guide | - |
| `__init__.py` | Python package marker | - |

### In Root Directory

| File | Purpose |
|------|---------|
| `pytest.ini` | Pytest configuration |
| `test-requirements.txt` | Testing dependencies |

## Quick Start

### 1. Install Testing Dependencies
```bash
pip install -r test-requirements.txt
```

### 2. Run All Tests
```bash
pytest -v
```

### 3. Check Coverage
```bash
pytest --cov=. --cov-report=html
```

## Test Coverage

### Authentication (`test_auth.py`) - 30+ tests
- ✅ Signup with validation (password, email, username)
- ✅ Duplicate prevention
- ✅ Password requirements
- ✅ Email domain validation (UWA only)
- ✅ Signin with credentials
- ✅ Session management
- ✅ User loading from session

### Friends Management (`test_friends.py`) - 25+ tests
- ✅ Friend list building and sorting
- ✅ Friend requests (send, accept, reject)
- ✅ Favorite friend marking
- ✅ Incoming and outgoing requests
- ✅ Multiple friend handling
- ✅ Friend discovery

### Events & Timetables (`test_events.py`) - 20+ tests
- ✅ Event creation and management
- ✅ Event querying (by user, day, date)
- ✅ ICS file import and parsing
- ✅ Multiple event handling
- ✅ Event overwriting on import
- ✅ Missing field handling

### Database Models (`test_models.py`) - 25+ tests
- ✅ User model with all fields
- ✅ Friend relationships
- ✅ Friend requests with status
- ✅ Events and scheduling
- ✅ Unique constraints
- ✅ Composite primary keys

### Database Operations (`test_database.py`) - 35+ tests
- ✅ Database initialization
- ✅ Session management
- ✅ Transaction handling
- ✅ Constraint enforcement
- ✅ Query operations
- ✅ Edge cases (null, special chars, unicode)

### Form Validation (`test_forms.py`) - 15+ tests
- ✅ SignupForm validation
- ✅ SigninForm validation
- ✅ ImportTimetableForm
- ✅ AddFriendForm
- ✅ FriendActionForm
- ✅ Required and optional fields

### Integration Tests (`test_integration.py`) - 15+ tests
- ✅ Full signup → signin flow
- ✅ Friend request workflows
- ✅ Event management workflows
- ✅ Multi-user scenarios
- ✅ Data isolation

### **NEW: Security Tests** (`test_security.py`) - 40+ tests
- ✅ CSRF protection
- ✅ XSS prevention
- ✅ SQL injection prevention
- ✅ Authentication bypass attempts
- ✅ Session fixation prevention
- ✅ Password security (hashing, algorithms)
- ✅ Information disclosure prevention
- ✅ User enumeration prevention
- ✅ Rate limiting concerns

### **NEW: Boundary Condition Tests** (`test_boundaries.py`) - 60+ tests
- ✅ Username boundaries (min/max length)
- ✅ Password boundaries
- ✅ Email boundaries
- ✅ Event time boundaries (midnight, end of day)
- ✅ Nickname length limits
- ✅ Friendship edge cases
- ✅ Friend request status transitions
- ✅ Date boundaries (leap year, past/future dates)
- ✅ Special character handling
- ✅ Unicode support

### **NEW: Error Handling Tests** (`test_errors.py`) - 50+ tests
- ✅ Database error handling
- ✅ Concurrent operations
- ✅ Rollback mechanisms
- ✅ ICS import error handling
- ✅ Data consistency validation
- ✅ NULL value handling
- ✅ Unicode character handling
- ✅ Case sensitivity handling
- ✅ Empty string handling
- ✅ Type validation
- ✅ Referential integrity

### **NEW: Performance Tests** (`test_performance.py`) - 30+ tests
- ✅ Query performance
- ✅ Large dataset handling (100+ users, 1000+ events)
- ✅ Many friends scenario
- ✅ Many pending requests
- ✅ Complex query patterns
- ✅ Cascade delete operations
- ✅ Sorting and filtering
- ✅ Business logic validation

### Form Validation (`test_forms.py`) - 15+ tests
- ✅ SignupForm validation
- ✅ SigninForm validation
- ✅ ImportTimetableForm
- ✅ AddFriendForm
- ✅ FriendActionForm
- ✅ Required and optional fields

### Integration Tests (`test_integration.py`) - 15+ tests
- ✅ Full signup → signin flow
- ✅ Friend request workflows
- ✅ Event management workflows
- ✅ Multi-user scenarios
- ✅ Data isolation

## Available Fixtures

### Database Fixtures
- `db_session` - Database session for tests
- `app` - Flask test application
- `client` - Flask test client
- `runner` - CLI test runner
- `temp_db` - Temporary test database

### User Fixtures
- `sample_user` - Test user (testuser)
- `sample_user_2` - Second test user (testuser2)
- `sample_user_3` - Third test user (testuser3)
- `authenticated_client` - Authenticated test client

### Data Fixtures
- `sample_event` - Test event

## Common Commands

```bash
# Run all tests
pytest -v

# Run specific test file
pytest test/test_auth.py -v

# Run specific test
pytest test/test_auth.py::TestSignup::test_signup_success -v

# Run tests matching pattern
pytest -k "signup"

# Generate coverage report
pytest --cov=. --cov-report=html

# Run with coverage output
pytest --cov=. --cov-report=term-missing

# Debug a test
pytest -xvs test/test_auth.py::TestSignup::test_signup_success

# Run in parallel (requires pytest-xdist)
pytest -n auto

# Stop on first failure
pytest -x

# Collect tests without running
pytest --collect-only
```

## Testing Best Practices Used

1. **Comprehensive Fixtures** - Reusable test setup via conftest.py
2. **Organized Structure** - Tests grouped by feature/component
3. **Clear Naming** - Descriptive test names explaining what's tested
4. **Isolation** - Each test is independent with clean database
5. **Edge Cases** - Tests for boundaries, errors, and special cases
6. **Multiple Assertions** - Tests verify both success and failure paths
7. **Utilities** - Helper functions for common testing tasks
8. **Documentation** - README and QUICKSTART guides included

## Directory Structure

```
AgileWebDev/
├── app.py
├── auth.py
├── models.py
├── database.py
├── ... (other source files)
├── pytest.ini                 # NEW - Pytest config
├── test-requirements.txt       # NEW - Test dependencies
│
└── test/                       # NEW - Test directory
    ├── __init__.py            # NEW
    ├── conftest.py            # NEW - Fixtures
    ├── test_auth.py           # NEW - Auth tests (30+)
    ├── test_friends.py        # NEW - Friends tests (25+)
    ├── test_events.py         # NEW - Events tests (20+)
    ├── test_models.py         # NEW - Model tests (25+)
    ├── test_database.py       # NEW - DB tests (35+)
    ├── test_forms.py          # NEW - Form tests (15+)
    ├── test_integration.py    # NEW - Integration tests (15+)
    ├── test_utils.py          # NEW - Test utilities
    ├── README.md              # NEW - Full documentation
    ├── QUICKSTART.md          # NEW - Quick start guide
    └── SUMMARY.md             # NEW - This file
```

## Next Steps

1. **Run the tests**
   ```bash
   pytest test/ -v
   ```

2. **Check coverage**
   ```bash
   pytest --cov=. --cov-report=html
   ```

3. **Read the guides**
   - [test/QUICKSTART.md](test/QUICKSTART.md) - 5-minute setup
   - [test/README.md](test/README.md) - Comprehensive guide

4. **Add new tests** when adding features
   - Keep coverage > 80%
   - Follow existing patterns
   - Use provided fixtures

5. **Run in CI/CD pipeline**
   ```bash
   pytest --cov=. --cov-report=xml --junitxml=junit.xml
   ```

## Testing Dependencies

```
pytest==7.4.3
pytest-cov==4.1.0
pytest-flask==1.3.0
pytest-mock==3.12.0
coverage==7.3.2
```

Install with: `pip install -r test-requirements.txt`

## Test Statistics

- **Total Tests**: 300+
- **Test Files**: 11 (+ utilities)
- **Lines of Test Code**: 5000+
- **Coverage Target**: >80%
- **Estimated Run Time**: 3-5 seconds

## Support

For questions or issues:
1. Check [test/README.md](test/README.md) for detailed docs
2. Check [test/QUICKSTART.md](test/QUICKSTART.md) for quick help
3. Review test examples in test files
4. Check conftest.py for available fixtures
5. Use test_utils.py helpers for common tasks

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Place tests in appropriate test file
3. Use existing fixtures when possible
4. Ensure all tests pass: `pytest -v`
5. Check coverage: `pytest --cov=.`
6. Keep coverage > 80%