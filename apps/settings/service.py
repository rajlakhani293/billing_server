from django.db import transaction
from django.utils import timezone
from django.conf import settings
import json
import math
import datetime
from decimal import Decimal
from apps.core.helpers import ResponseBuilder, uploadFile
from .models import Brand, Tax, Party
from apps.core.tenantQuery import TenantQuery
from apps.sales.models import CustomerLedger, MonthlyStatement, PaymentHistory
from apps.sales.service import SalesService
from apps.company.models import Company, Branch
from apps.core.models import CountryMaster, StateMaster, CityMaster
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import User, OTP
from apps.core.helpers import getAuthContext, normalizePhoneNumber, generateOtp

class BrandService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                brand = TenantQuery.createRecord(Brand, data, request)
                return ResponseBuilder.success(
                    data=brand,
                    message="Brand created successfully"
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, brand_id):
        try:
            with transaction.atomic():
                brand = TenantQuery.updateRecordById(Brand, brand_id, data, request)
                if not brand:
                    raise Exception("Brand not found")
                return ResponseBuilder.success(data=brand, message="Brand updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getAll(data, request):
        try:
            fieldConfig = [["brand_name", True, True]]
            options = {'attributes': ['id', 'brand_name', 'status']}
            result = TenantQuery.fetchPaginatedData(Brand, data, fieldConfig, options, request)
            return ResponseBuilder.success(data=result, message="Brands retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            brands = TenantQuery.findAllRecords(Brand, {}, {'attributes': ['id', 'brand_name'], 'order': ['brand_name']}, request)
            return ResponseBuilder.success(data=brands, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
            
    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = TenantQuery.softDeleteById(Brand, data.get('ids'), request)
                if count == 0: raise Exception("Already deleted")
                return ResponseBuilder.success(message="Brands deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(brand_id, request):
        try:
            brand = TenantQuery.findOneRecord(Brand, brand_id, {}, request)
            if not brand or brand.get('status') == 2: raise Exception("Brand not found")
            return ResponseBuilder.success(data=brand, message="Brand retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class TaxService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                tax = TenantQuery.createRecord(Tax, data, request)
                return ResponseBuilder.success(
                    data=tax,
                    message="Tax created successfully"
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, tax_id):
        try:
            with transaction.atomic():
                tax = TenantQuery.updateRecordById(Tax, tax_id, data, request)
                if not tax:
                    raise Exception("Tax not found")
                return ResponseBuilder.success(data=tax, message="Tax updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getAll(data, request):
        try:
            fieldConfig = [["tax_name", True, True], ["tax_value", True, True]]
            options = {'attributes': ['id', 'tax_name', 'tax_value', 'status']}
            result = TenantQuery.fetchPaginatedData(Tax, data, fieldConfig, options, request)
            return ResponseBuilder.success(data=result, message="Taxes retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            taxes = TenantQuery.findAllRecords(Tax, {}, {'attributes': ['id', 'tax_name', 'tax_value'], 'order': ['tax_name']}, request)
            return ResponseBuilder.success(data=taxes, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
            
    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = TenantQuery.softDeleteById(Tax, data.get('ids'), request)
                if count == 0: raise Exception("Already deleted")
                return ResponseBuilder.success(message="Taxes deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(tax_id, request):
        try:
            tax = TenantQuery.findOneRecord(Tax, tax_id, {}, request)
            if not tax or tax.get('status') == 2: raise Exception("Tax not found")
            return ResponseBuilder.success(data=tax, message="Tax retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

class PartyService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                TenantQuery.createRecord(Party, data, request)
                return ResponseBuilder.success(message="Party created successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, record_id):
        try:
            with transaction.atomic():
                TenantQuery.updateRecordById(Party, record_id, data, request)
                return ResponseBuilder.success(message="Party updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                TenantQuery.softDeleteById(Party, data.get('ids'), request)
                return ResponseBuilder.success(message="Parties deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getAll(data, request):
        try:
            # Field configuration: [field_name, is_searchable, is_sortable]
            fieldConfig = [
                ["name", True, True],
                ["phone_number", True, False],
                ["email", True, True],
                ["party_type", False, True],
            ]
 
            result = TenantQuery.fetchPaginatedData(Party, data, fieldConfig, {}, request)
            return ResponseBuilder.success(data=result, message="Parties retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(party_id, request):
        try:
            party = TenantQuery.findOneRecord(Party, party_id, {}, request)
            if not party or party.get('status') == 2: raise Exception("Party not found")
            return ResponseBuilder.success(data=party, message="Party retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            # Dropdown usually needs id and name
            parties = TenantQuery.findAllRecords(
                Party, 
                {}, 
                {'attributes': ['id', 'name', 'party_type', 'phone_number'], 'order': ['name']}, 
                request
            )
            return ResponseBuilder.success(data=parties, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getPartyCreditDays(party_id, data, request):
        try:
            base_month = int(data["month"])
            base_year = int(data["year"])

            def shift_month(year, month, delta):
                total = (year * 12 + (month - 1)) + delta
                new_year = total // 12
                new_month = total % 12 + 1
                return new_year, new_month

            year, month = base_year, base_month
            first_day = datetime.date(year, month, 1)
            next_month_year, next_month = shift_month(year, month, 1)
            next_month_first = datetime.date(next_month_year, next_month, 1)
            last_day = next_month_first - datetime.timedelta(days=1)
            prev_month_end = first_day - datetime.timedelta(days=1)

            statement = TenantQuery.findOneRecord(
                MonthlyStatement,
                {"party_id": party_id, "month": month, "year": year},
                {},
                request,
            )

            opening_balance = None
            month_due_total = None
            month_paid_total = None
            closing_balance = None

            if statement:
                opening_balance = Decimal(str(statement.get("opening_balance", "0.00")))
                month_due_total = Decimal(str(statement.get("month_due_total", "0.00")))
                month_paid_total = Decimal(str(statement.get("month_paid_total", "0.00")))
                closing_balance = Decimal(str(statement.get("closing_balance", "0.00")))
            else:
                opening_balance = Decimal(
                    str(
                        TenantQuery.sumRecords(
                            CustomerLedger,
                            "amount",
                            {"party": party_id, "date__lt": first_day},
                            request,
                        )
                    )
                )

            records = TenantQuery.findAllRecords(
                CustomerLedger,
                {
                    "party": party_id,
                    "date__gte": first_day,
                    "date__lte": last_day,
                },
                {
                    "attributes": [
                        "date",
                        "amount",
                        "note",
                        "sales__sales_code",
                    ],
                    "order": ["date"]
                },
                request,
            )

            grouped_data = {}
            if month_due_total is None:
                month_due_total = Decimal("0.00")
            if month_paid_total is None:
                month_paid_total = Decimal("0.00")
            month_net = Decimal("0.00")

            for record in records:
                date_str = record.get("date")
                if date_str not in grouped_data:
                    grouped_data[date_str] = {
                        "date": date_str,
                        "total_amount": Decimal("0.00"),
                        "transactions": []
                    }

                amount_val = Decimal(str(record.get("amount", "0.00")))
                grouped_data[date_str]["total_amount"] += amount_val
                grouped_data[date_str]["transactions"].append({
                    "amount": record.get("amount"),
                    "note": record.get("note"),
                    "sales_code": record.get("sales__sales_code")
                })

                month_net += amount_val
                if statement is None:
                    if amount_val >= 0:
                        month_due_total += amount_val
                    else:
                        month_paid_total += abs(amount_val)

            days = list(grouped_data.values())
            days.sort(key=lambda x: x["date"])

            if closing_balance is None:
                closing_balance = opening_balance + month_net

            payments = TenantQuery.findAllRecords(
                PaymentHistory,
                {
                    "party": party_id,
                    "date__gte": first_day,
                    "date__lte": last_day,
                },
                {
                    "attributes": [
                        "id",
                        "date",
                        "amount",
                        "note",
                    ],
                    "order": ["date"]
                },
                request,
            )

            month_block = {
                "month": f"{year}-{str(month).zfill(2)}",
                "opening_balance": opening_balance,
                "month_due_total": month_due_total,
                "month_paid_total": month_paid_total,
                "month_net": month_net,
                "closing_balance": closing_balance,
                "days": days,
            }

            return ResponseBuilder.success(
                message="Party credit month data retrieved successfully",
                data={"month": month_block, "payments": payments},
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getPartyDueList(data, request):
        try:
            data = data or {}
            if not data and getattr(request, "body", None):
                try:
                    parsed = json.loads(request.body.decode("utf-8"))
                    if isinstance(parsed, dict):
                        data = parsed
                except Exception:
                    pass

            if not data.get("month") or not data.get("year"):
                return ResponseBuilder.error(
                    message="month and year are required",
                    status_code=400,
                )

            month = int(data.get("month"))
            year = int(data.get("year"))

            page = max(int(data.get("page", 1)), 1)
            limit_val = data.get("limit")
            is_fetch_all = limit_val in ["all", "All"]
            limit = None if is_fetch_all else (int(limit_val) if limit_val else 10)
            offset = 0 if is_fetch_all else (page - 1) * limit

            ledger_rows = TenantQuery.findAllRecords(
                CustomerLedger,
                {"month": month, "year": year},
                {
                    "attributes": [
                        "party_id",
                        "party__name",
                        "party__phone_number",
                        "party__email",
                        "party__current_balance",
                        "party__balance_type",
                        "amount",
                    ],
                    "order": ["-created_at"],
                },
                request,
            )

            party_map = {}
            for row in ledger_rows:
                party_id = row.get("party_id")
                if not party_id:
                    continue
                amount = row.get("amount") or Decimal("0.00")
                entry = party_map.setdefault(
                    party_id,
                    {
                        "party_id": party_id,
                        "party__name": row.get("party__name"),
                        "party__phone_number": row.get("party__phone_number"),
                        "party__email": row.get("party__email"),
                        "party__current_balance": row.get("party__current_balance"),
                        "party__balance_type": row.get("party__balance_type"),
                        "total_amount": Decimal("0.00"),
                        "total_paid": Decimal("0.00"),
                    },
                )
                if amount >= 0:
                    entry["total_amount"] += amount
                else:
                    entry["total_paid"] += abs(amount)

            items = []
            for entry in party_map.values():
                due_amount = entry["total_amount"] - entry["total_paid"]
                if due_amount > 0:
                    entry["due_amount"] = due_amount
                    items.append(entry)

            items.sort(key=lambda x: (-(x["due_amount"] or Decimal("0.00")), x.get("party__name") or ""))
            total_count = len(items)

            if not is_fetch_all:
                items = items[offset : offset + limit]

            result = {
                "items": items,
                "total": total_count,
                "currentPage": 1 if is_fetch_all else page,
                "pageSize": total_count if is_fetch_all else limit,
                "totalPages": 1 if is_fetch_all else math.ceil(total_count / (limit or 1)),
                "hasNextPage": False if is_fetch_all else (offset + limit) < total_count,
                "hasPreviousPage": False if is_fetch_all else page > 1,
                "appliedFilters": {
                    "month": month,
                    "year": year,
                },
            }

            return ResponseBuilder.success(
                data=result, message="Party due list retrieved successfully"
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getPaymentHistory(data, request):
        try:
            fieldConfig = [
                ["party__name", True, True],
                ["amount", True, True],
                ["date", True, True],
                ["note", True, False],
            ]

            options = {
                "attributes": [
                    "id",
                    "party_id",
                    "party__name",
                    "amount",
                    "date",
                    "note",
                ],
            }

            result = TenantQuery.fetchPaginatedData(
                PaymentHistory, data, fieldConfig, options, request, date_field="date"
            )

            return ResponseBuilder.success(
                data=result, message="Payment history retrieved successfully"
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def addPayment(data, request):
        try:
            with transaction.atomic():
                party_id = data.get("party_id")
                amount = Decimal(str(data.get("amount") or "0.00"))
                if amount <= 0:
                    return ResponseBuilder.error(
                        message="Payment amount must be greater than zero",
                        status_code=400,
                    )

                note = (data.get("note") or "").strip() or "Payment received"
                payment_date = timezone.localdate()

                TenantQuery.createRecord(
                    PaymentHistory,
                    {
                        "party_id": party_id,
                        "amount": amount,
                        "date": payment_date,
                        "note": note,
                    },
                    request,
                )

                SalesService.createLedgerEntry(
                    request,
                    party_id=party_id,
                    amount=-amount,
                    note=note,
                    entry_date=payment_date,
                )

                return ResponseBuilder.success(message="Payment recorded successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class CompanyService:
    @staticmethod
    def update(data, request, company_id):
        try:
            with transaction.atomic():
                company_data = data.copy()
                
                # Get current company to check for existing logo
                current_company = TenantQuery.findOneRecord(Company, company_id, {}, request, False)
                old_logo = None
                if current_company and current_company.get('logo_image'):
                    old_logo = current_company['logo_image']
                    if 'company_logos/' in old_logo:
                        old_logo = old_logo.split('company_logos/')[-1]
                
                logo_field_in_request = False
                if hasattr(request, 'POST') and 'logo_image' in request.POST:
                    logo_field_in_request = True
                
                # Handle logo_image upload
                if 'logo_image' in request.FILES:
                    logo_file = request.FILES.get('logo_image')
                    saved = uploadFile(logo_file, subfolder='company_logos', old_file_name=old_logo)
                    file_url = next(iter(saved.values())) if saved else None
                    if file_url:
                        company_data['logo_image'] = f"company_logos/{file_url}"
                elif logo_field_in_request and (data.get('logo_image') is None or data.get('logo_image') == '' or data.get('logo_image') == 'null'):
                    if old_logo:
                        from apps.core.helpers import delete_file
                        delete_file('company_logos', old_logo)
                    company_data['logo_image'] = None
                else:
                    company_data.pop('logo_image', None)
                
                # Remove original fields and fetch actual model instances for foreign keys
                if data.get("country"):
                    company_data.pop("country", None)
                    company_data["country"] = CountryMaster.objects.get(id=data.get("country"))
                if data.get("state"):
                    company_data.pop("state", None)
                    company_data["state"] = StateMaster.objects.get(id=data.get("state"))
                if data.get("city"):
                    company_data.pop("city", None)
                    company_data["city"] = CityMaster.objects.get(id=data.get("city"))
                
                company = TenantQuery.updateRecordById(Company, company_id, company_data, request)
                if not company:
                    raise Exception("Company not found")
                
                # Normalize logo_image: convert string "null" to actual None
                if company.get('logo_image') == 'null':
                    company['logo_image'] = None
                
                # Construct full URL for logo_image if it exists
                if company.get('logo_image'):
                    url = str(company['logo_image'])
                    if not url.startswith('company_logos'):
                        url = f"company_logos/{url}"
                    company['logo_image'] = request.build_absolute_uri(settings.MEDIA_URL + url)
                
                return ResponseBuilder.success(message="Company updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(company_id, request):
        try:
            company = TenantQuery.findOneRecord(Company, company_id, {}, request)
            if not company or company.get('status') == 2:
                raise Exception("Company not found")
            
            # Normalize logo_image: convert string "null" to actual None
            if company.get('logo_image') == 'null':
                company['logo_image'] = None
            
            # Construct full URL for logo_image if it exists
            if company.get('logo_image'):
                url = str(company['logo_image'])
                if not url.startswith('company_logos'):
                    url = f"company_logos/{url}"
                company['logo_image'] = request.build_absolute_uri(settings.MEDIA_URL + url)
            
            return ResponseBuilder.success(data=company, message="Company retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class UserService:
    @staticmethod
    def update(data, request, user_id):
        try:
            with transaction.atomic():
                user_data = data.copy()
                
                # Get current user to check for existing profile image
                current_user = TenantQuery.findOneRecord(User, user_id, {}, request, False)
                old_profile_image = None
                if current_user and current_user.get('profile_image'):
                    old_profile_image = current_user['profile_image']
                    if 'profile_images/' in old_profile_image:
                        old_profile_image = old_profile_image.split('profile_images/')[-1]
                
                profile_image_field_in_request = False
                if hasattr(request, 'POST') and 'profile_image' in request.POST:
                    profile_image_field_in_request = True
                
                # Handle profile_image upload
                if 'profile_image' in request.FILES:
                    profile_image_file = request.FILES.get('profile_image')
                    saved = uploadFile(profile_image_file, subfolder='profile_images', old_file_name=old_profile_image)
                    file_url = next(iter(saved.values())) if saved else None
                    if file_url:
                        user_data['profile_image'] = f"profile_images/{file_url}"
                elif profile_image_field_in_request and (data.get('profile_image') is None or data.get('profile_image') == '' or data.get('profile_image') == 'null'):
                    if old_profile_image:
                        from apps.core.helpers import delete_file
                        delete_file('profile_images', old_profile_image)
                    user_data['profile_image'] = None
                else:
                    user_data.pop('profile_image', None)
                
                # Remove original fields and fetch actual model instances for foreign keys
                if data.get("country"):
                    user_data.pop("country", None)
                    user_data["country"] = CountryMaster.objects.get(id=data.get("country"))
                if data.get("state"):
                    user_data.pop("state", None)
                    user_data["state"] = StateMaster.objects.get(id=data.get("state"))
                if data.get("city"):
                    user_data.pop("city", None)
                    user_data["city"] = CityMaster.objects.get(id=data.get("city"))
                
                # Handle password update if provided
                if data.get("password"):
                    user_data.pop("password", None)
                    # Get the user instance to set password
                    user_instance = User.objects.get(id=user_id)
                    user_instance.set_password(data.get("password"))
                    user_instance.save()
                
                user = TenantQuery.updateRecordById(User, user_id, user_data, request)
                if not user:
                    raise Exception("User not found")
                
                # Normalize profile_image: convert string "null" to actual None
                if user.get('profile_image') == 'null':
                    user['profile_image'] = None
                
                # Construct full URL for profile_image if it exists
                if user.get('profile_image'):
                    url = str(user['profile_image'])
                    if not url.startswith('profile_images'):
                        url = f"profile_images/{url}"
                    user['profile_image'] = request.build_absolute_uri(settings.MEDIA_URL + url)
                
                return ResponseBuilder.success(message="User updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(user_id, request):
        try:
            user = TenantQuery.findOneRecord(User, user_id, {}, request)
            if not user or user.get('status') == 2:
                raise Exception("User not found")
            
            # Normalize profile_image: convert string "null" to actual None
            if user.get('profile_image') == 'null':
                user['profile_image'] = None
            
            # Construct full URL for profile_image if it exists
            if user.get('profile_image'):
                url = str(user['profile_image'])
                if not url.startswith('profile_images'):
                    url = f"profile_images/{url}"
                user['profile_image'] = request.build_absolute_uri(settings.MEDIA_URL + url)
            
            return ResponseBuilder.success(data=user, message="User retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def sendPasswordOTP(phone_number, request):
        try:
            phone = normalizePhoneNumber(phone_number)
            otp_instance = generateOtp(phone, otp_type='FORGOT-PASSWORD')
            
            return ResponseBuilder.success(
                message="OTP sent successfully for password update",
                data={"otp_code": otp_instance.otp_code}
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def updatePasswordWithOTP(data, request):
        try:
            phone_number = normalizePhoneNumber(data.get('phone_number'))
            otp_code = data.get('otp_code')
            new_password = data.get('new_password')

            # Get user instance by phone number
            try:
                user_instance = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                raise Exception("User not found with this phone number")
            phone = user_instance.phone_number
            
            # Get the OTP instance for this user's phone number
            otp_instance = OTP.objects.filter(phone_number=phone).order_by('-created_at').first()
            if not otp_instance:
                raise Exception("OTP not found or expired. Please request a new OTP.")
            
            # Check if OTP was already used
            if otp_instance.is_verified:
                raise Exception("OTP has already been used. Please request a new OTP.")
            
            # Verify the OTP
            if not otp_instance.verify(otp_code):
                raise Exception("Invalid OTP code")
            
            # Mark OTP as verified
            otp_instance.is_verified = True
            otp_instance.save()
            
            # Update password
            user_instance.set_password(new_password)
            user_instance.save()
            
            # Delete the OTP after successful password update
            otp_instance.delete()
            
            return ResponseBuilder.success(message="Password updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class BranchService:
    @staticmethod
    def getAll(data, request):
        try:
            fieldConfig = [["branch_name", True, True]]
            options = {
                'attributes': ['id', 'branch_name', 'company', 'city__name', 'state__name', 'status'],
                'select_related': ['city', 'state']
            }
            result = TenantQuery.fetchPaginatedData(Branch, data, fieldConfig, options, request)
            return ResponseBuilder.success(data=result, message="Branches retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                branch_data = data.copy()
                
                # Remove original fields and fetch actual model instances for foreign keys
                if data.get("country"):
                    branch_data.pop("country", None)
                    branch_data["country"] = CountryMaster.objects.get(id=data.get("country"))
                if data.get("state"):
                    branch_data.pop("state", None)
                    branch_data["state"] = StateMaster.objects.get(id=data.get("state"))
                if data.get("city"):
                    branch_data.pop("city", None)
                    branch_data["city"] = CityMaster.objects.get(id=data.get("city"))
                
                branch = TenantQuery.createRecord(Branch, branch_data, request)
                
                auth_ctx = getAuthContext(request)
                user_id = auth_ctx.get('user_id')
                if user_id and branch.get('id'):
                    user = User.objects.get(id=user_id)
                    if not user.branch_access:
                        user.branch_access = []
                    if branch['id'] not in user.branch_access:
                        user.branch_access.append(branch['id'])
                        user.save(update_fields=['branch_access'])

                return ResponseBuilder.success(
                    data=branch,
                    message="Branch created successfully"
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, branch_id):
        try:
            with transaction.atomic():
                branch = TenantQuery.updateRecordById(Branch, branch_id, data, request)
                if not branch:
                    raise Exception("Branch not found")
                return ResponseBuilder.success(data=branch, message="Branch updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(branch_id, request):
        try:
            branch = TenantQuery.findOneRecord(Branch, branch_id, {}, request)
            if not branch or branch.get('status') == 2:
                raise Exception("Branch not found")
            return ResponseBuilder.success(data=branch, message="Branch retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = TenantQuery.softDeleteById(Branch, data.get('ids'), request)
                if count == 0:
                    raise Exception("Already deleted")
                return ResponseBuilder.success(message="Branches deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def switchBranch(branch_id, request):
        try:
            
            # Get current auth context
            ctx = getAuthContext(request)
            current_user_id = ctx.get('user_id')
            current_company_id = ctx.get('company_id')
            
            # Get the branch
            branch = TenantQuery.findOneRecord(Branch, branch_id, {}, request, False)
            if not branch or branch.get('status') == 2:
                raise Exception("Branch not found")
            
            # Validate branch belongs to user's company
            branch_company_id = branch.get('company') or branch.get('company_id')
            if branch_company_id != current_company_id:
                raise Exception("Branch does not belong to your company")
            
            # Get user instance
            user = User.objects.get(id=current_user_id)
            
            # Generate new JWT token with branch context
            refresh = RefreshToken.for_user(user)
            
            # Add branch context to token
            refresh['branch_id'] = branch_id
            refresh['company_id'] = current_company_id
            
            return ResponseBuilder.success(
                data={
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'branch_id': branch_id,
                    'branch_name': branch.get('branch_name')
                },
                message="Branch switched successfully"
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            branches = TenantQuery.findAllRecords(
                Branch,
                {},
                {'attributes': ['id', 'branch_name'], 'order': ['branch_name']},
                request
            )
            return ResponseBuilder.success(data=branches, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
