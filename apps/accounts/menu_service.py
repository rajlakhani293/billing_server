from .models import MenuMaster, MenuModuleMaster
from .schema import MenuMasterResponseSchema, MenuModuleMasterResponseSchema


class MenuService:
    """Helper service class for menu operations"""
    
    @staticmethod
    def getAll():
        """Get all active and inactive menus"""
        try:
            menus = MenuMaster.objects.filter(status__in=[0, 1]).order_by('priority', 'created_at')
            return [
                MenuMasterResponseSchema(
                    id=str(menu.id),
                    menu_name=menu.menu_name,
                    cust_menu_name=menu.cust_menu_name,
                    priority=menu.priority,
                    menu_icon_name=menu.menu_icon_name,
                    menu_url=menu.menu_url,
                    status=menu.status,
                    created_at=menu.created_at,
                    updated_at=menu.updated_at
                ) for menu in menus
            ], None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def getById(menu_id: str):
        """Get menu by ID"""
        try:
            menu = MenuMaster.objects.get(id=menu_id)
            return MenuMasterResponseSchema(
                id=str(menu.id),
                menu_name=menu.menu_name,
                cust_menu_name=menu.cust_menu_name,
                priority=menu.priority,
                menu_icon_name=menu.menu_icon_name,
                menu_url=menu.menu_url,
                status=menu.status,
                created_at=menu.created_at,
                updated_at=menu.updated_at
            ), None
        except MenuMaster.DoesNotExist:
            return None, "Menu not found"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def create(menu_name: str, cust_menu_name: str, priority: int = 0, 
                   menu_icon_name: str = None, menu_url: str = None, status: int = 0):
        """Create new menu"""
        try:
            menu = MenuMaster.objects.create(
                menu_name=menu_name,
                cust_menu_name=cust_menu_name,
                priority=priority,
                menu_icon_name=menu_icon_name,
                menu_url=menu_url,
                status=status
            )
            return MenuMasterResponseSchema(
                id=str(menu.id),
                menu_name=menu.menu_name,
                cust_menu_name=menu.cust_menu_name,
                priority=menu.priority,
                menu_icon_name=menu.menu_icon_name,
                menu_url=menu.menu_url,
                status=menu.status,
                created_at=menu.created_at,
                updated_at=menu.updated_at
            ), None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def update(menu_id: str, **kwargs):
        """Update menu with provided fields"""
        try:
            menu = MenuMaster.objects.get(id=menu_id)
            
            # Update only provided fields
            for field, value in kwargs.items():
                if value is not None and hasattr(menu, field):
                    setattr(menu, field, value)
            
            menu.save()
            
            return MenuMasterResponseSchema(
                id=str(menu.id),
                menu_name=menu.menu_name,
                cust_menu_name=menu.cust_menu_name,
                priority=menu.priority,
                menu_icon_name=menu.menu_icon_name,
                menu_url=menu.menu_url,
                status=menu.status,
                created_at=menu.created_at,
                updated_at=menu.updated_at
            ), None
        except MenuMaster.DoesNotExist:
            return None, "Menu not found"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def delete(menu_id: str):
        """Soft delete menu"""
        try:
            menu = MenuMaster.objects.get(id=menu_id)
            menu.status = 2  # Soft delete
            menu.save()
            return True, None
        except MenuMaster.DoesNotExist:
            return False, "Menu not found"
        except Exception as e:
            return False, str(e)


class MenuModuleService:
    """Helper service class for menu module operations"""
    
    @staticmethod
    def getAll():
        """Get all active and inactive menu modules"""
        try:
            modules = MenuModuleMaster.objects.filter(status__in=[0, 1]).order_by('priority', 'created_at')
            return [
                MenuModuleMasterResponseSchema(
                    id=str(module.id),
                    menu=MenuMasterResponseSchema(
                        id=str(module.menu.id),
                        menu_name=module.menu.menu_name,
                        cust_menu_name=module.menu.cust_menu_name,
                        priority=module.menu.priority,
                        menu_icon_name=module.menu.menu_icon_name,
                        menu_url=module.menu.menu_url,
                        status=module.menu.status,
                        created_at=module.menu.created_at,
                        updated_at=module.menu.updated_at
                    ) if module.menu and module.menu.status != 2 else None,
                    module_name=module.module_name,
                    cust_module_name=module.cust_module_name,
                    module_url=module.module_url,
                    module_description=module.module_description,
                    module_permission_type_ids=module.module_permission_type_ids,
                    priority=module.priority,
                    module_icon_name=module.module_icon_name,
                    module_visibility=module.module_visibility,
                    status=module.status,
                    created_at=module.created_at,
                    updated_at=module.updated_at
                ) for module in modules
            ], None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def getById(module_id: str):
        """Get menu module by ID"""
        try:
            module = MenuModuleMaster.objects.get(id=module_id)
            return MenuModuleMasterResponseSchema(
                id=str(module.id),
                menu=MenuMasterResponseSchema(
                    id=str(module.menu.id),
                    menu_name=module.menu.menu_name,
                    cust_menu_name=module.menu.cust_menu_name,
                    priority=module.menu.priority,
                    menu_icon_name=module.menu.menu_icon_name,
                    menu_url=module.menu.menu_url,
                    status=module.menu.status,
                    created_at=module.menu.created_at,
                    updated_at=module.menu.updated_at
                ) if module.menu else None,
                module_name=module.module_name,
                cust_module_name=module.cust_module_name,
                module_url=module.module_url,
                module_description=module.module_description,
                module_permission_type_ids=module.module_permission_type_ids,
                priority=module.priority,
                module_icon_name=module.module_icon_name,
                module_visibility=module.module_visibility,
                status=module.status,
                created_at=module.created_at,
                updated_at=module.updated_at
            ), None
        except MenuModuleMaster.DoesNotExist:
            return None, "Menu module not found"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def create(module_name: str, cust_module_name: str, module_permission_type_ids: str,
                    menu: str, module_url: str = None, module_description: str = None,
                    priority: int = 0, module_icon_name: str = None,
                    module_visibility: int = 1, status: int = 0):
        """Create new menu module"""
        try:
            menu_obj = MenuMaster.objects.get(id=menu)
            
            module = MenuModuleMaster.objects.create(
                menu=menu_obj,
                module_name=module_name,
                cust_module_name=cust_module_name,
                module_url=module_url,
                module_description=module_description,
                module_permission_type_ids=module_permission_type_ids,
                priority=priority,
                module_icon_name=module_icon_name,
                module_visibility=module_visibility,
                status=status
            )
            return MenuModuleMasterResponseSchema(
                id=str(module.id),
                menu=MenuMasterResponseSchema(
                    id=str(module.menu.id),
                    menu_name=module.menu.menu_name,
                    cust_menu_name=module.menu.cust_menu_name,
                    priority=module.menu.priority,
                    menu_icon_name=module.menu.menu_icon_name,
                    menu_url=module.menu.menu_url,
                    status=module.menu.status,
                    created_at=module.menu.created_at,
                    updated_at=module.menu.updated_at
                ) if module.menu else None,
                module_name=module.module_name,
                cust_module_name=module.cust_module_name,
                module_url=module.module_url,
                module_description=module.module_description,
                module_permission_type_ids=module.module_permission_type_ids,
                priority=module.priority,
                module_icon_name=module.module_icon_name,
                module_visibility=module.module_visibility,
                status=module.status,
                created_at=module.created_at,
                updated_at=module.updated_at
            ), None
        except MenuMaster.DoesNotExist:
            return None, "Menu not found"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def update(module_id: str, **kwargs):
        """Update menu module with provided fields (excluding soft deleted)"""
        try:
            module = MenuModuleMaster.objects.get(id=module_id, status__in=[0, 1])
            
            # Handle menu field separately
            if 'menu' in kwargs:
                if kwargs['menu']:
                    menu_obj = MenuMaster.objects.get(id=kwargs['menu'], status__in=[0, 1])
                    module.menu = menu_obj
                else:
                    module.menu = None
                del kwargs['menu']
            
            # Update only provided fields
            for field, value in kwargs.items():
                if value is not None and hasattr(module, field):
                    setattr(module, field, value)
            
            module.save()
            
            return MenuModuleMasterResponseSchema(
                id=str(module.id),
                menu=MenuMasterResponseSchema(
                    id=str(module.menu.id),
                    menu_name=module.menu.menu_name,
                    cust_menu_name=module.menu.cust_menu_name,
                    priority=module.menu.priority,
                    menu_icon_name=module.menu.menu_icon_name,
                    menu_url=module.menu.menu_url,
                    status=module.menu.status,
                    created_at=module.menu.created_at,
                    updated_at=module.menu.updated_at
                ) if module.menu else None,
                module_name=module.module_name,
                cust_module_name=module.cust_module_name,
                module_url=module.module_url,
                module_description=module.module_description,
                module_permission_type_ids=module.module_permission_type_ids,
                priority=module.priority,
                module_icon_name=module.module_icon_name,
                module_visibility=module.module_visibility,
                status=module.status,
                created_at=module.created_at,
                updated_at=module.updated_at
            ), None
        except MenuModuleMaster.DoesNotExist:
            return None, "Menu module not found"
        except MenuMaster.DoesNotExist:
            return None, "Menu not found"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def delete(module_id: str):
        """Soft delete menu module (excluding soft deleted)"""
        try:
            module = MenuModuleMaster.objects.get(id=module_id, status__in=[0, 1])
            module.status = 2  # Soft delete
            module.save()
            return True, None
        except MenuModuleMaster.DoesNotExist:
            return False, "Menu module not found"
        except Exception as e:
            return False, str(e)
