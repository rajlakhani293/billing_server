from django.db import transaction
import json
import math
from decimal import Decimal
from apps.core.helpers import ResponseBuilder
from .models import Brand, Tax, Party
from apps.core.commonQuery import CommonQuery
from apps.sales.models import CustomerLedger


class BrandService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                brand = CommonQuery.createRecord(Brand, data, request)
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
                brand = CommonQuery.updateRecordById(Brand, brand_id, data, request)
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
            result = CommonQuery.fetchPaginatedData(Brand, data, fieldConfig, options, request)
            return ResponseBuilder.success(data=result, message="Brands retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            brands = CommonQuery.findAllRecords(Brand, {}, {'attributes': ['id', 'brand_name'], 'order': ['brand_name']}, request)
            return ResponseBuilder.success(data=brands, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
            
    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = CommonQuery.softDeleteById(Brand, data.get('ids'), request)
                if count == 0: raise Exception("Already deleted")
                return ResponseBuilder.success(message="Brands deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(brand_id, request):
        try:
            brand = CommonQuery.findOneRecord(Brand, brand_id, {}, request)
            if not brand or brand.get('status') == 2: raise Exception("Brand not found")
            return ResponseBuilder.success(data=brand, message="Brand retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class TaxService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                tax = CommonQuery.createRecord(Tax, data, request)
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
                tax = CommonQuery.updateRecordById(Tax, tax_id, data, request)
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
            result = CommonQuery.fetchPaginatedData(Tax, data, fieldConfig, options, request)
            return ResponseBuilder.success(data=result, message="Taxes retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            taxes = CommonQuery.findAllRecords(Tax, {}, {'attributes': ['id', 'tax_name', 'tax_value'], 'order': ['tax_name']}, request)
            return ResponseBuilder.success(data=taxes, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
            
    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = CommonQuery.softDeleteById(Tax, data.get('ids'), request)
                if count == 0: raise Exception("Already deleted")
                return ResponseBuilder.success(message="Taxes deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(tax_id, request):
        try:
            tax = CommonQuery.findOneRecord(Tax, tax_id, {}, request)
            if not tax or tax.get('status') == 2: raise Exception("Tax not found")
            return ResponseBuilder.success(data=tax, message="Tax retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

class PartyService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                CommonQuery.createRecord(Party, data, request)
                return ResponseBuilder.success(message="Party created successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, record_id):
        try:
            with transaction.atomic():
                CommonQuery.updateRecordById(Party, record_id, data, request)
                return ResponseBuilder.success(message="Party updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                CommonQuery.softDeleteById(Party, data.get('ids'), request)
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
 
            result = CommonQuery.fetchPaginatedData(Party, data, fieldConfig, {}, request)
            return ResponseBuilder.success(data=result, message="Parties retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(party_id, request):
        try:
            party = CommonQuery.findOneRecord(Party, party_id, {}, request)
            if not party or party.get('status') == 2: raise Exception("Party not found")
            return ResponseBuilder.success(data=party, message="Party retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            # Dropdown usually needs id and name
            parties = CommonQuery.findAllRecords(
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
            result = CommonQuery.findAllRecords(
                CustomerLedger,
                {
                    "month": data["month"],
                    "year": data["year"],
                    "party": party_id,
                },
                {
                    "attributes": [
                        "date",
                        "amount",
                        "note",
                        "sales__sales_code",
                    ]
                },
                request,
            )

            return ResponseBuilder.success(
                message="Party credit day data retrieved successfully",
                data=result,
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

            ledger_rows = CommonQuery.findAllRecords(
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
