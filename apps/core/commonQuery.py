from django.db import transaction as db_transaction
from django.db.models import Q, Sum, Case, When, Value, F
from ninja.errors import HttpError
import os
import time
import math # Added math import
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.forms.models import model_to_dict
from datetime import datetime

def uploadFile(files, subfolder="", old_file_name=None):
    """
    Equivalent to your Node uploadFile utility.
    'files' can be a single file object or a list/dict of files.
    """
    if not files:
        return {}

    # 1. Normalize files to a list (Handling req.file vs req.files)
    files_to_process = []
    if isinstance(files, list):
        files_to_process = files
    elif isinstance(files, dict):
        for key in files:
            val = files[key]
            if isinstance(val, list):
                files_to_process.extend(val)
            else:
                files_to_process.append(val)
    else:
        files_to_process = [files]

    saved_filenames = {}
    # baseDir is defined in settings.MEDIA_ROOT (usually 'uploads')
    target_folder = os.path.join(settings.MEDIA_ROOT, subfolder)
    
    # Ensure directory exists (Node's ensureDir)
    os.makedirs(target_folder, exist_ok=True)

    for file in files_to_process:
        # 2. Generate filename: {timestamp}_{name}{ext}
        ext = os.path.splitext(file.name)[1].lower()
        name = os.path.splitext(file.name)[0].replace(" ", "_")
        filename = f"{int(time.time() * 1000)}_{name}{ext}"
        
        full_path = os.path.join(target_folder, filename)

        try:
            # 3. Write file (Node's fs.writeFileSync)
            # Using default_storage handles the write stream for us
            with default_storage.open(os.path.join(subfolder, filename), 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Use fieldname or a default key
            field_name = getattr(file, 'field_name', 'file')
            saved_filenames[field_name] = filename
            
        except Exception as e:
            print(f"File write failed: {e}")
            raise HttpError(500, f"Failed to upload file: {file.name}")

    # 4. Handle Old File Deletion
    if saved_filenames and old_file_name:
        delete_file(subfolder, old_file_name)

    return saved_filenames


def get_auth_context(request):
    user_id = None
    shop_id = None
    
    if isinstance(request.auth, dict):
        user_id = request.auth.get('user').id if request.auth.get('user') else None
        shop_id = request.auth.get('shop').id if request.auth.get('shop') else None
    else:
        # Fallback for object-based auth or legacy
        user_id = getattr(request.auth, 'user_id', None)
        shop_id = getattr(request.auth, 'shop_id', None)
    
    if not user_id or not shop_id:
        raise HttpError(403, "Authentication context missing")
        
    return {"user_id": user_id, "shop_id": shop_id}


def serializeModelInstance(instance):
    if isinstance(instance, dict):
        return instance

    if not instance:
        return None
        
    data = model_to_dict(instance)
    
    # Ensure ID is included (model_to_dict excludes AutoField/primary_key by default)
    if instance.pk:
         data['id'] = instance.pk
    
    # Handle ImageField/FileField specifically
    for field in instance._meta.fields:
        if field.get_internal_type() in ['FileField', 'ImageField']:
            file_obj = getattr(instance, field.name)
            if file_obj:
                # Return relative path or url
                data[field.name] = file_obj.name
            else:
                data[field.name] = None
                
    return data

class CommonQuery:
    @staticmethod
    def getAuthContext(request):
        return get_auth_context(request)

    @staticmethod
    def findOneRecordForUpdate(model, query, options=None, request=None, require_tenant_fields=True):
        filter_kwargs = {}
        model_field_names = [f.name for f in model._meta.get_fields()]

        if isinstance(query, dict):
            for k, v in query.items():
                if "__" not in k and k not in model_field_names:
                    continue
                if isinstance(v, list):
                    filter_kwargs[f"{k}__in"] = v
                else:
                    filter_kwargs[k] = v
        else:
            filter_kwargs["id"] = query

        if "status" in model_field_names:
            has_status_filter = any(k.startswith("status") for k in filter_kwargs.keys())
            if not has_status_filter:
                filter_kwargs["status"] = 0

        if require_tenant_fields and request:
            try:
                ctx = get_auth_context(request)
                if "shop" in model_field_names and "shop_id" not in filter_kwargs:
                    filter_kwargs["shop_id"] = ctx["shop_id"]
            except:
                pass

        queryset = model.objects.select_for_update().filter(**filter_kwargs)

        if options:
            if options.get("select_related"):
                queryset = queryset.select_related(*options["select_related"])
            if options.get("attributes"):
                queryset = queryset.values(*options["attributes"])
                return queryset.first()

        return queryset.first()

    @staticmethod
    def createRecord(model, data, request, require_tenant_fields=True):
        """
        Generic function to enrich data and create a record.
        Mimics your Node.js createRecord.
        """
        enriched_data = {**data}
        
        if require_tenant_fields:
            ctx = get_auth_context(request)
            
            # Get list of fields in the model
            model_fields = [f.name for f in model._meta.get_fields()]
            
            if 'shop' in model_fields:
                enriched_data['shop_id'] = ctx['shop_id']
                
            if 'user' in model_fields:
                enriched_data['user_id'] = ctx['user_id']
            
        result = model.objects.create(**enriched_data)
        return serializeModelInstance(result)

    @staticmethod
    def findOneRecord(model, query, options=None, request=None, require_tenant_fields=True):
        filter_kwargs = {}
        model_field_names = [f.name for f in model._meta.get_fields()]

        # 1. Determine Identity filter
        if isinstance(query, dict):
             for k, v in query.items():
                if "__" not in k and k not in model_field_names:
                     continue
                if isinstance(v, list):
                    filter_kwargs[f"{k}__in"] = v
                else:
                    filter_kwargs[k] = v
        else:
            filter_kwargs['id'] = query
        
      
        if 'status' in model_field_names:
            has_status_filter = any(k.startswith('status') for k in filter_kwargs.keys())
            if not has_status_filter:
                filter_kwargs['status'] = 0

        # 3. Tenant Logic
        if require_tenant_fields and request:
            try:
                ctx = get_auth_context(request)
                if 'shop' in model_field_names and 'shop_id' not in filter_kwargs:
                    filter_kwargs['shop_id'] = ctx['shop_id']
            except:
                pass

        # 4. Execute
        queryset = model.objects.filter(**filter_kwargs)
        
        # Options logic (select_related, attributes)
        if options:
            if options.get('select_related'):
                 queryset = queryset.select_related(*options['select_related'])
            if options.get('attributes'):
                 queryset = queryset.values(*options['attributes'])
                 obj = queryset.first()
                 return obj # values returns dict
        
        obj = queryset.first()
        return serializeModelInstance(obj)

    @staticmethod
    def updateRecordById(model, record_id, data, request, require_tenant_fields=True):
        filter_kwargs = {}
        
        if isinstance(record_id, list):
            filter_kwargs['id__in'] = record_id
            is_bulk = True
        else:
            filter_kwargs['id'] = record_id
            is_bulk = False
        if require_tenant_fields and request:
            try:
                model_fields = [f.name for f in model._meta.get_fields()]
                ctx = get_auth_context(request)
                
                if 'shop' in model_fields:
                    filter_kwargs['shop_id'] = ctx['shop_id']
                if 'user' in model_fields:
                    pass 
            except:
                pass

        obj = model.objects.filter(**filter_kwargs).first()
        
        if not obj:
            return None
            
        # Update fields
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        
        obj.save()
        obj.refresh_from_db()
        
        return serializeModelInstance(obj)

    @staticmethod
    def fetchPaginatedData(model, req_body, field_config, options=None, request=None, require_tenant_fields=True, date_field="created_at", custom_related_fields=None):
        try:
            if options is None:
                options = {}
            
            # Handle JSON parsing if req_body is None and request has JSON body
            if req_body is None and request and hasattr(request, 'content_type') and request.content_type == 'application/json':
                import json
                try:
                    req_body = json.loads(request.body.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                    req_body = {}
            
            if req_body is None:
                req_body = {}
            
            # Standardize config for easy access
            standardized_config = []
            for item in field_config:
                key = item[0]
                searchable = item[1] if len(item) > 1 else False
                sortable = item[2] if len(item) > 2 else False
                standardized_config.append({'key': key, 'searchable': searchable, 'sortable': sortable})

            # Pagination
            page = max(int(req_body.get('page', 1)), 1)
            limit_val = req_body.get('limit')
            is_fetch_all = limit_val in ["all", "All"]
            
            limit = None if is_fetch_all else (int(limit_val) if limit_val else 10)
            offset = 0 if is_fetch_all else (page - 1) * limit

            # Initial QuerySet
            queryset = model.objects.all()
            model_field_names = [f.name for f in model._meta.get_fields()]

            # --- Filtering ---
            filters = Q()

            # A. Status
            status = req_body.get('status')
            if status is not None and status != "All" and 'status' in model_field_names:
                if isinstance(status, list) and status:
                     filters &= Q(status__in=status)
                else:
                    if status in ["Active", "0", 0]:
                        filters &= Q(status=0)
                    elif status in ["Deactive", "1", 1]:
                        filters &= Q(status=1)
                    else:
                        filters &= Q(status=status)
            elif status is None and 'status' in model_field_names:
                 filters &= Q(status=0)

            # B. Filter Object (Exact matches)
            req_filters = req_body.get('filter')
            if req_filters and isinstance(req_filters, dict):
                for k, v in req_filters.items():
                    # Check if field exists to prevent errors
                    # Complex lookups (__) might be valid even if direct name differs, but basic check helps
                    if "__" not in k and k not in model_field_names:
                        continue 
                        
                    if isinstance(v, list) and v:
                        filters &= Q(**{f"{k}__in": v})
                    elif v is not None and v != "":
                         filters &= Q(**{k: v})

            # C. Explicit Tenant Overrides
            if req_body.get('shop_id') and 'shop' in model_field_names: filters &= Q(shop_id=req_body['shop_id'])
            if req_body.get('user_id') and 'user' in model_field_names: filters &= Q(user_id=req_body['user_id'])
            
            # Apply Tenant Context (Automatic)
            if require_tenant_fields and request:
                 try:
                    ctx = get_auth_context(request)
                    if 'shop' in model_field_names and not req_body.get('shop_id'):
                        filters &= Q(shop_id=ctx['shop_id'])
                 except:
                    pass

            # D. Date Range
            start_date = req_body.get('startDate')
            end_date = req_body.get('endDate')
            
            if (start_date or end_date) and date_field in model_field_names:
                if start_date:
                    # Parse ISO date string to datetime object
                    if isinstance(start_date, str):
                        try:
                            from datetime import datetime
                            from dateutil.parser import parse
                            start_date = parse(start_date)
                        except (ImportError, ValueError):
                            # Fallback to basic ISO format parsing
                            try:
                                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            except ValueError:
                                pass  # Keep original string if parsing fails
                    if start_date:
                        filters &= Q(**{f"{date_field}__gte": start_date})
                
                if end_date:
                    # Parse ISO date string to datetime object
                    if isinstance(end_date, str):
                        try:
                            from datetime import datetime
                            from dateutil.parser import parse
                            end_date = parse(end_date)
                        except (ImportError, ValueError):
                            # Fallback to basic ISO format parsing
                            try:
                                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                            except ValueError:
                                pass  # Keep original string if parsing fails
                    if end_date:
                        filters &= Q(**{f"{date_field}__lte": end_date})

            # E. Search
            search_term = req_body.get('search')
            allowed_searchable = [f for f in standardized_config if f['searchable']]
            
            # Determine fields to search on
            req_search_fields = req_body.get('searchFields')
            target_search_keys = []
            
            if req_search_fields:
                 # Filter requested fields to only allowed ones
                 target_search_keys = [key for key in req_search_fields if any(f['key'] == key for f in allowed_searchable)]
            else:
                 target_search_keys = [f['key'] for f in allowed_searchable]

            if search_term and target_search_keys:
                search_q = Q()
                for key in target_search_keys:
                    search_q |= Q(**{f"{key}__icontains": search_term})
                
                filters &= search_q

            # Apply accumulated filters
            queryset = queryset.filter(filters)

            # --- Sorting ---
            sort_by = req_body.get('sortBy')
            sort_dir = req_body.get('sortDirection', 'descending')
            
            sortable_keys = [f['key'] for f in standardized_config if f['sortable']]
            
            if sort_by and sort_by in sortable_keys:
                prefix = "-" if sort_dir == "descending" else ""
                queryset = queryset.order_by(f"{prefix}{sort_by}")
            elif 'created_at' in model_field_names:
                queryset = queryset.order_by("-created_at")

            # --- Aggregates (Totals) ---
            totals = {}
            sum_fields = options.get('sumField')
            if sum_fields:
                aggs = {}
                if isinstance(sum_fields, str):
                    aggs[sum_fields] = Sum(sum_fields)
                elif isinstance(sum_fields, list):
                    for f in sum_fields:
                        aggs[f] = Sum(f)
                
                if aggs:
                    agg_results = queryset.aggregate(**aggs)
                    totals = agg_results

            # --- Count ---
            total_count = queryset.count()

            # --- Pagination Slice ---
            if not is_fetch_all:
                paginated_qs = queryset[offset : offset + limit]
            else:
                paginated_qs = queryset

            # --- Fetch Data & Serialize ---
            
            # Handle attributes (Projection)
            if options.get('attributes'):
                 paginated_qs = paginated_qs.values(*options['attributes'])
            
            # Handle select_related
            elif options.get('select_related'):
                 paginated_qs = paginated_qs.select_related(*options['select_related'])
            
            data = list(paginated_qs)
            serialized_data = []
            
            for obj in data:
                # Use global serializeModelInstance
                record_data = serializeModelInstance(obj)
                
                # Handle custom related fields (Works with both Model Instances and Dictionaries)
                if custom_related_fields:
                     for rel_field, rel_attrs in custom_related_fields.items():
                          if not isinstance(obj, dict):
                              # Handle Model Instance
                              if hasattr(obj, rel_field):
                                           rel_obj = getattr(obj, rel_field)
                                           if rel_obj:
                                                rel_data = {}
                                                for attr in rel_attrs:
                                                     if hasattr(rel_obj, attr):
                                                          rel_data[attr] = getattr(rel_obj, attr)
                                                record_data[rel_field] = rel_data
                                           else:
                                                record_data[rel_field] = None
                          elif rel_field in record_data and record_data[rel_field] is not None:
                              # Handle Dictionary case - need to fetch the related object separately
                              try:
                                  rel_obj_id = record_data[rel_field]
                                  if rel_obj_id:
                                      # Get the related model dynamically
                                      rel_model = obj._meta.get_field(rel_field).remote_field.model
                                      rel_obj = rel_model.objects.get(id=rel_obj_id)
                                      rel_data = {}
                                      for attr in rel_attrs:
                                           if hasattr(rel_obj, attr):
                                                rel_data[attr] = getattr(rel_obj, attr)
                                      record_data[rel_field] = rel_data
                              except:
                                  pass  # Keep original value if fetching fails
                
                serialized_data.append(record_data)


            # --- Response Structure ---
            return {
                "items": serialized_data,
                "total": total_count,
                "totals": totals,
                "currentPage": 1 if is_fetch_all else page,
                "pageSize": total_count if is_fetch_all else limit,
                "totalPages": 1 if is_fetch_all else math.ceil(total_count / (limit or 1)),
                "hasNextPage": False if is_fetch_all else (offset + limit) < total_count,
                "hasPreviousPage": False if is_fetch_all else page > 1,
                "appliedFilters": {
                    **req_body, 
                    "filtersCount": len(req_filters) if req_filters else 0,
                    "searchFields": [f['key'] for f in allowed_searchable],
                    "sortableFields": sortable_keys
                }
            }

        except Exception as err:
            print(f"FetchPaginatedData Error: {err}")
            raise err

    @staticmethod
    def findAllRecords(model, query_filters=None, options=None, request=None, require_tenant_fields=True, transaction=None):

        try:
            if query_filters is None:
                query_filters = {}
            if options is None:
                options = {}
                
            queryset = model.objects.all()
            model_field_names = [f.name for f in model._meta.get_fields()]
            
            # --- Filtering ---
            filters = Q()
            
            # Application Filters
            for k, v in query_filters.items():
                if "__" not in k and k not in model_field_names:
                     continue
                     
                if isinstance(v, list):
                    filters &= Q(**{f"{k}__in": v})
                elif v is not None:
                    filters &= Q(**{k: v})
            
            # Default to status=0 if not specified and field exists
            if 'status' in model_field_names and 'status' not in query_filters:
                filters &= Q(status=0)
                    
            # Tenant Filters
            if require_tenant_fields and request:
                try:
                    ctx = get_auth_context(request)
                    if 'shop' in model_field_names and 'shop_id' not in query_filters and 'shop' not in query_filters:
                        filters &= Q(shop_id=ctx['shop_id'])
                except:
                    pass
            
            queryset = queryset.filter(filters)
            
            # --- Sorting ---
            order = options.get('order')
            if order:
                if isinstance(order, list):
                    queryset = queryset.order_by(*order)
                elif isinstance(order, str):
                    queryset = queryset.order_by(order)
            elif 'created_at' in model_field_names:
                queryset = queryset.order_by('-created_at')
                
            if options.get('select_related'):
                 queryset = queryset.select_related(*options['select_related'])
            
            # --- Offset & Limit ---
            skip = options.get('skip', 0)
            limit = options.get('limit')
            
            if limit:
                queryset = queryset[int(skip) : int(skip) + int(limit)]
            elif skip:
                queryset = queryset[int(skip):]
                
            # --- Projection (Attributes) ---
            if options.get('attributes'):
                return list(queryset.values(*options['attributes']))
                        
            data = []
            for obj in queryset:
                data.append(serializeModelInstance(obj))
                
            return data

        except Exception as e:
            print(f"FindAllRecords Error: {e}")
            raise e

    @staticmethod
    def findAllRecordsForUpdate(model, query_filters=None, options=None, request=None, require_tenant_fields=True):
        try:
            if query_filters is None:
                query_filters = {}
            if options is None:
                options = {}

            queryset = model.objects.select_for_update().all()
            model_field_names = [f.name for f in model._meta.get_fields()]

            filters = Q()
            for k, v in query_filters.items():
                if "__" not in k and k not in model_field_names:
                    continue
                if isinstance(v, list):
                    filters &= Q(**{f"{k}__in": v})
                elif v is not None:
                    filters &= Q(**{k: v})

            if "status" in model_field_names and "status" not in query_filters:
                filters &= Q(status=0)

            if require_tenant_fields and request:
                try:
                    ctx = get_auth_context(request)
                    if "shop" in model_field_names and "shop_id" not in query_filters and "shop" not in query_filters:
                        filters &= Q(shop_id=ctx["shop_id"])
                except:
                    pass

            queryset = queryset.filter(filters)

            order = options.get("order")
            if order:
                if isinstance(order, list):
                    queryset = queryset.order_by(*order)
                elif isinstance(order, str):
                    queryset = queryset.order_by(order)

            if options.get("select_related"):
                queryset = queryset.select_related(*options["select_related"])

            skip = options.get("skip", 0)
            limit = options.get("limit")
            if limit:
                queryset = queryset[int(skip) : int(skip) + int(limit)]
            elif skip:
                queryset = queryset[int(skip) :]

            if options.get("attributes"):
                return list(queryset.values(*options["attributes"]))

            return list(queryset)

        except Exception as e:
            print(f"FindAllRecordsForUpdate Error: {e}")
            raise e

    @staticmethod
    def softDeleteById(model, ids, request):
        if not isinstance(ids, list) or not ids:
            raise Exception("Select at least one record")
            
        filter_kwargs = {
            'id__in': ids,
            'status__in': [0, 1]
        }
        
        if request:
            model_fields = [f.name for f in model._meta.get_fields()]
            if 'shop' in model_fields:
                ctx = get_auth_context(request)
                filter_kwargs['shop_id'] = ctx['shop_id']
        
        return model.objects.filter(**filter_kwargs).update(status=2)

    @staticmethod
    def updateStatusById(model, data, request):
        ids = data.get('ids')
        status = data.get('status')
        
        if not isinstance(ids, list) or not ids:
            raise Exception("Select at least one record")
            
        if status not in [0, 1]:
            raise Exception("Invalid status")
            
        filter_kwargs = {'id__in': ids}
        
        # Tenant Logic
        if request:
            try:
                model_fields = [f.name for f in model._meta.get_fields()]
                if 'shop' in model_fields:
                    ctx = get_auth_context(request)
                    filter_kwargs['shop_id'] = ctx['shop_id']
            except:
                pass
                
        return model.objects.filter(**filter_kwargs).update(status=status)

common_query = CommonQuery()
