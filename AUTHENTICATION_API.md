# Authentication API Documentation

## Overview

This billing software implements a dual authentication system:
1. **Phone + OTP Login**: Users can login using phone number and OTP
2. **Email + Password Login**: Users can login using email and password (after setting password)

## Authentication Flow

### Shop Registration Flow

```
1. User enters phone number → Send OTP
2. User verifies OTP (optional but recommended)
3. User submits shop information → Shop created (OTP verification checked within 10 minutes)
4. User receives JWT tokens
```

**Note:** The OTP verification is checked during shop registration. The OTP must have been verified within the last 10 minutes.

### Login Flows

#### 1. Phone Number + OTP Login
```
1. User enters phone number → Send OTP
2. User enters phone + OTP in login → Receives JWT tokens
```

#### 2. Email + Password Login
```
1. User enters email + password in login → Receives JWT tokens
   Note: Password must be set first (functionality to be implemented)
```

## API Endpoints

Base URL: `http://localhost:8000`

### 1. Send OTP

**Endpoint:** `POST /auth/send-otp`

**Description:** Generate and send OTP to phone number for verification

**Request Body:**
```json
{
  "phone_number": "+919876543210"
}
```

Phone number formats accepted:
- `+919876543210` (with country code)
- `919876543210` (without +)
- `9876543210` (10 digits, assumes +91)

**Response (200):**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "phone_number": "+919876543210",
  "otp_code": "123456"
}
```

**Response (400):**
```json
{
  "success": false,
  "message": "You have reached the OTP service limit. Try after 60 minutes."
}
```

**Rate Limiting:**
- Maximum 3 OTP requests per hour per phone number
- If limit exceeded, user is blocked for 1 hour
- OTP expires after 5 minutes (controlled by pyotp TOTP interval)

**Note:** In development, OTP is returned in response. In production, remove `otp_code` from response and send via SMS.

---

### 2. Verify OTP

**Endpoint:** `POST /auth/verify-otp`

**Description:** Verify OTP for phone number (optional step - verification also happens during registration/login)

**Request Body:**
```json
{
  "phone_number": "+919876543210",
  "otp_code": "123456"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "OTP verified successfully",
  "phone_number": "+919876543210"
}
```

**Response (400):**
```json
{
  "success": false,
  "message": "Invalid OTP. 2 attempts remaining."
}
```

**Error Responses:**
```json
{
  "success": false,
  "message": "No OTP found. Please request a new one."
}
```

```json
{
  "success": false,
  "message": "OTP has expired or maximum attempts reached."
}
```

```json
{
  "success": false,
  "message": "You have reached the OTP service limit. Try after 60 minutes."
}
```

**Verification Rules:**
- Maximum 3 verification attempts per OTP
- After 3 failed attempts, user is blocked for 1 hour
- Verified OTPs are marked as `is_verified=True` in the database

---

### 3. Register Shop

**Endpoint:** `POST /auth/register-shop`

**Description:** Register shop after phone verification. This creates both User and Shop and returns JWT tokens.

**Request Body:**
```json
{
  "phone_number": "+919876543210",
  "shop_code": "SHOP001",
  "shop_name": "ABC Retail Store",
  "legal_name": "ABC Retail Private Limited",
  "email": "contact@abcretail.com",
  "tax_no": "27AABCU9603R1ZM",
  "pan_no": "AABCU9603R",
  "address": "123 Main Street, Near City Mall, Mumbai",
  "pincode": "400001",
  "country_id": 274,
  "state_id": 3932,
  "city_id": 38139,
  "default_shop": 0
}
```

**Required Fields:**
- `phone_number` (string)
- `shop_code` (string, unique)
- `shop_name` (string)
- `legal_name` (string)
- `email` (string, unique)

**Optional Fields:**
- `address` (string)
- `pincode` (string)
- `country_id` (integer) - From cities_light Country table
- `state_id` (integer) - From cities_light Region table
- `city_id` (integer) - From cities_light City table
- `tax_no` (string) - GST/Tax number
- `pan_no` (string) - PAN number
- `default_shop` (integer, default: 0) - 0: No, 1: Yes

**How to get Country/State/City IDs:**

Use the Location API endpoints to get the IDs:

1. **Get all countries:**
   ```bash
   GET /locations/countries
   ```

2. **Search for a country:**
   ```bash
   GET /locations/search/countries?query=India
   # Returns: [{"id": 274, "name": "India", "code2": "IN", "code3": "IND"}]
   ```

3. **Get states/regions for a country:**
   ```bash
   GET /locations/countries/274/regions
   # Returns regions for India
   ```

4. **Search for a state:**
   ```bash
   GET /locations/search/regions?query=Maharashtra&country_id=274
   ```

5. **Get cities for a state:**
   ```bash
   GET /locations/regions/3932/cities
   # Returns cities for the region
   ```

6. **Search for a city:**
   ```bash
   GET /locations/search/cities?query=Mumbai&region_id=3932
   ```

**Example Location IDs:**
- India (Country): `274`
- Andhra Pradesh (State): `3932`
- Maharashtra (State): Find using search endpoint
- Mumbai (City): Find using search endpoint

**Response (200):**
```json
{
  "success": true,
  "message": "Shop registered successfully",
  "user": {
    "id": "uuid-here",
    "phone_number": "+919876543210",
    "email": "contact@abcretail.com",
    "user_name": null,
    "is_verified": true,
    "has_password": false
  },
  "shop": {
    "id": "uuid-here",
    "shop_code": "SHOP001",
    "shop_name": "ABC Retail Store",
    "legal_name": "ABC Retail Private Limited",
    "email": "contact@abcretail.com",
    "phone_number": "+919876543210",
    "tax_no": "27AABCU9603R1ZM",
    "pan_no": "AABCU9603R",
    "address": "123 Main Street, Near City Mall, Mumbai",
    "pincode": "400001",
    "default_shop": 0,
    "status": 0,
    "created_at": "2025-12-08T10:00:00Z"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user_id": "uuid-here",
    "phone_number": "+919876543210",
    "email": "contact@abcretail.com",
    "has_password": false
  }
}
```

**Response (400):**
```json
{
  "success": false,
  "message": "Phone number not verified. Please verify OTP first."
}
```

```json
{
  "success": false,
  "message": "User already has a registered shop. Please login."
}
```

**Important Notes:**
- Phone number must have a verified OTP within the last 10 minutes
- The verified OTP is automatically deleted after successful registration
- Shop email must be unique across all shops
- Shop code must be unique across all shops
- Creates or updates User with phone verification status
- Automatically sets user as shop owner (User.owned_shops)
- Returns JWT tokens for immediate login

---

### 4. Login (Dual Authentication)

**Endpoint:** `POST /auth/login`

**Description:** Login using either phone+OTP or email+password

#### Option 1: Phone Number + OTP Login

**Request Body:**
```json
{
  "identifier": "+919876543210",
  "otp_code": "123456"
}
```

**Note:** First send OTP using `/auth/send-otp` endpoint. The OTP will be verified automatically during login.

#### Option 2: Email + Password Login

**Request Body:**
```json
{
  "identifier": "contact@abcretail.com",
  "password": "mySecurePassword123"
}
```

**Note:** Password must be set first (password setting feature to be implemented)

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": "uuid-here",
  "phone_number": "+919876543210",
  "email": "contact@abcretail.com",
  "has_password": false
}
```

**Response (400) - Phone Login Errors:**
```json
{
  "success": false,
  "message": "OTP is required for phone number login"
}
```

```json
{
  "success": false,
  "message": "User not found. Please register first."
}
```

**Response (400) - Email Login Errors:**
```json
{
  "success": false,
  "message": "Password is required for email login"
}
```

```json
{
  "success": false,
  "message": "Invalid email or password"
}
```

```json
{
  "success": false,
  "message": "Password not set. Please set password first or use phone number login."
}
```

**Response (400) - General Errors:**
```json
{
  "success": false,
  "message": "User account is inactive"
}
```

**Login Logic:**
- System detects login method by checking if identifier contains `@`
- If `@` present → Email + Password authentication
- If `@` absent → Phone + OTP authentication
- OTP verification happens automatically during phone login
- Returns JWT access and refresh tokens on successful login

---

### 5. Get Current User (Protected)

**Endpoint:** `GET /auth/me`

**Description:** Get current authenticated user information and their shops

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "success": true,
  "user": {
    "id": "uuid-here",
    "phone_number": "+919876543210",
    "email": "contact@abcretail.com",
    "user_name": null,
    "is_verified": true
  },
  "shops": [
    {
      "id": "uuid-here",
      "shop_code": "SHOP001",
      "shop_name": "ABC Retail Store",
      "legal_name": "ABC Retail Private Limited",
      "email": "contact@abcretail.com"
    }
  ]
}
```

**Response (401):**
```json
{
  "success": false,
  "message": "Unauthorized"
}
```

**Notes:**
- Requires valid JWT access token in Authorization header
- Returns only active shops (status = 0)
- Shows shops where user is the owner (User.owned_shops)
- User details include verification status but not password info

---

## Location APIs (Helper Endpoints)

These endpoints help you get the correct IDs for country, state/region, and city fields when registering a shop.

### 1. Get All Countries

**Endpoint:** `GET /locations/countries`

**Description:** Get list of all available countries

**Response (200):**
```json
[
  {
    "id": 274,
    "name": "India",
    "code2": "IN",
    "code3": "IND"
  },
  {
    "id": 1,
    "name": "Australia",
    "code2": "AU",
    "code3": "AUS"
  }
]
```

---

### 2. Search Countries

**Endpoint:** `GET /locations/search/countries?query={search_term}`

**Description:** Search countries by name

**Example:**
```bash
GET /locations/search/countries?query=India
```

**Response (200):**
```json
[
  {
    "id": 274,
    "name": "India",
    "code2": "IN",
    "code3": "IND"
  }
]
```

---

### 3. Get States/Regions by Country

**Endpoint:** `GET /locations/countries/{country_id}/regions`

**Description:** Get all states/regions for a specific country

**Example:**
```bash
GET /locations/countries/274/regions
```

**Response (200):**
```json
[
  {
    "id": 3932,
    "name": "Andhra Pradesh",
    "geoname_code": "AP"
  },
  {
    "id": 3929,
    "name": "Bihar",
    "geoname_code": "BR"
  },
  {
    "id": 3928,
    "name": "Maharashtra",
    "geoname_code": "MH"
  }
]
```

---

### 4. Search States/Regions

**Endpoint:** `GET /locations/search/regions?query={search_term}&country_id={country_id}`

**Description:** Search states/regions by name, optionally filtered by country

**Example:**
```bash
GET /locations/search/regions?query=Maharashtra&country_id=274
```

**Response (200):**
```json
[
  {
    "id": 3928,
    "name": "Maharashtra",
    "geoname_code": "MH",
    "country_id": 274
  }
]
```

---

### 5. Get Cities by State/Region

**Endpoint:** `GET /locations/regions/{region_id}/cities`

**Description:** Get all cities for a specific state/region

**Example:**
```bash
GET /locations/regions/3928/cities
```

**Response (200):**
```json
[
  {
    "id": 40123,
    "name": "Mumbai",
    "geoname_id": 1275339
  },
  {
    "id": 40124,
    "name": "Pune",
    "geoname_id": 1259229
  }
]
```

---

### 6. Search Cities

**Endpoint:** `GET /locations/search/cities?query={search_term}&region_id={region_id}`

**Description:** Search cities by name, optionally filtered by state/region

**Example:**
```bash
GET /locations/search/cities?query=Mumbai&region_id=3928
```

**Response (200):**
```json
[
  {
    "id": 40123,
    "name": "Mumbai",
    "geoname_id": 1275339,
    "region_id": 3928
  }
]
```

---

## Using Location APIs in Postman

**Step-by-Step Guide to Get Location IDs:**

1. **Find Country ID:**
   ```
   GET http://localhost:8000/locations/search/countries?query=India
   → Get id: 274
   ```

2. **Find State/Region ID:**
   ```
   GET http://localhost:8000/locations/search/regions?query=Maharashtra&country_id=274
   → Get id: 3928
   ```

3. **Find City ID:**
   ```
   GET http://localhost:8000/locations/search/cities?query=Mumbai&region_id=3928
   → Get id: 40123
   ```

4. **Use in Shop Registration:**
   ```json
   {
     "phone_number": "+919876543210",
     "shop_code": "SHOP001",
     "shop_name": "My Shop",
     "legal_name": "My Shop Pvt Ltd",
     "email": "shop@example.com",
     "address": "123 Main Street",
     "pincode": "400001",
     "country_id": 274,
     "state_id": 3928,
     "city_id": 40123
   }
   ```

**Note:** The location fields (country_id, state_id, city_id) are now **optional** in shop registration. You can omit them if you don't want to specify the location.

---

## Complete User Journey Examples

### Example 1: New User Registration with Phone Only

```bash
# Step 1: Send OTP
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210"
  }'

# Response: {"success": true, "message": "OTP sent successfully", "phone_number": "+919876543210", "otp_code": "123456"}

# Step 2: Verify OTP (Optional but recommended)
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "otp_code": "123456"
  }'

# Response: {"success": true, "message": "OTP verified successfully", "phone_number": "+919876543210"}

# Step 3: Register Shop (must be within 10 minutes of OTP verification)
curl -X POST http://localhost:8000/auth/register-shop \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "shop_code": "SHOP001",
    "shop_name": "My Store",
    "legal_name": "My Store Pvt Ltd",
    "email": "info@mystore.com",
    "address": "123 Main St",
    "pincode": "400001",
    "country_id": 1,
    "state_id": 10,
    "city_id": 100,
    "tax_no": "27AABCU9603R1ZM",
    "pan_no": "AABCU9603R"
  }'

# Response: Shop created with user and JWT tokens returned
# User can now use the access token to make authenticated requests
```

### Example 2: Existing User Login via Phone + OTP

```bash
# Step 1: Send OTP
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210"
  }'

# Response: {"success": true, "message": "OTP sent successfully", "phone_number": "+919876543210", "otp_code": "123456"}

# Step 2: Login with OTP (OTP verification happens automatically)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "+919876543210",
    "otp_code": "123456"
  }'

# Response: JWT tokens returned
```

### Example 3: Get Current User Information

```bash
# Use the access token from login/registration
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."

# Response: User info with all owned shops
```

### Example 4: User Login via Email + Password (To be implemented)

```bash
# Password setting endpoints need to be implemented
# Once implemented, users can login with email + password
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "info@mystore.com",
    "password": "myPassword123"
  }'
```

---

## Models Overview

### User Model
Fields:
- `id`: UUID (primary key)
- `phone_number`: CharField (max 15, unique, nullable) - Primary identifier
- `email`: EmailField (unique, nullable)
- `password`: CharField (max 128, nullable) - Hashed password
- `user_name`: CharField (max 150, nullable)
- `role`: ForeignKey to RolePermission (nullable)
- `shops`: ManyToManyField to Shop - Shops this user has access to
- `primary_shop`: ForeignKey to Shop (nullable) - User's primary shop
- `permissions`: JSONField (default: list) - User-specific permissions
- `address`: CharField (max 255, nullable)
- `city`: ForeignKey to City (nullable)
- `state`: ForeignKey to Region (nullable)
- `country`: ForeignKey to Country (nullable)
- `pincode`: CharField (max 10, nullable)
- `is_staff`: BooleanField (default: False)
- `is_active`: BooleanField (default: True)
- `is_verified`: BooleanField (default: False) - Phone number verified via OTP
- `user_lock`: BooleanField (default: False)
- `status`: IntegerField (default: 0) - 0: Active, 1: Inactive, 2: Deleted
- `created_at`, `updated_at`: Timestamps

Relations:
- Can own multiple shops (Shop.owner → User.owned_shops)
- Can have access to multiple shops (User.shops → Shop.staff)
- Can have a primary shop (User.primary_shop)
- Can have a role with permissions (User.role)
- Has location data via cities_light (Country, Region, City)

### Shop Model
Fields:
- `id`: UUID (primary key)
- `owner`: ForeignKey to User - Shop owner
- `shop_code`: CharField (max 150, unique) - Unique shop identifier
- `shop_name`: CharField (max 150)
- `legal_name`: CharField (max 150)
- `phone_number`: CharField (max 15, nullable)
- `email`: EmailField (unique)
- `password`: CharField (max 128, nullable) - Shop-level password
- `tax_no`: CharField (max 15, nullable) - GST/Tax number
- `pan_no`: CharField (max 15, nullable) - PAN number
- `address`: TextField (nullable)
- `pincode`: CharField (max 10, nullable)
- `city`: ForeignKey to City (nullable)
- `state`: ForeignKey to Region (nullable)
- `country`: ForeignKey to Country (nullable)
- `logo_image`: ImageField (nullable)
- `default_shop`: IntegerField (default: 0) - 0: No, 1: Yes
- `status`: IntegerField (default: 0) - 0: Active, 1: Inactive, 2: Deleted
- `created_at`, `updated_at`: Timestamps

Relations:
- Owned by one User (Shop.owner → User.owned_shops)
- Can have multiple staff users (Shop.staff)
- Uses cities_light for location (Country, Region, City)

### OTP Model
Fields:
- `id`: UUID (primary key)
- `phone_number`: CharField (max 15, nullable)
- `email`: EmailField (nullable)
- `otp_code`: CharField (max 6) - 6-digit OTP code
- `otp_type`: CharField (max 50) - 'REGISTRATION' or 'LOGIN' (default: 'LOGIN')
- `attempts`: IntegerField (default: 0) - Number of verification attempts
- `blocked_until`: DateTimeField (nullable) - User blocked until this time
- `is_verified`: BooleanField (default: False) - Whether OTP was verified
- `created_at`, `updated_at`: Timestamps

Features:
- 6-digit code generated using pyotp
- 5-minute expiry (TOTP interval)
- Maximum 3 verification attempts
- Maximum 3 OTP requests per hour
- 1-hour block after exceeding limits
- Previous OTPs auto-deleted when new one generated
- Verified OTPs marked with `is_verified=True`
- Deleted after successful registration

### RolePermission Model
Fields:
- `id`: UUID (primary key)
- `role_name`: CharField (max 150)
- `permissions`: JSONField (default: list) - List of permission strings
- `shop`: ForeignKey to Shop (nullable) - Shop-specific role
- `status`: IntegerField (default: 0) - 0: Active, 1: Inactive, 2: Deleted
- `created_at`, `updated_at`: Timestamps

Relations:
- Can be assigned to multiple users (User.role)
- Can be shop-specific (RolePermission.shop)

---

## API Documentation UI

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

**Note:** The base API path is `/` (root), not `/api/`. All auth endpoints are under `/auth/`.

---

## Security Notes

1. **OTP in Development**:
   - OTP is returned in API response for development/testing
   - In production, integrate SMS provider and remove `otp_code` from response
   - OTP is also printed to console for debugging

2. **SMS Integration**:
   - Integrate with SMS provider (Twilio, MSG91, etc.) in production
   - Update `AuthService.send_otp()` in [apps/accounts/services.py](apps/accounts/services.py:38)
   - Remove `otp_code` from OTPResponseSchema

3. **JWT Tokens**:
   - Uses djangorestframework-simplejwt
   - Access token and refresh token generated on login/registration
   - Token validity configured in Django settings
   - Bearer token authentication for protected endpoints

4. **Password Requirements**:
   - Minimum 8 characters (enforced in service layer)
   - Password hashing using Django's default (PBKDF2)
   - Password setting/update endpoints need to be added to API

5. **Phone Number Format**:
   - Supports Indian phone numbers (+91)
   - Auto-normalizes to E.164 format
   - Accepts: +919876543210, 919876543210, 9876543210
   - Uses phonenumbers library for validation

6. **Rate Limiting**:
   - Built-in OTP rate limiting (3 requests/hour per phone)
   - 3 verification attempts per OTP
   - 1-hour block after exceeding limits
   - Consider adding Django rate limiting middleware for API endpoints

7. **Data Validation**:
   - All inputs validated using Ninja schemas
   - Phone number normalization and validation
   - Email uniqueness enforced at database level
   - Shop code uniqueness enforced at database level

---

## Implementation Status

### Implemented Features ✓
- Phone number + OTP authentication
- Shop registration with OTP verification
- Phone + OTP login
- Email + Password login (backend ready)
- Get current user endpoint
- JWT token generation
- OTP rate limiting and blocking
- Phone number normalization
- User and Shop models with proper relations
- Role-based permission system (models ready)
- Location APIs (Country, State/Region, City lookup)
- Cities Light integration for location data

### To Be Implemented
- [ ] Password setting endpoints (set-password, update-password)
- [ ] Password reset flow (forgot password)
- [ ] Email verification
- [ ] SMS integration for OTP delivery
- [ ] Refresh token endpoint
- [ ] Logout endpoint (token blacklisting)
- [ ] User profile update endpoints
- [ ] Shop management endpoints (update, delete)
- [ ] Staff user management
- [ ] Role and permission management APIs
- [ ] Multi-shop switching for users
- [ ] Admin endpoints for user/shop management

---

## Next Steps

### High Priority
1. **Add Password Management Endpoints**:
   - Implement set-password endpoint (protected)
   - Implement update-password endpoint
   - Implement forgot-password flow

2. **Integrate SMS Provider**:
   - Add Twilio/MSG91/AWS SNS for OTP delivery
   - Remove OTP from API responses
   - Add SMS sending status tracking

3. **Add Token Management**:
   - Implement refresh token endpoint
   - Add logout endpoint with token blacklisting
   - Add token revocation

### Medium Priority
4. **Add Email Verification**:
   - Send verification email after registration
   - Add email verification endpoint
   - Make verified email required for certain operations

5. **Enhance Security**:
   - Add API rate limiting middleware
   - Add logging for authentication attempts
   - Add IP-based blocking for suspicious activity
   - Add 2FA support

6. **Shop Management**:
   - Add shop update endpoint
   - Add shop deletion endpoint (soft delete)
   - Add shop staff management
   - Add shop switching for users with multiple shops

### Low Priority
7. **User Profile Management**:
   - Add user profile update endpoint
   - Add avatar upload
   - Add user preferences

8. **Admin Features**:
   - Add admin endpoints for user management
   - Add shop approval workflow
   - Add user suspension/ban features

---

## Dependencies

All required packages are installed:
- `django` - Web framework
- `django-ninja` - API framework
- `djangorestframework` - REST framework utilities
- `djangorestframework-simplejwt` - JWT authentication
- `pyotp` - OTP generation
- `phonenumbers` - Phone number validation
- `django-phonenumber-field` - Phone number field
- `django-cities-light` - Country/State/City data

---

## Running the Server

```bash
# Start development server
python3 manage.py runserver

# Access API at
http://localhost:8000

# Access API documentation at
http://localhost:8000/docs
```

## Database Migrations

```bash
# Create migrations
python3 manage.py makemigrations

# Apply migrations
python3 manage.py migrate
```

## Testing the API

Use the examples in "Complete User Journey Examples" section to test the API with curl or any API client (Postman, Insomnia, etc.).
