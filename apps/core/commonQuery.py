from django.db.models import Q, Sum, Min, Max, F

class CommonQuery:  
    
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
            pass
        else:
            raise ValueError("Invalid where clause provided")
        
        # --- 2. Apply Shop Filter from JWT ---
        if request and hasattr(request, 'shop_id') and request.shop_id:
            where_q &= Q(shop_id=request.shop_id)
        
        # --- 3. Apply User Filter from JWT ---
        if request and hasattr(request, 'user_id') and request.user_id:
            where_q &= Q(user_id=request.user_id)
        
        # --- 3. Apply Status Filter ---
        if 'status' not in str(where_q):
            where_q &= ~Q(status=2)
                
        return where_q

    @staticmethod
    def serializeModelInstance(instance, includes=None, attributes=None, custom_related_fields=None):
        """
        Serializes a model instance with support for:
        1. Attribute filtering (attributes=[...])
        2. Nested includes (includes={...})
        3. Default ID-only for relations not in includes
        """
        if not instance: return None
        
        # Backward compatibility: map custom_related_fields to includes
        if custom_related_fields and not includes:
            includes = custom_related_fields
        
        includes = includes or {}
        data = {}
        
        # Determine fields to serialize
        fields_to_serialize = instance._meta.fields
        if attributes:
            fields_to_serialize = [f for f in instance._meta.fields if f.name in attributes]
            
        for field in fields_to_serialize:
            try:
                # Handle Relations (Foreign Keys)
                if field.is_relation and field.many_to_one:
                    # Check if included
                    if field.name in includes:
                        related_obj = getattr(instance, field.name)
                        include_config = includes[field.name]
                        
                        # Determine nested attributes and includes
                        nested_attributes = None
                        nested_includes = None
                        
                        if isinstance(include_config, list):
                            # usage: 'shop': ['id', 'name'] -> attributes only
                            nested_attributes = include_config
                        elif isinstance(include_config, dict):
                            # usage: 'shop': {'attributes': [...], 'includes': {...}}
                            nested_attributes = include_config.get('attributes')
                            nested_includes = include_config.get('includes')
                        
                        data[field.name] = CommonQuery.serializeModelInstance(
                            related_obj, 
                            includes=nested_includes, 
                            attributes=nested_attributes
                        )
                    else:
                        # DEFAULT: Return ID only (e.g. shop_id)
                        # field.attname gives the confusing 'shop_id' usually, but field.name is 'shop'.
                        # If we want the actual ID value, we used getattr(instance, field.attname) usually?
                        # Or simply getattr(instance, field.name).id if it exists, but that triggers query if not fetched.
                        # best is getattr(instance, field.attname) which is the underlying ID column.
                        val = getattr(instance, field.attname)
                        data[field.name] = val
                
                # Handle Normal Fields
                else:
                    val = getattr(instance, field.name)
                    if hasattr(val, 'url'):
                        try:
                            data[field.name] = val.url if val and hasattr(val, 'url') else None
                        except (ValueError, AttributeError):
                            data[field.name] = None
                    elif hasattr(val, 'isoformat'):
                        data[field.name] = val.isoformat()
                    else:
                        data[field.name] = val
                        
            except Exception:
                data[field.name] = None
        
        return data

    # ------------------------------------------------------------------
    # CRUD OPERATIONS
    # ------------------------------------------------------------------

    @staticmethod
    def createRecord(model, data, request=None, transaction=None):
        enriched = data.copy()
        
        if request and hasattr(request, 'shop_id') and request.shop_id:
            if hasattr(model, '_meta') and any(field.name == 'shop_id' for field in model._meta.fields):
                shop_field = next((f for f in model._meta.fields if f.name == 'shop_id'), None)
                if shop_field and shop_field.is_relation:
                    from apps.shops.models import Shop
                    try:
                        shop_instance = Shop.objects.get(id=request.shop_id)
                        enriched['shop_id'] = shop_instance
                    except Shop.DoesNotExist:
                        pass
                else:
                    enriched['shop_id'] = request.shop_id
        
        if request and hasattr(request, 'user_id') and request.user_id:
            if hasattr(model, '_meta') and any(field.name == 'user_id' for field in model._meta.fields):
                enriched['user_id'] = request.user_id
        
        if hasattr(model, '_meta'):
            valid_fields = {f.name for f in model._meta.fields}
            enriched = {k: v for k, v in enriched.items() if k in valid_fields}
        
        if transaction:
            with transaction:
                result = model.objects.create(**enriched)
        else:
            from django.db import transaction as db_transaction
            with db_transaction.atomic():
                result = model.objects.create(**enriched)
        
        return result

    @staticmethod
    def updateRecordById(model, whereInput, data, request=None):
        where_q = CommonQuery.buildWhere(whereInput, request)
        
        old_record = model.objects.filter(where_q).first()
        if not old_record: 
            return None
                
        # Filter data to include only valid model fields
        if hasattr(model, '_meta'):
            valid_fields = {f.name for f in model._meta.fields}
            data = {k: v for k, v in data.items() if k in valid_fields}

        # Update the record
        count = model.objects.filter(where_q).update(**data)
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
            # custom_related_fields is legacy/alias for includes
            includes = options.get('includes') or options.get('custom_related_fields')
            attributes = options.get('attributes')
            return CommonQuery.serializeModelInstance(result, includes=includes, attributes=attributes)
        
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
            reqBody = reqBody or {}
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
            
            # Extract dynamic fields (prioritize options if set to act as server-side override, or accept from payload)
            # User wants server-side configuration to be possible.
            attributes = options.get('attributes') or reqBody.get('attributes')
            
            # Extract custom_related_fields
            # Prioritize payload if desired, OR options. The user wants to "set here" (in code), 
            # so options should probably be processed.
            # Let's support both, merging might be complex, so let's check options first (server override) or reqBody.
            dict_config = options.get('includes') or options.get('custom_related_fields') or options.get('related_fields')
            dynamic_related = reqBody.get('custom_related_fields') or reqBody.get('includes') or reqBody.get('related_fields')
            
            final_related = dict_config if dict_config else dynamic_related
            if final_related:
                custom_related_fields = final_related

            # Serialize items for response with custom related fields
            data = [CommonQuery.serializeModelInstance(item, includes=custom_related_fields, attributes=attributes) for item in original_items]
            
            # Calculate totals using original items (ensure fields exist since attributes might hide them)
            # Actually, totals are calculated on original_items which are Model instances, so attributes filtering doesn't affect calculation.
            totals = {f: sum(getattr(i, f, 0) or 0 for i in original_items) for f in (options.get('sumField', []) if isinstance(options.get('sumField'), list) else [options.get('sumField')] if options.get('sumField') else [])}

            return {'items': data, 'total': total, 'totals': totals, 'currentPage': page, 'totalPages': 1 if is_all else (total + limit - 1) // limit}
        except Exception as e:
            raise e

common_query = CommonQuery()