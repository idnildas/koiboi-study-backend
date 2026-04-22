# Implementation Plan: Koiboi Backend Implementation

## Overview

This implementation plan breaks down the Koiboi backend into executable tasks organized by feature area. Each task builds incrementally on previous work, with clear dependencies and acceptance criteria. The implementation follows a layered architecture: database models → services → API routes → testing.

## Tasks

### Phase 1: Project Setup & Infrastructure

- [x] 1. Set up project structure and dependencies
  - Initialize FastAPI application with required dependencies (fastapi, sqlalchemy, pydantic, bcrypt, python-jose, python-multipart)
  - Create directory structure: src/app/{core,db,models,schemas,services,api,middleware}
  - Set up requirements.txt with all dependencies
  - Create .env.example with all required environment variables
  - _Requirements: 27_

- [x] 2. Configure environment and settings management
  - Create src/app/core/config.py with Pydantic Settings
  - Load DATABASE_URL, JWT_SECRET, JWT_EXPIRATION_HOURS, STORAGE_TYPE, CORS_ORIGINS, LOG_LEVEL
  - Validate all required environment variables on startup
  - Support .env file loading for local development
  - _Requirements: 27_

- [x] 3. Set up database connection and session management
  - Create src/app/db/base.py with SQLAlchemy declarative base
  - Create src/app/db/session.py with database engine and session factory
  - Configure connection pooling (pool_size=20, max_overflow=40, pool_recycle=3600)
  - Implement request-scoped session dependency for FastAPI
  - _Requirements: 22_

### Phase 2: Database Models & Migrations

- [x] 4. Create core user and authentication models
  - Create src/app/models/user.py with User model (id, name, email, password_hash, avatar_style_id, avatar_color_id, created_at, updated_at, last_login_at, is_active)
  - Create src/app/models/session.py with UserSession model (id, user_id, token, expires_at, created_at, ip_address, user_agent)
  - Create src/app/models/reset_token.py with PasswordResetToken model (id, user_id, token, expires_at, created_at, used_at)
  - Add unique constraints on users.email, user_sessions.token, password_reset_tokens.token
  - _Requirements: 1, 2, 3, 18_

- [x] 5. Create master data models
  - Create src/app/models/avatar_style.py with AvatarStyle model (id, name, slug, description, svg_template, animation_type, animation_duration, color_customizable, display_order, is_active, created_at)
  - Create src/app/models/avatar_color.py with AvatarColor model (id, name, hex_code, rgb, hsl, display_order, is_active, created_at)
  - Create src/app/models/tint_palette.py with TintPalette model (id, name, hsl, hex_code, category, display_order, is_active, created_at)
  - Add unique constraints on avatar_styles.slug, avatar_colors.hex_code, tint_palette.name
  - _Requirements: 5, 6, 7_

- [x] 6. Create color palette models
  - Create src/app/models/color_palette.py with ColorPalette model (id, name, description, palette_type, is_active, created_at)
  - Create src/app/models/palette_color.py with PaletteColor model (id, palette_id, hex_code, hsl, color_name, display_order, created_at)
  - Add foreign key relationship with cascade delete from ColorPalette to PaletteColor
  - _Requirements: 8_

- [x] 7. Create subject, topic, and note models
  - Create src/app/models/subject.py with Subject model (id, user_id, name, color_id, description, created_at, updated_at)
  - Create src/app/models/topic.py with Topic model (id, subject_id, name, status, confidence, tint_id, created_at, updated_at)
  - Create src/app/models/note.py with Note model (id, topic_id, title, body, tint_id, scribbles, created_at, updated_at)
  - Add check constraint on topics.confidence (0-5 range)
  - Add foreign key relationships with cascade delete
  - _Requirements: 8, 10, 12, 18_

- [x] 8. Create material and snippet models
  - Create src/app/models/material.py with Material model (id, subject_id, title, file_name, mime_type, file_size, page_count, storage_key, created_at, updated_at)
  - Create src/app/models/snippet.py with PlaygroundSnippet model (id, user_id, note_id, language, code, output, created_at, updated_at)
  - Add unique constraint on materials.storage_key
  - Add foreign key relationships with cascade delete
  - _Requirements: 14, 16, 18_

- [x] 9. Initialize Alembic and create initial migration
  - Initialize Alembic in src/app/db/migrations/
  - Configure alembic.ini with database URL
  - Create initial migration with all 13 tables and relationships
  - Seed master data: 8 avatar styles, 8 avatar colors, 8 tints
  - Test migration up and down
  - _Requirements: 25_

### Phase 3: Authentication & Security

- [x] 10. Implement password hashing and JWT utilities
  - Create src/app/core/security.py with password hashing functions (hash_password, verify_password using bcrypt with 10+ rounds)
  - Implement JWT token generation (create_access_token with user_id, exp, iat)
  - Implement JWT token validation (verify_token, extract_user_id)
  - Use JWT_SECRET and JWT_EXPIRATION_HOURS from config
  - _Requirements: 1, 2, 19, 23_

- [x] 11. Create authentication service
  - Create src/app/services/auth.py with AuthService class
  - Implement sign_up(name, email, password, avatar_style_id, avatar_color_id) → (user, token)
  - Implement sign_in(email, password) → (user, token)
  - Implement sign_out(user_id, token) → delete session
  - Implement forgot_password(email) → send reset email
  - Implement reset_password(email, token, new_password) → update password
  - Implement change_password(user_id, current_password, new_password) → update password
  - Validate all inputs and return appropriate errors
  - _Requirements: 1, 2, 3, 4, 19, 23_

- [x] 12. Create authentication middleware and dependencies
  - Create src/app/api/dependencies.py with get_current_user dependency
  - Extract JWT token from Authorization header
  - Validate token and extract user_id
  - Return 401 Unauthorized for missing/invalid/expired tokens
  - Create optional_current_user for public endpoints
  - _Requirements: 19_

### Phase 4: API Schemas & Response Formatting

- [x] 13. Create base response schemas
  - Create src/app/schemas/base.py with SuccessResponse and ErrorResponse classes
  - Implement generic SuccessResponse[T] with success, data, message, total fields
  - Implement ErrorResponse with success, error, message, details fields
  - Create PaginationParams with limit (max 50), offset (min 0)
  - _Requirements: 20, 21_

- [x] 14. Create resource schemas
  - Create src/app/schemas/user.py with UserCreate, UserUpdate, UserResponse schemas
  - Create src/app/schemas/subject.py with SubjectCreate, SubjectUpdate, SubjectResponse schemas
  - Create src/app/schemas/topic.py with TopicCreate, TopicUpdate, TopicResponse schemas
  - Create src/app/schemas/note.py with NoteCreate, NoteUpdate, NoteResponse, ScribbleStroke schemas
  - Create src/app/schemas/material.py with MaterialCreate, MaterialUpdate, MaterialResponse schemas
  - Create src/app/schemas/snippet.py with SnippetCreate, SnippetUpdate, SnippetResponse schemas
  - Create src/app/schemas/master_data.py with AvatarStyleResponse, AvatarColorResponse, TintPaletteResponse schemas
  - Add validators for all fields (email format, UUID format, enum values, ranges)
  - _Requirements: 20, 21_

### Phase 5: Master Data Endpoints

- [x] 15. Implement avatar styles endpoint
  - Create GET /master/avatar-styles endpoint with pagination (limit, offset)
  - Return all active avatar styles sorted by display_order
  - Create GET /master/avatar-styles/{id} endpoint
  - Return complete style including SVG template
  - Cache results in memory or Redis
  - _Requirements: 5, 22_

- [x] 16. Implement avatar colors endpoint
  - Create GET /master/avatar-colors endpoint with pagination
  - Return all active colors with hex, RGB, HSL representations
  - Sort by display_order
  - Cache results
  - _Requirements: 6, 22_

- [x] 17. Implement tint palette endpoint
  - Create GET /master/tint-palette endpoint with pagination
  - Return all active tints with name, HSL, hex code, category
  - Sort by display_order
  - Cache results
  - _Requirements: 7, 22_

### Phase 6: Authentication Endpoints

- [x] 18. Implement sign-up endpoint
  - Create POST /auth/sign-up endpoint
  - Accept name, email, password, avatar_style_id, avatar_color_id
  - Validate inputs (name 2-100 chars, email format, password 6-128 chars, avatar IDs exist)
  - Return 409 Conflict if email exists
  - Return JWT token and user profile on success
  - _Requirements: 1, 20, 21_

- [x] 19. Implement sign-in endpoint
  - Create POST /auth/sign-in endpoint
  - Accept email and password
  - Verify credentials against bcrypt hash
  - Return 401 Unauthorized for invalid credentials
  - Create session record with token, expiration, IP address, user agent
  - Return JWT token and user profile on success
  - _Requirements: 2, 20, 21_

- [x] 20. Implement sign-out endpoint
  - Create POST /auth/sign-out endpoint (auth required)
  - Delete session record for current user
  - Return 200 OK with success message
  - _Requirements: 2, 20_

- [x] 21. Implement password reset endpoints
  - Create POST /auth/forgot-password endpoint
  - Accept email, return 200 OK regardless (security)
  - Generate cryptographically secure reset token with 1-hour expiration
  - Send password reset email with token
  - Create POST /auth/reset-password endpoint
  - Accept email, token, new_password
  - Validate token is valid and not expired
  - Update password and mark token as used
  - Invalidate all existing sessions
  - Create POST /auth/change-password endpoint (auth required)
  - Accept current_password and new_password
  - Verify current password is correct
  - Update password on success
  - _Requirements: 3, 4, 20, 21, 28_

### Phase 7: User Management Endpoints

- [x] 22. Implement user profile endpoints
  - Create GET /users/me endpoint (auth required)
  - Return user profile with name, email, avatar_style_id, avatar_color_id, timestamps
  - Create PATCH /users/me endpoint (auth required)
  - Accept name and/or avatar selections
  - Validate avatar IDs exist
  - Update user record and return updated profile
  - _Requirements: 4, 20, 21_

- [x] 23. Checkpoint - Ensure authentication and user management tests pass
  - Ensure all tests pass, ask the user if questions arise.

### Phase 8: Subject Management Endpoints

- [x] 24. Implement subject creation and listing
  - Create POST /subjects endpoint (auth required)
  - Accept name, optional color_id, optional description
  - Validate name (1-255 chars), description (max 1000 chars), color_id exists
  - Create subject associated with authenticated user
  - Return 201 Created with subject data
  - Create GET /subjects endpoint (auth required)
  - Return all subjects owned by user with pagination
  - Support limit, offset, sort (created_at, name) parameters
  - _Requirements: 8, 20, 21, 22_

- [x] 25. Implement subject update and delete
  - Create PATCH /subjects/{id} endpoint (auth required)
  - Validate user owns subject (403 Forbidden if not)
  - Validate inputs and update record
  - Return updated subject
  - Create DELETE /subjects/{id} endpoint (auth required)
  - Validate user owns subject (403 Forbidden if not)
  - Cascade delete all associated topics, notes, materials
  - Return 200 OK with success message
  - _Requirements: 9, 20_

- [x] 26. Implement subject authorization checks
  - Add authorization middleware to all subject endpoints
  - Verify user_id from JWT matches subject.user_id
  - Return 403 Forbidden for unauthorized access
  - _Requirements: 9, 19_

### Phase 9: Topic Management Endpoints

- [x] 27. Implement topic creation and listing
  - Create POST /subjects/{subjectId}/topics endpoint (auth required)
  - Accept name, optional tint_id
  - Validate subject exists and user owns it (403 Forbidden if not)
  - Validate name (1-255 chars), tint_id exists
  - Assign random tint if not provided
  - Create topic with default status "not-started" and confidence 0
  - Return 201 Created with topic data
  - Create GET /subjects/{subjectId}/topics endpoint (auth required)
  - Validate user owns subject
  - Return all topics with pagination
  - Support limit, offset, status filter parameters
  - _Requirements: 10, 20, 21, 22_

- [x] 28. Implement topic update and delete
  - Create PATCH /topics/{id} endpoint (auth required)
  - Validate user owns topic (403 Forbidden if not)
  - Validate status is one of: not-started, in-progress, revising, completed
  - Validate confidence is 0-5 integer
  - Update record and return updated topic
  - Create DELETE /topics/{id} endpoint (auth required)
  - Validate user owns topic (403 Forbidden if not)
  - Cascade delete all associated notes
  - Return 200 OK with success message
  - _Requirements: 11, 20_

- [x] 29. Implement topic authorization checks
  - Add authorization middleware to all topic endpoints
  - Verify user owns parent subject through topic relationship
  - Return 403 Forbidden for unauthorized access
  - _Requirements: 11, 19_

### Phase 10: Note Management Endpoints

- [x] 30. Implement note creation and listing
  - Create POST /topics/{topicId}/notes endpoint (auth required)
  - Accept title, optional body, optional tint_id
  - Validate topic exists and user owns it (403 Forbidden if not)
  - Validate title (1-255 chars), tint_id exists
  - Assign random tint if not provided
  - Create note with empty scribbles array
  - Return 201 Created with note data
  - Create GET /topics/{topicId}/notes endpoint (auth required)
  - Validate user owns topic
  - Return all notes with pagination
  - Support limit, offset, sort (created_at, updated_at) parameters
  - _Requirements: 12, 20, 21, 22_

- [x] 31. Implement note read, update, and delete
  - Create GET /notes/{id} endpoint (auth required)
  - Validate user owns note (403 Forbidden if not)
  - Return complete note including scribbles
  - Create PATCH /notes/{id} endpoint (auth required)
  - Validate user owns note (403 Forbidden if not)
  - Validate scribbles array: each scribble has id, tool, color, width, opacity, points
  - Validate points array: each point has x, y coordinates as numbers
  - Update record and return updated note
  - Create DELETE /notes/{id} endpoint (auth required)
  - Validate user owns note (403 Forbidden if not)
  - Set associated snippets note_id to NULL (cascade)
  - Return 200 OK with success message
  - _Requirements: 13, 20, 21_

- [x] 32. Implement note authorization checks
  - Add authorization middleware to all note endpoints
  - Verify user owns parent topic through note relationship
  - Return 403 Forbidden for unauthorized access
  - _Requirements: 13, 19_

### Phase 11: Material Management Endpoints

- [x] 33. Implement material upload endpoint
  - Create POST /subjects/{subjectId}/materials endpoint (auth required, multipart/form-data)
  - Accept title and PDF file
  - Validate subject exists and user owns it (403 Forbidden if not)
  - Validate title (1-255 chars)
  - Validate file is PDF (MIME type application/pdf)
  - Validate file size ≤ 100MB (return 413 Payload Too Large if exceeded)
  - Store file in cloud storage (S3/GCS) with unique storage_key
  - Create material record with file metadata
  - Return 201 Created with material data including storage_key
  - _Requirements: 14, 24, 20, 21_

- [x] 34. Implement material listing and metadata endpoints
  - Create GET /subjects/{subjectId}/materials endpoint (auth required)
  - Validate user owns subject
  - Return all materials with pagination
  - Support limit, offset parameters
  - Create PATCH /materials/{id} endpoint (auth required)
  - Validate user owns material (403 Forbidden if not)
  - Validate title (max 255 chars), page_count (positive integer)
  - Update record and return updated material
  - _Requirements: 15, 20, 21, 22_

- [x] 35. Implement material download endpoint
  - Create GET /materials/{id}/download endpoint (auth required)
  - Validate user owns material (403 Forbidden if not)
  - Retrieve file from cloud storage using storage_key
  - Return file with proper Content-Type (application/pdf) and Content-Disposition headers
  - _Requirements: 14, 24, 20_

- [x] 36. Implement material delete endpoint
  - Create DELETE /materials/{id} endpoint (auth required)
  - Validate user owns material (403 Forbidden if not)
  - Delete file from cloud storage
  - Delete material record from database
  - Return 200 OK with success message
  - _Requirements: 14, 24, 20_

### Phase 12: Code Snippet Endpoints

- [x] 37. Implement snippet creation and listing
  - Create POST /snippets endpoint (auth required)
  - Accept language, code, optional note_id
  - Validate language and code are not empty
  - Validate note_id exists and user owns it (403 Forbidden if not)
  - Create snippet with empty output field
  - Return 201 Created with snippet data
  - Create GET /snippets endpoint (auth required)
  - Return all snippets owned by user with pagination
  - Support limit, offset, language filter parameters
  - Sort by created_at descending
  - _Requirements: 16, 20, 21, 22_

- [x] 38. Implement snippet update and delete
  - Create PATCH /snippets/{id} endpoint (auth required)
  - Validate user owns snippet (403 Forbidden if not)
  - Accept optional code and output fields
  - Update record and return updated snippet
  - Create DELETE /snippets/{id} endpoint (auth required)
  - Validate user owns snippet (403 Forbidden if not)
  - Delete record from database
  - Return 200 OK with success message
  - _Requirements: 17, 20_

- [x] 39. Implement snippet authorization checks
  - Add authorization middleware to all snippet endpoints
  - Verify user_id from JWT matches snippet.user_id
  - Return 403 Forbidden for unauthorized access
  - _Requirements: 17, 19_

### Phase 13: Health & Monitoring

- [x] 40. Implement health check endpoints
  - Create GET /health endpoint (public)
  - Return 200 OK with success: true and version info
  - Create GET /health/ready endpoint (public)
  - Check database connectivity
  - Return 200 OK if ready, 503 Service Unavailable if not
  - Create GET /health/live endpoint (public)
  - Return 200 OK with basic system status
  - _Requirements: 30_

- [x] 41. Implement logging middleware
  - Create src/app/middleware/logging.py with request/response logging
  - Log all API requests: method, path, status, response_time
  - Log authentication events: sign-up, sign-in, sign-out, password reset
  - Log database operations with query execution time
  - Log all errors with stack traces and context
  - Use structured JSON logging format
  - Support configurable log levels (DEBUG, INFO, WARNING, ERROR)
  - _Requirements: 26_

### Phase 14: Testing

- [ ] 42. Write unit tests for services
  - Create tests/unit/test_auth_service.py
    - Test password hashing and verification
    - Test JWT token generation and validation
    - Test sign-up validation and user creation
    - Test sign-in credential verification
    - Test password reset flow
  - Create tests/unit/test_user_service.py
    - Test profile retrieval and updates
    - Test avatar selection validation
  - Create tests/unit/test_subject_service.py
    - Test CRUD operations
    - Test authorization checks
  - Create tests/unit/test_topic_service.py
    - Test status and confidence validation
    - Test authorization checks
  - Create tests/unit/test_note_service.py
    - Test scribble validation
    - Test authorization checks
  - Create tests/unit/test_material_service.py
    - Test file type and size validation
    - Test authorization checks
  - Create tests/unit/test_snippet_service.py
    - Test language validation
    - Test authorization checks
  - Target 80%+ code coverage
  - _Requirements: 18, 19, 23_

- [ ] 43. Write integration tests for endpoints
  - Create tests/integration/test_auth_endpoints.py
    - Test sign-up with valid/invalid inputs
    - Test sign-in with valid/invalid credentials
    - Test sign-out invalidates token
    - Test password reset flow
    - Test change password
  - Create tests/integration/test_user_endpoints.py
    - Test get profile
    - Test update profile
  - Create tests/integration/test_subject_endpoints.py
    - Test create, list, update, delete subjects
    - Test authorization (403 Forbidden for non-owners)
  - Create tests/integration/test_topic_endpoints.py
    - Test create, list, update, delete topics
    - Test status and confidence validation
    - Test authorization checks
  - Create tests/integration/test_note_endpoints.py
    - Test create, list, get, update, delete notes
    - Test scribble validation
    - Test authorization checks
  - Create tests/integration/test_material_endpoints.py
    - Test upload with valid/invalid files
    - Test list, update, download, delete materials
    - Test authorization checks
  - Create tests/integration/test_snippet_endpoints.py
    - Test create, list, update, delete snippets
    - Test language filtering
    - Test authorization checks
  - Create tests/integration/test_master_data_endpoints.py
    - Test avatar styles, colors, tints endpoints
    - Test pagination
  - Create tests/integration/test_health_endpoints.py
    - Test health, ready, live endpoints
  - _Requirements: 20, 21, 22_

- [ ] 44. Write schema validation and security tests
  - Create tests/schema/test_migrations.py
    - Verify all 13 tables created correctly
    - Verify indexes on foreign keys and frequently queried columns
    - Verify unique constraints (email, storage_key, token)
    - Verify check constraints (confidence 0-5)
  - Create tests/schema/test_constraints.py
    - Test cascade delete relationships
    - Test foreign key constraints
  - Create tests/security/test_authentication.py
    - Test JWT token generation and validation
    - Test token expiration
    - Test invalid token rejection
  - Create tests/security/test_authorization.py
    - Test user can only access own data
    - Test 403 Forbidden for unauthorized access
  - Create tests/security/test_password_hashing.py
    - Test bcrypt with 10+ rounds
    - Test password verification
  - _Requirements: 18, 19, 23_

- [ ] 45. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

### Phase 15: Documentation & Deployment

- [ ] 46. Create API documentation
  - Generate OpenAPI/Swagger documentation automatically
  - Document all endpoints with request/response examples
  - Document all query parameters and path parameters
  - Document all error responses with status codes
  - Document authentication requirements for each endpoint
  - Provide interactive API documentation at /docs endpoint
  - Include rate limiting information
  - _Requirements: 29_

- [ ] 47. Create deployment configuration
  - Create Dockerfile for FastAPI application
  - Use Python 3.11+ slim image
  - Install dependencies from requirements.txt
  - Expose port 8000
  - Create docker-compose.yml for local development (FastAPI + PostgreSQL)
  - Create deployment guide with environment setup instructions
  - Document database migration process
  - Document master data seeding process
  - _Requirements: 25, 27_

## Notes

- All tasks reference specific requirements for traceability
- Each task builds on previous tasks with clear dependencies
- Authorization checks are implemented at both service and endpoint layers
- Cascade deletes are enforced at the database level
- All timestamps are in ISO 8601 format with timezone
- Pagination defaults: limit=50 (max), offset=0
- Master data is cached in memory or Redis for performance
- Error responses follow consistent format with error codes
- All inputs validated on backend before database operations
- Rate limiting implemented on authentication endpoints
- CORS configured for allowed origins from environment variable
