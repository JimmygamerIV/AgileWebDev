# Testing Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies (1 min)
```bash
pip install -r test-requirements.txt
```

### Step 2: Run All Tests (2 min)
```bash
pytest -v
```

### Step 3: Check Coverage (1 min)
```bash
pytest --cov=. --cov-report=term-missing
```

### Step 4: View Results (1 min)
See the test output with pass/fail status and coverage percentage.

---

## Common Commands

### Run Specific Test Files
```bash
pytest test/test_auth.py              # Authentication tests
pytest test/test_friends.py           # Friends tests
pytest test/test_events.py            # Events tests
pytest test/test_models.py            # Model tests
pytest test/test_database.py          # Database tests
pytest test/test_integration.py       # Integration tests
```

### Run Specific Test
```bash
pytest test/test_auth.py::TestSignup::test_signup_success -v
```

### Run Tests Matching Pattern
```bash
pytest -k "signup"
pytest -k "friend"
pytest -k "event"
```

### Debug a Failing Test
```bash
pytest -xvs test/test_auth.py::TestSignup::test_signup_success
```
- `-x`: Stop on first failure
- `-v`: Verbose output
- `-s`: Show print statements

### Generate Coverage Report
```bash
# Terminal report
pytest --cov=. --cov-report=term-missing

# HTML report (open htmlcov/index.html in browser)
pytest --cov=. --cov-report=html

# Both
pytest --cov=. --cov-report=html --cov-report=term-missing
```

---

## Test Files Overview

| File | Tests | Coverage |
|------|-------|----------|
| `test_auth.py` | Signup, signin, session | Authentication flow |
| `test_friends.py` | Friend requests, favorites | Friends management |
| `test_events.py` | Event creation, ICS import | Events & timetables |
| `test_models.py` | Model validation | Database models |
| `test_database.py` | Queries, constraints | Database operations |
| `test_forms.py` | Form validation | Form inputs |
| `test_integration.py` | Multi-component flows | Complex scenarios |

---

## What's Tested

✅ **Authentication (55+ tests)**
- Signup with validation
- Signin with verification
- Session management
- Password requirements
- Email validation

✅ **Friends (30+ tests)**
- Friend requests
- Accepting/rejecting
- Favorite marking
- Friend lists
- Multiple friends

✅ **Events (25+ tests)**
- Creating events
- Querying by user/day/date
- ICS file import
- Multiple events
- Event overwriting

✅ **Database (40+ tests)**
- Model constraints
- Query operations
- Transactions
- Foreign keys
- Edge cases

✅ **Forms (20+ tests)**
- Field validation
- Error handling
- Optional fields
- Length constraints

✅ **Integration (15+ tests)**
- Full signup→signin flow
- Friend workflows
- Event management
- Multi-user scenarios

---

## Expected Results

When you run `pytest -v`, you should see:
```
test/test_auth.py::TestSignup::test_signup_success PASSED
test/test_auth.py::TestSignup::test_signup_duplicate_username PASSED
test/test_auth.py::TestSignin::test_signin_success PASSED
...

============== 175 passed in 2.45s ==============
```

---

## Troubleshooting

### Tests won't run
- Check Python is installed: `python --version`
- Check pytest is installed: `pytest --version`
- Run: `pip install -r test-requirements.txt`

### Import errors
- Make sure you're in project root directory
- Check conftest.py exists in `test/` folder
- Run: `python -m pytest` instead of `pytest`

### Database errors
- Tests use temporary in-memory SQLite
- Usually resolves automatically
- Check disk space if persistent errors

### Specific test fails
- Run with `-vv` for detailed output: `pytest -vv`
- Use `--pdb` to debug: `pytest --pdb`
- Check recent code changes

---

## Tips

1. **First time?** Run: `pytest --collect-only` to see all tests
2. **Focus mode?** Run: `pytest -k test_name`
3. **Need speed?** Run: `pytest -x` (stops on first failure)
4. **Parallel?** Run: `pip install pytest-xdist && pytest -n auto`
5. **Check coverage?** Run: `pytest --cov=. --cov-report=term`

---

## Next Steps

1. ✅ Run the tests: `pytest -v`
2. ✅ Check coverage: `pytest --cov=.`
3. ✅ Read the full docs: [test/README.md](README.md)
4. ✅ Add new tests for new features
5. ✅ Keep coverage > 80%

---

## Resources

- [Pytest Docs](https://docs.pytest.org/)
- [Test README](README.md)
- [Test Utils](test_utils.py)
- [Conftest Fixtures](conftest.py)
