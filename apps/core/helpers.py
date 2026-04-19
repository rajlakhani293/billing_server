import re
from apps.accounts.models import OTP
from phonenumbers import parse as parse_phone_number, is_valid_number
from datetime import timedelta
from django.utils import timezone
import pyotp
from ninja.errors import ValidationError, HttpError
from django.http import JsonResponse
import datetime
from django.http.multipartparser import MultiPartParser
import os
import time
from django.conf import settings
from django.core.files.storage import default_storage
from django.forms.models import model_to_dict


def serializeModelInstance(instance, include_configs=None):
    if isinstance(instance, dict):
        return instance

    if not instance:
        return None
        
    data = model_to_dict(instance)
    
    # Ensure ID is included (model_to_dict excludes AutoField/primary_key by default)
    if instance.pk:
         data['id'] = instance.pk
    
    # Normalize FK and file fields
    for field in instance._meta.fields:
        # File/Image fields
        if field.get_internal_type() in ['FileField', 'ImageField']:
            file_obj = getattr(instance, field.name)
            if file_obj:
                data[field.name] = file_obj.name
            else:
                data[field.name] = None
            continue

        # Foreign keys -> store id instead of model instance
        if field.is_relation and hasattr(field, "remote_field") and field.remote_field:
            try:
                rel_obj = getattr(instance, field.name)
                # Use field_name_id for foreign keys to match API expectations
                data[f"{field.name}_id"] = rel_obj.id if rel_obj else None
                # Remove the original field name to avoid duplication
                data.pop(field.name, None)
            except Exception:
                pass
    
    # Handle related objects that might be prefetched
    if include_configs:
        for include_config in include_configs:
            if isinstance(include_config, dict):
                as_name = include_config.get('as')
                attributes = include_config.get('attributes', [])
                included_model = include_config.get('model')
                
                if hasattr(instance, as_name):
                    related_obj = getattr(instance, as_name)
                    if related_obj:
                        if hasattr(related_obj, 'all'):  # Reverse ForeignKey or ManyToMany
                            related_data = [serializeModelInstance(item) for item in related_obj.all()]
                        else:  # Single related object
                            related_data = serializeModelInstance(related_obj)
                        
                        # Check if this is a forward relationship (should not be flattened)
                        is_forward_relationship = False
                        if included_model:
                            for field in instance._meta.fields:
                                if hasattr(field, 'remote_field') and field.remote_field:
                                    if field.remote_field.model == included_model:
                                        is_forward_relationship = True
                                        break
                        
                        # Check if attributes is empty array - only flatten for reverse relationships
                        if attributes == [] and not is_forward_relationship:
                            if isinstance(related_data, list):
                                # For multiple related objects, we can't flatten, keep as array
                                data[as_name] = related_data
                            else:
                                # For single related object, flatten the fields
                                if isinstance(related_data, dict):
                                    for key, value in related_data.items():
                                        if key != 'id':  # Avoid overwriting the main ID
                                            data[key] = value
                                else:
                                    data[as_name] = related_data
                        else:
                            # Keep as nested object with only specified attributes
                            if isinstance(related_data, list):
                                data[as_name] = [
                                    {attr: item.get(attr) for attr in attributes if attr in item}
                                    for item in related_data
                                ]
                            elif isinstance(related_data, dict):
                                if attributes:  # Only filter if specific attributes are requested
                                    data[as_name] = {attr: related_data.get(attr) for attr in attributes if attr in related_data}
                                else:  # Include all fields for forward relationships
                                    data[as_name] = related_data
                            else:
                                data[as_name] = related_data
                    else:
                        data[as_name] = None
    
    return data

def jsonsafe(value):
    """
    Recursively converts Django model instances and nested structures to JSON-safe dictionaries.
    Use this function to ensure all API responses are JSON serializable.
    """
    if isinstance(value, dict):
        return {k: jsonsafe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [jsonsafe(v) for v in value]
    # Check for Django model instances
    if hasattr(value, "_meta") and hasattr(value, "pk"):
        return serializeModelInstance(value)
    return value

def parseMultipartRequest(request):
    if request.method in ['PUT', 'PATCH'] and request.content_type.startswith('multipart/form-data'):
        # If files/post are already populated, don't re-parse
        if hasattr(request, '_files') and request._files:
            return request
        if hasattr(request, '_post') and request._post:
            return request
            
        # Initializing the parser with the request meta and stream
        parser = MultiPartParser(request.META, request.environ['wsgi.input'], request.upload_handlers, request.encoding)
        post, files = parser.parse()
        request._post = post
        request._files = files
    return request

def getAuthContext(request):
    user_id = None
    company_id = None
    branch_id = None

    if isinstance(request.auth, dict):
        user_id = request.auth.get('user').id if request.auth.get('user') else None
        company_id = request.auth.get('company').id if request.auth.get('company') else None
        branch_id = request.auth.get('branch').id if request.auth.get('branch') else None
    else:
        user_id = getattr(request.auth, 'user_id', None)
        company_id = getattr(request.auth, 'company_id', None)
        branch_id = getattr(request.auth, 'branch_id', None)

    if not user_id or not company_id or not branch_id:
        raise HttpError(403, "Authentication context missing")

    return {"user_id": user_id, "company_id": company_id, "branch_id": branch_id}

def validationErrorHandler(request, exc: ValidationError):
    first_error = exc.errors[0]
    field = str(first_error["loc"][-1])
    error_type = first_error.get("type")
    
    # Clean up field name
    if field.endswith('_id'):
        field = field[:-3]
    
    field_name = field.replace('_', ' ').title()
    
    # Standardize messages based on Pydantic error types
    if error_type == "missing":
        message = f"{field_name} is required"
    elif error_type == "string_type":
        message = f"{field_name} must be a valid string"
    elif error_type == "int_parsing" or error_type == "int_type":
        message = f"{field_name} must be a valid integer"
    elif error_type == "decimal_parsing":
        message = f"{field_name} must be a valid decimal number"
    elif error_type == "bool_type":
        message = f"{field_name} must be a true/false value"
    elif error_type == "value_error.missing":
        message = f"{field_name} is required"
    elif error_type == "value_error":
         # Use the custom message from the validator if available
         msg = first_error.get("msg")
         if msg and not "Value error," in msg:
             message = msg
         else:
             message = f"Invalid value for {field_name}"    
    else:
        # Fallback to the raw message but cleaner
        raw_msg = first_error.get("msg", "Invalid Input")
        message = f"{field_name}: {raw_msg}"

    return JsonResponse({
        "success": False,
        "code": 400,
        "message": message,
    }, status=400)

def uploadFile(files, subfolder="", old_file_name=None):
    if not files:
        return {}

    # 1. Normalize files to a list (Handling req.file vs req.files)
    files_to_process = []
    if isinstance(files, list):
        files_to_process = files
    elif isinstance(files, dict):
        for key in files:
            val = files[key]
            if isinstance(val, list):
                files_to_process.extend(val)
            else:
                files_to_process.append(val)
    else:
        files_to_process = [files]

    saved_filenames = {}
    # baseDir is defined in settings.MEDIA_ROOT (usually 'uploads')
    target_folder = os.path.join(settings.MEDIA_ROOT, subfolder)
    
    # Ensure directory exists (Node's ensureDir)
    os.makedirs(target_folder, exist_ok=True)

    for file in files_to_process:
        # 2. Generate filename: {timestamp}_{name}{ext}
        ext = os.path.splitext(file.name)[1].lower()
        name = os.path.splitext(file.name)[0].replace(" ", "_")
        filename = f"{int(time.time() * 1000)}_{name}{ext}"
        
        full_path = os.path.join(target_folder, filename)

        try:
            # 3. Write file (Node's fs.writeFileSync)
            # Using default_storage handles the write stream for us
            with default_storage.open(os.path.join(subfolder, filename), 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Use fieldname or a default key
            field_name = getattr(file, 'field_name', 'file')
            saved_filenames[field_name] = filename
            
        except Exception as e:
            print(f"File write failed: {e}")
            raise HttpError(500, f"Failed to upload file: {file.name}")

    # 4. Handle Old File Deletion
    if saved_filenames and old_file_name:
        delete_file(subfolder, old_file_name)

    return saved_filenames

def delete_file(subfolder, filename):
    """Delete a file from the filesystem"""
    if not filename:
        return
    
    try:
        file_path = os.path.join(settings.MEDIA_ROOT, subfolder, filename)
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
    except Exception as e:
        print(f"Failed to delete file {filename}: {e}")

class ResponseBuilder:
    """Standardized response builder for API responses"""
    
    @staticmethod
    def success(message: str, data=None) -> dict:
        """Return success response"""
        return {
            'success': True,
            'code': 200,
            'message': message,
            'data': data
        }
    
    @staticmethod
    def error(message: str, status_code: int = 400) -> dict:
        return {
            'success': False,
            'code': status_code or 400,
            'message': ResponseBuilder.parseErrorContent(message),
        }
    
    @staticmethod
    def parseErrorContent(message: str) -> str:
        message_str = str(message)

        if "(1062," in message_str and "Duplicate entry" in message_str:
            try:
                # Extract value and key
                import re
                match = re.search(r"Duplicate entry '(.+?)' for key '(.+?)'", message_str)
                if match:
                    value = match.group(1)
                    key = match.group(2)
                  
                    key_clean = key
                    for suffix in ['_uniq', '_unique', '_key']:
                        if key_clean.endswith(suffix):
                            key_clean = key_clean[:-len(suffix)]
                            
                    parts = key_clean.split('_')
                    meaningful_parts = []
                    for part in parts:
                        if len(part) > 6 and re.match(r'^[a-f0-9]+$', part):
                            continue
                        if part.isdigit():
                            continue
                        
                        if part in ['company', 'id', 'pk']:
                            continue
                            
                        meaningful_parts.append(part)
                    
                    if len(meaningful_parts) > 1:
                        if meaningful_parts[0].endswith('s'):
                            meaningful_parts = meaningful_parts[1:]
                            
                    field_name = ' '.join(meaningful_parts).title()
                    
                    return f"{field_name} already exists"
            except:
                pass

        if "(1048," in message_str and "cannot be null" in message_str:
            try:
                import re
                match = re.search(r"Column '(.+?)' cannot be null", message_str)
                if match:
                    column = match.group(1)
                    # Clean up column name
                    column = column.replace('_', ' ').title()
                    return f"{column} is required"
            except:
                pass
                
        if message_str.startswith("['") and message_str.endswith("']"):
            return message_str[2:-2]
            
        return message_str

def normalizePhoneNumber(phone_number: str) -> str:
        try:
            # Remove all non-digit characters
            cleaned = re.sub(r'\D', '', phone_number)

            # If starts with country code
            if cleaned.startswith('91') and len(cleaned) == 12:
                phone_number = '+' + cleaned
            elif len(cleaned) == 10:
                phone_number = '+91' + cleaned
            else:
                phone_number = '+' + cleaned

            # Validate
            parsed = parse_phone_number(phone_number, 'IN')
            if not is_valid_number(parsed):
                raise ValueError('Invalid phone number')

            return phone_number
        except Exception as e:
            raise ValueError(f'Invalid phone number format: {str(e)}')

def generateOtp(phone_number: str, validity_minutes: int = 5, otp_type: str = 'LOGIN'):
    """Generate OTP with rate limiting - block for 1 hour if 3 OTPs requested within last hour"""
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    # Count OTPs requested in the last hour
    request_count = OTP.objects.filter(
        phone_number=phone_number,
        created_at__gte=one_hour_ago
    ).count()

    if request_count >= 3:
        # Get the most recent OTP record to check block time
        recent = OTP.objects.filter(phone_number=phone_number).first()
        if recent:
            # Set block time if not already set
            if not recent.blocked_until:
                recent.blocked_until = timezone.now() + timedelta(hours=1)
                recent.save()
            
            # Calculate remaining time
            remaining_seconds = recent.get_block_remaining_time()
            if remaining_seconds > 0:
                remaining_minutes = remaining_seconds // 60
                remaining_seconds_mod = remaining_seconds % 60
                raise Exception(f"OTP Limit reached. Try again after {remaining_minutes} minutes and {remaining_seconds_mod} seconds.")
        else:
            raise Exception("OTP Limit reached. Try again after 1 hour.")

    # Generate new OTP
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret, digits=6, interval=validity_minutes * 60)
    otp_code = totp.now()

    return OTP.objects.create(
        phone_number=phone_number,
        otp_code=otp_code,
        otp_type=otp_type
    )

def generateSequentialCode(model, field_name='sales_code', prefix='SL'):
    # Format: PREFIX-YYYYMMDD-N (Sequential number)
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    prefix_full = f"{prefix}-{date_str}-"
    
    # Find the last entry with this prefix
    filter_kwargs = {f"{field_name}__startswith": prefix_full}
    last_entry = model.objects.filter(**filter_kwargs).order_by('-id').first()
    
    if last_entry:
        # Extract the last number
        try:
            code_value = getattr(last_entry, field_name)
            last_number = int(code_value.split('-')[-1])
            new_number = last_number + 1
        except ValueError:
            new_number = 1
    else:
        new_number = 1
        
    return f"{prefix_full}{new_number}"
