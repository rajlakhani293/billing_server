import json
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from apps.core.helpers import getAuthContext, normalizePhoneNumber, ResponseBuilder, generateOtp
from apps.accounts.schema import CompanyRegistrationSchema
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.tenantQuery import TenantQuery
from .models import User, OTP
from apps.company.models import Company, Branch
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
    def sendOtp(phone_number: str) -> dict:
        try:
            phone = normalizePhoneNumber(phone_number)

            user = TenantQuery.findOneRecord(
                User,
                {"phone_number": phone},
                None,
                False,
            )
            if user:
                return ResponseBuilder.error('User already registered with this phone number')

            # Generate OTP
            otp = generateOtp(phone, otp_type='REGISTRATION')

            return ResponseBuilder.success(
                'OTP sent successfully',
                {
                    'otp_code': otp.otp_code
                }
            )
        except ValueError as e:
            return ResponseBuilder.error(str(e))

    @staticmethod
    def verifyOtp(payload: dict) -> dict:
        try:
            phone = normalizePhoneNumber(payload['phone_number'])

            user = TenantQuery.findOneRecord(
                User,
                {"phone_number": phone},
                None,
                False,
            )
            if user:
                return ResponseBuilder.error('User already registered with this phone number')

            otp_code = TenantQuery.findOneRecord(
                OTP,
                {"phone_number": phone},
                {"order": "-created_at"},
                None,
                False,
            )

            if not otp_code:
                return ResponseBuilder.error('OTP not found')

            # Get the actual OTP model instance to call verify method
            otp_instance = OTP.objects.filter(phone_number=phone).order_by('-created_at').first()
            if not otp_instance:
                return ResponseBuilder.error('OTP not found')

            if otp_instance.verify(payload['otp_code']):               
                otp_instance.is_verified = True
                otp_instance.save()
                
                registration_token = jwt.encode(
                    {
                        'phone_number': phone,
                        'scope': 'registration_verification',
                        'exp': timezone.now() + timedelta(minutes=10)
                    },
                    settings.SECRET_KEY,
                    algorithm='HS256'
                )
                
                return ResponseBuilder.success(
                    'OTP verified successfully',
                    {
                        'phone_number': phone,
                        'registration_token': registration_token,
                    }
                )
            else:
                return ResponseBuilder.error('Invalid OTP code')
        except ValueError as e:
            return ResponseBuilder.error(str(e))

    @staticmethod
    def registerCompany(payload: CompanyRegistrationSchema) -> dict:
        data = payload.dict() if hasattr(payload, "dict") else dict(payload)
        
        try:
            token_valid, token_message, verified_phone = CompanyService.validateRegistrationToken(
                data['registration_token']
            )
            if not token_valid:
                return ResponseBuilder.error(token_message)

            existing_user = TenantQuery.findOneRecord(
                User,
                {"phone_number": verified_phone, "status__in": [0, 1, 2]},
                None,
                False,
            )
            if existing_user:
                return ResponseBuilder.error('User already registered with this phone number')

            email = data.get('email')
            if email and email != "" and email is not None:
                existing_email = TenantQuery.findOneRecord(
                    User,
                    {"email": email, "status__in": [0, 1, 2]},
                    None,
                    False,
                )
                if existing_email:
                    return ResponseBuilder.error('Email already registered with another account')

            with transaction.atomic():
                user, company, branch = CompanyService.createUserCompanyBranch(data, verified_phone)
                return CompanyService.buildResponse(user, company, branch)

        except Exception as e:
            return ResponseBuilder.error(f'Failed to register company: {str(e)}')

    @staticmethod
    def sendLoginOtp(phone_number: str) -> dict:
        try:
            phone = normalizePhoneNumber(phone_number)

            # Check if user exists
            user = TenantQuery.findOneRecord(
                User,
                {"phone_number": phone},
                None,
                None,
                False,
            )
            if not user:
                return ResponseBuilder.error(HttpError(400, 'User not found with this phone number'))

            # Generate OTP
            otp_instance = generateOtp(phone, otp_type='LOGIN')

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
                phone = normalizePhoneNumber(phone_number)
                
                if not otp_code:
                    return ResponseBuilder.error('OTP code is required for phone number login')
                
                # Always use normalized phone number for consistency
                user = TenantQuery.findOneRecord(
                    User,
                    {"phone_number": phone},
                    None,
                    None,
                    False,
                )
                
                if not user:
                    return ResponseBuilder.error('User not found')

                # Get the actual User model instance using normalized phone
                try:
                    user_instance = User.objects.get(phone_number=phone)
                except User.DoesNotExist:
                    return ResponseBuilder.error('User not found')
                
                # Find existing OTP with normalized phone number
                otp_instance = OTP.objects.filter(phone_number=phone).order_by('-created_at').first()
                
                if not otp_instance:
                    return ResponseBuilder.error('OTP not found or expired')
                
                # Verify the OTP
                if not otp_instance.verify(otp_code):
                    return ResponseBuilder.error('Invalid OTP code')

                # Delete the OTP after successful verification
                otp_instance.delete()

                token = RefreshToken.for_user(user_instance)
                access_token = token.access_token
                access_token['user_id'] = user_instance.id
                company = user_instance.company
                company_id = company.id if company else None
                branch_id = user_instance.branch.id if user_instance.branch else None

                access_token['company_id'] = company_id
                access_token['branch_id'] = branch_id
                
                return ResponseBuilder.success(
                    'Login successful',
                    {
                        'token': str(access_token)
                    }
                )

            # 2. PASSWORD LOGIN FLOW
            elif email:
                if not password:
                    return ResponseBuilder.error('Password is required for email login')
                
                user = TenantQuery.findOneRecord(
                    User,
                    {"email": email},
                    None,
                    None,
                    False,
                )

                if not user:
                    return ResponseBuilder.error('User not found')

                # Get the actual User model instance
                user_instance = User.objects.get(email=email)

                if not user_instance.password:
                    return ResponseBuilder.error('Password not set for this account')

                auth_user = authenticate(
                    username=user_instance.phone_number or user_instance.email,
                    password=password
                )

                if not auth_user:
                    return ResponseBuilder.error('Invalid credentials')

                token = RefreshToken.for_user(auth_user)
                access_token = token.access_token
                access_token['user_id'] = auth_user.id
                company = auth_user.company
                company_id = company.id if company else None
                branch_id = auth_user.branch.id if auth_user.branch else None

                access_token['company_id'] = company_id
                access_token['branch_id'] = branch_id
                
                return ResponseBuilder.success(
                    'Login successful',
                    {
                        'token': str(access_token)
                    }
                )

        except User.DoesNotExist:
            return ResponseBuilder.error('User not found')
        except Exception as e:
            return ResponseBuilder.error(f'Login failed: {str(e)}')

    @staticmethod
    def logout(request):
        try:
            # Get refresh token from request body
            data = json.loads(request.body)
            refresh_token = data.get('refresh_token') or data.get('refresh')
            
            if not refresh_token:
                return ResponseBuilder.error('Refresh token is required for logout')
            
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return ResponseBuilder.success('Logout successful')
        except Exception as e:
            return ResponseBuilder.error(f'Logout failed: {str(e)}')

    # @staticmethod
    # def getSessionData(request):
    #     try:  
    #         auth_ctx = getAuthContext(request)
    #         user_id = auth_ctx.get("user_id")
    #         company_id = auth_ctx.get("company_id")
    #         branch_id = auth_ctx.get("branch_id")

    #         user_data = TenantQuery.findOneRecord(
    #             User,
    #             {"id": user_id},
    #             {},
    #             request,
    #             False,
    #         )

    #         company_data = TenantQuery.findOneRecord(
    #             Company,
    #             {"id": company_id},
    #             {},
    #             request,
    #             False,
    #         )
            
    #         branch_data = TenantQuery.findOneRecord(
    #             Branch,
    #             {"id": branch_id},
    #             {},
    #             request,
    #             False,
    #         )
            
    #         return ResponseBuilder.success(
    #             'Session data retrieved successfully',
    #             {
    #                 "user": user_data,
    #                 "company": company_data,
    #                 "branch": branch_data,
    #             },
    #         )
    #     except Exception as e:
    #         return ResponseBuilder.error(f'Failed to get session data: {str(e)}')

    @staticmethod
    def getSessionData(request):
        """Optimized method using Django ORM values() for better performance"""
        try:  
            auth_ctx = getAuthContext(request)
            user_id = auth_ctx.get("user_id")
            company_id = auth_ctx.get("company_id")
            branch_id = auth_ctx.get("branch_id")

            # Using TenantQuery for better tenant isolation
            user_data = TenantQuery.findOneRecord(
                User,
                {"id": user_id},
                {},
                request
            )

            # Add has_password field
            if user_data:
                user_data['has_password'] = User.objects.filter(id=user_id).exclude(password__isnull=True).exclude(password='').exists()

            company_data = TenantQuery.findOneRecord(
                Company,
                {"id": company_id},
                {},
                request
            )
            
            # Convert logo_image to string URL
            if company_data and company_data.get('logo_image'):
                company_data['logo_image_url'] = str(company_data['logo_image'])
                del company_data['logo_image']

            branch_data = TenantQuery.findOneRecord(
                Branch,
                {"id": branch_id},
                {},
                request
            )
            
            return ResponseBuilder.success(
                'Session data retrieved successfully (Optimized)',
                {
                    "user": user_data,
                    "company": company_data,
                    "branch": branch_data,
                },
            )
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get session data (Optimized): {str(e)}')


    # Backward-compatible alias      
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Company Service
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class CompanyService:
    
    @staticmethod
    def generateCompanyCode(company_name: str) -> str:
        clean_name = re.sub(r'[^\w\s]', '', company_name)
        clean_name = re.sub(r'\s+', '', clean_name)
        
        prefix = clean_name[:6].upper()
        
        suffix = ''.join(random.choices(string.digits, k=4))
        
        company_code = f"{prefix}{suffix}"
        
        attempts = 0
        max_attempts = 10
        
        while Company.objects.filter(company_code=company_code).exists() and attempts < max_attempts:
            suffix = ''.join(random.choices(string.digits, k=4))
            company_code = f"{prefix}{suffix}"
            attempts += 1
        
        if attempts >= max_attempts:
            import time
            timestamp = str(int(time.time()))[-6:]
            company_code = f"COMPANY{timestamp}"
        
        return company_code

    @staticmethod
    def validateRegistrationToken(token: str) -> tuple[bool, str, str]:
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
    def createUserCompanyBranch(data: dict, phone_number: str) -> tuple[User, Company]:
        email = data.get("email")
        if email == "" or email is None:
            email = None
        
        user = TenantQuery.createRecord(
            User,
            {
                "phone_number": phone_number,
                "user_name": "Super User",
                "email": email,
                "country_id": data.get("country"),
                "state_id": data.get("state"),
                "city_id": data.get("city"),
                "address": data.get("address"),
                "pincode": data.get("pincode"),
                "is_verified": True,
                "is_superuser": False,
                "is_staff": True,
            },
            None,
            False,
        )

        if data.get("password"):
            user.set_password(data["password"])
            user.save()

        # Generate unique company code
        company_code = CompanyService.generateCompanyCode(data["company_name"])
        
        company = TenantQuery.createRecord(
            Company,
            {
                "company_code": company_code,
                "company_name": data["company_name"],
                "business_type_id": data.get("business_type_id", 0),
                "tax_no": data.get("tax_no"),
                "pan_no": data.get("pan_no"),
                "address": data.get("address"),
                "pincode": data.get("pincode"),
                "country_id": data["country"],
                "state_id": data["state"],
                "city_id": data["city"],
                "phone_number": phone_number,
                "email": email,
                "logo_image": data.get("logo_image"),
                "website_url": data.get("website_url"),
                "owner": user,
            },
            None,
            False
        )

        # Create a default branch for the new company
        branch_name = "Main Branch"
        branch = TenantQuery.createRecord(
            Branch,
            {
                "branch_name": branch_name,
                "contact_person_name": user.user_name,
                "phone_number": phone_number,
                "email": email,
                "address": data.get("address"),
                "pincode": data.get("pincode"),
                "country_id": data["country"],
                "state_id": data["state"],
                "city_id": data["city"],
                "company": company,
            },
            None,
            False,
        )

        user.branch_access = [branch.id]
        # Set primary company and branch for user
        user.company = company
        user.branch = branch
        user.save()

        TenantQuery.hardDeleteRecords(
            OTP,
            {"phone_number": phone_number},
            None,
            False,
        )
        
        return user, company, branch
    
    @staticmethod
    def buildResponse(user: User, company: Company, branch: Branch = None) -> dict:
        
        response_data = {
            'user': {
                'id': user.id,
                'phone_number': user.phone_number,
                'email': user.email,
                'user_name': user.user_name,
                'is_verified': user.is_verified,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'has_password': bool(user.password),
                'profile_image_url': None
            },
            'company': {
                'id': company.id,
                'company_code': company.company_code,
                'company_name': company.company_name,
                'email': company.email,
                'phone_number': company.phone_number,
                'pan_no': company.pan_no,
                'address': company.address,
                'pincode': company.pincode,
                'city': company.city_id,
                'state': company.state_id,
                'country': company.country_id,
                'logo_image_url': str(company.logo_image) if company.logo_image else None,
                'status': company.status,
            }
        }
        
        # Add branch data if provided
        if branch:
            response_data['branch'] = {
                'id': branch.id,
                'branch_name': branch.branch_name,
                'contact_person_name': branch.contact_person_name,
                'phone_number': branch.phone_number,
                'email': branch.email,
                'address': branch.address,
                'pincode': branch.pincode,
                'city': branch.city_id,
                'state': branch.state_id,
                'country': branch.country_id,
                'status': branch.status,
                'company': branch.company_id,
            }
        
        return ResponseBuilder.success(
            'Company registered successfully',
            response_data
        )

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# OTP Limit Service
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class OTPLimitService:
    """Service for managing OTP limits and blocked users"""
    
    @staticmethod
    def getBlockedUsers(request=None, tenant_config=True) -> dict:
        """Get all users who have reached OTP limit and are currently blocked"""
        try:
            # Get all OTP records where users are currently blocked
            all_otps = TenantQuery.findAllRecords(
                OTP,
                {},
                request
            )
            
            # Filter for blocked users and sort by blocked_until
            blocked_otps = [
                otp for otp in all_otps 
                if otp.get('blocked_until') and otp.get('blocked_until') > timezone.now()
            ]
            blocked_otps.sort(key=lambda x: x.get('blocked_until'), reverse=True)
            
            blocked_users = []
            for otp in blocked_otps:
                # Try to get user details
                user = User.objects.filter(phone_number=otp.get('phone_number')).first()
                
                # Calculate remaining time
                blocked_until = otp.get('blocked_until')
                if blocked_until:
                    remaining_seconds = int((blocked_until - timezone.now()).total_seconds())
                    remaining_minutes = remaining_seconds // 60
                else:
                    remaining_minutes = 0
                
                blocked_users.append({
                    'phone_number': otp.get('phone_number'),
                    'user_name': user.user_name if user else None,
                    'email': user.email if user else None,
                    'blocked_until': blocked_until,
                    'remaining_minutes': remaining_minutes,
                    'otp_attempts': otp.get('attempts', 0)
                })
            
            return ResponseBuilder.success(
                f'Found {len(blocked_users)} blocked users',
                blocked_users
            )
            
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get blocked users: {str(e)}')
    
    @staticmethod
    def resetOtpLimit(phone_number: str, request=None, tenant_config=True) -> dict:
        """Reset OTP limit for a specific phone number"""
        try:
            # Normalize phone number
            normalized_phone = normalizePhoneNumber(phone_number)
            
            # Delete all OTP records for this phone number to completely reset the limit
            otp_records = TenantQuery.findAllRecords(
                OTP,
                {"phone_number": normalized_phone},
                request,
            )
            
            if not otp_records:
                return ResponseBuilder.error('No OTP records found for this phone number')
            
            # Delete all records using hardDeleteRecords
            deleted_count = len(otp_records)
            TenantQuery.hardDeleteRecords(
                OTP,
                {"phone_number": normalized_phone},
                request,
            )
            
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
