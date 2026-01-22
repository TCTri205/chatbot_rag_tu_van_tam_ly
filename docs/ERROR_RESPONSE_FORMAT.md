# 📚 FastAPI Error Response Format Reference

## Overview

This document describes the different error response formats returned by FastAPI and how the frontend should handle them.

---

## ⚠️ IMPORTANT: API Route Path Matching

> **IMPORTANT**: API endpoints must match the **exact path defined in FastAPI routes**. Due to `redirect_slashes=False` configuration (see `src/main.py:27`), paths must be called exactly as defined.

### Why This Matters

FastAPI is configured with `redirect_slashes=False` to prevent automatic redirects that can cause CORS errors when the redirect changes the request origin. This means paths must match exactly - no automatic correction.

### Route Definitions Reference

Most routes are defined **without** trailing slashes:

**✅ Routes WITHOUT trailing slash:**

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /api/health`
- `POST /api/v1/chat`
- `POST /api/v1/moods`
- `POST /api/v1/sessions/init`
- `GET /api/v1/chat/history`
- `DELETE /api/v1/conversations/{id}`

**✅ Routes WITH trailing slash:**

- `GET /api/v1/conversations/`
- `GET /api/v1/exercises/`

### Implementation Note

Check the actual FastAPI route definition (e.g., `@router.post("")` vs `@router.get("/")`) to determine the correct path. When in doubt, test with the exact path from the route definition.

**Example**:

```javascript
// ✅ CORRECT - matches route definition
const response = await fetch('/api/v1/auth/login', { ... });

// ❌ WRONG - if route is defined without trailing slash
const response = await fetch('/api/v1/auth/login/', { ... }); // 404 if route has no slash
```

---

## 1. Validation Errors (422 Unprocessable Entity)

### Response Format

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Human-readable error message",
      "type": "error_type"
    }
  ]
}
```

### Example 1: Invalid Email

**Request**:

```json
POST /api/v1/auth/register/
{
  "email": "bad-email",
  "password": "12345678",
  "username": "test"
}
```

**Response (422)**:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### Example 2: Password Too Short

**Request**:

```json
POST /api/v1/auth/register/
{
  "email": "test@example.com",
  "password": "123",
  "username": "test"
}
```

**Response (422)**:

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 8}
    }
  ]
}
```

### Example 3: Multiple Validation Errors

**Request**:

```json
POST /api/v1/auth/register/
{
  "email": "bad-email",
  "password": "123"
}
```

**Response (422)**:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### Frontend Handling (JavaScript)

```javascript
if (response.status === 422 && Array.isArray(errorData.detail)) {
    // Extract readable error messages
    const messages = errorData.detail.map(err => {
        const field = err.loc[err.loc.length - 1]; // Get field name
        return `${field}: ${err.msg}`;
    }).join(', ');
    
    throw new Error(messages);
    // Result: "email: value is not a valid email address, password: ensure this value has at least 8 characters"
}
```

---

## 2. Application Errors (400, 401, 403, etc.)

### Response Format

```json
{
  "detail": "Simple error message string"
}
```

### Example 1: Unauthorized (401)

**Request**:

```json
POST /api/v1/auth/login/
{
  "email": "wrong@example.com",
  "password": "wrongpassword"
}
```

**Response (401)**:

```json
{
  "detail": "Incorrect email or password"
}
```

### Example 2: Email Already Registered (400)

**Request**:

```json
POST /api/v1/auth/register/
{
  "email": "existing@example.com",
  "password": "12345678",
  "username": "test"
}
```

**Response (400)**:

```json
{
  "detail": "Email already registered"
}
```

### Example 3: Forbidden (403)

**Request**:

```json
POST /api/v1/auth/login/
{
  "email": "banned@example.com",
  "password": "12345678"
}
```

**Response (403)**:

```json
{
  "detail": "Account is inactive"
}
```

### Frontend Handling (JavaScript)

```javascript
// Handle string detail (non-validation errors)
throw new Error(errorData.detail || errorData.message || 'Operation failed');
// Result: "Email already registered"
```

---

## 3. Complete Error Handling Pattern

### Recommended Implementation

```javascript
async function handleAPIError(response) {
    const errorData = await response.json();
    
    // Case 1: FastAPI Validation Errors (422)
    if (response.status === 422 && Array.isArray(errorData.detail)) {
        const messages = errorData.detail.map(err => {
            const field = err.loc ? err.loc[err.loc.length - 1] : 'field';
            return `${field}: ${err.msg}`;
        }).join(', ');
        return messages || 'Dữ liệu không hợp lệ';
    }
    
    // Case 2: Application Errors (string detail)
    if (typeof errorData.detail === 'string') {
        return errorData.detail;
    }
    
    // Case 3: Unknown error format
    return errorData.message || 'Đã xảy ra lỗi không xác định';
}

// Usage
try {
    const response = await fetch('/api/v1/auth/register/', { ... });
    
    if (!response.ok) {
        const errorMessage = await handleAPIError(response);
        throw new Error(errorMessage);
    }
    
    const data = await response.json();
    return data;
    
} catch (error) {
    console.error('API Error:', error.message);
    showErrorToUser(error.message);
}
```

---

## 4. Common Validation Error Types

| Type | Description | Example Message |
|------|-------------|-----------------|
| `value_error.email` | Invalid email format | "value is not a valid email address" |
| `value_error.any_str.min_length` | String too short | "ensure this value has at least 8 characters" |
| `value_error.any_str.max_length` | String too long | "ensure this value has at most 50 characters" |
| `value_error.missing` | Required field missing | "field required" |
| `type_error.integer` | Wrong data type | "value is not a valid integer" |
| `type_error.none.not_allowed` | None/null not allowed | "none is not an allowed value" |

---

## 5. Testing Error Handling

### Test Case 1: Invalid Email

```bash
curl -X POST http://localhost/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "not-an-email",
    "password": "12345678",
    "username": "test"
  }'
```

**Expected**: 422 with email validation error

### Test Case 2: Short Password

```bash
curl -X POST http://localhost/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123",
    "username": "test"
  }'
```

**Expected**: 422 with password length error

### Test Case 3: Wrong Login

```bash
curl -X POST http://localhost/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "wrong@example.com",
    "password": "wrongpass"
  }'
```

**Expected**: 401 with "Incorrect email or password"

---

## 6. Backend Schema Validation

### UserCreate Schema (src/schemas/auth.py)

```python
class UserCreate(BaseModel):
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    username: Optional[str] = Field(None, max_length=50)
```

### Validation Rules

- **Email**: Must be valid email format (RFC 5322)
- **Password**: Minimum 8 characters
- **Username**: Optional, max 50 characters

---

## 7. Best Practices

### ✅ DO

- Always check if `detail` is an array for 422 errors
- Extract field names from `loc` array (last element)
- Combine multiple errors into single message
- Provide user-friendly Vietnamese translations
- Log original error for debugging

### ❌ DON'T

- Don't assume `detail` is always a string
- Don't show raw technical errors to users
- Don't ignore validation error details
- Don't display `[object Object]`
- Don't hardcode error messages

---

## 8. Error Message Localization

### English → Vietnamese Translation Map

```javascript
const errorTranslations = {
    "value is not a valid email address": "Email không hợp lệ",
    "ensure this value has at least 8 characters": "Mật khẩu phải có ít nhất 8 ký tự",
    "field required": "Trường này là bắt buộc",
    "Incorrect email or password": "Email hoặc mật khẩu không đúng",
    "Email already registered": "Email đã được đăng ký",
    "Account is inactive": "Tài khoản đã bị vô hiệu hóa"
};

function translateError(errorMsg) {
    return errorTranslations[errorMsg] || errorMsg;
}
```

---

## 9. References

- **FastAPI Error Handling**: <https://fastapi.tiangolo.com/tutorial/handling-errors/>
- **Pydantic Validation**: <https://docs.pydantic.dev/latest/concepts/validators/>
- **HTTP Status Codes**: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status>

---

**Last Updated**: 2025-12-16  
**Version**: 1.0  
**Status**: ✅ Production Ready
