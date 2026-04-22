# Koiboi Backend Implementation - Technical Design

## Overview

Koiboi is a personal study workspace and note-taking application backend built with FastAPI and PostgreSQL. This design document provides a comprehensive technical blueprint for implementing the complete backend system, including system architecture, database design, API structure, authentication, and operational considerations.

The system enables users to organize their learning through a hierarchical structure of subjects, topics, and notes, with support for animated avatars, color customization, PDF material uploads, and code snippet management.

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Routes Layer (v1)                 │   │
│  │  /auth  /users  /subjects  /topics  /notes  /materials   │   │
│  │  /snippets  /master  /health                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Middleware & Authentication                 │   │
│  │  - JWT Token Validation                                  │   │
│  │  - CORS Configuration                                    │   │
│  │  - Rate Limiting                                         │   │
│  │  - Request/Response Logging                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Service Layer                           │   │
│  │  - AuthService      - SubjectService                     │   │
│  │  - UserService      - TopicService                       │   │
│  │  - NoteService      - MaterialService                    │   │
│  │  - SnippetService   - MasterDataService                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Data Access Layer                       │   │
│  │  - SQLAlchemy ORM Models                                 │   │
│  │  - Database Session Management                           │   │
│  │  - Query Optimization                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              External Services                           │   │
│  │  - PostgreSQL Database                                   │   │
│  │  - Cloud Storage (S3/GCS)                                │   │
│  │  - Email Service (SendGrid/SES)                          │   │
│  │  - Redis Cache (optional)                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Layered Architecture

**Route Layer**: Handles HTTP requests/responses, parameter validation, and routing to services.

**Service Layer**: Contains business logic, data validation, authorization checks, and orchestration of database operations.

**Data Access Layer**: SQLAlchemy ORM models, database session management, and query optimization.

**External Services**: PostgreSQL, cloud storage, email, caching.

## Components and Interfaces

### 1. Authentication & Authorization

**JWT Token Structure**:
- Header: `{"alg": "HS256", "typ": "JWT"}`
- Payload: `{"user_id": "uuid", "exp": timestamp, "iat": timestamp}`
- Signature: HMAC-SHA256 with JWT_SECRET

**Token Lifecycle**:
- Generated on sign-up and sign-in (24-hour expiration)
- Validated on every protected endpoint
- Invalidated on sign-out (session record deleted)
- Expired tokens return 401 Unauthorized

**Authorization Pattern**:
- Extract user_id from JWT token
- Verify user owns the resource being accessed
- Return 403 Forbidden if unauthorized

### 2. Database Layer

**Connection Management**:
- SQLAlchemy with PostgreSQL dialect
- Connection pooling (pool_size=20, max_overflow=40)
- Automatic connection recycling (pool_recycle=3600)

**Session Management**:
- Request-scoped sessions (one per HTTP request)
- Automatic rollback on exceptions
- Automatic commit on successful completion

**Transaction Handling**:
- Implicit transactions for all database operations
- Cascade deletes for hierarchical relationships
- Foreign key constraints enforced

### 3. File Storage

**Cloud Storage Abstraction**:
- Abstract interface supporting S3 and GCS
- Storage key format: `materials/{user_id}/{material_id}/{filename}`
- File validation: MIME type and size checks
- Automatic cleanup on material deletion

**File Operations**:
- Upload: Validate → Store → Create DB record
- Download: Verify ownership → Retrieve from storage → Return with headers
- Delete: Remove DB record → Delete from storage

### 4. Error Handling

**Error Response Format**:
```json
{
  "success": false,
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {}
}
```

**HTTP Status Codes**:
- 200 OK: Successful GET/PATCH
- 201 Created: Successful POST
- 400 Bad Request: Validation errors
- 401 Unauthorized: Missing/invalid JWT token
- 403 Forbidden: User lacks permission
- 404 Not Found: Resource doesn't exist
- 409 Conflict: Duplicate email/storage_key
- 413 Payload Too Large: File exceeds 100MB
- 500 Internal Server Error: Unexpected errors

**Error Codes**:
- `VALIDATION_ERROR`: Input validation failed
- `AUTHENTICATION_ERROR`: JWT token invalid/expired
- `AUTHORIZATION_ERROR`: User lacks permission
- `RESOURCE_NOT_FOUND`: Resource doesn't exist
- `DUPLICATE_EMAIL`: Email already registered
- `INVALID_FILE_TYPE`: File is not PDF
- `FILE_TOO_LARGE`: File exceeds size limit
- `DATABASE_ERROR`: Database operation failed
- `EXTERNAL_SERVICE_ERROR`: Cloud storage/email service failed

### 5. Logging & Monitoring

**Log Levels**:
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages for potential issues
- ERROR: Error messages with stack traces

**Logged Events**:
- API requests: method, path, status, response_time
- Authentication: sign-up, sign-in, sign-out, password reset
- Database operations: query execution time
- File operations: upload, download, delete
- Errors: full stack traces with context

**Log Format**:
```json
{
  "timestamp": "2026-04-21T10:00:00Z",
  "level": "INFO",
  "logger": "koiboi.api.routes",
  "message": "User signed in successfully",
  "user_id": "uuid",
  "request_id": "uuid",
  "duration_ms": 145
}
```

## Data Models

### Core Entities

#### User
- **id** (UUID): Primary key
- **name** (VARCHAR 255): Display name
- **email** (VARCHAR 255): Unique email
- **password_hash** (VARCHAR 255): Bcrypt hash
- **avatar_style_id** (UUID FK): Reference to avatar_styles
- **avatar_color_id** (UUID FK): Reference to avatar_colors
- **created_at** (TIMESTAMP): Account creation
- **updated_at** (TIMESTAMP): Last profile update
- **last_login_at** (TIMESTAMP): Last successful login
- **is_active** (BOOLEAN): Account status

#### Subject
- **id** (UUID): Primary key
- **user_id** (UUID FK): Owner
- **name** (VARCHAR 255): Subject name
- **color_id** (UUID FK): Reference to palette_colors
- **description** (TEXT): Optional description
- **created_at** (TIMESTAMP)
- **updated_at** (TIMESTAMP)

#### Topic
- **id** (UUID): Primary key
- **subject_id** (UUID FK): Parent subject
- **name** (VARCHAR 255): Topic name
- **status** (ENUM): not-started, in-progress, revising, completed
- **confidence** (INTEGER 0-5): Learning confidence
- **tint_id** (UUID FK): Reference to tint_palette
- **created_at** (TIMESTAMP)
- **updated_at** (TIMESTAMP)

#### Note
- **id** (UUID): Primary key
- **topic_id** (UUID FK): Parent topic
- **title** (VARCHAR 255): Note title
- **body** (TEXT): Markdown content
- **tint_id** (UUID FK): Reference to tint_palette
- **scribbles** (JSONB): Array of ScribbleStroke objects
- **created_at** (TIMESTAMP)
- **updated_at** (TIMESTAMP)

#### Material
- **id** (UUID): Primary key
- **subject_id** (UUID FK): Associated subject
- **title** (VARCHAR 255): Material title
- **file_name** (VARCHAR 255): Original filename
- **mime_type** (VARCHAR 50): Always application/pdf
- **file_size** (BIGINT): Size in bytes
- **page_count** (INTEGER): Number of pages
- **storage_key** (VARCHAR 255): Unique cloud storage key
- **created_at** (TIMESTAMP)
- **updated_at** (TIMESTAMP)

#### PlaygroundSnippet
- **id** (UUID): Primary key
- **user_id** (UUID FK): Owner
- **note_id** (UUID FK): Optional associated note
- **language** (VARCHAR 50): Programming language
- **code** (TEXT): Source code
- **output** (TEXT): Execution output
- **created_at** (TIMESTAMP)
- **updated_at** (TIMESTAMP)

#### UserSession
- **id** (UUID): Primary key
- **user_id** (UUID FK): Associated user
- **token** (VARCHAR 500): JWT token
- **expires_at** (TIMESTAMP): Token expiration
- **created_at** (TIMESTAMP)
- **ip_address** (VARCHAR 45): Client IP
- **user_agent** (TEXT): Client user agent

#### PasswordResetToken
- **id** (UUID): Primary key
- **user_id** (UUID FK): Associated user
- **token** (VARCHAR 255): Reset token
- **expires_at** (TIMESTAMP): Token expiration (1 hour)
- **created_at** (TIMESTAMP)
- **used_at** (TIMESTAMP): When token was used

### Master Data Entities

#### AvatarStyle
- **id** (UUID): Primary key
- **name** (VARCHAR 100): Style name
- **slug** (VARCHAR 100): URL-friendly slug
- **description** (TEXT): Animation description
- **svg_template** (TEXT): SVG with animations
- **animation_type** (VARCHAR 50): float, bounce, rotate, pulse, wave, morph, particle
- **animation_duration** (DECIMAL 5,2): Duration in seconds
- **color_customizable** (BOOLEAN): Can be colored
- **display_order** (INTEGER): UI display order
- **is_active** (BOOLEAN): Available for selection
- **created_at** (TIMESTAMP)

#### AvatarColor
- **id** (UUID): Primary key
- **name** (VARCHAR 100): Color name
- **hex_code** (VARCHAR 7): Hex color code
- **rgb** (VARCHAR 20): RGB representation
- **hsl** (VARCHAR 50): HSL representation
- **display_order** (INTEGER): UI display order
- **is_active** (BOOLEAN): Available for selection
- **created_at** (TIMESTAMP)

#### TintPalette
- **id** (UUID): Primary key
- **name** (VARCHAR 100): Tint name
- **hsl** (VARCHAR 50): HSL color triplet
- **hex_code** (VARCHAR 7): Hex equivalent
- **category** (VARCHAR 50): warm, cool, neutral
- **display_order** (INTEGER): UI display order
- **is_active** (BOOLEAN): Available for selection
- **created_at** (TIMESTAMP)

#### ColorPalette
- **id** (UUID): Primary key
- **name** (VARCHAR 100): Palette name
- **description** (TEXT): Palette description
- **palette_type** (ENUM): subject, note, both
- **is_active** (BOOLEAN): Available for selection
- **created_at** (TIMESTAMP)

#### PaletteColor
- **id** (UUID): Primary key
- **palette_id** (UUID FK): Parent palette
- **hex_code** (VARCHAR 7): Hex color code
- **hsl** (VARCHAR 50): HSL representation
- **color_name** (VARCHAR 100): Color name in palette
- **display_order** (INTEGER): Order within palette
- **created_at** (TIMESTAMP)

### Scribble Data Structure

```json
{
  "id": "string (uuid)",
  "tool": "brush",
  "color": "string (hex color)",
  "width": "number (1-20)",
  "opacity": "number (0-1)",
  "points": [
    { "x": "number", "y": "number" },
    { "x": "number", "y": "number" }
  ]
}
```

## API Design

### Request/Response Schemas

**Pagination Query Parameters**:
```python
class PaginationParams:
    limit: int = 50  # max 50
    offset: int = 0  # must be >= 0
```

**Success Response**:
```python
class SuccessResponse(Generic[T]):
    success: bool = True
    data: T
    message: Optional[str] = None
    total: Optional[int] = None  # for list endpoints
```

**Error Response**:
```python
class ErrorResponse:
    success: bool = False
    error: str  # error code
    message: str  # human-readable message
    details: Optional[dict] = None
```

### Endpoint Categories

**Master Data Endpoints** (Public, no auth):
- GET /master/avatar-styles
- GET /master/avatar-styles/{id}
- GET /master/avatar-colors
- GET /master/tint-palette

**Authentication Endpoints** (Public):
- POST /auth/sign-up
- POST /auth/sign-in
- POST /auth/sign-out (auth required)
- POST /auth/forgot-password
- POST /auth/reset-password
- POST /auth/change-password (auth required)

**User Endpoints** (Auth required):
- GET /users/me
- PATCH /users/me

**Subject Endpoints** (Auth required):
- GET /subjects
- POST /subjects
- PATCH /subjects/{id}
- DELETE /subjects/{id}

**Topic Endpoints** (Auth required):
- GET /subjects/{subjectId}/topics
- POST /subjects/{subjectId}/topics
- PATCH /topics/{id}
- DELETE /topics/{id}

**Note Endpoints** (Auth required):
- GET /topics/{topicId}/notes
- POST /topics/{topicId}/notes
- GET /notes/{id}
- PATCH /notes/{id}
- DELETE /notes/{id}

**Material Endpoints** (Auth required):
- GET /subjects/{subjectId}/materials
- POST /subjects/{subjectId}/materials (multipart/form-data)
- GET /materials/{id}
- PATCH /materials/{id}
- DELETE /materials/{id}
- GET /materials/{id}/download

**Snippet Endpoints** (Auth required):
- GET /snippets
- POST /snippets
- PATCH /snippets/{id}
- DELETE /snippets/{id}

**Health Endpoints** (Public):
- GET /health
- GET /health/ready
- GET /health/live

## Configuration Management

**Environment Variables**:
```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/koiboi

# JWT
JWT_SECRET=your-secret-key-min-32-chars
JWT_EXPIRATION_HOURS=24

# Cloud Storage
STORAGE_TYPE=s3  # or gcs
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_S3_BUCKET=koiboi-materials
AWS_REGION=us-east-1

# Email
EMAIL_SERVICE=sendgrid  # or ses
SENDGRID_API_KEY=xxx
SENDGRID_FROM_EMAIL=noreply@koiboi.app

# CORS
CORS_ORIGINS=http://localhost:3000,https://koiboi.app

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

**Settings Management**:
- Use Pydantic Settings for validation
- Support .env file loading
- Validate all required variables on startup
- Provide sensible defaults for optional variables

## Code Organization

```
src/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings management
│   │   ├── security.py         # JWT, password hashing
│   │   └── constants.py        # Constants and enums
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy Base
│   │   ├── session.py          # Session management
│   │   └── migrations/         # Alembic migrations
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── subject.py
│   │   ├── topic.py
│   │   ├── note.py
│   │   ├── material.py
│   │   ├── snippet.py
│   │   ├── session.py
│   │   ├── reset_token.py
│   │   ├── avatar_style.py
│   │   ├── avatar_color.py
│   │   ├── tint_palette.py
│   │   ├── color_palette.py
│   │   └── palette_color.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base.py             # Base response schemas
│   │   ├── user.py
│   │   ├── subject.py
│   │   ├── topic.py
│   │   ├── note.py
│   │   ├── material.py
│   │   ├── snippet.py
│   │   └── master_data.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── subject.py
│   │   ├── topic.py
│   │   ├── note.py
│   │   ├── material.py
│   │   ├── snippet.py
│   │   ├── master_data.py
│   │   └── storage.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py     # Dependency injection
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── routes.py       # All routes
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── subjects.py
│   │       ├── topics.py
│   │       ├── notes.py
│   │       ├── materials.py
│   │       ├── snippets.py
│   │       ├── master_data.py
│   │       └── health.py
│   └── middleware/
│       ├── __init__.py
│       ├── logging.py
│       ├── error_handler.py
│       └── rate_limiter.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_subjects.py
│   ├── test_topics.py
│   ├── test_notes.py
│   ├── test_materials.py
│   ├── test_snippets.py
│   └── test_master_data.py
└── requirements.txt
```

## Security Implementation

### Password Security
- Use bcrypt with minimum 10 rounds
- Never store plain text passwords
- Validate password strength (min 6 chars, max 128 chars)
- Hash passwords before database insertion

### Token Security
- Use cryptographically secure random tokens for reset/session tokens
- Generate with `secrets.token_urlsafe(32)`
- Store hashed tokens in database (optional, for reset tokens)
- Validate token signature using JWT_SECRET
- Implement token expiration (24 hours for JWT, 1 hour for reset tokens)

### Input Validation
- Validate all user inputs on backend
- Use Pydantic schemas for request validation
- Implement custom validators for complex rules
- Return 400 Bad Request with validation details

### SQL Injection Prevention
- Use SQLAlchemy ORM (parameterized queries)
- Never concatenate user input into SQL strings
- Use prepared statements for all database operations

### Authorization
- Extract user_id from JWT token
- Verify user owns resource before allowing access
- Return 403 Forbidden for unauthorized access
- Implement role-based access control (future enhancement)

### Rate Limiting
- Implement rate limiting on auth endpoints
- Use sliding window algorithm
- Store rate limit state in Redis or memory
- Return 429 Too Many Requests when limit exceeded

### CORS Configuration
- Whitelist allowed origins from CORS_ORIGINS env var
- Allow credentials in CORS headers
- Restrict HTTP methods to GET, POST, PATCH, DELETE
- Restrict headers to Content-Type, Authorization

### HTTPS
- Enforce HTTPS in production
- Use secure cookies (HttpOnly, Secure, SameSite)
- Implement HSTS headers

## Testing Strategy

### Property-Based Testing Applicability

**Property-based testing is NOT applicable to this feature** because:

1. **Infrastructure Focus**: This is a backend API implementation with infrastructure components (database, migrations, configuration) rather than pure algorithmic logic.

2. **External Dependencies**: Most operations involve external services (PostgreSQL, cloud storage, email) which are not suitable for property-based testing.

3. **Configuration-Driven**: Much of the implementation is configuration and setup (environment variables, CORS, rate limiting) which doesn't benefit from property-based testing.

4. **Side-Effect Operations**: Many operations are side-effect heavy (database writes, file uploads, email sending) which are better tested with integration tests and mocks.

5. **Deterministic External Behavior**: External services behave deterministically and don't vary meaningfully with input in ways that property-based testing would help.

### Unit Tests

Test individual service methods with mocked dependencies:
- **AuthService**: Password hashing, token generation, credential validation
- **UserService**: Profile updates, avatar selection validation
- **SubjectService**: CRUD operations, authorization checks
- **TopicService**: Status/confidence validation, authorization
- **NoteService**: Scribble validation, authorization
- **MaterialService**: File type/size validation, authorization
- **SnippetService**: Language validation, authorization
- **StorageService**: Cloud storage abstraction

**Coverage Target**: 80%+ code coverage

### Integration Tests

Test API endpoints with real database and mocked external services:
- **Authentication**: Sign-up, sign-in, sign-out, password reset flows
- **CRUD Operations**: Create, read, update, delete for all resources
- **Authorization**: Verify 403 Forbidden for unauthorized access
- **Cascade Deletes**: Verify topics/notes deleted when subject deleted
- **Foreign Key Constraints**: Verify constraints enforced
- **File Operations**: Upload/download with mocked cloud storage
- **Pagination**: Verify limit/offset parameters work correctly
- **Error Handling**: Verify error responses match specification

### Schema Validation Tests

Test database schema and migrations:
- Verify all 13 tables created correctly
- Verify indexes created on foreign keys and frequently queried columns
- Verify unique constraints enforced (email, storage_key, token)
- Verify check constraints enforced (confidence 0-5, email format)
- Verify master data seeded correctly (8 avatar styles, 8 colors, 8 tints)
- Verify cascade delete relationships work

### API Contract Tests

Test API response formats and contracts:
- Verify response schemas match specification
- Verify error response formats (success: false, error code, message)
- Verify pagination responses include total count
- Verify timestamps in ISO 8601 format with timezone
- Verify all required fields present in responses
- Verify HTTP status codes correct for all scenarios

### Security Tests

Test security implementations:
- **Password Hashing**: Verify bcrypt with 10+ rounds
- **JWT Tokens**: Verify token generation, validation, expiration
- **Authorization**: Verify user can only access own data
- **Rate Limiting**: Verify rate limits enforced on auth endpoints
- **CORS**: Verify CORS headers configured correctly
- **Input Validation**: Verify all inputs validated before database operations
- **SQL Injection**: Verify parameterized queries used throughout

### Test Database

- Use PostgreSQL test database (separate from production)
- Run migrations before each test suite
- Clean up data after each test (truncate tables)
- Use fixtures for common test data (users, subjects, topics, notes)
- Support parallel test execution with isolated databases

### Test Organization

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── unit/
│   ├── test_auth_service.py
│   ├── test_user_service.py
│   ├── test_subject_service.py
│   ├── test_topic_service.py
│   ├── test_note_service.py
│   ├── test_material_service.py
│   ├── test_snippet_service.py
│   └── test_storage_service.py
├── integration/
│   ├── test_auth_endpoints.py
│   ├── test_user_endpoints.py
│   ├── test_subject_endpoints.py
│   ├── test_topic_endpoints.py
│   ├── test_note_endpoints.py
│   ├── test_material_endpoints.py
│   ├── test_snippet_endpoints.py
│   ├── test_master_data_endpoints.py
│   └── test_health_endpoints.py
├── schema/
│   ├── test_migrations.py
│   ├── test_constraints.py
│   └── test_indexes.py
├── security/
│   ├── test_authentication.py
│   ├── test_authorization.py
│   ├── test_password_hashing.py
│   └── test_jwt_tokens.py
└── fixtures/
    ├── users.py
    ├── subjects.py
    ├── topics.py
    ├── notes.py
    ├── materials.py
    └── snippets.py
```

### Test Execution

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with coverage
pytest --cov=src/app --cov-report=html

# Run specific test file
pytest tests/integration/test_auth_endpoints.py

# Run with verbose output
pytest -v
```

### Test Dependencies

```
pytest>=7.0
pytest-asyncio>=0.20
pytest-cov>=4.0
pytest-mock>=3.10
httpx>=0.23  # async HTTP client for testing
factory-boy>=3.2  # test data factories
faker>=15.0  # fake data generation
```

## Database Migrations

### Alembic Setup
- Initialize Alembic in `src/app/db/migrations/`
- Configure `alembic.ini` with database URL
- Create initial migration for all 13 tables
- Seed master data in migration

### Migration Strategy
1. Create migration file: `alembic revision --autogenerate -m "description"`
2. Review generated migration
3. Apply migration: `alembic upgrade head`
4. Rollback if needed: `alembic downgrade -1`

### Master Data Seeding
- Seed avatar_styles with 8 predefined styles
- Seed avatar_colors with 8 predefined colors
- Seed tint_palette with 8 predefined tints
- Run seeding in initial migration

## Performance Optimization

### Database Indexes
- Foreign key columns: user_id, subject_id, topic_id, material_id
- Frequently queried columns: created_at, updated_at, status, is_active
- Composite indexes: (user_id, created_at), (subject_id, name)
- Unique indexes: email, storage_key, token

### Query Optimization
- Use eager loading for relationships (joinedload)
- Implement pagination on all list endpoints
- Use database-level filtering instead of application-level
- Avoid N+1 query problems

### Caching Strategy
- Cache master data (avatar styles, colors, tints) in memory
- Implement Redis caching for user profiles (optional)
- Cache subject/topic hierarchy for authenticated users
- Invalidate cache on data updates

### Connection Pooling
- Configure SQLAlchemy connection pool
- Pool size: 20, max overflow: 40
- Pool recycle: 3600 seconds
- Use PgBouncer for additional connection pooling (optional)

## Deployment Considerations

### Docker
- Create Dockerfile for FastAPI application
- Use Python 3.11+ slim image
- Install dependencies from requirements.txt
- Expose port 8000

### Environment Setup
- Use environment variables for all configuration
- Support .env file for local development
- Validate all required variables on startup
- Provide clear error messages for missing variables

### Database Setup
- Run migrations on application startup
- Seed master data on first migration
- Support multiple database environments (dev, staging, prod)

### Monitoring
- Implement structured logging
- Track API response times
- Monitor database query performance
- Set up alerts for errors and performance issues

### Scaling
- Use connection pooling for database
- Implement caching for frequently accessed data
- Support horizontal scaling with stateless design
- Use load balancer for multiple instances

## Error Handling

### Common Error Scenarios

**Validation Errors**:
- Empty required fields
- Invalid email format
- Password too short/long
- Invalid UUID format
- File not PDF
- File too large

**Authentication Errors**:
- Missing JWT token
- Invalid JWT token
- Expired JWT token
- Invalid credentials (sign-in)

**Authorization Errors**:
- User doesn't own resource
- User doesn't own subject/topic/note
- User doesn't own material/snippet

**Resource Errors**:
- Resource not found (404)
- Duplicate email (409)
- Duplicate storage_key (409)

**External Service Errors**:
- Database connection failed
- Cloud storage unavailable
- Email service failed

### Error Recovery
- Implement retry logic for transient failures
- Log all errors with context
- Return user-friendly error messages
- Never expose sensitive information in errors

## Future Enhancements

- Role-based access control (admin, moderator)
- Collaborative study spaces (shared subjects/topics)
- Real-time collaboration on notes
- Advanced search and filtering
- Analytics and learning insights
- Mobile application support
- Offline synchronization
- Integration with external services (GitHub, LeetCode)
- AI-powered study recommendations
