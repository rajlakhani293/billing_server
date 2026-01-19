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
    def getClientIp(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

    @staticmethod
    def buildWhere(whereInput, request=None):
        """Builds Django Q objects with status and tenant filters"""
        where_q = Q()
        
        # --- 1. Normalize Input ---
        if isinstance(whereInput, list):
            where_q &= Q(id__in=whereInput)
        elif isinstance(whereInput, (str, int)):
            where_q &= Q(id=whereInput)
        elif isinstance(whereInput, dict):
            where_q &= Q(**whereInput)
        elif whereInput is None:
            pass  # Empty where clause
        else:
            raise ValueError("Invalid where clause provided")
        
        # --- 2. Apply Status Filter ---
        if 'status' not in str(where_q):
            where_q &= ~Q(status=2)
                
        return where_q

    @staticmethod
    def serializeModelInstance(instance, custom_related_fields=None):
        if not instance: return None
        data = {}
        
        # Serialize regular fields
        for field in instance._meta.fields:
            try:
                val = getattr(instance, field.name)
                if hasattr(val, 'url'):  # Handle ImageFieldFile and FileField
                    try:
                        data[field.name] = val.url if val and hasattr(val, 'url') else None
                    except (ValueError, AttributeError):
                        # Handle case where file has no associated file or other file-related errors
                        data[field.name] = None
                elif hasattr(val, 'isoformat'):  # Handle datetime objects
                    data[field.name] = val.isoformat()
                else:
                    data[field.name] = val
            except Exception:
                # Handle any other field access errors gracefully
                data[field.name] = None
        
        # Handle foreign key fields (from select_related)
        for field in instance._meta.fields:
            if field.is_relation and field.many_to_one:
                try:
                    related_obj = getattr(instance, field.name)
                    if related_obj:
                        # Check if custom serialization is defined for this field
                        if custom_related_fields and field.name in custom_related_fields:
                            custom_fields = custom_related_fields[field.name]
                            related_data = {}
                            for custom_field in custom_fields:
                                try:
                                    val = getattr(related_obj, custom_field)
                                    if hasattr(val, 'isoformat'):  # Handle datetime objects
                                        related_data[custom_field] = val.isoformat()
                                    else:
                                        related_data[custom_field] = val
                                except Exception:
                                    related_data[custom_field] = None
                            data[field.name] = related_data
                        else:
                            # Default serialization - only basic fields for related objects
                            related_data = {}
                            for related_field in related_obj._meta.fields:
                                if not related_field.is_relation:  # Only serialize non-relational fields
                                    try:
                                        val = getattr(related_obj, related_field.name)
                                        if hasattr(val, 'url'):  # Handle ImageFieldFile and FileField in related objects
                                            try:
                                                related_data[related_field.name] = val.url if val and hasattr(val, 'url') else None
                                            except (ValueError, AttributeError):
                                                # Handle case where file has no associated file
                                                related_data[related_field.name] = None
                                        elif hasattr(val, 'isoformat'):  # Handle datetime objects
                                            related_data[related_field.name] = val.isoformat()
                                        else:
                                            related_data[related_field.name] = val
                                    except Exception:
                                        # Handle any field access errors gracefully
                                        related_data[related_field.name] = None
                            data[field.name] = related_data
                except Exception:
                    # Handle any relation access errors gracefully
                    data[field.name] = None
        
        return data

    # ------------------------------------------------------------------
    # CRUD OPERATIONS
    # ------------------------------------------------------------------

    @staticmethod
    def createRecord(model, data, request=None, transaction=None):
        enriched = data.copy()
        
        with transaction.atomic() if not transaction else transaction.mark_for_rollback_at_column_break():
            result = model.objects.create(**enriched)
        
        return result

    @staticmethod
    def updateRecordById(model, whereInput, data, request=None):
        where_q = CommonQuery.buildWhere(whereInput, request)
        
        old_record = model.objects.filter(where_q).first()
        if not old_record: 
            return None
                
        # Update the record
        count = model.objects.filter(where_q).update(**safe_data)
        if count == 0: 
            return None
        
        new_record = model.objects.filter(where_q).first()
        
        return new_record

    @staticmethod
    def softDeleteById(model, whereInput, request=None):
        where_q = CommonQuery.buildWhere(whereInput, request)
        
        records_to_delete = list(model.objects.filter(where_q))
        if not records_to_delete: 
            return 0
        
        # Soft delete the records
        count = model.objects.filter(where_q).update(status=2)
        
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
        where_q = CommonQuery.buildWhere(whereInput, request)
        qs = model.objects.filter(where_q)
        
        # Handle attributes (field selection)
        if 'attributes' in options:
            if isinstance(options['attributes'], list):
                qs = qs.values(*options['attributes'])
            else:
                qs = qs.values()
        
        # Handle select_related (equivalent to includes in Sequelize)
        elif 'select_related' in options: 
            qs = qs.select_related(*options['select_related'])
        if 'prefetch_related' in options: 
            qs = qs.prefetch_related(*options['prefetch_related'])
            
        result = qs.order_by(*options.get('order', [])).first()
        
        # Auto-serialize if it's a model instance
        if result and hasattr(result, '_meta'):
            custom_related_fields = options.get('custom_related_fields')
            return CommonQuery.serializeModelInstance(result, custom_related_fields)
        
        return result

    @staticmethod
    def findAllRecords(model, filters={}, options={}, request=None):
        where_q = CommonQuery.buildWhere(filters, request)
        qs = model.objects.filter(where_q)
        
        # Handle attributes (field selection)
        if 'attributes' in options:
            if isinstance(options['attributes'], list):
                qs = qs.values(*options['attributes'])
            else:
                qs = qs.values()
        
        # Handle select_related (equivalent to includes in Sequelize)
        elif 'select_related' in options: 
            qs = qs.select_related(*options['select_related'])
        if 'prefetch_related' in options: 
            qs = qs.prefetch_related(*options['prefetch_related'])
        
        # Handle ordering
        if 'order' in options: 
            qs = qs.order_by(*options['order'])
        
        # Handle pagination (skip/limit equivalent to offset/limit)
        if 'skip' in options or 'limit' in options:
            offset = options.get('skip', 0)
            limit = options.get('limit')
            if limit:
                qs = qs[offset : offset + limit]
            elif offset:
                qs = qs[offset:]
        
        result = list(qs)
        
        # Auto-serialize if they are model instances
        if result and result[0] and hasattr(result[0], '_meta'):
            custom_related_fields = options.get('custom_related_fields')
            return [CommonQuery.serializeModelInstance(item, custom_related_fields) for item in result]
        
        return result

    @staticmethod
    def sumRecords(model, field, filters={}, request=None):
        return model.objects.filter(CommonQuery.buildWhere(filters, request)).aggregate(s=Sum(field))['s'] or 0

    @staticmethod
    def minRecords(model, field, whereInput={}, request=None):
        return model.objects.filter(CommonQuery.buildWhere(whereInput, request)).aggregate(m=Min(field))['m']

    @staticmethod
    def maxRecords(model, field, whereInput={}, request=None):
        return model.objects.filter(CommonQuery.buildWhere(whereInput, request)).aggregate(m=Max(field))['m']

    @staticmethod
    def incrementRecords(model, field, by=1, whereInput={}, request=None):
        return model.objects.filter(CommonQuery.buildWhere(whereInput, request)).update(**{field: F(field) + by})

    @staticmethod
    def decrementRecords(model, field, by=1, whereInput={}, request=None):
        return model.objects.filter(CommonQuery.buildWhere(whereInput, request)).update(**{field: F(field) - by})

    # ------------------------------------------------------------------
    # ADVANCED PAGINATION
    # ------------------------------------------------------------------

    @staticmethod
    def fetchPaginatedData(model, reqBody, fieldConfig, options={}, request=None, dateField="created_at", custom_related_fields=None):
        try:
            page = max(int(reqBody.get('page', 1)), 1)
            limit_val = reqBody.get('limit', 10)
            is_all = str(limit_val).lower() == 'all'
            limit = None if is_all else int(limit_val)
            
            filters_q = CommonQuery.buildWhere(reqBody.get('filter', {}), request)
            
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
            
            # Keep original queryset for totals calculation
            original_items = list(qs)
            
            # Serialize items for response with custom related fields
            data = [CommonQuery.serializeModelInstance(item, custom_related_fields) for item in original_items]
            
            # Calculate totals using original items
            totals = {f: sum(getattr(i, f, 0) or 0 for i in original_items) for f in (options.get('sumField', []) if isinstance(options.get('sumField'), list) else [options.get('sumField')] if options.get('sumField') else [])}

            return {'items': data, 'total': total, 'totals': totals, 'currentPage': page, 'totalPages': 1 if is_all else (total + limit - 1) // limit}
        except Exception as e:
            raise e

common_query = CommonQuery()