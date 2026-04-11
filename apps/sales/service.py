from django.db import transaction, models
from django.utils import timezone
from datetime import timedelta
import json
from decimal import Decimal
from apps.core.helpers import ResponseBuilder, generateSequentialCode
from .models import Sales, SalesTransaction, CustomerLedger, MonthlyStatement
from apps.core.tenantQuery import TenantQuery
from apps.items.service import InventoryService
from apps.items.models import Item
from apps.settings.models import Party
import datetime

class SalesService:
    OPENING_BALANCE_NOTE = "Opening Balance"

    @staticmethod
    def _getOpeningBalanceBeforeDate(party_id, cutoff_date):
        if not party_id or not cutoff_date:
            return Decimal("0.00")
        return Decimal(
            str(
                CustomerLedger.objects.filter(
                    party_id=party_id,
                    date__lt=cutoff_date,
                ).aggregate(total=models.Sum("amount")).get("total") or 0
            )
        )

    @staticmethod
    def ensureMonthlyOpeningBalance(request, party, entry_date):
        if not party or not entry_date:
            return

        # Only create once per month
        existing = TenantQuery.findOneRecord(
            CustomerLedger,
            {
                "party_id": party.id,
                "month": entry_date.month,
                "year": entry_date.year,
                "note": SalesService.OPENING_BALANCE_NOTE,
            },
            {},
            request,
        )
        if existing:
            return

        first_day = entry_date.replace(day=1)
        signed_balance = SalesService._getOpeningBalanceBeforeDate(party.id, first_day)

        if signed_balance == 0:
            return

        TenantQuery.createRecord(
            CustomerLedger,
            {
                "party_id": party.id,
                "amount": signed_balance,
                "date": first_day,
                "month": first_day.month,
                "year": first_day.year,
                "note": SalesService.OPENING_BALANCE_NOTE,
            },
            request,
        )

    @staticmethod
    def ensureMonthlyOpeningBalanceForDate(party, first_day):
        if not party or not first_day:
            return

        exists = CustomerLedger.objects.filter(
            party_id=party.id,
            month=first_day.month,
            year=first_day.year,
            note=SalesService.OPENING_BALANCE_NOTE,
        ).exists()
        if exists:
            return

        signed_balance = SalesService._getOpeningBalanceBeforeDate(party.id, first_day)
        if signed_balance == 0:
            return

        CustomerLedger.objects.create(
            party_id=party.id,
            amount=signed_balance,
            date=first_day,
            month=first_day.month,
            year=first_day.year,
            note=SalesService.OPENING_BALANCE_NOTE,
            company_id=party.company_id,
            branch_id=party.branch_id,
        )

    @staticmethod
    def createLedgerEntry(request, party_id, amount, sales_id=None, note=None, entry_date=None, affect_balance=True):
        party = TenantQuery.findOneRecordForUpdate(
            Party, {"id": party_id}, request
        )
        if not party:
            return None

        entry_date = entry_date or timezone.localdate()
        # entry_date = datetime.date(2026, 3, 18)

        # Ensure opening balance exists before first transaction in a month
        if note != SalesService.OPENING_BALANCE_NOTE:
            SalesService.ensureMonthlyOpeningBalance(request, party, entry_date)

        stored_amount = Decimal(str(party.current_balance or "0.00"))
        balance_type = party.balance_type or 1
        signed_balance = stored_amount if balance_type == 1 else -stored_amount

        signed_delta = Decimal(str(amount))
        new_signed = signed_balance + signed_delta

        if new_signed > 0:
            party.balance_type = 1
            party.current_balance = new_signed
        elif new_signed < 0:
            party.balance_type = 2
            party.current_balance = abs(new_signed)
        else:
            party.balance_type = None
            party.current_balance = Decimal("0.00")

        if affect_balance:
            party.save(update_fields=["current_balance", "balance_type", "updated_at"])

        TenantQuery.createRecord(
            CustomerLedger,
            {
                "party_id": party.id,
                "sales_id": sales_id,
                "amount": Decimal(str(amount)),
                "date": entry_date,
                "month": entry_date.month,
                "year": entry_date.year,
                "note": note,
            },
            request,
        )

        if note != SalesService.OPENING_BALANCE_NOTE:
            SalesService.updateMonthlyStatement(request, party, entry_date, Decimal(str(amount)))
        return new_signed

    @staticmethod
    def updateMonthlyStatement(request, party, entry_date, amount):
        if not party or not entry_date:
            return

        month = entry_date.month
        year = entry_date.year
        first_day = entry_date.replace(day=1)

        statement = TenantQuery.findOneRecordForUpdate(
            MonthlyStatement,
            {"party_id": party.id, "month": month, "year": year},
            request,
        )

        if not statement:
            opening_balance = SalesService._getOpeningBalanceBeforeDate(party.id, first_day)
            statement = MonthlyStatement.objects.create(
                party_id=party.id,
                month=month,
                year=year,
                opening_balance=opening_balance,
                month_due_total=Decimal("0.00"),
                month_paid_total=Decimal("0.00"),
                closing_balance=opening_balance,
                company_id=party.company_id,
                branch_id=party.branch_id,
            )

        if amount >= 0:
            statement.month_due_total = (statement.month_due_total or Decimal("0.00")) + amount
        else:
            statement.month_paid_total = (statement.month_paid_total or Decimal("0.00")) + abs(amount)

        statement.closing_balance = (
            (statement.opening_balance or Decimal("0.00"))
            + (statement.month_due_total or Decimal("0.00"))
            - (statement.month_paid_total or Decimal("0.00"))
        )

        statement.save(update_fields=["month_due_total", "month_paid_total", "closing_balance", "updated_at"])

    @staticmethod
    def generateMonthlyStatementForParty(party, year, month, allow_zero=False):
        if not party:
            return None

        first_day = datetime.date(year, month, 1)
        next_month_year = year + (1 if month == 12 else 0)
        next_month = 1 if month == 12 else month + 1
        next_month_first = datetime.date(next_month_year, next_month, 1)

        statement = MonthlyStatement.objects.filter(
            party_id=party.id,
            year=year,
            month=month,
        ).first()

        if statement:
            return statement

        opening_balance = SalesService._getOpeningBalanceBeforeDate(party.id, first_day)

        if opening_balance == 0 and not allow_zero:
            return None

        # Ensure opening balance entry exists in ledger for the month when needed
        if opening_balance != 0:
            SalesService.ensureMonthlyOpeningBalanceForDate(party, first_day)

        month_entries = CustomerLedger.objects.filter(
            party_id=party.id,
            date__gte=first_day,
            date__lt=next_month_first,
        ).exclude(note=SalesService.OPENING_BALANCE_NOTE)

        month_due_total = Decimal(str(month_entries.filter(amount__gte=0).aggregate(total=models.Sum("amount")).get("total") or 0))
        month_paid_total = Decimal(str(month_entries.filter(amount__lt=0).aggregate(total=models.Sum("amount")).get("total") or 0))
        month_paid_total = abs(month_paid_total)

        closing_balance = opening_balance + month_due_total - month_paid_total

        return MonthlyStatement.objects.create(
            party_id=party.id,
            month=month,
            year=year,
            opening_balance=opening_balance,
            month_due_total=month_due_total,
            month_paid_total=month_paid_total,
            closing_balance=closing_balance,
            company_id=party.company_id,
            branch_id=party.branch_id,
        )
    
    @staticmethod
    def create(request, payload: dict):
        try:
            if payload.get('payment_mode') == 3:
                if not payload.get('party_id'):
                    return ResponseBuilder.error(
                        message="Party ID is required when payment mode is Partial",
                        status_code=400
                    )
                if float(payload.get('paid_amount', 0)) < 0:
                    return ResponseBuilder.error(
                        message="Paid amount must be 0 or greater when payment mode is Partial",
                        status_code=400
                    )
            
            with transaction.atomic():
                # Extract transactions data
                transactions_data = payload.pop('transactions', [])
                payload["sales_date"] = timezone.localdate()
                # payload["sales_date"] = datetime.date(2026, 3, 18)

                total_amount = Decimal(str(payload.get('total_amount', "0.00")))
                paid_amount_raw = payload.get('paid_amount', "0.00")
                paid_amount = Decimal(str(paid_amount_raw if paid_amount_raw not in [None, ""] else "0.00"))

                if payload.get('payment_mode') == 3:
                    if paid_amount > total_amount:
                        paid_amount = total_amount
                else:
                    paid_amount = total_amount

                payload['paid_amount'] = paid_amount
                payload['balance_amount'] = max(Decimal("0.00"), total_amount - paid_amount)

                # Generate Sales Code
                payload['sales_code'] = generateSequentialCode(Sales, 'sales_code', 'SL')
                
                # Create Sales Record
                sales = TenantQuery.createRecord(Sales, payload, request)
                
                # Create Sales Transactions
                for trans_data in transactions_data:
                    trans_data['sales_id'] = sales['id']
                    
                    TenantQuery.createRecord(SalesTransaction, trans_data, request)

                    InventoryService.applyStockMovement(
                        request,
                        item_id=trans_data['item_id'],
                        movement_type="SALE",
                        quantity=trans_data['item_quantity'],
                        note=f"Sales invoice {sales['sales_code']}",
                        reference_type="SALES",
                        reference_id=sales['id'],
                    )

                party_id = sales.get("party_id") or sales.get("party") or payload.get("party_id")
                if payload.get("payment_mode") == 3 and party_id:
                    due_amount = max(Decimal("0.00"), total_amount - paid_amount)
                    if due_amount > 0:
                        SalesService.createLedgerEntry(
                            request,
                            party_id=party_id,
                            amount=due_amount,
                            sales_id=sales["id"],
                            note=f"Sales invoice {sales['sales_code']}",
                        )
                
                return ResponseBuilder.success(
                    message="Sales created successfully",
                    data=sales
                )
        except Exception as e:
            return ResponseBuilder.error(str(e))

    @staticmethod
    def getAll(data, request):
        try:
            # Field configuration: [field_name, is_searchable, is_sortable]
            fieldConfig = [
                ["sales_code", True, True],
                ["party__name", True, True],
                ["total_amount", True, True],
                ["payment_mode", True, True],
            ]
            
            options = {
                'attributes': [
                    'id', 'sales_code', 'party__name',
                    'total_amount', 'paid_amount', 'balance_amount', 'payment_mode', 'status'
                ],
            }
            
            result = TenantQuery.fetchPaginatedData(
                Sales, data, fieldConfig, options, request
            )
            
            return ResponseBuilder.success(
                data=result,
                message="Sales retrieved successfully"
            )
            
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )

    @staticmethod
    def getById(sales_id, request):
        try:
            sales = TenantQuery.findOneRecord(
                Sales, 
                {"id": sales_id}, 
                {
                    "include": [
                        {"model": SalesTransaction, "as": "transactions"},
                    ],
                }, 
                request
            )
            if not sales or sales.get("status") == 2:
                raise Exception("Sales record not found")

           
            return ResponseBuilder.success(data=sales, message="Sales retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

  
    @staticmethod
    def getInvoiceView(sales_id, request):
        try:
            sales = TenantQuery.findOneRecord(
                Sales, 
                {"id": sales_id}, 
                {
                    "include": [
                        {"model": SalesTransaction, "as": "transactions"},
                        {"model": Party, "as": "party"},
                    ],
                }, 
                request
            )

            if not sales or sales.get("status") == 2:
                raise Exception("Sales record not found")

            return ResponseBuilder.success(data=sales, message="Sales retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(request, sales_id: int, payload: dict):
        try:
            with transaction.atomic():
                sales = TenantQuery.findOneRecordForUpdate(
                    Sales, {"id": sales_id}, request
                )
                if not sales:
                    raise Exception("Sales record not found")
                if sales.status == 3:
                    raise Exception("Cannot update a fully returned sales record")

                add_lines = payload.get("add_transactions") or []
                return_lines = payload.get("return_transactions") or []
                if not add_lines and not return_lines:
                    raise Exception("At least one return or add item is required")

                total_return_amount = Decimal("0.00")
                added_subtotal = Decimal("0.00")
                added_tax = Decimal("0.00")
                added_discount = Decimal("0.00")
                added_total = Decimal("0.00")

                if return_lines:
                    for row in return_lines:
                        sales_transaction_id = row.get("sales_transaction_id")
                        return_qty = Decimal(str(row.get("return_quantity")))

                        sales_transaction = TenantQuery.findOneRecordForUpdate(
                            SalesTransaction,
                            {"id": sales_transaction_id, "sales_id": sales.id},
                            request,
                        )
                        if not sales_transaction:
                            raise Exception(f"Sales transaction {sales_transaction_id} not found")

                        remaining_qty = sales_transaction.item_quantity - sales_transaction.returned_quantity
                        if return_qty > remaining_qty:
                            raise Exception(
                                f"Return quantity exceeds available quantity for transaction {sales_transaction_id}"
                            )

                        line_amount = return_qty * sales_transaction.item_rate
                        sales_transaction.returned_quantity += return_qty
                        sales_transaction.save(update_fields=["returned_quantity", "updated_at"])

                        InventoryService.applyStockMovement(
                            request,
                            item_id=sales_transaction.item_id,
                            movement_type="SALES_RETURN",
                            quantity=return_qty,
                            note=f"Sales return for {sales.sales_code}",
                            reference_type="SALES_UPDATE",
                            reference_id=sales.id,
                        )

                        total_return_amount += line_amount

                if add_lines:
                    for trans_data in add_lines:
                        item_id = trans_data.get("item_id")
                        item = TenantQuery.findOneRecord(
                            Item, {"id": item_id}, {}, request
                        )
                        if not item:
                            raise Exception(f"Item {item_id} not found")
                        item_id_val = item["id"] if isinstance(item, dict) else item.id
                        item_name_val = item.get("item_name") if isinstance(item, dict) else item.item_name

                        qty = Decimal(str(trans_data.get("item_quantity")))
                        rate = Decimal(str(trans_data.get("item_rate")))
                        line_subtotal = qty * rate
                        line_tax = Decimal(str(trans_data.get("tax_amount") or "0.00"))
                        line_discount = Decimal(str(trans_data.get("discount_amount") or "0.00"))
                        line_total = Decimal(str(trans_data.get("total_amount") or line_subtotal))

                        if qty <= 0:
                            raise Exception("Quantity must be greater than 0")
                        if rate < 0:
                            raise Exception("Unit price cannot be negative")

                        TenantQuery.createRecord(
                            SalesTransaction,
                            {
                                "sales_id": sales.id,
                                "item_id": item_id_val,
                                "item_quantity": qty,
                                "item_rate": rate,
                                "item_description": trans_data.get("item_description") or item_name_val,
                                "discount_percentage": Decimal(str(trans_data.get("discount_percentage") or "0.00")),
                                "discount_amount": line_discount,
                                "tax_amount": line_tax,
                                "total_amount": line_total,
                            },
                            request,
                        )

                        InventoryService.applyStockMovement(
                            request,
                            item_id=item_id_val,
                            movement_type="SALE",
                            quantity=qty,
                            note=f"Sales update {sales.sales_code}",
                            reference_type="SALES_UPDATE",
                            reference_id=sales.id,
                        )

                        added_subtotal += line_subtotal
                        added_tax += line_tax
                        added_discount += line_discount
                        added_total += line_total

                    if sales.payment_mode == 3 and sales.party_id and added_total > 0:
                        SalesService.createLedgerEntry(
                            request,
                            party_id=sales.party_id,
                            amount=added_total,
                            sales_id=sales.id,
                            note=f"Sales update {sales.sales_code}",
                        )

                if total_return_amount > 0:
                    sales.total_amount = max(Decimal("0.00"), sales.total_amount - total_return_amount)
                    if sales.paid_amount > sales.total_amount:
                        sales.paid_amount = sales.total_amount

                    if sales.payment_mode == 3 and sales.party_id:
                        SalesService.createLedgerEntry(
                            request,
                            party_id=sales.party_id,
                            amount=-total_return_amount,
                            sales_id=sales.id,
                            note=f"Sales return for {sales.sales_code}",
                        )

                if added_total > 0:
                    sales.subtotal = (sales.subtotal or Decimal("0.00")) + added_subtotal
                    sales.tax_amount = (sales.tax_amount or Decimal("0.00")) + added_tax
                    sales.discount_amount = (sales.discount_amount or Decimal("0.00")) + added_discount
                    sales.total_amount = (sales.total_amount or Decimal("0.00")) + added_total

                return_note = str(payload.get("return_notes") or "").strip()
                update_note = str(payload.get("update_notes") or "").strip()
                if return_note:
                    if sales.notes:
                        sales.notes = f"{sales.notes}\n[RETURN] {return_note}"
                    else:
                        sales.notes = f"[RETURN] {return_note}"
                if update_note:
                    if sales.notes:
                        sales.notes = f"{sales.notes}\n[UPDATE] {update_note}"
                    else:
                        sales.notes = f"[UPDATE] {update_note}"

                sales.balance_amount = max(Decimal("0.00"), sales.total_amount - sales.paid_amount)
                sales.save(update_fields=["subtotal", "tax_amount", "discount_amount", "total_amount", "paid_amount", "balance_amount", "notes", "updated_at"])

                return ResponseBuilder.success(
                    message="Sales updated successfully",
                    data={
                        "sales_id": sales.id,
                        "sales_code": sales.sales_code,
                        "returned_total": total_return_amount,
                        "added_total": added_total,
                        "total_amount": sales.total_amount,
                    },
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getDashboardStats(request):
        try:
            today = timezone.localdate()

            # Use countRecords and sumRecords for database-level calculations
            total_sales_count = TenantQuery.countRecords(Sales, {}, request)
            total_sales_amount = TenantQuery.sumRecords(Sales, "total_amount", {}, request)

            today_sales_count = TenantQuery.countRecords(Sales, {"sales_date": today}, request)
            today_sales_amount = TenantQuery.sumRecords(Sales, "total_amount", {"sales_date": today}, request)
            today_collection = TenantQuery.sumRecords(Sales, "paid_amount", {"sales_date": today}, request)

            items_count = TenantQuery.countRecords(Item, {}, request)
            total_stock = TenantQuery.sumRecords(Item, "current_stock", {}, request)

            return ResponseBuilder.success(
                data={
                    "total_sales_count": total_sales_count,
                    "total_sales_amount": total_sales_amount,
                    "today_sales_count": today_sales_count,
                    "today_sales_amount": today_sales_amount,
                    "today_collection": today_collection,
                    "items_count": items_count,
                    "total_stock": total_stock,
                },
                message="Dashboard stats retrieved successfully",
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getSalesCharts(request, payload: dict):
        try:
            period = None
            if isinstance(payload, dict):
                period = payload.get("period")
            if not period:
                try:
                    body = request.body
                    if body:
                        parsed = json.loads(body.decode("utf-8"))
                        if isinstance(parsed, dict):
                            period = parsed.get("period")
                except Exception:
                    pass
            if not period:
                try:
                    period = request.query_params.get("period")
                except Exception:
                    period = None
            period = str(period or "daily").lower()
            if period not in {"daily", "monthly", "yearly"}:
                period = "daily"

            today = timezone.localdate()
            if period == "monthly":
                days = int(payload.get("days") or 30)
                start_date = today - timedelta(days=days)
                end_date = today
            elif period == "yearly":
                months = int(payload.get("months") or 12)
                start_date = today - timedelta(days=months * 31)
                end_date = today
            else:
                hours = int(payload.get("hours") or 24)
                start_date = today
                end_date = today

            qs = TenantQuery.findAllRecords(
                Sales,
                {
                    "sales_date__gte": start_date,
                    "sales_date__lte": end_date,
                },
                {"attributes": ["sales_date", "total_amount"]},
                request,
            )

            buckets = {}
            for row in qs:
                if period == "monthly":
                    dt = row.get("sales_date")
                    if dt is None:
                        continue
                    key = dt.strftime("%Y-%m-%d")
                    label = dt.strftime("%d %b")
                elif period == "yearly":
                    dt = row.get("sales_date")
                    if dt is None:
                        continue
                    key = dt.strftime("%Y-%m")
                    label = dt.strftime("%b %Y")
                else:
                    dt = row.get("sales_date")
                    if dt is None:
                        continue
                    dt_datetime = datetime.datetime.combine(dt, datetime.time.min)
                    key = dt_datetime.strftime("%Y-%m-%d %H:00")
                    label = dt_datetime.strftime("%I %p")

                buckets.setdefault(key, {"label": label, "total": Decimal("0.00"), "count": 0})
                buckets[key]["total"] += row.get("total_amount") or Decimal("0.00")
                buckets[key]["count"] += 1

            chart_data = []
            if period == "monthly":
                current = start_date
                end = end_date
                while current <= end:
                    key = current.strftime("%Y-%m-%d")
                    label = current.strftime("%d %b")
                    entry = buckets.get(key) or {"label": label, "total": Decimal("0.00"), "count": 0}
                    chart_data.append(entry)
                    current += timedelta(days=1)
            elif period == "yearly":
                current = start_date.replace(day=1)
                end = end_date.replace(day=1)
                while current <= end:
                    key = current.strftime("%Y-%m")
                    label = current.strftime("%b %Y")
                    entry = buckets.get(key) or {"label": label, "total": Decimal("0.00"), "count": 0}
                    chart_data.append(entry)
                    month = current.month + 1
                    year = current.year
                    if month > 12:
                        month = 1
                        year += 1
                    current = current.replace(year=year, month=month)
            else:
                current = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0, microsecond=0)
                end = current + timedelta(hours=hours)
                while current < end:
                    key = current.strftime("%Y-%m-%d %H:00")
                    label = current.strftime("%I %p")
                    entry = buckets.get(key) or {"label": label, "total": Decimal("0.00"), "count": 0}
                    chart_data.append(entry)
                    current += timedelta(hours=1)

            return ResponseBuilder.success(
                data={
                    "period": period,
                    "series": chart_data,
                },
                message="Sales chart data retrieved successfully",
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getTopProducts(request, payload: dict):
        try:
            days = int((payload or {}).get("days") or 30)
            limit = int((payload or {}).get("limit") or 5)
            today = timezone.localdate()
            start_date = today - timedelta(days=days)

            tx_rows = TenantQuery.findAllRecords(
                SalesTransaction,
                {
                    "sales__status": 0,
                    "sales__sales_date__gte": start_date,
                },
                {"attributes": ["item_id", "item__item_name", "item_quantity", "total_amount"]},
                request,
            )

            agg = {}
            for row in tx_rows:
                item_id = row.get("item_id")
                if not item_id:
                    continue
                if item_id not in agg:
                    agg[item_id] = {
                        "item_id": item_id,
                        "item__item_name": row.get("item__item_name"),
                        "total_sold": Decimal("0.00"),
                        "total_revenue": Decimal("0.00"),
                    }
                agg[item_id]["total_sold"] += row.get("item_quantity") or Decimal("0.00")
                agg[item_id]["total_revenue"] += row.get("total_amount") or Decimal("0.00")

            items = sorted(agg.values(), key=lambda x: x["total_revenue"], reverse=True)[:limit]
            return ResponseBuilder.success(
                data=items,
                message="Top products retrieved successfully",
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
