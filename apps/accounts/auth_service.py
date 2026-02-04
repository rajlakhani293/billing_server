import json
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from apps.core.helpers import check_recent_verification, normalize_phone_number, ResponseBuilder, generate_otp
from apps.accounts.schema import ShopRegistrationSchema
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, OTP
from .menu_service import MenuService
from apps.shops.models import Shop
from ninja.errors import HttpError
import re
import random
import string
from django.db import transaction
import jwt
from django.conf import settings

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# AuthService
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class AuthService:

    @staticmethod
    def _build_user_data(user: User) -> dict:
        """Build complete user data object for login response"""
        return {
            'id': user.id,
            'user_name': user.user_name,
            'phone_number': user.phone_number,
            'email': user.email,
            'address': user.address,
            'city': {
                        'id': user.city.id if user.city else None,
                        'name': user.city.name if user.city else None
                    } if user.city else None,
                    'state': {
                        'id': user.state.id if user.state else None,
                        'name': user.state.name if user.state else None
                    } if user.state else None,
                    'country': {
                        'id': user.country.id if user.country else None,
                        'name': user.country.name if user.country else None
                    } if user.country else None,
            'pincode': user.pincode,
            'profile_image_url': str(user.profile_image) if user.profile_image else None,
            'shop_id': user.primary_shop.id if user.primary_shop else None
        }

    @staticmethod
    def _build_login_response(user: User) -> dict:
        """Build login response with tokens and user data"""
        token = RefreshToken.for_user(user)
        
        # Add user_id and shop_id to the access token payload
        access_token = token.access_token
        access_token['user_id'] = user.id
        access_token['shop_id'] = user.primary_shop.id if user.primary_shop else None
        
        return ResponseBuilder.success(
            'Login successful',
            {
                'token': str(access_token),
                'user': AuthService._build_user_data(user)
            }
        )

    @staticmethod
    def send_otp(phone_number: str) -> dict:
        try:
            # Normalize phone number
            normalized_phone = normalize_phone_number(phone_number)

            # Check if user already exists (prevent sign-up OTP for existing users)
            if User.objects.filter(phone_number=normalized_phone).exists():
                return ResponseBuilder.error('User already registered with this phone number')

            # Generate OTP
            otp_instance = generate_otp(normalized_phone, otp_type='REGISTRATION')

            return ResponseBuilder.success(
                'OTP sent successfully',
                {
                    'otp_code': otp_instance.otp_code
                }
            )
        except ValueError as e:
            return ResponseBuilder.error(str(e))

    @staticmethod
    def verify_otp(payload: dict) -> dict:
        """Verify OTP code and return registration token"""
        try:
            # Normalize phone number
            normalized_phone = normalize_phone_number(payload['phone_number'])

            # Check if user already exists with this phone number
            if User.objects.filter(phone_number=normalized_phone).exists():
                return ResponseBuilder.error('User already registered with this phone number')

            # Get OTP instance
            otp_code = OTP.objects.filter(
                phone_number=normalized_phone
            ).order_by('-created_at').first()

            if not otp_code:
                return ResponseBuilder.error('OTP not found')

            # Verify OTP
            if otp_code.verify(payload['otp_code']):               
                # Mark OTP as verified
                otp_code.is_verified = True
                otp_code.save()
                
                registration_token = jwt.encode(
                    {
                        'phone_number': normalized_phone,
                        'scope': 'registration_verification',
                        'exp': timezone.now() + timedelta(minutes=10)
                    },
                    settings.SECRET_KEY,
                    algorithm='HS256'
                )
                
                return ResponseBuilder.success(
                    'OTP verified successfully',
                    {
                        'phone_number': normalized_phone,
                        'registration_token': registration_token,
                    }
                )
            else:
                return ResponseBuilder.error('Invalid OTP code')
        except ValueError as e:
            return ResponseBuilder.error(str(e))


    @staticmethod
    def register_shop(payload: ShopRegistrationSchema) -> dict:
        """Register a new shop with user - requires valid registration token"""
        data = payload.dict()
        
        try:
            # Validate required fields
            is_valid, errors = ShopService._validate_registration_data(data)
            if not is_valid:
                return ResponseBuilder.error('Validation Error', errors)

            # Validate registration token
            token_valid, token_message, verified_phone = ShopService._validate_registration_token(
                data['registration_token']
            )
            if not token_valid:
                return ResponseBuilder.error(token_message)

            # Check if phone number was verified within last 10 minutes
            verification_check = check_recent_verification(verified_phone)
            if not verification_check['was_verified_recently']:
                return ResponseBuilder.error(
                    'Registration session expired. Please verify your phone number again to continue.'  
                )

            # Check if user already exists
            if User.objects.filter(phone_number=verified_phone).exists():
                return ResponseBuilder.error('User already registered with this phone number')

            # Check if email already exists (only if email is provided and not empty)
            email = data.get('email')
            if email and email != "" and email is not None:  # Only check if email is not empty and not null
                if User.objects.filter(email=email).exists():
                    return ResponseBuilder.error('Email already registered with another account')

            # Create user and shop in transaction
            with transaction.atomic():
                user, shop = ShopService._create_user_and_shop(data, verified_phone)
                return ShopService._build_response(user, shop)

        except Exception as e:
            # Handle specific database errors
            error_message = str(e)
            
            if "Duplicate entry" in error_message and "email" in error_message:
                return ResponseBuilder.error(
                    'Email address is already registered. Please use a different email address.'
                )
            elif "Duplicate entry" in error_message and "phone_number" in error_message:
                return ResponseBuilder.error(
                    'Phone number is already registered. Please use a different phone number.'
                )
            elif "Duplicate entry" in error_message:
                return ResponseBuilder.error(
                    'Registration failed: Some information already exists in our system.'
                )
            else:
                return ResponseBuilder.error(f'Failed to register shop: {str(e)}')

    @staticmethod
    def send_login_otp(phone_number: str) -> dict:
        """Send login OTP"""
        try:
            # Normalize phone number
            normalized_phone = normalize_phone_number(phone_number)

            # Check if user exists
            if not User.objects.filter(phone_number=normalized_phone).exists():
                return ResponseBuilder.error(HttpError(400, 'User not found with this phone number'))

            # Generate OTP
            otp_instance = generate_otp(normalized_phone, otp_type='LOGIN')

            return ResponseBuilder.success(
                'Login OTP sent successfully',
                {
                    'otp_code': otp_instance.otp_code
                }
            )
        except Exception as e:
            return ResponseBuilder.error(HttpError(400, str(e)))

    @staticmethod
    def login(payload: dict) -> dict:
        """Login user with phone/email + password or OTP"""
        try:
            phone_number = payload.get('phone_number')
            email = payload.get('email')
            password = payload.get('password')
            otp_code = payload.get('otp_code')
            
            if phone_number and email:
                return ResponseBuilder.error('Provide either phone number or email, not both')
            
            if not phone_number and not email:
                return ResponseBuilder.error('Provide either phone number or email')
            
            # 1. OTP LOGIN FLOW
            if phone_number:
                normalized_phone = normalize_phone_number(phone_number)
                
                if not otp_code:
                    return ResponseBuilder.error('OTP code is required for phone number login')
                
                user = User.objects.get(phone_number=normalized_phone)
                
                # Get the most recent OTP
                otp_instance = OTP.objects.filter(
                    phone_number=normalized_phone
                ).order_by('-created_at').first()

                # Verify OTP (This calls the logic in your OTP model)
                if not otp_instance or not otp_instance.verify(otp_code):
                    return ResponseBuilder.error('Invalid OTP code')

                # This deletes the "wasted" OTP count so the user isn't blocked later
                OTP.objects.filter(phone_number=normalized_phone).delete()

                return AuthService._build_login_response(user)

            # 2. PASSWORD LOGIN FLOW
            elif email:
                if not password:
                    return ResponseBuilder.error('Password is required for email login')
                
                user = User.objects.filter(email=email).first()

                if not user:
                    return ResponseBuilder.error('User not found')

                if not user.password:
                    return ResponseBuilder.error('Password not set for this account')

                # Authenticate using Django's built-in system
                auth_user = authenticate(
                    username=user.phone_number or user.email,
                    password=password
                )

                if not auth_user:
                    return ResponseBuilder.error('Invalid credentials')

                return AuthService._build_login_response(auth_user)

        except User.DoesNotExist:
            return ResponseBuilder.error('User not found')
        except Exception as e:
            return ResponseBuilder.error(f'Login failed: {str(e)}')

    @staticmethod
    def logout(request):
        try:
            data = json.loads(request.body)
            refresh_token = data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist() 
            return ResponseBuilder.success('Logout successful')
        except Exception as e:
            return ResponseBuilder.error(f'Logout failed: {str(e)}')

    @staticmethod
    def get_session_data(request) -> dict:
        """Get comprehensive user session data"""
        try:
            # Extract user and shop from authenticated request
            auth_data = request.auth
            if not auth_data:
                return ResponseBuilder.error("Authentication required")
            
            user = auth_data['user']
            shop = auth_data['shop']
            
            # Get user's shops
            shops = user.shops.all()
            primary_shop = user.primary_shop
                 
            # Build shop list with enriched data
            shop_list = []
            for shop_item in shops:
                shop_data = {
                    'shop_id': shop_item.id,
                    'shop_code': shop_item.shop_code,
                    'shop_name': shop_item.shop_name,
                    'legal_name': shop_item.legal_name,
                    'email': shop_item.email,
                    'phone_number': shop_item.phone_number,
                    'tax_no': shop_item.tax_no,
                    'pan_no': shop_item.pan_no,
                    'address': shop_item.address,
                    'pincode': shop_item.pincode,
                    'city': {
                        'id': shop_item.city.id if shop_item.city else None,
                        'name': shop_item.city.name if shop_item.city else None
                    } if shop_item.city else None,
                    'state': {
                        'id': shop_item.state.id if shop_item.state else None,
                        'name': shop_item.state.name if shop_item.state else None
                    } if shop_item.state else None,
                    'country': {
                        'id': shop_item.country.id if shop_item.country else None,
                        'name': shop_item.country.name if shop_item.country else None
                    } if shop_item.country else None,
                    'logo_image_url': str(shop_item.logo_image) if shop_item.logo_image else None,
                    'default_shop': shop_item.default_shop,
                    'status': shop_item.status,
                }
                shop_list.append(shop_data)
            
            # Current shop (from token)
            current_shop = None
            if shop:
                current_shop = next((shop_item for shop_item in shop_list if shop_item['shop_id'] == shop.id), None)
            
            # Enriched user data
            enriched_user = {
                'id': user.id,
                'phone_number': user.phone_number,
                'email': user.email,
                'user_name': user.user_name,
                'is_verified': user.is_verified,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'has_password': bool(user.password),
                'profile_image_url': None
            }
            
            # Get sidebar menu
            sidebar_menu_result = MenuService.get_menus_with_modules()
            sidebar_menu = sidebar_menu_result.get('data', []) if sidebar_menu_result.get('success') else []
            
            return ResponseBuilder.success(
                'Session data retrieved successfully',
                {
                    'shop_list': shop_list,
                    'shop': current_shop,
                    'user': enriched_user,
                    'sidebarMenu': sidebar_menu
                }
            )
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get session data: {str(e)}')

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Shop Service
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class ShopService:
    
    @staticmethod
    def generate_shop_code(shop_name: str) -> str:
        """Generate unique shop code with industry best practices"""
        
        # Clean and normalize shop name
        clean_name = re.sub(r'[^\w\s]', '', shop_name)
        clean_name = re.sub(r'\s+', '', clean_name)
        
        # Take first 6 characters of shop name (uppercase)
        prefix = clean_name[:6].upper()
        
        # Generate random 4-digit suffix
        suffix = ''.join(random.choices(string.digits, k=4))
        
        # Combine to create shop code
        shop_code = f"{prefix}{suffix}"
        
        # Ensure uniqueness, regenerate if exists
        attempts = 0
        max_attempts = 10
        
        while Shop.objects.filter(shop_code=shop_code).exists() and attempts < max_attempts:
            suffix = ''.join(random.choices(string.digits, k=4))
            shop_code = f"{prefix}{suffix}"
            attempts += 1
        
        if attempts >= max_attempts:
            # Fallback to timestamp-based code
            import time
            timestamp = str(int(time.time()))[-6:]
            shop_code = f"SHOP{timestamp}"
        
        return shop_code
    
    @staticmethod
    def _validate_registration_data(data: dict) -> tuple[bool, dict]:
        """Validate required registration fields"""
        required_fields = {
            'registration_token': 'Registration Token',
            'shop_name': 'Shop Name',
            'country': 'Country',
            'state': 'State',
            'city': 'City'
        }

        errors = {}
        for field, label in required_fields.items():
            if not data.get(field):
                errors[field] = f"{label} is required"

        # Validate city, state, country existence
        if data.get('city'):
            from apps.core.models import CityMaster, StateMaster, CountryMaster
            if not CityMaster.objects.filter(id=data['city']).exists():
                errors['city'] = 'Invalid city ID'
        
        if data.get('state'):
            if not StateMaster.objects.filter(id=data['state']).exists():
                errors['state'] = 'Invalid state ID'
        
        if data.get('country'):
            if not CountryMaster.objects.filter(id=data['country']).exists():
                errors['country'] = 'Invalid country ID'

        return (len(errors) == 0, errors)
    
    @staticmethod
    def _validate_registration_token(token: str) -> tuple[bool, str, str]:
        """Validate registration token and return phone number"""
        try:
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            if decoded.get("scope") != "registration_verification":
                return False, "Invalid token scope", None

            verified_phone = decoded.get("phone_number")
            if not verified_phone:
                return False, "Invalid token", None

            return True, "Token valid", verified_phone

        except jwt.ExpiredSignatureError:
            return False, "Registration token expired", None
        except jwt.InvalidTokenError:
            return False, "Invalid registration token", None
    
    @staticmethod
    def _create_user_and_shop(data: dict, phone_number: str) -> tuple[User, Shop]:
        """Create user and shop in a transaction"""
        # Handle email - accept null or empty string as None
        email = data.get("email")
        if email == "" or email is None:
            email = None
        
        user = User.objects.create(
            phone_number=phone_number,
            user_name="Super User",
            email=email, 
            country_id=data.get("country"),
            state_id=data.get("state"),
            city_id=data.get("city"),
            address=data.get("address"),
            pincode=data.get("pincode"),
            is_verified=True,
            is_superuser=False, 
            is_staff=True       
        )

        if data.get("password"):
            user.set_password(data["password"])
            user.save()

        # Generate unique shop code
        shop_code = ShopService.generate_shop_code(data["shop_name"])
        
        # Check if this is the first shop for this user
        existing_shops_count = Shop.objects.filter(owner=user).count()
        is_first_shop = existing_shops_count == 0

        shop = Shop.objects.create(
            shop_code=shop_code,
            shop_name=data["shop_name"],
            legal_name=data.get("legal_name"),
            business_type_id=data.get("business_type_id", 0),
            tax_no=data.get("tax_no"),
            pan_no=data.get("pan_no"),
            address=data.get("address"),
            pincode=data.get("pincode"),
            country_id=data["country"],
            state_id=data["state"],
            city_id=data["city"],
            phone_number=phone_number,
            email=email,  # Use the same processed email (None if null or empty)
            default_shop=1 if is_first_shop else 0,  # First shop becomes default
            owner=user
        )

        user.primary_shop = shop
        user.shops.add(shop)
        user.save()

        OTP.objects.filter(phone_number=phone_number).delete()
        
        return user, shop
    
    @staticmethod
    def _build_response(user: User, shop: Shop) -> dict:
        """Build successful registration response"""
        refresh = RefreshToken.for_user(user)
        
        return ResponseBuilder.success(
            'Shop registered successfully',
            None,
        )

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# OTP Limit Service
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class OTPLimitService:
    """Service for managing OTP limits and blocked users"""
    
    @staticmethod
    def get_blocked_users() -> dict:
        """Get all users who have reached OTP limit and are currently blocked"""
        try:
            # Get all OTP records where users are currently blocked
            blocked_otps = OTP.objects.filter(
                blocked_until__gt=timezone.now()
            ).order_by('-blocked_until')
            
            blocked_users = []
            for otp in blocked_otps:
                # Try to get user details
                user = User.objects.filter(phone_number=otp.phone_number).first()
                
                # Calculate remaining time
                remaining_seconds = otp.get_block_remaining_time()
                remaining_minutes = remaining_seconds // 60
                
                blocked_users.append({
                    'phone_number': otp.phone_number,
                    'user_name': user.user_name if user else None,
                    'email': user.email if user else None,
                    'blocked_until': otp.blocked_until,
                    'remaining_minutes': remaining_minutes,
                    'otp_attempts': otp.attempts
                })
            
            return ResponseBuilder.success(
                f'Found {len(blocked_users)} blocked users',
                blocked_users
            )
            
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get blocked users: {str(e)}')
    
    @staticmethod
    def reset_otp_limit(phone_number: str) -> dict:
        """Reset OTP limit for a specific phone number"""
        try:
            # Normalize phone number
            normalized_phone = normalize_phone_number(phone_number)
            
            # Delete all OTP records for this phone number to completely reset the limit
            otp_records = OTP.objects.filter(phone_number=normalized_phone)
            
            if not otp_records.exists():
                return ResponseBuilder.error('No OTP records found for this phone number')
            
            # Delete all records instead of just updating them
            deleted_count = otp_records.count()
            otp_records.delete()
            
            return ResponseBuilder.success(
                f'OTP limit reset successfully for {normalized_phone}. Deleted {deleted_count} records.',
                {
                    'phone_number': normalized_phone,
                    'records_updated': deleted_count
                }
            )
            
        except ValueError as e:
            return ResponseBuilder.error(str(e))
        except Exception as e:
            return ResponseBuilder.error(f'Failed to reset OTP limit: {str(e)}')
