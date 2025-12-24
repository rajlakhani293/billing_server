# Testing Shop Registration After Migration

## Migration Status ✓

The following migration has been successfully applied:
- **Migration:** `0006_user_address_user_city_user_country_user_pincode_and_more.py`
- **Changes:**
  - Added `address` field to User model
  - Added `city` field to User model (ForeignKey to cities_light.City)
  - Added `country` field to User model (ForeignKey to cities_light.Country)
  - Added `pincode` field to User model
  - Added `state` field to User model (ForeignKey to cities_light.Region)

## Database Schema Updated ✓

User model now has all location fields. You can verify by running:
```bash
python3 manage.py dbshell
# Then run: DESCRIBE users;
```

## Test Shop Registration

### Option 1: Without Location Data

```bash
# Step 1: Send OTP
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210"
  }'

# Step 2: Verify OTP (get otp_code from step 1 response)
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "otp_code": "123456"
  }'

# Step 3: Register Shop (within 10 minutes)
curl -X POST http://localhost:8000/auth/register-shop \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "shop_code": "SHOP001",
    "shop_name": "Test Shop",
    "legal_name": "Test Shop Pvt Ltd",
    "email": "test@shop.com"
  }'
```

### Option 2: With Location Data

```bash
# Step 1: Get location IDs
curl http://localhost:8000/locations/search/countries?query=India
# Get country_id: 274

curl http://localhost:8000/locations/search/regions?query=Maharashtra&country_id=274
# Get state_id

curl http://localhost:8000/locations/search/cities?query=Mumbai
# Get city_id

# Step 2: Send OTP
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919999999999"
  }'

# Step 3: Verify OTP
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919999999999",
    "otp_code": "PASTE_OTP_HERE"
  }'

# Step 4: Register Shop with location
curl -X POST http://localhost:8000/auth/register-shop \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919999999999",
    "shop_code": "SHOP002",
    "shop_name": "Mumbai Shop",
    "legal_name": "Mumbai Shop Pvt Ltd",
    "email": "mumbai@shop.com",
    "address": "123 Main Street, Mumbai",
    "pincode": "400001",
    "country_id": 274,
    "state_id": 3928,
    "city_id": 40123,
    "tax_no": "27AABCU9603R1ZM",
    "pan_no": "AABCU9603R",
    "default_shop": 0
  }'
```

## Expected Response

```json
{
  "success": true,
  "message": "Shop registered successfully",
  "user": {
    "id": "uuid-here",
    "phone_number": "+919999999999",
    "email": "mumbai@shop.com",
    "user_name": null,
    "is_verified": true,
    "has_password": false
  },
  "shop": {
    "id": "uuid-here",
    "shop_code": "SHOP002",
    "shop_name": "Mumbai Shop",
    "legal_name": "Mumbai Shop Pvt Ltd",
    "email": "mumbai@shop.com",
    "phone_number": "+919999999999",
    "tax_no": "27AABCU9603R1ZM",
    "pan_no": "AABCU9603R",
    "address": "123 Main Street, Mumbai",
    "pincode": "400001",
    "default_shop": 0,
    "status": 0,
    "created_at": "2025-12-08T11:44:00Z"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user_id": "uuid-here",
    "phone_number": "+919999999999",
    "email": "mumbai@shop.com",
    "has_password": false
  }
}
```

## Troubleshooting

### Error: "Unknown column 'users.address'"
**Solution:** Run migrations
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### Error: "Phone number not verified"
**Solution:** Make sure you verify the OTP within 10 minutes before registering the shop

### Error: "User already has a registered shop"
**Solution:** Use a different phone number or login with the existing account

## Next Steps

1. Test the registration flow in Postman
2. Verify that location data is properly saved
3. Test the `/auth/me` endpoint to see user and shop data
4. Test login with the registered user

## Available Endpoints

- `POST /auth/send-otp` - Send OTP
- `POST /auth/verify-otp` - Verify OTP
- `POST /auth/register-shop` - Register shop
- `POST /auth/login` - Login
- `GET /auth/me` - Get current user (protected)
- `GET /locations/countries` - Get all countries
- `GET /locations/search/countries?query=India` - Search countries
- `GET /locations/countries/274/regions` - Get states for country
- `GET /locations/search/regions?query=Maharashtra&country_id=274` - Search states
- `GET /locations/regions/3928/cities` - Get cities for state
- `GET /locations/search/cities?query=Mumbai&region_id=3928` - Search cities

## API Documentation

Visit: http://localhost:8000/docs
