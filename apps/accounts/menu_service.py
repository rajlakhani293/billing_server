from apps.accounts.helpers import ResponseBuilder, validate_unique_fields
from .models import MenuMaster, MenuModuleMaster


class MenuService:
    """Helper service class for menu operations"""
    
    @staticmethod
    def getAll():
        """Get all active and inactive menus"""
        try:
            menus = MenuMaster.objects.filter(status__in=[0, 1]).order_by('priority', 'created_at')
            menu_data = [
                {
                    'id': menu.id,
                    'menu_name': menu.menu_name,
                    'cust_menu_name': menu.cust_menu_name,
                    'priority': menu.priority,
                    'menu_icon_name': menu.menu_icon_name,
                    'menu_url': menu.menu_url,
                    'status': menu.status,
                    'created_at': menu.created_at,
                    'updated_at': menu.updated_at
                } for menu in menus
            ]
            return ResponseBuilder.success(
                'Menus retrieved successfully',
                menu_data
            )
        except ValueError as e:
            return ResponseBuilder.error(str(e))
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get menus: {str(e)}')
       
    @staticmethod
    def getById(menu_id: str):
        """Get menu by ID"""
        try:
            menu = MenuMaster.objects.get(id=menu_id)
            menu_data = {
                'id': menu.id,
                'menu_name': menu.menu_name,
                'cust_menu_name': menu.cust_menu_name,
                'priority': menu.priority,
                'menu_icon_name': menu.menu_icon_name,
                'menu_url': menu.menu_url,
                'status': menu.status,
            }
            return ResponseBuilder.success(
                'Menu retrieved successfully',
                menu_data
            )
        except MenuMaster.DoesNotExist:
            return ResponseBuilder.error('Menu not found')
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get menu: {str(e)}')
    
    @staticmethod
    def create(payload: dict):
        """Create new menu"""
        try:
            # Validate unique fields using the new validation function
            validation_config = {
                'model': MenuMaster,
                'fields': ['menu_name', 'cust_menu_name']
            }
            
            is_valid, errors = validate_unique_fields(payload, validation_config)
            if not is_valid:
                # Return the first error (or you could return all errors)
                first_error = list(errors.values())[0]
                return ResponseBuilder.error(first_error)
            
            menu = MenuMaster.objects.create(
                menu_name=payload['menu_name'],
                cust_menu_name=payload['cust_menu_name'],
                priority=payload.get('priority', 0),
                menu_icon_name=payload.get('menu_icon_name'),
                menu_url=payload.get('menu_url'),
                status=payload.get('status', 0)
            )
            menu_data = {
                'id': menu.id,
                'menu_name': menu.menu_name,
                'cust_menu_name': menu.cust_menu_name,
                'priority': menu.priority,
                'menu_icon_name': menu.menu_icon_name,
                'menu_url': menu.menu_url,
                'status': menu.status,
                'created_at': menu.created_at,
                'updated_at': menu.updated_at
            }
            return ResponseBuilder.success(
                'Menu created successfully',
                menu_data
            )
        except Exception as e:
            return ResponseBuilder.error(f'Failed to create menu: {str(e)}')
    
    @staticmethod
    def update(payload: dict):
        """Update menu with provided fields"""
        try:
            menu_id = payload.pop('id')  # Extract id from payload
            menu = MenuMaster.objects.get(id=menu_id)
            
            # Validate unique fields using the new validation function
            validation_config = {
                'model': MenuMaster,
                'fields': ['menu_name', 'cust_menu_name']
            }
            
            is_valid, errors = validate_unique_fields(payload, validation_config, exclude_id=menu_id)
            if not is_valid:
                # Return the first error (or you could return all errors)
                first_error = list(errors.values())[0]
                return ResponseBuilder.error(first_error)
            
            # Update only provided fields
            for field, value in payload.items():
                if value is not None and hasattr(menu, field):
                    setattr(menu, field, value)
            
            menu.save()
            
            menu_data = {
                'id': menu.id,
                'menu_name': menu.menu_name,
                'cust_menu_name': menu.cust_menu_name,
                'priority': menu.priority,
                'menu_icon_name': menu.menu_icon_name,
                'menu_url': menu.menu_url,
                'status': menu.status,
                'created_at': menu.created_at,
                'updated_at': menu.updated_at
            }
            return ResponseBuilder.success(
                'Menu updated successfully',
                menu_data
            )
        except MenuMaster.DoesNotExist:
            return ResponseBuilder.error('Menu not found')
        except Exception as e:
            return ResponseBuilder.error(f'Failed to update menu: {str(e)}')
    
    @staticmethod
    def delete(menu_id: str):
        """Soft delete menu"""
        try:
            menu = MenuMaster.objects.get(id=menu_id)
            menu.status = 2  # Soft delete
            menu.save()
            return ResponseBuilder.success('Menu deleted successfully')
        except MenuMaster.DoesNotExist:
            return ResponseBuilder.error('Menu not found')
        except Exception as e:
            return ResponseBuilder.error(f'Failed to delete menu: {str(e)}')


class MenuModuleService:
    """Helper service class for menu module operations"""
    
    @staticmethod
    def getAll():
        """Get all active and inactive menu modules"""
        try:
            modules = MenuModuleMaster.objects.filter(status__in=[0, 1]).order_by('priority', 'created_at')
            module_data = [
                {
                    'id': module.id,
                    'menu': {
                        'id': module.menu.id,
                        'menu_name': module.menu.menu_name,
                        'cust_menu_name': module.menu.cust_menu_name,
                        'priority': module.menu.priority,
                        'menu_icon_name': module.menu.menu_icon_name,
                        'menu_url': module.menu.menu_url,
                        'status': module.menu.status,
                        'created_at': module.menu.created_at,
                        'updated_at': module.menu.updated_at
                    } if module.menu and module.menu.status != 2 else None,
                    'module_name': module.module_name,
                    'cust_module_name': module.cust_module_name,
                    'module_url': module.module_url,
                    'module_description': module.module_description,
                    'module_permission_type_ids': module.module_permission_type_ids,
                    'priority': module.priority,
                    'module_icon_name': module.module_icon_name,
                    'module_visibility': module.module_visibility,
                    'status': module.status,
                    'created_at': module.created_at,
                    'updated_at': module.updated_at
                } for module in modules
            ]
            return ResponseBuilder.success(
                'Menu modules retrieved successfully',
                module_data
            )
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get menu modules: {str(e)}')
    
    @staticmethod
    def getById(module_id: str):
        """Get menu module by ID"""
        try:
            module = MenuModuleMaster.objects.get(id=module_id)
            module_data = {
                'id': module.id,
                'menu': {
                    'id': module.menu.id,
                    'menu_name': module.menu.menu_name,
                    'cust_menu_name': module.menu.cust_menu_name,
                    'priority': module.menu.priority,
                    'menu_icon_name': module.menu.menu_icon_name,
                    'menu_url': module.menu.menu_url,
                    'status': module.menu.status,
                    'created_at': module.menu.created_at,
                    'updated_at': module.menu.updated_at
                } if module.menu else None,
                'module_name': module.module_name,
                'cust_module_name': module.cust_module_name,
                'module_url': module.module_url,
                'module_description': module.module_description,
                'module_permission_type_ids': module.module_permission_type_ids,
                'priority': module.priority,
                'module_icon_name': module.module_icon_name,
                'module_visibility': module.module_visibility,
                'status': module.status,
                'created_at': module.created_at,
                'updated_at': module.updated_at
            }
            return ResponseBuilder.success(
                'Menu module retrieved successfully',
                module_data
            )
        except MenuModuleMaster.DoesNotExist:
            return ResponseBuilder.error('Menu module not found')
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get menu module: {str(e)}')
    
    @staticmethod
    def create(payload: dict):
        """Create new menu module"""
        try:
            # Validate unique fields using the new validation function
            validation_config = {
                'model': MenuModuleMaster,
                'fields': ['module_name', 'cust_module_name']
            }
            
            is_valid, errors = validate_unique_fields(payload, validation_config)
            if not is_valid:
                # Return the first error (or you could return all errors)
                first_error = list(errors.values())[0]
                return ResponseBuilder.error(first_error)
            
            menu_obj = MenuMaster.objects.get(id=payload['menu'])
            
            module = MenuModuleMaster.objects.create(
                menu=menu_obj,
                module_name=payload['module_name'],
                cust_module_name=payload['cust_module_name'],
                module_url=payload.get('module_url'),
                module_description=payload.get('module_description'),
                module_permission_type_ids=payload['module_permission_type_ids'],
                priority=payload.get('priority', 0),
                module_icon_name=payload.get('module_icon_name'),
                module_visibility=payload.get('module_visibility', 1),
                status=payload.get('status', 0)
            )
            module_data = {
                'id': module.id,
                'menu': {
                    'id': module.menu.id,
                    'menu_name': module.menu.menu_name,
                    'cust_menu_name': module.menu.cust_menu_name,
                    'priority': module.menu.priority,
                    'menu_icon_name': module.menu.menu_icon_name,
                    'menu_url': module.menu.menu_url,
                    'status': module.menu.status,
                } if module.menu else None,
                'module_name': module.module_name,
                'cust_module_name': module.cust_module_name,
                'module_url': module.module_url,
                'module_description': module.module_description,
                'module_permission_type_ids': module.module_permission_type_ids,
                'priority': module.priority,
                'module_icon_name': module.module_icon_name,
                'module_visibility': module.module_visibility,
                'status': module.status
            }
            return ResponseBuilder.success(
                'Menu module created successfully',
                module_data
            )
        except MenuMaster.DoesNotExist:
            return ResponseBuilder.error('Menu not found')
        except Exception as e:
            return ResponseBuilder.error(f'Failed to create menu module: {str(e)}')
    
    @staticmethod
    def update(payload: dict):
        """Update menu module with provided fields (excluding soft deleted)"""
        try:
            module_id = payload.pop('id')  # Extract id from payload
            module = MenuModuleMaster.objects.get(id=module_id, status__in=[0, 1])
            
            # Validate unique fields using the new validation function
            validation_config = {
                'model': MenuModuleMaster,
                'fields': ['module_name', 'cust_module_name']
            }
            
            is_valid, errors = validate_unique_fields(payload, validation_config, exclude_id=module_id)
            if not is_valid:
                # Return the first error (or you could return all errors)
                first_error = list(errors.values())[0]
                return ResponseBuilder.error(first_error)
            
            # Handle menu field separately
            if 'menu' in payload:
                if payload['menu']:
                    menu_obj = MenuMaster.objects.get(id=payload['menu'], status__in=[0, 1])
                    module.menu = menu_obj
                else:
                    module.menu = None
                del payload['menu']
            
            # Update only provided fields
            for field, value in payload.items():
                if value is not None and hasattr(module, field):
                    setattr(module, field, value)
            
            module.save()
            
            module_data = {
                'id': module.id,
                'menu': {
                    'id': module.menu.id,
                    'menu_name': module.menu.menu_name,
                    'cust_menu_name': module.menu.cust_menu_name,
                    'priority': module.menu.priority,
                    'menu_icon_name': module.menu.menu_icon_name,
                    'menu_url': module.menu.menu_url,
                    'status': module.menu.status,
                } if module.menu else None,
                'module_name': module.module_name,
                'cust_module_name': module.cust_module_name,
                'module_url': module.module_url,
                'module_description': module.module_description,
                'module_permission_type_ids': module.module_permission_type_ids,
                'priority': module.priority,
                'module_icon_name': module.module_icon_name,
                'module_visibility': module.module_visibility,
                'status': module.status,
            }
            return ResponseBuilder.success(
                'Menu module updated successfully',
                module_data
            )
        except MenuModuleMaster.DoesNotExist:
            return ResponseBuilder.error('Menu module not found')
        except MenuMaster.DoesNotExist:
            return ResponseBuilder.error('Menu not found')
        except Exception as e:
            return ResponseBuilder.error(f'Failed to update menu module: {str(e)}')
    
    @staticmethod
    def delete(module_id: str):
        """Soft delete menu module (excluding soft deleted)"""
        try:
            module = MenuModuleMaster.objects.get(id=module_id, status__in=[0, 1])
            module.status = 2  # Soft delete
            module.save()
            return ResponseBuilder.success('Menu module deleted successfully')
        except MenuModuleMaster.DoesNotExist:
            return ResponseBuilder.error('Menu module not found')
        except Exception as e:
            return ResponseBuilder.error(f'Failed to delete menu module: {str(e)}')
