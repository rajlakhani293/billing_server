from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from apps.accounts.helpers import check_recent_verification, normalize_phone_number, ResponseBuilder, generate_otp
from apps.accounts.schema import ShopRegistrationSchema
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, OTP
from apps.shops.models import Shop
import re
from django.db import transaction
import jwt
from django.conf import settings


class AuthService:

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
        except Exception as e:
            return ResponseBuilder.error(f'Failed to send OTP: {str(e)}')

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
            otp_instance = OTP.objects.filter(
                phone_number=normalized_phone
            ).order_by('-created_at').first()

            if not otp_instance:
                return ResponseBuilder.error('OTP not found', code=404)

            # Verify OTP
            if otp_instance.verify(payload['otp_code']):               
                
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
        except Exception as e:
            return ResponseBuilder.error(f'Failed to verify OTP: {str(e)}')


    @staticmethod
    def register_shop(request, payload: ShopRegistrationSchema) -> dict:
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
                return ResponseBuilder.error(token_message, code=401)

            # Check if phone number was verified within last 10 minutes
            verification_check = check_recent_verification(verified_phone)
            if not verification_check['was_verified_recently']:
                return ResponseBuilder.error(
                    'Registration session expired. Please verify your phone number again to continue.',
                    code=429
                )

            # Check if user already exists
            if User.objects.filter(phone_number=verified_phone).exists():
                return ResponseBuilder.error('User already registered with this phone number')

            # Create user and shop in transaction
            with transaction.atomic():
                user, shop = ShopService._create_user_and_shop(data, verified_phone)
                return ShopService._build_response(user, shop)

        except Exception as e:
            return ResponseBuilder.error(f'Failed to register shop: {str(e)}')

    @staticmethod
    def send_login_otp(phone_number: str) -> dict:
        """Send login OTP"""
        try:
            # Normalize phone number
            normalized_phone = normalize_phone_number(phone_number)

            # Check if user exists
            if not User.objects.filter(phone_number=normalized_phone).exists():
                return ResponseBuilder.error('User not found with this phone number')

            # Generate OTP
            otp_instance = generate_otp(normalized_phone, otp_type='LOGIN')

            return ResponseBuilder.success(
                'Login OTP sent successfully',
                {
                    'otp_code': otp_instance.otp_code
                }
            )
        except ValueError as e:
            return ResponseBuilder.error(str(e))
        except Exception as e:
            return ResponseBuilder.error(f'Failed to send login OTP: {str(e)}')

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

                # Generate tokens
                refresh = RefreshToken.for_user(user)
                return ResponseBuilder.success(
                    'Login successful',
                    {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                        'user_id': str(user.id),
                        'phone_number': user.phone_number,
                        'email': user.email,
                        'has_password': bool(user.password)
                    }
                )

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

                refresh = RefreshToken.for_user(auth_user)
                return ResponseBuilder.success(
                    'Login successful',
                    {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                        'user_id': str(auth_user.id),
                        'phone_number': auth_user.phone_number,
                        'email': auth_user.email,
                        'has_password': bool(auth_user.password)
                    }
                )

        except User.DoesNotExist:
            return ResponseBuilder.error('User not found')
        except Exception as e:
            return ResponseBuilder.error(f'Login failed: {str(e)}')

    @staticmethod
    def logout(refresh_token: str) -> dict:
        """Logout user by blacklisting refresh token"""
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            
            # Get refresh token
            try:
                token = RefreshToken(refresh_token)
                outstanding_token = OutstandingToken.objects.get(token=token)
                
                # Blacklist token
                BlacklistedToken.objects.get_or_create(
                    token=outstanding_token.token,
                    blacklisted_at=timezone.now()
                )
                
                return ResponseBuilder.success('Logout successful')
            except Exception:
                return ResponseBuilder.error('Invalid refresh token')
        except Exception as e:
            return ResponseBuilder.error(f'Logout failed: {str(e)}')

    @staticmethod
    def get_session_data(user: User) -> dict:
        """Get user session data"""
        try:
            # Get user's shops
            shops = user.shops.all()
            primary_shop = user.primary_shop
            
            return ResponseBuilder.success(
                'Session data retrieved successfully',
                {
                    'user': {
                        'id': str(user.id),
                        'phone_number': user.phone_number,
                        'email': user.email,
                        'user_name': user.user_name,
                        'is_verified': user.is_verified,
                        'is_staff': user.is_staff,
                        'has_password': bool(user.password),
                        'role': user.role.role_name if user.role else None,
                        'permissions': user.permissions
                    },
                    'shops': [
                        {
                            'id': str(shop.id),
                            'shop_code': shop.shop_code,
                            'shop_name': shop.shop_name,
                            'legal_name': shop.legal_name,
                            'email': shop.email,
                            'phone_number': shop.phone_number,
                            'tax_no': shop.tax_no,
                            'pan_no': shop.pan_no,
                            'address': shop.address,
                            'pincode': shop.pincode,
                            'city_id': shop.city.id if shop.city else None,
                            'state_id': shop.state.id if shop.state else None,
                            'country_id': shop.country.id if shop.country else None,
                            'default_shop': shop.default_shop,
                            'status': shop.status,
                            'created_at': shop.created_at
                        } for shop in shops
                    ],
                    'primary_shop': {
                        'id': str(primary_shop.id),
                        'shop_code': primary_shop.shop_code,
                        'shop_name': primary_shop.shop_name,
                        'legal_name': primary_shop.legal_name,
                        'email': primary_shop.email,
                        'phone_number': primary_shop.phone_number,
                        'tax_no': primary_shop.tax_no,
                        'pan_no': primary_shop.pan_no,
                        'address': primary_shop.address,
                        'pincode': primary_shop.pincode,
                        'city_id': primary_shop.city.id if primary_shop.city else None,
                        'state_id': primary_shop.state.id if primary_shop.state else None,
                        'country_id': primary_shop.country.id if primary_shop.country else None,
                        'default_shop': primary_shop.default_shop,
                        'status': primary_shop.status,
                        'created_at': primary_shop.created_at
                    } if primary_shop else None,
                    'role': user.role.role_name if user.role else None,
                    'permissions': user.permissions
                }
            )
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get session data: {str(e)}')


class ShopService:
    
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
        user = User.objects.create(
            phone_number=phone_number,
            user_name=data["shop_name"],
            email=data.get("email"),
            is_verified=True
        )

        if data.get("password"):
            user.set_password(data["password"])
            user.save()

        shop = Shop.objects.create(
            shop_code=data.get("shop_code"),
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
            email=data.get("email"),
            default_shop=data.get("default_shop", 0)
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
            {
                "user_id": str(user.id),
                "phone_number": user.phone_number,
                "email": user.email,
                "user_name": user.user_name,
                "has_password": bool(user.password)
            },
            code=201
        )


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
                return ResponseBuilder.error('No OTP records found for this phone number', code=404)
            
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
