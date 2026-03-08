from django.db import transaction
from decimal import Decimal
from apps.core.helpers import ResponseBuilder, generate_sequential_code
from .models import Sales, SalesTransaction, SalesReturn, SalesReturnTransaction
from apps.core.commonQuery import CommonQuery, get_auth_context
from apps.items.service import InventoryService

class SalesService:
    
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
                if not payload.get('paid_amount') or float(payload.get('paid_amount', 0)) <= 0:
                    return ResponseBuilder.error(
                        message="Paid amount is required and must be greater than 0 when payment mode is Partial",
                        status_code=400
                    )
            
            with transaction.atomic():
                # Extract transactions data
                transactions_data = payload.pop('transactions', [])
                
                # Generate Sales Code
                payload['sales_code'] = generate_sequential_code(Sales, 'sales_code', 'SL')
                
                # Create Sales Record
                sales = CommonQuery.createRecord(Sales, payload, request)
                
                # Create Sales Transactions
                for trans_data in transactions_data:
                    trans_data['sales_id'] = sales['id']
                    # Ensure status is active by default if not provided
                    if 'status' not in trans_data:
                        trans_data['status'] = 0
                    CommonQuery.createRecord(SalesTransaction, trans_data, request)
                    InventoryService.apply_stock_movement(
                        request=request,
                        item_id=trans_data['item_id'],
                        movement_type="SALE_STOCK",
                        quantity=trans_data['item_quantity'],
                        note=f"Sales invoice {sales['sales_code']}",
                        reference_type="SALES",
                        reference_id=sales['id'],
                    )
                
                return ResponseBuilder.success(
                    message="Sales created successfully",
                    data=sales
                )
        except Exception as e:
            return ResponseBuilder.error(str(e))

    @staticmethod
    def delete(data, request):
        return ResponseBuilder.error(
            message="Sales delete is disabled to preserve stock audit history",
            status_code=400
        )

    @staticmethod
    def getAll(data, request):
        try:
            # Field configuration: [field_name, is_searchable, is_sortable]
            fieldConfig = [
                ["sales_code", True, True],
                ["party__name", True, True],
                ["total_amount", True, True],
                ["payment_mode", True, True],
                ["sales_date", True, True],
            ]
            
            options = {
                'attributes': [
                    'id', 'sales_code', 'party__name', 'sales_date', 
                    'total_amount', 'paid_amount', 'payment_mode', 'is_reverted', 'status'
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
            ctx = get_auth_context(request)
            sales = Sales.objects.filter(id=sales_id, shop_id=ctx["shop_id"]).first()
            if not sales or sales.status == 2:
                raise Exception("Sales record not found")

            transaction_rows = SalesTransaction.objects.filter(
                sales_id=sales.id,
                shop_id=ctx["shop_id"],
                status=0
            ).select_related("item").order_by("created_at")

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

            returns = SalesReturn.objects.filter(
                sales_id=sales.id,
                shop_id=ctx["shop_id"],
                status=0
            ).prefetch_related("transactions").order_by("-created_at")

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
                "sales_date": sales.sales_date,
                "subtotal": sales.subtotal,
                "tax_amount": sales.tax_amount,
                "discount_percentage": sales.discount_percentage,
                "discount_amount": sales.discount_amount,
                "total_amount": sales.total_amount,
                "paid_amount": sales.paid_amount,
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
            ctx = get_auth_context(request)
            with transaction.atomic():
                sales = Sales.objects.select_for_update().filter(
                    id=sales_id,
                    shop_id=ctx["shop_id"],
                    status=0
                ).first()
                if not sales:
                    raise Exception("Sales record not found")
                if sales.is_reverted:
                    raise Exception("Cannot create return for a reverted sales record")

                transactions_data = payload.get("transactions") or []
                if not transactions_data:
                    raise Exception("At least one return line is required")

                return_code = generate_sequential_code(SalesReturn, "return_code", "SRN")
                sales_return = SalesReturn.objects.create(
                    return_code=return_code,
                    sales=sales,
                    notes=payload.get("notes"),
                    shop_id=ctx["shop_id"],
                )

                total_return_amount = Decimal("0.00")
                created_lines = []

                for row in transactions_data:
                    sales_transaction_id = row.get("sales_transaction_id")
                    return_qty = Decimal(str(row.get("return_quantity")))

                    sales_transaction = SalesTransaction.objects.select_for_update().filter(
                        id=sales_transaction_id,
                        sales_id=sales.id,
                        shop_id=ctx["shop_id"],
                        status=0
                    ).first()
                    if not sales_transaction:
                        raise Exception(f"Sales transaction {sales_transaction_id} not found")

                    remaining_qty = sales_transaction.item_quantity - sales_transaction.returned_quantity
                    if return_qty > remaining_qty:
                        raise Exception(
                            f"Return quantity exceeds available quantity for transaction {sales_transaction_id}"
                        )

                    line_amount = return_qty * sales_transaction.item_rate
                    SalesReturnTransaction.objects.create(
                        sales_return=sales_return,
                        sales_transaction=sales_transaction,
                        item_id=sales_transaction.item_id,
                        return_quantity=return_qty,
                        item_rate=sales_transaction.item_rate,
                        total_amount=line_amount,
                        shop_id=ctx["shop_id"],
                    )

                    sales_transaction.returned_quantity += return_qty
                    sales_transaction.save(update_fields=["returned_quantity", "updated_at"])

                    InventoryService.apply_stock_movement(
                        request=request,
                        item_id=sales_transaction.item_id,
                        movement_type="RETURN_STOCK",
                        quantity=return_qty,
                        note=f"Sales return {return_code}",
                        reference_type="SALES_RETURN",
                        reference_id=sales_return.id,
                    )

                    total_return_amount += line_amount
                    created_lines.append({
                        "sales_transaction_id": sales_transaction.id,
                        "item_id": sales_transaction.item_id,
                        "return_quantity": return_qty,
                        "line_amount": line_amount,
                    })

                sales_return.total_return_amount = total_return_amount
                sales_return.save(update_fields=["total_return_amount", "updated_at"])

                sales.total_amount = max(Decimal("0.00"), sales.total_amount - total_return_amount)
                if sales.paid_amount > sales.total_amount:
                    sales.paid_amount = sales.total_amount
                sales.save(update_fields=["total_amount", "paid_amount", "updated_at"])

                return ResponseBuilder.success(
                    message="Sales return created successfully",
                    data={
                        "sales_return_id": sales_return.id,
                        "return_code": sales_return.return_code,
                        "total_return_amount": total_return_amount,
                        "transactions": created_lines,
                    }
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def revertSale(request, sales_id: int, payload: dict):
        try:
            ctx = get_auth_context(request)
            with transaction.atomic():
                sales = Sales.objects.select_for_update().filter(
                    id=sales_id,
                    shop_id=ctx["shop_id"],
                    status=0
                ).first()
                if not sales:
                    raise Exception("Sales record not found")
                if sales.is_reverted:
                    raise Exception("Sales record is already reverted")

                sales_transactions = SalesTransaction.objects.select_for_update().filter(
                    sales_id=sales.id,
                    shop_id=ctx["shop_id"],
                    status=0
                )
                if not sales_transactions.exists():
                    raise Exception("No transactions found for sales record")

                return_code = generate_sequential_code(SalesReturn, "return_code", "SRN")
                notes = payload.get("notes") or "Full sales revert"
                sales_return = SalesReturn.objects.create(
                    return_code=return_code,
                    sales=sales,
                    notes=notes,
                    shop_id=ctx["shop_id"],
                )

                total_return_amount = Decimal("0.00")
                reverted_lines = []

                for sales_transaction in sales_transactions:
                    remaining_qty = sales_transaction.item_quantity - sales_transaction.returned_quantity
                    if remaining_qty <= 0:
                        continue

                    line_amount = remaining_qty * sales_transaction.item_rate
                    SalesReturnTransaction.objects.create(
                        sales_return=sales_return,
                        sales_transaction=sales_transaction,
                        item_id=sales_transaction.item_id,
                        return_quantity=remaining_qty,
                        item_rate=sales_transaction.item_rate,
                        total_amount=line_amount,
                        shop_id=ctx["shop_id"],
                    )

                    sales_transaction.returned_quantity = sales_transaction.item_quantity
                    sales_transaction.save(update_fields=["returned_quantity", "updated_at"])

                    InventoryService.apply_stock_movement(
                        request=request,
                        item_id=sales_transaction.item_id,
                        movement_type="RETURN_STOCK",
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

                sales_return.total_return_amount = total_return_amount
                sales_return.save(update_fields=["total_return_amount", "updated_at"])

                sales.total_amount = max(Decimal("0.00"), sales.total_amount - total_return_amount)
                if sales.paid_amount > sales.total_amount:
                    sales.paid_amount = sales.total_amount
                sales.is_reverted = True
                if sales.notes:
                    sales.notes = f"{sales.notes}\n[REVERTED] {notes}"
                else:
                    sales.notes = f"[REVERTED] {notes}"
                sales.save(update_fields=["total_amount", "paid_amount", "is_reverted", "notes", "updated_at"])

                return ResponseBuilder.success(
                    message="Sales reverted successfully",
                    data={
                        "sales_id": sales.id,
                        "sales_code": sales.sales_code,
                        "sales_return_id": sales_return.id,
                        "return_code": sales_return.return_code,
                        "total_return_amount": total_return_amount,
                        "reverted_lines": reverted_lines,
                    }
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
