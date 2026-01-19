from apps.core.helpers import ResponseBuilder
from .models import MenuMaster, MenuModuleMaster


class MenuService:
    
    @staticmethod
    def get_menus_with_modules() -> dict:
        """Get all active menus with their modules"""
        try:
            # Get all active menus ordered by priority
            menus = MenuMaster.objects.filter(
                status=0  # Active status
            ).order_by('priority', 'created_at')
            
            menu_data = []
            for menu in menus:
                # Get active modules for this menu
                modules = MenuModuleMaster.objects.filter(
                    menu=menu,
                    status=0,  # Active status
                    module_visibility=1  # Visible
                ).order_by('priority', 'created_at')
                
                # Build menu object with modules
                menu_obj = {
                    'id': menu.id,
                    'menu_name': menu.menu_name,
                    'cust_menu_name': menu.cust_menu_name,
                    'priority': menu.priority,
                    'menu_icon_name': menu.menu_icon_name,
                    'menu_url': menu.menu_url,
                    'modules': []
                }
                
                # Add modules to menu
                for module in modules:
                    module_obj = {
                        'id': module.id,
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
                    menu_obj['modules'].append(module_obj)
                
                menu_data.append(menu_obj)
            
            return ResponseBuilder.success(
                'Menus retrieved successfully',
                menu_data
            )
            
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get menus: {str(e)}')
    
    @staticmethod
    def get_menu_by_id(menu_id: int) -> dict:
        """Get a specific menu with its modules"""
        try:
            menu = MenuMaster.objects.filter(
                id=menu_id,
                status=0  # Active status
            ).first()
            
            if not menu:
                return ResponseBuilder.error('Menu not found')
            
            # Get active modules for this menu
            modules = MenuModuleMaster.objects.filter(
                menu=menu,
                status=0,  # Active status
                module_visibility=1  # Visible
            ).order_by('priority', 'created_at')
            
            # Build menu object with modules
            menu_obj = {
                'id': menu.id,
                'menu_name': menu.menu_name,
                'cust_menu_name': menu.cust_menu_name,
                'priority': menu.priority,
                'menu_icon_name': menu.menu_icon_name,
                'menu_url': menu.menu_url,
                'status': menu.status,
                'modules': []
            }
            
            # Add modules to menu
            for module in modules:
                module_obj = {
                    'id': module.id,
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
                menu_obj['modules'].append(module_obj)
            
            return ResponseBuilder.success(
                'Menu retrieved successfully',
                menu_obj
            )
            
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get menu: {str(e)}')
    
    @staticmethod
    def get_all_menus() -> dict:
        """Get all active menus without modules (for dropdown/list)"""
        try:
            menus = MenuMaster.objects.filter(
                status=0  # Active status
            ).order_by('priority', 'created_at')
            
            menu_list = []
            for menu in menus:
                menu_obj = {
                    'id': menu.id,
                    'menu_name': menu.menu_name,
                    'cust_menu_name': menu.cust_menu_name,
                    'priority': menu.priority,
                    'menu_icon_name': menu.menu_icon_name,
                    'menu_url': menu.menu_url,
                    'status': menu.status
                }
                menu_list.append(menu_obj)
            
            return ResponseBuilder.success(
                'Menus list retrieved successfully',
                menu_list
            )
            
        except Exception as e:
            return ResponseBuilder.error(f'Failed to get menus list: {str(e)}')
