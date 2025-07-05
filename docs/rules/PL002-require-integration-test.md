# PL002: require-integration-test

## Summary

Functions that interact with external systems or multiple components should have integration tests.

## Description

This rule enforces that functions have corresponding integration tests. Integration tests verify that different parts of the system work correctly together, including interactions with databases, APIs, file systems, or other services.

## Why This Matters

- **System Integration**: Ensures components work together correctly
- **External Dependencies**: Tests interactions with databases, APIs, etc.
- **Real-World Scenarios**: Tests the system in conditions closer to production
- **Configuration Validation**: Ensures proper setup and configuration

## Examples

### Bad Example

```python
# src/user_service.py
def create_user(db, user_data):
    # Interacts with database
    return db.users.insert(user_data)  # PL002: Function 'create_user' has no integration test found

def send_welcome_email(user, email_service):
    # Interacts with email service
    return email_service.send(user.email, "Welcome!")  # PL002: Function 'send_welcome_email' has no integration test found
```

### Good Example

```python
# src/user_service.py
def create_user(db, user_data):
    # OK - has test_integration_create_user in test/integration/
    return db.users.insert(user_data)

def send_welcome_email(user, email_service):
    # OK - has test_integration_send_welcome_email
    return email_service.send(user.email, "Welcome!")

# test/integration/test_user_service.py
def test_integration_create_user(test_db):
    user_data = {"name": "Test User", "email": "test@example.com"}
    result = create_user(test_db, user_data)
    assert test_db.users.find_one({"_id": result.id}) is not None

def test_integration_send_welcome_email(mock_email_service):
    user = User(email="test@example.com")
    send_welcome_email(user, mock_email_service)
    assert mock_email_service.sent_emails[0].to == "test@example.com"
```

## Test Discovery

The linter looks for integration tests using the following patterns:
- `test_integration_{function_name}`
- `test_int_{function_name}`
- `test_{function_name}`
- `test_integration_{class_name}_{function_name}` (for methods)

Integration tests should be placed in the `test/integration/` directory.

## Exceptions

The following functions are automatically excluded:
- Private functions (starting with `_`)
- `__init__` methods
- Protocol methods (methods in Protocol classes)

## Disabling the Rule

You can disable this rule for specific functions using:

```python
def pure_calculation_function(x, y):  # noqa: PL002
    return x * y  # Pure functions might not need integration tests
```

Or disable it globally in `pyproject.toml`:

```toml
[tool.proboscis.rules]
PL002 = false
```

## Best Practices

- Use test fixtures for database connections and external services
- Mock external APIs to avoid dependencies on third-party services
- Test error handling and edge cases in integration scenarios
- Keep integration tests focused on integration points, not business logic