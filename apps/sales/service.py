from django.db import transaction
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
    def _create_ledger_entry(request, party_id, amount, sales_id=None, note=None):
        party = CommonQuery.findOneRecordForUpdate(
            Party, {"id": party_id}, request=request
        )
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

        entry_date = timezone.localdate()
        CommonQuery.createRecord(
            CustomerLedger,
            {
                "party_id": party.id,
                "sales_id": sales_id,
                "amount": amount,
                "date": entry_date,
                "month": entry_date.month,
                "year": entry_date.year,
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
                payload["sales_date"] = timezone.localdate()

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
                if payload.get("payment_mode") == 3 and party_id:
                    due_amount = max(Decimal("0.00"), total_amount - paid_amount)
                    if due_amount > 0:
                        SalesService._create_ledger_entry(
                            request=request,
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
    def getById(sales_id, request):
        try:
            sales = CommonQuery.findOneRecord(
                Sales, {"id": sales_id}, {}, request
            )
            if not sales or sales.get("status") == 2:
                raise Exception("Sales record not found")

            transaction_rows = CommonQuery.findAllRecords(
                SalesTransaction,
                {"sales_id": sales["id"]},
                {
                    "attributes": [
                        "id",
                        "item_id",
                        "item__item_name",
                        "item_quantity",
                        "returned_quantity",
                        "item_rate",
                        "total_amount",
                        "item_description",
                        "discount_percentage",
                        "discount_amount",
                        "tax_amount",
                    ],
                    "order": ["created_at"],
                },
                request,
            )
            transactions = transaction_rows

            returns = CommonQuery.findAllRecords(
                SalesReturn,
                {"sales_id": sales["id"]},
                {"order": ["-created_at"]},
                request,
            )

            return_lines = CommonQuery.findAllRecords(
                SalesReturnTransaction,
                {"sales_return__sales_id": sales["id"]},
                {
                    "attributes": [
                        "id",
                        "sales_return_id",
                        "sales_transaction_id",
                        "item_id",
                        "item__item_name",
                        "return_quantity",
                        "item_rate",
                        "total_amount",
                    ]
                },
                request,
            )

            lines_by_return = {}
            for line in return_lines:
                lines_by_return.setdefault(line["sales_return_id"], []).append({
                    "id": line["id"],
                    "sales_transaction_id": line["sales_transaction_id"],
                    "item_id": line["item_id"],
                    "item_name": line.get("item__item_name"),
                    "return_quantity": line["return_quantity"],
                    "item_rate": line["item_rate"],
                    "total_amount": line["total_amount"],
                })

            returns_data = []
            for sales_return in returns:
                return_id = sales_return["id"] if isinstance(sales_return, dict) else sales_return.get("id")
                returns_data.append({
                    "id": return_id,
                    "return_code": sales_return.get("return_code"),
                    "return_date": sales_return.get("return_date"),
                    "total_return_amount": sales_return.get("total_return_amount"),
                    "notes": sales_return.get("notes"),
                    "transactions": lines_by_return.get(return_id, []),
                })

            sales_data = {
                "id": sales.get("id"),
                "sales_code": sales.get("sales_code"),
                "sales_date": sales.get("sales_date"),
                "party_id": sales.get("party_id"),
                "subtotal": sales.get("subtotal"),
                "tax_amount": sales.get("tax_amount"),
                "discount_percentage": sales.get("discount_percentage"),
                "discount_amount": sales.get("discount_amount"),
                "total_amount": sales.get("total_amount"),
                "paid_amount": sales.get("paid_amount"),
                "balance_amount": sales.get("balance_amount"),
                "payment_mode": sales.get("payment_mode"),
                "notes": sales.get("notes"),
                "is_reverted": sales.get("is_reverted"),
                "status": sales.get("status"),
                "transactions": transactions,
                "returns": returns_data,
            }

            return ResponseBuilder.success(data=sales_data, message="Sales retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getInvoiceView(sales_id, request):
        try:
            sales = CommonQuery.findOneRecord(
                Sales,
                {"id": sales_id},
                {
                    "attributes": [
                        "id",
                        "sales_code",
                        "sales_date",
                        "created_at",
                        "party_id",
                        "shop_id",
                        "subtotal",
                        "tax_amount",
                        "discount_percentage",
                        "discount_amount",
                        "total_amount",
                        "paid_amount",
                        "balance_amount",
                        "payment_mode",
                        "notes",
                        "is_reverted",
                        "status",
                        "party__name",
                        "party__phone_number",
                        "party__email",
                        "party__address",
                        "party__pincode",
                        "party__city__name",
                        "party__state__name",
                        "party__country__name",
                    ]
                },
                request,
            )
            if not sales or sales.get("status") == 2:
                raise Exception("Sales record not found")

            transactions = CommonQuery.findAllRecords(
                SalesTransaction,
                {"sales": sales["id"]},
                {
                    "attributes": [
                        "id",
                        "item_id",
                        "item__item_code",
                        "item__item_name",
                        "item__primary_unit__short_name",
                        "item_quantity",
                        "returned_quantity",
                        "item_rate",
                        "total_amount",
                        "item_description",
                        "discount_percentage",
                        "discount_amount",
                        "tax_amount",
                    ],
                    "order": ["created_at"],
                },
                request,
            )

            returns = CommonQuery.findAllRecords(
                SalesReturn,
                {"sales": sales["id"]},
                {"order": ["-created_at"]},
                request,
            )

            return_lines = CommonQuery.findAllRecords(
                SalesReturnTransaction,
                {"sales_return__sales_id": sales["id"]},
                {
                    "attributes": [
                        "id",
                        "sales_return_id",
                        "sales_transaction_id",
                        "item_id",
                        "item__item_name",
                        "return_quantity",
                        "item_rate",
                        "total_amount",
                    ]
                },
                request,
            )

            lines_by_return = {}
            for line in return_lines:
                lines_by_return.setdefault(line["sales_return_id"], []).append({
                    "id": line["id"],
                    "sales_transaction_id": line["sales_transaction_id"],
                    "item_id": line["item_id"],
                    "item_name": line.get("item__item_name"),
                    "return_quantity": line["return_quantity"],
                    "item_rate": line["item_rate"],
                    "total_amount": line["total_amount"],
                })

            returns_data = []
            for sales_return in returns:
                return_id = sales_return["id"] if isinstance(sales_return, dict) else sales_return.get("id")
                returns_data.append({
                    "id": return_id,
                    "return_code": sales_return.get("return_code"),
                    "return_date": sales_return.get("return_date"),
                    "total_return_amount": sales_return.get("total_return_amount"),
                    "notes": sales_return.get("notes"),
                    "transactions": lines_by_return.get(return_id, []),
                })

            payment_mode_label = dict(Sales.PAYMENT_MODE_CHOICES).get(sales.get("payment_mode"))

            invoice_data = {
                "sales": {
                    "id": sales.get("id"),
                    "sales_code": sales.get("sales_code"),
                    "sales_date": sales.get("sales_date"),
                    "created_at": sales.get("created_at"),
                    "subtotal": sales.get("subtotal"),
                    "tax_amount": sales.get("tax_amount"),
                    "discount_percentage": sales.get("discount_percentage"),
                    "discount_amount": sales.get("discount_amount"),
                    "total_amount": sales.get("total_amount"),
                    "paid_amount": sales.get("paid_amount"),
                    "balance_amount": sales.get("balance_amount"),
                    "payment_mode": sales.get("payment_mode"),
                    "payment_mode_label": payment_mode_label,
                    "notes": sales.get("notes"),
                    "is_reverted": sales.get("is_reverted"),
                    "status": sales.get("status"),
                },
                "party": {
                    "id": sales.get("party_id"),
                    "name": sales.get("party__name"),
                    "phone_number": sales.get("party__phone_number"),
                    "email": sales.get("party__email"),
                    "address": sales.get("party__address"),
                    "pincode": sales.get("party__pincode"),
                    "city": sales.get("party__city__name"),
                    "state": sales.get("party__state__name"),
                    "country": sales.get("party__country__name"),
                },
                "transactions": transactions,
                "returns": returns_data,
            }

            return ResponseBuilder.success(data=invoice_data, message="Sales invoice retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def createReturn(request, sales_id: int, payload: dict):
        try:
            with transaction.atomic():
                sales = CommonQuery.findOneRecordForUpdate(
                    Sales, {"id": sales_id}, request=request
                )
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

                    sales_transaction = CommonQuery.findOneRecordForUpdate(
                        SalesTransaction,
                        {"id": sales_transaction_id, "sales_id": sales.id},
                        request=request,
                    )
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

                if sales.payment_mode == 3 and sales.party_id and total_return_amount > 0:
                    SalesService._create_ledger_entry(
                        request=request,
                        party_id=sales.party_id,
                        amount=-total_return_amount,
                        sales_id=sales.id,
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
                sales = CommonQuery.findOneRecordForUpdate(
                    Sales, {"id": sales_id}, request=request
                )
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

                        sales_transaction = CommonQuery.findOneRecordForUpdate(
                            SalesTransaction,
                            {"id": sales_transaction_id, "sales_id": sales.id},
                            request=request,
                        )
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

                    if sales.payment_mode == 3 and sales.party_id and total_return_amount > 0:
                        SalesService._create_ledger_entry(
                            request=request,
                            party_id=sales.party_id,
                            amount=-total_return_amount,
                            sales_id=sales.id,
                            note=f"Sales return {return_code}",
                        )

                if add_lines:
                    for trans_data in add_lines:
                        item_id = trans_data.get("item_id")
                        item = CommonQuery.findOneRecord(
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

                        CommonQuery.createRecord(
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

                        InventoryService.apply_stock_movement(
                            request=request,
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
                        SalesService._create_ledger_entry(
                            request=request,
                            party_id=sales.party_id,
                            amount=added_total,
                            sales_id=sales.id,
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
            today = timezone.localdate()

            sales_rows = CommonQuery.findAllRecords(
                Sales,
                {},
                {"attributes": ["total_amount", "paid_amount"]},
                request,
            )
            today_sales_rows = CommonQuery.findAllRecords(
                Sales,
                {"sales_date": today},
                {"attributes": ["total_amount", "paid_amount"]},
                request,
            )

            total_sales_count = len(sales_rows)
            total_sales_amount = sum(
                (row.get("total_amount") or Decimal("0.00")) for row in sales_rows
            ) if sales_rows else Decimal("0.00")
            today_sales_count = len(today_sales_rows)
            today_sales_amount = sum(
                (row.get("total_amount") or Decimal("0.00")) for row in today_sales_rows
            ) if today_sales_rows else Decimal("0.00")
            today_collection = sum(
                (row.get("paid_amount") or Decimal("0.00")) for row in today_sales_rows
            ) if today_sales_rows else Decimal("0.00")

            items_rows = CommonQuery.findAllRecords(
                Item,
                {},
                {"attributes": ["current_stock"]},
                request,
            )
            items_count = len(items_rows)
            total_stock = sum(
                (row.get("current_stock") or Decimal("0.00")) for row in items_rows
            ) if items_rows else Decimal("0.00")

            returns_rows = CommonQuery.findAllRecords(
                SalesReturn,
                {},
                {"attributes": ["total_return_amount"]},
                request,
            )
            total_returns_count = len(returns_rows)
            total_returns_amount = sum(
                (row.get("total_return_amount") or Decimal("0.00")) for row in returns_rows
            ) if returns_rows else Decimal("0.00")

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

            today = timezone.localdate()
            if period == "monthly":
                days = int(payload.get("days") or 30)
                start_date = today - timedelta(days=days)
                fmt = "%d %b"
                end_date = today
            elif period == "yearly":
                months = int(payload.get("months") or 12)
                start_date = today - timedelta(days=months * 31)
                fmt = "%b %Y"
                end_date = today
            else:
                hours = int(payload.get("hours") or 24)
                start_date = today
                fmt = "%H:%M"
                end_date = today

            qs = CommonQuery.findAllRecords(
                Sales,
                {
                    "sales_date__gte": start_date,
                    "sales_date__lte": end_date,
                },
                {"attributes": ["sales_date", "created_at", "total_amount"]},
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
                    dt = row.get("created_at")
                    if dt is None:
                        continue
                    if timezone.is_aware(dt):
                        dt = timezone.localtime(dt)
                    key = dt.strftime("%Y-%m-%d %H:00")
                    label = dt.strftime("%I %p")

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

            tx_rows = CommonQuery.findAllRecords(
                SalesTransaction,
                {
                    "sales__status": 0,
                    "sales__is_reverted": False,
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

    @staticmethod
    def revertSale(request, sales_id: int, payload: dict):
        try:
            with transaction.atomic():
                sales = CommonQuery.findOneRecordForUpdate(
                    Sales, {"id": sales_id}, request=request
                )
                if not sales:
                    raise Exception("Sales record not found")
                if sales.is_reverted:
                    raise Exception("Sales record is already reverted")

                sales_transactions = CommonQuery.findAllRecordsForUpdate(
                    SalesTransaction,
                    {"sales_id": sales.id},
                    {},
                    request,
                )
                if not sales_transactions:
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

                if sales.payment_mode == 3 and sales.party_id and total_return_amount > 0:
                    SalesService._create_ledger_entry(
                        request=request,
                        party_id=sales.party_id,
                        amount=-total_return_amount,
                        sales_id=sales.id,
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
