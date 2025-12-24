# Module Management API Documentation

This document describes the API endpoints for managing Menu Masters and Menu Module Masters in the billing system.

---

## Base URL
```
http://localhost:8000/api
```

## Authentication
All module management endpoints require JWT authentication (except for GET endpoints).

**Headers:**
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

---

# Menu Master APIs

## 1. Get All Menu Masters

**Endpoint:** `GET /menu-master/get-transactions`

**Description:** Retrieve all menu masters (active and inactive, excluding deleted)

**Response:**
```json
{
  "success": true,
  "message": "Data retrieved successfully",
  "data": [
    {
      "id": "uuid-string",
      "menu_name": "Dashboard",
      "cust_menu_name": "Dashboard",
      "priority": 1,
      "menu_icon_name": "dashboard-icon",
      "menu_url": "/dashboard",
      "status": 0,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request

---

## 2. Get Menu Master by ID

**Endpoint:** `GET /menu-master/{menu_id}`

**Description:** Retrieve a specific menu master by ID (excluding deleted)

**Path Parameters:**
- `menu_id` (string, required): UUID of the menu master

**Response:**
```json
{
  "success": true,
  "message": "Data retrieved successfully",
  "data": {
    "id": "uuid-string",
    "menu_name": "Dashboard",
    "cust_menu_name": "Dashboard",
    "priority": 1,
    "menu_icon_name": "dashboard-icon",
    "menu_url": "/dashboard",
    "status": 0,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request
- `404` - Menu not found

**Error Response (404):**
```json
{
  "success": false,
  "message": "Menu not found"
}
```

---

## 3. Create Menu Master

**Endpoint:** `POST /menu-master/`

**Description:** Create a new menu master

**Authentication:** Required

**Request Body:**
```json
{
  "menu_name": "Products",
  "cust_menu_name": "Product Management",
  "priority": 2,
  "menu_icon_name": "products-icon",
  "menu_url": "/products",
  "status": 0
}
```

**Required Fields:**
- `menu_name` (string): Internal menu name
- `cust_menu_name` (string): Custom display name for users

**Optional Fields:**
- `priority` (integer): Display order (default: 0)
- `menu_icon_name` (string): Icon identifier
- `menu_url` (string): URL path for the menu
- `status` (integer): 0=Active, 1=Inactive (default: 0)

**Response (201):**
```json
{
  "success": true,
  "message": "Menu created successfully",
  "data": {
    "id": "new-uuid-string",
    "menu_name": "Products",
    "cust_menu_name": "Product Management",
    "priority": 2,
    "menu_icon_name": "products-icon",
    "menu_url": "/products",
    "status": 0,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  }
}
```

**Status Codes:**
- `201` - Created successfully
- `400` - Bad Request

---

## 4. Update Menu Master

**Endpoint:** `PUT /menu-master/{menu_id}`

**Description:** Update an existing menu master

**Authentication:** Required

**Path Parameters:**
- `menu_id` (string, required): UUID of the menu master

**Request Body:**
```json
{
  "menu_name": "Updated Products",
  "cust_menu_name": "Product Management Updated",
  "priority": 3,
  "menu_icon_name": "updated-icon",
  "menu_url": "/products-updated",
  "status": 1
}
```

**Note:** Only include fields you want to update. All fields are optional.

**Response:**
```json
{
  "success": true,
  "message": "Menu updated successfully",
  "data": {
    "id": "uuid-string",
    "menu_name": "Updated Products",
    "cust_menu_name": "Product Management Updated",
    "priority": 3,
    "menu_icon_name": "updated-icon",
    "menu_url": "/products-updated",
    "status": 1,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T11:00:00Z"
  }
}
```

**Status Codes:**
- `200` - Updated successfully
- `400` - Bad Request
- `404` - Menu not found

---

## 5. Delete Menu Master (Soft Delete)

**Endpoint:** `DELETE /menu-master/{menu_id}`

**Description:** Soft delete a menu master (sets status to 2)

**Authentication:** Required

**Path Parameters:**
- `menu_id` (string, required): UUID of the menu master

**Response:**
```json
{
  "success": true,
  "message": "Menu deleted successfully"
}
```

**Status Codes:**
- `200` - Deleted successfully
- `400` - Bad Request
- `404` - Menu not found

---

# Menu Module Master APIs

## 1. Get All Menu Module Masters

**Endpoint:** `GET /module-master/get-transactions`

**Description:** Retrieve all menu module masters (active and inactive, excluding deleted)

**Response:**
```json
{
  "success": true,
  "message": "Data retrieved successfully",
  "data": [
    {
      "id": "uuid-string",
      "menu": {
        "id": "menu-uuid",
        "menu_name": "Products",
        "cust_menu_name": "Product Management",
        "priority": 2,
        "menu_icon_name": "products-icon",
        "menu_url": "/products",
        "status": 0,
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
      },
      "module_name": "Add Product",
      "cust_module_name": "Add New Product",
      "module_url": "/products/add",
      "module_description": "Add new product to inventory",
      "module_permission_type_ids": "1,2,3",
      "priority": 1,
      "module_icon_name": "add-icon",
      "module_visibility": 1,
      "status": 0,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request

---

## 2. Get Menu Module Master by ID

**Endpoint:** `GET /module-master/{module_id}`

**Description:** Retrieve a specific menu module master by ID (excluding deleted)

**Path Parameters:**
- `module_id` (string, required): UUID of the menu module master

**Response:**
```json
{
  "success": true,
  "message": "Data retrieved successfully",
  "data": {
    "id": "uuid-string",
    "menu": {
      "id": "menu-uuid",
      "menu_name": "Products",
      "cust_menu_name": "Product Management",
      "priority": 2,
      "menu_icon_name": "products-icon",
      "menu_url": "/products",
      "status": 0,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    },
    "module_name": "Add Product",
    "cust_module_name": "Add New Product",
    "module_url": "/products/add",
    "module_description": "Add new product to inventory",
    "module_permission_type_ids": "1,2,3",
    "priority": 1,
    "module_icon_name": "add-icon",
    "module_visibility": 1,
    "status": 0,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request
- `404` - Menu module not found

---

## 3. Create Menu Module Master

**Endpoint:** `POST /module-master/`

**Description:** Create a new menu module master

**Authentication:** Required

**Request Body:**
```json
{
  "menu": "menu-uuid-string",
  "module_name": "Edit Product",
  "cust_module_name": "Edit Existing Product",
  "module_url": "/products/edit",
  "module_description": "Edit existing product details",
  "module_permission_type_ids": "1,2,4",
  "priority": 2,
  "module_icon_name": "edit-icon",
  "module_visibility": 1,
  "status": 0
}
```

**Required Fields:**
- `menu` (string): UUID of parent menu (required)
- `module_name` (string): Internal module name
- `cust_module_name` (string): Custom display name for users
- `module_permission_type_ids` (string): Comma-separated permission IDs
**Optional Fields:**
- `module_url` (string): URL path for the module
- `module_description` (string): Module description
- `priority` (integer): Display order (default: 0)
- `module_icon_name` (string): Icon identifier
- `module_visibility` (integer): 1=Visible, 2=Hidden (default: 1)
- `status` (integer): 0=Active, 1=Inactive (default: 0)

**Response (201):**
```json
{
  "success": true,
  "message": "Module created successfully",
  "data": {
    "id": "new-uuid-string",
    "menu": {
      "id": "menu-uuid",
      "menu_name": "Products",
      "cust_menu_name": "Product Management",
      "priority": 2,
      "menu_icon_name": "products-icon",
      "menu_url": "/products",
      "status": 0,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    },
    "module_name": "Edit Product",
    "cust_module_name": "Edit Existing Product",
    "module_url": "/products/edit",
    "module_description": "Edit existing product details",
    "module_permission_type_ids": "1,2,4",
    "priority": 2,
    "module_icon_name": "edit-icon",
    "module_visibility": 1,
    "status": 0,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  }
}
```

**Status Codes:**
- `201` - Created successfully
- `400` - Bad Request

---

## 4. Update Menu Module Master

**Endpoint:** `PUT /module-master/{module_id}`

**Description:** Update an existing menu module master

**Authentication:** Required

**Path Parameters:**
- `module_id` (string, required): UUID of the menu module master

**Request Body:**
```json
{
  "menu": "updated-menu-uuid",
  "module_name": "Updated Edit Product",
  "cust_module_name": "Updated Edit Existing Product",
  "module_url": "/products/edit-updated",
  "module_description": "Updated description",
  "module_permission_type_ids": "1,2,4,5",
  "priority": 3,
  "module_icon_name": "updated-edit-icon",
  "module_visibility": 2,
  "status": 1
}
```

**Note:** Only include fields you want to update. All fields are optional.

**Response:**
```json
{
  "success": true,
  "message": "Module updated successfully",
  "data": {
    "id": "uuid-string",
    "menu": {
      "id": "updated-menu-uuid",
      "menu_name": "Updated Products",
      "cust_module_name": "Updated Product Management",
      "priority": 2,
      "menu_icon_name": "updated-products-icon",
      "menu_url": "/products-updated",
      "status": 0,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    },
    "module_name": "Updated Edit Product",
    "cust_module_name": "Updated Edit Existing Product",
    "module_url": "/products/edit-updated",
    "module_description": "Updated description",
    "module_permission_type_ids": "1,2,4,5",
    "priority": 3,
    "module_icon_name": "updated-edit-icon",
    "module_visibility": 2,
    "status": 1,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T11:00:00Z"
  }
}
```

**Status Codes:**
- `200` - Updated successfully
- `400` - Bad Request
- `404` - Menu module not found

---

## 5. Delete Menu Module Master (Soft Delete)

**Endpoint:** `DELETE /module-master/{module_id}`

**Description:** Soft delete a menu module master (sets status to 2)

**Authentication:** Required

**Path Parameters:**
- `module_id` (string, required): UUID of the menu module master

**Response:**
```json
{
  "success": true,
  "message": "Module deleted successfully"
}
```

**Status Codes:**
- `200` - Deleted successfully
- `400` - Bad Request
- `404` - Menu module not found

---

# Status Codes Reference

## Menu Status Values
- `0` - Active
- `1` - Inactive
- `2` - Deleted (Soft Delete)

## Module Visibility Values
- `1` - Visible
- `2` - Hidden

## HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

---

# Error Response Format

All error responses follow this format:

```json
{
  "success": false,
  "message": "Error description",
  "errors": {
    "field_name": ["Error details"]
  }
}
```

---

# Soft Delete Behavior

- **GET operations** automatically exclude records with `status=2`
- **PUT/UPDATE operations** cannot modify records with `status=2`
- **DELETE operations** perform soft delete by setting `status=2`
- Deleted records remain in database but are excluded from normal queries
- **Menu relationships** in modules are automatically filtered to exclude deleted menus (status=2)
- **Module operations** require parent menu to be active (status != 2)

---

# Example Usage

## Create Menu with Modules

1. **Create Menu:**
```bash
POST /api/menu-master/
Authorization: Bearer <token>
Content-Type: application/json

{
  "menu_name": "Inventory",
  "cust_menu_name": "Inventory Management",
  "priority": 3,
  "menu_icon_name": "inventory-icon",
  "menu_url": "/inventory",
  "status": 0
}
```

2. **Create Module under Menu:**
```bash
POST /api/module-master/
Authorization: Bearer <token>
Content-Type: application/json

{
  "menu": "menu-uuid-from-step-1",
  "module_name": "Stock Management",
  "cust_module_name": "Manage Stock Levels",
  "module_url": "/inventory/stock",
  "module_description": "Manage product stock levels",
  "module_permission_type_ids": "1,2,3",
  "priority": 1,
  "module_icon_name": "stock-icon",
  "module_visibility": 1,
  "status": 0
}
```

## Get Menu with Modules

```bash
GET /api/module-master/get-transactions
Authorization: Bearer <token>
```

This will return all modules with their parent menu information included.
