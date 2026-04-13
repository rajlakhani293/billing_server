from django.db import transaction
from django.utils import timezone
import json
import math
import datetime
from decimal import Decimal
from apps.core.helpers import ResponseBuilder
from .models import Brand, Tax, Party
from apps.core.tenantQuery import TenantQuery
from apps.sales.models import CustomerLedger, MonthlyStatement, PaymentHistory
from apps.sales.service import SalesService


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

                # Apply payment to previous month first (if due exists), remainder to current month
                first_day_current = payment_date.replace(day=1)
                prev_month_end = first_day_current - datetime.timedelta(days=1)

                prev_closing = Decimal(
                    str(
                        TenantQuery.sumRecords(
                            CustomerLedger,
                            "amount",
                            {"party_id": party_id, "date__lte": prev_month_end},
                            request,
                        )
                    )
                )
                prev_due = prev_closing if prev_closing > 0 else Decimal("0.00")

                apply_prev = min(amount, prev_due)
                remaining = amount - apply_prev

                if apply_prev > 0:
                    SalesService.createLedgerEntry(
                        request,
                        party_id=party_id,
                        amount=-apply_prev,
                        note="Payment adjusted for previous month",
                        entry_date=prev_month_end,
                    )

                if remaining > 0:
                    SalesService.createLedgerEntry(
                        request,
                        party_id=party_id,
                        amount=-remaining,
                        note=note,
                        entry_date=payment_date,
                    )

                return ResponseBuilder.success(message="Payment recorded successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
