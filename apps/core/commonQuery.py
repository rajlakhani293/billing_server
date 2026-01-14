from django.db.models import Q, Sum, Min, Max, F
import os

class CommonQuery:  
    DEBUG_SQL = os.getenv('DEBUG_SQL', 'false').lower() == 'true'
    
    @staticmethod
    def debug_sql(sql, params=None):
        """Debug SQL logging"""
        if CommonQuery.DEBUG_SQL:
            if params:
                print(f"\033[36m[SQL]\033[0m {sql % tuple(params)}")
            else:
                print(f"\033[36m[SQL]\033[0m {sql}")
    
    @staticmethod
    def getContextData(request=None):
        """Extracts tenant IDs and IP from request"""
        context_data = {'user_id': None, 'shop_id': None, 'ip_address': None}
        if request:
            if hasattr(request, 'user') and request.user.is_authenticated:
                context_data['user_id'] = request.user.id
                shop_id = (
                    request.META.get('HTTP_X_SHOP_ID') or 
                    request.GET.get('shop_id') or
                    getattr(request.user, 'primary_shop_id', None)
                )
                if shop_id:
                    context_data['shop_id'] = int(shop_id)
            context_data['ip_address'] = CommonQuery.getClientIp(request)
        return context_data

    @staticmethod
    def getClientIp(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

    @staticmethod
    def buildWhere(whereInput, apply_defaults=True, request=None):
        """Builds Django Q objects with status and tenant filters"""
        where_q = Q()
        if isinstance(whereInput, list):
            where_q &= Q(id__in=whereInput)
        elif isinstance(whereInput, (str, int)):
            where_q &= Q(id=whereInput)
        elif isinstance(whereInput, dict):
            where_q &= Q(**whereInput)
        
        # Default: Exclude status 2 (deleted)
        if 'status' not in str(where_q):
            where_q &= ~Q(status=2)
        
        if apply_defaults and request:
            ctx = CommonQuery.getContextData(request)
            if ctx['shop_id']: where_q &= Q(shop_id=ctx['shop_id'])
            if ctx['user_id']: where_q &= Q(user_id=ctx['user_id'])
        return where_q

    @staticmethod
    def serializeModelInstance(instance):
        if not instance: return None
        data = {}
        for field in instance._meta.fields:
            val = getattr(instance, field.name)
            data[field.name] = val.isoformat() if hasattr(val, 'isoformat') else val
        return data

    # ------------------------------------------------------------------
    # CRUD OPERATIONS
    # ------------------------------------------------------------------

    @staticmethod
    def createRecord(model, data, request=None, transaction=None, requireTenantFields=True):
        ctx = CommonQuery.getContextData(request)
        enriched = data.copy()
        if requireTenantFields:
            enriched.update({'shop_id': ctx['shop_id'], 'user_id': ctx['user_id']})
        
        with transaction.atomic() if not transaction else transaction.mark_for_rollback_at_column_break():
            result = model.objects.create(**enriched)
        
        return result

    @staticmethod
    def updateRecordById(model, whereInput, data, request=None, requireTenantFields=True):
        where_q = CommonQuery.buildWhere(whereInput, requireTenantFields, request)
        old_record = model.objects.filter(where_q).first()
        if not old_record: return None
        
        model.objects.filter(where_q).update(**data)
        new_record = model.objects.filter(where_q).first()

        return new_record

    @staticmethod
    def softDeleteById(model, whereInput, request=None):
        where_q = CommonQuery.buildWhere(whereInput, True, request)
        records = model.objects.filter(where_q)
        
        count = records.update(status=2)
        return count

    @staticmethod
    def hardDeleteById(model, record_id):
        record = model.objects.filter(id=record_id).first()
        if record:
            record.delete()
            return record
        return None

    # ------------------------------------------------------------------
    # FINDERS & AGGREGATES
    # ------------------------------------------------------------------

    @staticmethod
    def findOneRecord(model, whereInput={}, options={}, request=None):
        where_q = CommonQuery.buildWhere(whereInput, True, request)
        qs = model.objects.filter(where_q)
        if 'select_related' in options: qs = qs.select_related(*options['select_related'])
        if 'prefetch_related' in options: qs = qs.prefetch_related(*options['prefetch_related'])
        return qs.order_by(*options.get('order', [])).first()

    @staticmethod
    def findAllRecords(model, filters={}, options={}, request=None):
        where_q = CommonQuery.buildWhere(filters, True, request)
        qs = model.objects.filter(where_q)
        if 'order' in options: qs = qs.order_by(*options['order'])
        if 'limit' in options:
            offset = options.get('offset', 0)
            qs = qs[offset : offset + options['limit']]
        return list(qs)

    @staticmethod
    def sumRecords(model, field, filters={}, request=None):
        return model.objects.filter(CommonQuery.buildWhere(filters, True, request)).aggregate(s=Sum(field))['s'] or 0

    @staticmethod
    def minRecords(model, field, whereInput={}, request=None):
        return model.objects.filter(CommonQuery.buildWhere(whereInput, True, request)).aggregate(m=Min(field))['m']

    @staticmethod
    def maxRecords(model, field, whereInput={}, request=None):
        return model.objects.filter(CommonQuery.buildWhere(whereInput, True, request)).aggregate(m=Max(field))['m']

    @staticmethod
    def incrementRecords(model, field, by=1, whereInput={}, request=None):
        return model.objects.filter(CommonQuery.buildWhere(whereInput, True, request)).update(**{field: F(field) + by})

    @staticmethod
    def decrementRecords(model, field, by=1, whereInput={}, request=None):
        return model.objects.filter(CommonQuery.buildWhere(whereInput, True, request)).update(**{field: F(field) - by})

    # ------------------------------------------------------------------
    # ADVANCED PAGINATION
    # ------------------------------------------------------------------

    @staticmethod
    def fetchPaginatedData(model, reqBody, fieldConfig, options={}, request=None, dateField="created_at"):
        try:
            page = max(int(reqBody.get('page', 1)), 1)
            limit_val = reqBody.get('limit', 10)
            is_all = str(limit_val).lower() == 'all'
            limit = None if is_all else int(limit_val)
            
            filters_q = CommonQuery.buildWhere(reqBody.get('filter', {}), True, request)
            
            # Status Logic
            status = reqBody.get('status')
            if status and status != 'All':
                filters_q &= Q(status__in=status) if isinstance(status, list) else Q(status=status)
            
            # Date Range
            if reqBody.get('startDate'): filters_q &= Q(**{f"{dateField}__gte": reqBody['startDate']})
            if reqBody.get('endDate'): filters_q &= Q(**{f"{dateField}__lte": reqBody['endDate']})
            
            # Search
            search = reqBody.get('search')
            if search:
                search_q = Q()
                for field in [f[0] for f in fieldConfig if f[1]]:
                    search_q |= Q(**{f"{field}__icontains": search})
                filters_q &= search_q

            qs = model.objects.filter(filters_q)
            total = qs.count()
            
            sort_by = reqBody.get('sortBy', 'created_at')
            prefix = '-' if reqBody.get('sortDirection') == 'descending' else ''
            qs = qs.order_by(f"{prefix}{sort_by}")
            
            if limit: qs = qs[(page-1)*limit : page*limit]
            
            data = list(qs)
            totals = {f: sum(getattr(i, f, 0) or 0 for i in data) for f in (options.get('sumField', []) if isinstance(options.get('sumField'), list) else [options.get('sumField')] if options.get('sumField') else [])}

            return {'items': data, 'total': total, 'totals': totals, 'currentPage': page, 'totalPages': 1 if is_all else (total + limit - 1) // limit}
        except Exception as e:
            raise e

common_query = CommonQuery()