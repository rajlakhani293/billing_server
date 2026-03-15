from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
import json
from decimal import Decimal
from apps.core.helpers import ResponseBuilder, generate_sequential_code
from .models import Sales, SalesTransaction, SalesReturn, SalesReturnTransaction, CustomerLedger
from apps.core.commonQuery import CommonQuery
from apps.items.service import InventoryService
from apps.items.models import Item
from apps.settings.models import Party

class SalesService:

    @staticmethod
    def _create_ledger_entry(request, party_id, amount, entry_type, sales_id=None, reference_type=None, reference_id=None, note=None):
        party = CommonQuery.query(
            Party, request=request, for_update=True, apply_status=True
        ).filter(id=party_id).first()
        if not party:
            return None

        new_balance = (party.current_balance or Decimal("0.00")) + Decimal(str(amount))
        party.current_balance = new_balance

        if new_balance > 0:
            party.balance_type = 1
            party.wallet_balance = new_balance
        elif new_balance < 0:
            party.balance_type = 2
            party.wallet_balance = abs(new_balance)
        else:
            party.balance_type = None
            party.wallet_balance = Decimal("0.00")

        party.save(update_fields=["current_balance", "balance_type", "wallet_balance", "updated_at"])

        CommonQuery.createRecord(
            CustomerLedger,
            {
                "party_id": party.id,
                "sales_id": sales_id,
                "entry_type": entry_type,
                "amount": amount,
                "balance_after": new_balance,
                "reference_type": reference_type,
                "reference_id": reference_id,
                "note": note,
            },
            request,
        )
        return new_balance
    
    @staticmethod
    def create(request, payload: dict):
        try:
            # Validate business logic: party_id and paid_amount are required for Partial payment mode
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
                payload['sales_code'] = generate_sequential_code(Sales, 'sales_code', 'SL')
                
                # Create Sales Record
                sales = CommonQuery.createRecord(Sales, payload, request)
                
                # Create Sales Transactions
                for trans_data in transactions_data:
                    trans_data['sales_id'] = sales['id']
                    CommonQuery.createRecord(SalesTransaction, trans_data, request)
                    InventoryService.apply_stock_movement(
                        request=request,
                        item_id=trans_data['item_id'],
                        movement_type="SALE",
                        quantity=trans_data['item_quantity'],
                        note=f"Sales invoice {sales['sales_code']}",
                        reference_type="SALES",
                        reference_id=sales['id'],
                    )

                party_id = sales.get("party_id") or sales.get("party") or payload.get("party_id")
                if party_id:
                    SalesService._create_ledger_entry(
                        request=request,
                        party_id=party_id,
                        amount=total_amount,
                        entry_type="SALE",
                        sales_id=sales["id"],
                        reference_type="SALES",
                        reference_id=sales["id"],
                        note=f"Sales invoice {sales['sales_code']}",
                    )
                    if paid_amount > 0:
                        SalesService._create_ledger_entry(
                            request=request,
                            party_id=party_id,
                            amount=-paid_amount,
                            entry_type="PAYMENT",
                            sales_id=sales["id"],
                            reference_type="SALES_PAYMENT",
                            reference_id=sales["id"],
                            note=f"Payment for {sales['sales_code']}",
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
                    'total_amount', 'paid_amount', 'balance_amount', 'payment_mode', 'is_reverted', 'status'
                ],
            }
            
            result = CommonQuery.fetchPaginatedData(
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
    def getLedgerTransactions(data, request):
        try:
            data = data or {}
            fieldConfig = [
                ["party__name", True, True],
                ["sales__sales_code", True, True],
                ["entry_type", True, True],
                ["note", True, False],
                ["amount", False, True],
                ["balance_after", False, True],
                ["reference_type", True, True],
                ["reference_id", False, True],
                ["created_at", False, True],
            ]

            options = {
                "attributes": [
                    "id",
                    "party__name",
                    "sales__sales_code",
                    "entry_type",
                    "amount",
                    "balance_after",
                    "reference_type",
                    "reference_id",
                    "note",
                    "created_at",
                ],
            }

            result = CommonQuery.fetchPaginatedData(
                CustomerLedger,
                data,
                fieldConfig,
                options,
                request,
                date_field="created_at",
            )

            return ResponseBuilder.success(
                data=result,
                message="Ledger transactions retrieved successfully",
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getLedgerPayments(data, request):
        try:
            data = data or {}
            existing_filter = data.get("filter") or {}
            data["filter"] = {**existing_filter, "entry_type": "PAYMENT"}
            return SalesService.getLedgerTransactions(data, request)
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getPartyCreditSummary(data, request):
        try:
            data = data or {}
            period = str(data.get("period") or "monthly").lower()
            if period not in {"monthly", "yearly"}:
                period = "monthly"

            now = timezone.localtime(timezone.now())
            if period == "yearly":
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            else:
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(microseconds=1)

            sales_rows = (
                CommonQuery.query(Sales, request=request, apply_status=True)
                .filter(created_at__range=(start_date, end_date), is_reverted=False)
                .values("party_id", "party__name")
                .annotate(total_amount=Sum("total_amount"), total_paid=Sum("paid_amount"))
            )

            rows = []
            for row in sales_rows:
                party_id = row.get("party_id")
                if not party_id:
                    continue
                total_amount = row.get("total_amount") or Decimal("0.00")
                total_paid = row.get("total_paid") or Decimal("0.00")
                due_amount = total_amount - total_paid
                if due_amount <= 0:
                    continue
                rows.append({
                    "party_id": party_id,
                    "party__name": row.get("party__name"),
                    "total_amount": total_amount,
                    "total_paid": total_paid,
                    "due_amount": due_amount,
                })

            rows.sort(key=lambda x: x["due_amount"], reverse=True)

            return ResponseBuilder.success(
                data={
                    "period": period,
                    "start_date": start_date,
                    "end_date": end_date,
                    "items": rows,
                    "total": len(rows),
                },
                message="Party credit summary retrieved successfully",
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getPartyCreditDays(party_id, data, request):
        try:
            data = data or {}
            period = str(data.get("period") or "monthly").lower()
            if period not in {"monthly", "yearly"}:
                period = "monthly"

            now = timezone.localtime(timezone.now())
            if period == "yearly":
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            else:
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(microseconds=1)

            qs = (
                CommonQuery.query(Sales, request=request, apply_status=True)
                .filter(
                    created_at__range=(start_date, end_date),
                    party_id=party_id,
                    is_reverted=False,
                )
                .values("created_at", "sales_code", "total_amount", "paid_amount")
                .order_by("created_at")
            )

            day_map = {}
            for row in qs:
                dt = row.get("created_at")
                if dt is None:
                    continue
                if timezone.is_aware(dt):
                    dt = timezone.localtime(dt)
                day_key = dt.strftime("%Y-%m-%d")
                day_label = dt.strftime("%d %b")
                day_map.setdefault(day_key, {
                    "label": day_label,
                    "total_amount": Decimal("0.00"),
                    "total_paid": Decimal("0.00"),
                    "due_amount": Decimal("0.00"),
                    "sales": [],
                })
                total_amount = row.get("total_amount") or Decimal("0.00")
                total_paid = row.get("paid_amount") or Decimal("0.00")
                due_amount = total_amount - total_paid
                day_map[day_key]["total_amount"] += total_amount
                day_map[day_key]["total_paid"] += total_paid
                day_map[day_key]["due_amount"] += due_amount
                day_map[day_key]["sales"].append({
                    "sales_code": row.get("sales_code"),
                    "total_amount": total_amount,
                    "paid_amount": total_paid,
                    "due_amount": due_amount,
                    "created_at": row.get("created_at"),
                })

            days = list(day_map.values())
            days.sort(key=lambda x: x["label"])

            return ResponseBuilder.success(
                data={
                    "period": period,
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": days,
                },
                message="Party credit day data retrieved successfully",
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(sales_id, request):
        try:
            sales = CommonQuery.query(
                Sales, request=request, apply_status=False
            ).filter(id=sales_id).first()
            if not sales or sales.status == 2:
                raise Exception("Sales record not found")

            transaction_rows = CommonQuery.query(
                SalesTransaction, request=request, apply_status=True
            ).filter(sales_id=sales.id).select_related("item").order_by("created_at")

            transactions = [
                {
                    "id": row.id,
                    "item_id": row.item_id,
                    "item__item_name": row.item.item_name,
                    "item_quantity": row.item_quantity,
                    "returned_quantity": row.returned_quantity,
                    "item_rate": row.item_rate,
                    "total_amount": row.total_amount,
                    "item_description": row.item_description,
                    "discount_percentage": row.discount_percentage,
                    "discount_amount": row.discount_amount,
                    "tax_amount": row.tax_amount,
                }
                for row in transaction_rows
            ]

            returns = CommonQuery.query(
                SalesReturn, request=request, apply_status=True
            ).filter(sales_id=sales.id).prefetch_related("transactions").order_by("-created_at")

            returns_data = []
            for sales_return in returns:
                return_lines = []
                for line in sales_return.transactions.filter(status=0).select_related("item", "sales_transaction"):
                    return_lines.append({
                        "id": line.id,
                        "sales_transaction_id": line.sales_transaction_id,
                        "item_id": line.item_id,
                        "item_name": line.item.item_name,
                        "return_quantity": line.return_quantity,
                        "item_rate": line.item_rate,
                        "total_amount": line.total_amount,
                    })

                returns_data.append({
                    "id": sales_return.id,
                    "return_code": sales_return.return_code,
                    "return_date": sales_return.return_date,
                    "total_return_amount": sales_return.total_return_amount,
                    "notes": sales_return.notes,
                    "transactions": return_lines,
                })

            sales_data = {
                "id": sales.id,
                "sales_code": sales.sales_code,
                "party_id": sales.party_id,
                "subtotal": sales.subtotal,
                "tax_amount": sales.tax_amount,
                "discount_percentage": sales.discount_percentage,
                "discount_amount": sales.discount_amount,
                "total_amount": sales.total_amount,
                "paid_amount": sales.paid_amount,
                "balance_amount": sales.balance_amount,
                "payment_mode": sales.payment_mode,
                "notes": sales.notes,
                "is_reverted": sales.is_reverted,
                "status": sales.status,
                "transactions": transactions,
                "returns": returns_data,
            }

            return ResponseBuilder.success(data=sales_data, message="Sales retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def createReturn(request, sales_id: int, payload: dict):
        try:
            with transaction.atomic():
                sales = CommonQuery.query(
                    Sales, request=request, for_update=True, apply_status=True
                ).filter(id=sales_id).first()
                if not sales:
                    raise Exception("Sales record not found")
                if sales.is_reverted:
                    raise Exception("Cannot create return for a reverted sales record")

                transactions_data = payload.get("transactions") or []
                if not transactions_data:
                    raise Exception("At least one return line is required")

                return_code = generate_sequential_code(SalesReturn, "return_code", "SRN")
                sales_return = CommonQuery.createRecord(
                    SalesReturn,
                    {
                        "return_code": return_code,
                        "sales_id": sales.id,
                        "notes": payload.get("notes"),
                    },
                    request,
                )
                sales_return_id = sales_return["id"] if isinstance(sales_return, dict) else sales_return.id

                total_return_amount = Decimal("0.00")
                created_lines = []

                for row in transactions_data:
                    sales_transaction_id = row.get("sales_transaction_id")
                    return_qty = Decimal(str(row.get("return_quantity")))

                    sales_transaction = CommonQuery.query(
                        SalesTransaction, request=request, for_update=True, apply_status=True
                    ).filter(id=sales_transaction_id, sales_id=sales.id).first()
                    if not sales_transaction:
                        raise Exception(f"Sales transaction {sales_transaction_id} not found")

                    remaining_qty = sales_transaction.item_quantity - sales_transaction.returned_quantity
                    if return_qty > remaining_qty:
                        raise Exception(
                            f"Return quantity exceeds available quantity for transaction {sales_transaction_id}"
                        )

                    line_amount = return_qty * sales_transaction.item_rate
                    CommonQuery.createRecord(
                        SalesReturnTransaction,
                        {
                            "sales_return_id": sales_return_id,
                            "sales_transaction_id": sales_transaction.id,
                            "item_id": sales_transaction.item_id,
                            "return_quantity": return_qty,
                            "item_rate": sales_transaction.item_rate,
                            "total_amount": line_amount,
                        },
                        request,
                    )

                    sales_transaction.returned_quantity += return_qty
                    sales_transaction.save(update_fields=["returned_quantity", "updated_at"])

                    InventoryService.apply_stock_movement(
                        request=request,
                        item_id=sales_transaction.item_id,
                        movement_type="SALES_RETURN",
                        quantity=return_qty,
                        note=f"Sales return {return_code}",
                        reference_type="SALES_RETURN",
                        reference_id=sales_return_id,
                    )

                    total_return_amount += line_amount
                    created_lines.append({
                        "sales_transaction_id": sales_transaction.id,
                        "item_id": sales_transaction.item_id,
                        "return_quantity": return_qty,
                        "line_amount": line_amount,
                    })

                CommonQuery.updateRecordById(
                    SalesReturn,
                    sales_return_id,
                    {"total_return_amount": total_return_amount},
                    request,
                )

                sales.total_amount = max(Decimal("0.00"), sales.total_amount - total_return_amount)
                if sales.paid_amount > sales.total_amount:
                    sales.paid_amount = sales.total_amount
                sales.balance_amount = max(Decimal("0.00"), sales.total_amount - sales.paid_amount)
                sales.save(update_fields=["total_amount", "paid_amount", "balance_amount", "updated_at"])

                if sales.party_id and total_return_amount > 0:
                    SalesService._create_ledger_entry(
                        request=request,
                        party_id=sales.party_id,
                        amount=-total_return_amount,
                        entry_type="RETURN",
                        sales_id=sales.id,
                        reference_type="SALES_RETURN",
                        reference_id=sales_return_id,
                        note=f"Sales return {return_code}",
                    )

                return ResponseBuilder.success(
                    message="Sales return created successfully",
                    data={
                        "sales_return_id": sales_return_id,
                        "return_code": sales_return["return_code"] if isinstance(sales_return, dict) else sales_return.return_code,
                        "total_return_amount": total_return_amount,
                        "transactions": created_lines,
                    }
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(request, sales_id: int, payload: dict):
        try:
            with transaction.atomic():
                sales = CommonQuery.query(
                    Sales, request=request, for_update=True, apply_status=True
                ).filter(id=sales_id).first()
                if not sales:
                    raise Exception("Sales record not found")
                if sales.is_reverted:
                    raise Exception("Cannot update a reverted sales record")

                return_lines = payload.get("return_transactions") or []
                add_lines = payload.get("add_transactions") or []
                if not return_lines and not add_lines:
                    raise Exception("At least one return or add item is required")

                total_return_amount = Decimal("0.00")
                added_subtotal = Decimal("0.00")
                added_tax = Decimal("0.00")
                added_discount = Decimal("0.00")
                added_total = Decimal("0.00")

                if return_lines:
                    return_code = generate_sequential_code(SalesReturn, "return_code", "SRN")
                    sales_return = CommonQuery.createRecord(
                        SalesReturn,
                        {
                            "return_code": return_code,
                            "sales_id": sales.id,
                            "notes": payload.get("return_notes"),
                        },
                        request,
                    )
                    sales_return_id = sales_return["id"] if isinstance(sales_return, dict) else sales_return.id

                    for row in return_lines:
                        sales_transaction_id = row.get("sales_transaction_id")
                        return_qty = Decimal(str(row.get("return_quantity")))

                        sales_transaction = CommonQuery.query(
                            SalesTransaction, request=request, for_update=True, apply_status=True
                        ).filter(id=sales_transaction_id, sales_id=sales.id).first()
                        if not sales_transaction:
                            raise Exception(f"Sales transaction {sales_transaction_id} not found")

                        remaining_qty = sales_transaction.item_quantity - sales_transaction.returned_quantity
                        if return_qty > remaining_qty:
                            raise Exception(
                                f"Return quantity exceeds available quantity for transaction {sales_transaction_id}"
                            )

                        line_amount = return_qty * sales_transaction.item_rate
                        CommonQuery.createRecord(
                            SalesReturnTransaction,
                            {
                                "sales_return_id": sales_return_id,
                                "sales_transaction_id": sales_transaction.id,
                                "item_id": sales_transaction.item_id,
                                "return_quantity": return_qty,
                                "item_rate": sales_transaction.item_rate,
                                "total_amount": line_amount,
                            },
                            request,
                        )

                        sales_transaction.returned_quantity += return_qty
                        sales_transaction.save(update_fields=["returned_quantity", "updated_at"])

                        InventoryService.apply_stock_movement(
                            request=request,
                            item_id=sales_transaction.item_id,
                            movement_type="SALES_RETURN",
                            quantity=return_qty,
                            note=f"Sales return {return_code}",
                            reference_type="SALES_RETURN",
                            reference_id=sales_return_id,
                        )

                        total_return_amount += line_amount

                    CommonQuery.updateRecordById(
                        SalesReturn,
                        sales_return_id,
                        {"total_return_amount": total_return_amount},
                        request,
                    )

                    if sales.party_id and total_return_amount > 0:
                        SalesService._create_ledger_entry(
                            request=request,
                            party_id=sales.party_id,
                            amount=-total_return_amount,
                            entry_type="RETURN",
                            sales_id=sales.id,
                            reference_type="SALES_RETURN",
                            reference_id=sales_return_id,
                            note=f"Sales return {return_code}",
                        )

                if add_lines:
                    for trans_data in add_lines:
                        item_id = trans_data.get("item_id")
                        item = CommonQuery.query(
                            Item, request=request, apply_status=True
                        ).filter(id=item_id).first()
                        if not item:
                            raise Exception(f"Item {item_id} not found")

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

                        CommonQuery.createRecord(
                            SalesTransaction,
                            {
                                "sales_id": sales.id,
                                "item_id": item.id,
                                "item_quantity": qty,
                                "item_rate": rate,
                                "item_description": trans_data.get("item_description") or item.item_name,
                                "discount_percentage": Decimal(str(trans_data.get("discount_percentage") or "0.00")),
                                "discount_amount": line_discount,
                                "tax_amount": line_tax,
                                "total_amount": line_total,
                            },
                            request,
                        )

                        InventoryService.apply_stock_movement(
                            request=request,
                            item_id=item.id,
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

                    if sales.party_id and added_total > 0:
                        SalesService._create_ledger_entry(
                            request=request,
                            party_id=sales.party_id,
                            amount=added_total,
                            entry_type="SALE",
                            sales_id=sales.id,
                            reference_type="SALES_UPDATE",
                            reference_id=sales.id,
                            note=f"Sales update {sales.sales_code}",
                        )

                if total_return_amount > 0:
                    sales.total_amount = max(Decimal("0.00"), sales.total_amount - total_return_amount)
                    if sales.paid_amount > sales.total_amount:
                        sales.paid_amount = sales.total_amount

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
            now = timezone.localtime(timezone.now())
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

            sales_qs = CommonQuery.query(Sales, request=request, apply_status=True)
            today_sales_qs = sales_qs.filter(created_at__range=(start_of_day, end_of_day))

            total_sales_count = sales_qs.count()
            total_sales_amount = sales_qs.aggregate(total=Sum("total_amount")).get("total") or Decimal("0.00")
            today_sales_count = today_sales_qs.count()
            today_sales_amount = today_sales_qs.aggregate(total=Sum("total_amount")).get("total") or Decimal("0.00")
            today_collection = today_sales_qs.aggregate(total=Sum("paid_amount")).get("total") or Decimal("0.00")

            items_count = CommonQuery.query(Item, request=request, apply_status=True).count()
            total_stock = CommonQuery.query(Item, request=request, apply_status=True).aggregate(
                total=Sum("current_stock")
            ).get("total") or Decimal("0.00")
            total_returns_count = CommonQuery.query(SalesReturn, request=request, apply_status=True).count()
            total_returns_amount = CommonQuery.query(SalesReturn, request=request, apply_status=True).aggregate(
                total=Sum("total_return_amount")
            ).get("total") or Decimal("0.00")

            return ResponseBuilder.success(
                data={
                    "total_sales_count": total_sales_count,
                    "total_sales_amount": total_sales_amount,
                    "today_sales_count": today_sales_count,
                    "today_sales_amount": today_sales_amount,
                    "today_collection": today_collection,
                    "items_count": items_count,
                    "total_stock": total_stock,
                    "total_returns_count": total_returns_count,
                    "total_returns_amount": total_returns_amount,
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

            now = timezone.localtime(timezone.now())
            if period == "monthly":
                days = int(payload.get("days") or 30)
                start_date = now - timedelta(days=days)
                fmt = "%d %b"
                end_date = now
            elif period == "yearly":
                months = int(payload.get("months") or 12)
                start_date = now - timedelta(days=months * 31)
                fmt = "%b %Y"
                end_date = now
            else:
                hours = int(payload.get("hours") or 24)
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                fmt = "%H:%M"
                end_date = start_date + timedelta(days=1)

            qs = (
                CommonQuery.query(Sales, request=request, apply_status=True)
                .filter(created_at__gte=start_date, created_at__lt=end_date)
                .values("created_at", "total_amount")
            )

            buckets = {}
            for row in qs:
                dt = row.get("created_at")
                if dt is None:
                    continue
                if timezone.is_aware(dt):
                    dt = timezone.localtime(dt)

                if period == "monthly":
                    key = dt.strftime("%Y-%m-%d")
                    label = dt.strftime("%d %b")
                elif period == "yearly":
                    key = dt.strftime("%Y-%m")
                    label = dt.strftime("%b %Y")
                else:
                    key = dt.strftime("%Y-%m-%d %H:00")
                    label = dt.strftime("%I %p")

                buckets.setdefault(key, {"label": label, "total": Decimal("0.00"), "count": 0})
                buckets[key]["total"] += row.get("total_amount") or Decimal("0.00")
                buckets[key]["count"] += 1

            chart_data = []
            if period == "monthly":
                current = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end = now.replace(hour=0, minute=0, second=0, microsecond=0)
                while current <= end:
                    key = current.strftime("%Y-%m-%d")
                    label = current.strftime("%d %b")
                    entry = buckets.get(key) or {"label": label, "total": Decimal("0.00"), "count": 0}
                    chart_data.append(entry)
                    current += timedelta(days=1)
            elif period == "yearly":
                current = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
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
                current = start_date
                end = start_date + timedelta(days=1)
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
    def createPayment(request, payload: dict):
        try:
            party_id = payload.get("party_id")
            amount = Decimal(str(payload.get("amount")))
            note = payload.get("note")
            if not party_id:
                raise Exception("Party ID is required")
            if amount <= 0:
                raise Exception("Amount must be greater than 0")

            with transaction.atomic():
                SalesService._create_ledger_entry(
                    request=request,
                    party_id=party_id,
                    amount=-amount,
                    entry_type="PAYMENT",
                    sales_id=None,
                    reference_type="PARTY_PAYMENT",
                    reference_id=None,
                    note=note or "Customer payment",
                )

            return ResponseBuilder.success(
                message="Payment recorded successfully",
                data={"party_id": party_id, "amount": amount},
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getTopProducts(request, payload: dict):
        try:
            days = int((payload or {}).get("days") or 30)
            limit = int((payload or {}).get("limit") or 5)
            now = timezone.localtime(timezone.now())
            start_date = now - timedelta(days=days)

            qs = (
                CommonQuery.query(SalesTransaction, request=request, apply_status=True)
                .filter(
                    sales__status=0,
                    sales__is_reverted=False,
                    sales__created_at__gte=start_date,
                )
                .values("item_id", "item__item_name")
                .annotate(
                    total_sold=Sum("item_quantity"),
                    total_revenue=Sum("total_amount"),
                )
                .order_by("-total_revenue")
            )

            items = list(qs[:limit])
            return ResponseBuilder.success(
                data=items,
                message="Top products retrieved successfully",
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def revertSale(request, sales_id: int, payload: dict):
        try:
            with transaction.atomic():
                sales = CommonQuery.query(
                    Sales, request=request, for_update=True, apply_status=True
                ).filter(id=sales_id).first()
                if not sales:
                    raise Exception("Sales record not found")
                if sales.is_reverted:
                    raise Exception("Sales record is already reverted")

                sales_transactions = CommonQuery.query(
                    SalesTransaction, request=request, for_update=True, apply_status=True
                ).filter(sales_id=sales.id)
                if not sales_transactions.exists():
                    raise Exception("No transactions found for sales record")

                return_code = generate_sequential_code(SalesReturn, "return_code", "SRN")
                notes = payload.get("notes") or "Full sales revert"
                sales_return = CommonQuery.createRecord(
                    SalesReturn,
                    {
                        "return_code": return_code,
                        "sales_id": sales.id,
                        "notes": notes,
                    },
                    request,
                )
                sales_return_id = sales_return["id"] if isinstance(sales_return, dict) else sales_return.id

                total_return_amount = Decimal("0.00")
                reverted_lines = []

                for sales_transaction in sales_transactions:
                    remaining_qty = sales_transaction.item_quantity - sales_transaction.returned_quantity
                    if remaining_qty <= 0:
                        continue

                    line_amount = remaining_qty * sales_transaction.item_rate
                    CommonQuery.createRecord(
                        SalesReturnTransaction,
                        {
                            "sales_return_id": sales_return_id,
                            "sales_transaction_id": sales_transaction.id,
                            "item_id": sales_transaction.item_id,
                            "return_quantity": remaining_qty,
                            "item_rate": sales_transaction.item_rate,
                            "total_amount": line_amount,
                        },
                        request,
                    )

                    sales_transaction.returned_quantity = sales_transaction.item_quantity
                    sales_transaction.save(update_fields=["returned_quantity", "updated_at"])

                    InventoryService.apply_stock_movement(
                        request=request,
                        item_id=sales_transaction.item_id,
                        movement_type="SALES_RETURN",
                        quantity=remaining_qty,
                        note=f"Sales revert {sales.sales_code}",
                        reference_type="SALES_REVERT",
                        reference_id=sales.id,
                    )

                    total_return_amount += line_amount
                    reverted_lines.append({
                        "sales_transaction_id": sales_transaction.id,
                        "item_id": sales_transaction.item_id,
                        "return_quantity": remaining_qty,
                        "line_amount": line_amount,
                    })

                CommonQuery.updateRecordById(
                    SalesReturn,
                    sales_return_id,
                    {"total_return_amount": total_return_amount},
                    request,
                )

                sales.total_amount = max(Decimal("0.00"), sales.total_amount - total_return_amount)
                if sales.paid_amount > sales.total_amount:
                    sales.paid_amount = sales.total_amount
                sales.balance_amount = max(Decimal("0.00"), sales.total_amount - sales.paid_amount)
                sales.is_reverted = True
                if sales.notes:
                    sales.notes = f"{sales.notes}\n[REVERTED] {notes}"
                else:
                    sales.notes = f"[REVERTED] {notes}"
                sales.save(update_fields=["total_amount", "paid_amount", "balance_amount", "is_reverted", "notes", "updated_at"])

                if sales.party_id and total_return_amount > 0:
                    SalesService._create_ledger_entry(
                        request=request,
                        party_id=sales.party_id,
                        amount=-total_return_amount,
                        entry_type="RETURN",
                        sales_id=sales.id,
                        reference_type="SALES_REVERT",
                        reference_id=sales.id,
                        note=f"Sales revert {sales.sales_code}",
                    )

                return ResponseBuilder.success(
                    message="Sales reverted successfully",
                    data={
                        "sales_id": sales.id,
                        "sales_code": sales.sales_code,
                        "sales_return_id": sales_return_id,
                        "return_code": sales_return["return_code"] if isinstance(sales_return, dict) else sales_return.return_code,
                        "total_return_amount": total_return_amount,
                        "reverted_lines": reverted_lines,
                    }
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
