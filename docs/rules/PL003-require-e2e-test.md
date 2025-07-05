# PL003: require-e2e-test

## Summary

Critical user-facing features and workflows should have end-to-end tests.

## Description

This rule enforces that functions have corresponding end-to-end (E2E) tests. E2E tests verify complete user workflows from start to finish, ensuring the entire system works correctly from the user's perspective.

## Why This Matters

- **User Experience**: Ensures features work as users expect
- **Full Stack Testing**: Tests the entire application stack together
- **Critical Path Coverage**: Validates important user journeys
- **Regression Prevention**: Catches issues that unit/integration tests might miss

## Examples

### Bad Example

```python
# src/checkout.py
def process_checkout(cart, payment_info, shipping_address):
    # Critical user-facing functionality
    # ... complex checkout logic ...
    return order  # PL003: Function 'process_checkout' has no e2e test found

def submit_order(order):
    # Final step in user journey
    # ... order submission ...
    return confirmation  # PL003: Function 'submit_order' has no e2e test found
```

### Good Example

```python
# src/checkout.py
def process_checkout(cart, payment_info, shipping_address):
    # OK - has test_e2e_process_checkout in test/e2e/
    # ... complex checkout logic ...
    return order

def submit_order(order):
    # OK - has test_e2e_submit_order
    # ... order submission ...
    return confirmation

# test/e2e/test_checkout.py
def test_e2e_process_checkout(browser, test_user):
    # Login
    browser.visit("/login")
    browser.fill("email", test_user.email)
    browser.fill("password", test_user.password)
    browser.click("Login")
    
    # Add items to cart
    browser.visit("/products")
    browser.click("Add to Cart", index=0)
    
    # Checkout
    browser.visit("/checkout")
    browser.fill("card_number", "4242424242424242")
    browser.fill("address", "123 Test St")
    browser.click("Complete Order")
    
    # Verify order confirmation
    assert browser.is_text_present("Order Confirmed")
    assert browser.find_by_css(".order-number").first.text != ""

def test_e2e_submit_order(api_client, browser):
    # Complete workflow test including order submission
    # ... test implementation ...
```

## Test Discovery

The linter looks for E2E tests using the following patterns:
- `test_e2e_{function_name}`
- `test_end_to_end_{function_name}`
- `test_{function_name}`
- `test_e2e_{class_name}_{function_name}` (for methods)

E2E tests should be placed in the `test/e2e/` directory.

## Exceptions

The following functions are automatically excluded:
- Private functions (starting with `_`)
- `__init__` methods
- Protocol methods (methods in Protocol classes)

## Disabling the Rule

You can disable this rule for specific functions using:

```python
def internal_helper_function():  # noqa: PL003
    pass  # Helper functions might not need E2E tests
```

Or disable it globally in `pyproject.toml`:

```toml
[tool.proboscis.rules]
PL003 = false
```

## Best Practices

- Focus E2E tests on critical user journeys
- Use page objects or similar patterns for maintainability
- Keep E2E tests independent and repeatable
- Consider using headless browsers for faster execution
- E2E tests should complement, not replace, unit and integration tests

## When to Use E2E Tests

E2E tests are most valuable for:
- User authentication flows
- Payment processing
- Critical business workflows
- Multi-step processes
- Features that span multiple services