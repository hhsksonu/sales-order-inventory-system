# Sales Order & Inventory Management System

A RESTful backend API built with Django and Django REST Framework for managing products, inventory, dealers, and sales orders with full business logic implementation.

---

## Project Overview

This system simulates a simplified B2B sales order and inventory management platform where:

- Admin can manage products, inventory, and dealers
- Dealers can place orders for products
- System automatically validates and manages stock levels
- Orders follow a strict status flow: Draft → Confirmed → Delivered

---

## Tech Stack

| Component  | Technology                        |
|------------|-----------------------------------|
| Language   | Python 3.12                       |
| Framework  | Django 4.2+ with Django REST Framework |
| Database   | PostgreSQL                        |
| API Format | RESTful JSON APIs                 |
| Config     | python-decouple (.env file)       |

---

## Features Implemented

- Product management with unique SKU
- Auto inventory creation when product is created (Django Signals)
- Dealer management with order history
- Draft order creation with multiple items
- Stock validation before order confirmation
- Stock deduction only on Draft → Confirmed transition
- Atomic transactions to prevent race conditions
- Race-condition-safe order number generation (ORD-YYYYMMDD-XXXX)
- Status transition validation (Draft → Confirmed → Delivered only)
- Confirmed/Delivered orders cannot be edited
- Auto calculation of line_total and total_amount
- Price history preserved via unit_price in OrderItem
- Order filtering by status and dealer
- Order summary/report endpoint
- Protected deletes (cannot delete product/dealer with existing orders)

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/hhsksonu/sales-order-inventory-system.git
cd sales-order-inventory-system
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create PostgreSQL Database

```sql
CREATE DATABASE sales_db;
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=sales_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

### 6. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

### 8. Run the Server

```bash
python manage.py runserver
```

Server will start at `http://127.0.0.1:8000`

---

## Project Structure

```
sales-order-inventory-system/
│
├── sales_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── orders/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
│
├── .env                  ← not committed
├── .env.example          ← committed
├── .gitignore
├── manage.py
└── requirements.txt
```

---

## API Documentation

Base URL: `http://127.0.0.1:8000/api`

---

### Products

#### GET /api/products/
List all products with stock info.

**Response 200:**
```json
[
    {
        "id": 1,
        "name": "Brake Pad",
        "sku": "BP-001",
        "description": "High quality brake pad",
        "price": "500.00",
        "stock_quantity": 100,
        "created_at": "2026-03-12T10:00:00Z",
        "updated_at": "2026-03-12T10:00:00Z"
    }
]
```

#### POST /api/products/
Create a new product. Inventory record is auto-created with quantity 0.

**Request Body:**
```json
{
    "name": "Brake Pad",
    "sku": "BP-001",
    "description": "High quality brake pad",
    "price": "500.00"
}
```

**Response 201:**
```json
{
    "id": 1,
    "name": "Brake Pad",
    "sku": "BP-001",
    "description": "High quality brake pad",
    "price": "500.00",
    "stock_quantity": 0,
    "created_at": "2026-03-12T10:00:00Z",
    "updated_at": "2026-03-12T10:00:00Z"
}
```

#### GET /api/products/{id}/
Get single product details.

#### PUT /api/products/{id}/
Update a product.

**Request Body:**
```json
{
    "name": "Brake Pad Premium",
    "sku": "BP-001",
    "description": "Premium quality brake pad",
    "price": "600.00"
}
```

#### DELETE /api/products/{id}/
Delete a product. Fails if product has existing orders.

**Error Response 400:**
```json
{
    "error": "Cannot delete this product because it has existing orders."
}
```

---

### Inventory

#### GET /api/inventory/
List all inventory levels.

**Response 200:**
```json
[
    {
        "id": 1,
        "product": 1,
        "product_name": "Brake Pad",
        "quantity": 100,
        "updated_at": "2026-03-12T10:00:00Z"
    }
]
```

#### PUT /api/inventory/{product_id}/
Update stock quantity for a product. Only quantity field is accepted.

**Request Body:**
```json
{
    "quantity": 100
}
```

---

### Dealers

#### GET /api/dealers/
List all dealers.

#### POST /api/dealers/
Create a new dealer.

**Request Body:**
```json
{
    "name": "ABC Motors",
    "email": "abc@motors.com",
    "phone": "9876543210",
    "address": "123 Main Street, Mumbai"
}
```

**Response 201:**
```json
{
    "id": 1,
    "name": "ABC Motors",
    "email": "abc@motors.com",
    "phone": "9876543210",
    "address": "123 Main Street, Mumbai",
    "orders": [],
    "created_at": "2026-03-12T10:00:00Z"
}
```

#### GET /api/dealers/{id}/
Get dealer details including their order history.

**Response 200:**
```json
{
    "id": 1,
    "name": "ABC Motors",
    "email": "abc@motors.com",
    "phone": "9876543210",
    "address": "123 Main Street, Mumbai",
    "orders": [
        {
            "id": 1,
            "order_number": "ORD-20260312-0001",
            "status": "Confirmed",
            "total_amount": "5000.00",
            "created_at": "2026-03-12T10:00:00Z"
        }
    ],
    "created_at": "2026-03-12T10:00:00Z"
}
```

#### PUT /api/dealers/{id}/
Update dealer details.

#### DELETE /api/dealers/{id}/
Delete a dealer. Fails if dealer has existing orders.

---

### Orders

#### GET /api/orders/
List all orders. Supports filters:
- `?status=Draft` — filter by status
- `?dealer_id=1` — filter by dealer

#### POST /api/orders/
Create a new draft order with items.

**Request Body:**
```json
{
    "dealer": 1,
    "items": [
        {
            "product": 1,
            "quantity": 10,
            "unit_price": "500.00"
        },
        {
            "product": 2,
            "quantity": 5,
            "unit_price": "350.00"
        }
    ]
}
```

**Response 201:**
```json
{
    "id": 1,
    "order_number": "ORD-20260312-0001",
    "dealer": 1,
    "dealer_name": "ABC Motors",
    "status": "Draft",
    "total_amount": "6750.00",
    "items": [
        {
            "id": 1,
            "product": 1,
            "product_name": "Brake Pad",
            "quantity": 10,
            "unit_price": "500.00",
            "line_total": "5000.00"
        },
        {
            "id": 2,
            "product": 2,
            "product_name": "Engine Oil",
            "quantity": 5,
            "unit_price": "350.00",
            "line_total": "1750.00"
        }
    ],
    "created_at": "2026-03-12T10:00:00Z",
    "updated_at": "2026-03-12T10:00:00Z"
}
```

#### GET /api/orders/{id}/
Get order details with all items.

#### PUT /api/orders/{id}/
Update a Draft order. Confirmed/Delivered orders cannot be edited.

**Error Response 400:**
```json
{
    "error": "Cannot edit an order with status 'Confirmed'."
}
```

#### POST /api/orders/{id}/confirm/
Confirm a draft order. Validates stock for all items and deducts stock atomically.

**Response 200:**
```json
{
    "message": "Order confirmed successfully."
}
```

**Error Response 400 (insufficient stock):**
```json
{
    "error": "Insufficient stock for 'Brake Pad'. Available: 5, Requested: 10."
}
```

#### POST /api/orders/{id}/deliver/
Mark a confirmed order as delivered.

**Response 200:**
```json
{
    "message": "Order marked as delivered successfully."
}
```

#### GET /api/orders/{id}/summary/
Get a full order summary report.

**Response 200:**
```json
{
    "order_number": "ORD-20260312-0001",
    "dealer": "ABC Motors",
    "status": "Delivered",
    "total_items": 2,
    "total_amount": "6750.00",
    "items": [
        {
            "product": "Brake Pad",
            "quantity": 10,
            "unit_price": "500.00",
            "line_total": "5000.00"
        }
    ],
    "created_at": "2026-03-12T10:00:00Z"
}
```

---

## Business Rules

### Order Status Flow
```
Draft → Confirmed → Delivered
```
- Any other transition is rejected with an error
- Draft: order can be edited freely
- Confirmed: stock is deducted, order is locked
- Delivered: final state, order is complete

### Stock Management
- Stock is only deducted when order moves from Draft → Confirmed
- If any item has insufficient stock, the entire confirmation is rejected
- Atomic transactions prevent race conditions during confirmation
- Manual stock corrections via `PUT /api/inventory/{product_id}/`

### Auto Calculations
- `line_total = quantity × unit_price` (calculated on save)
- `total_amount = sum of all line_totals` (recalculated on every change)
- `order_number` is auto-generated in format `ORD-YYYYMMDD-XXXX`

---

## Assumptions Made

1. Authentication and authorization are not implemented — all endpoints are publicly accessible. In production, token-based auth would be added.
2. Unit price is sent by the client when creating order items to preserve price history. In production this could be auto-filled from the product price.
3. Stock can only be manually adjusted via the inventory endpoint — there is no automatic restocking.
4. Deleting a confirmed order does not restore stock (basic implementation).
5. A dealer cannot be deleted if they have existing orders.
6. A product cannot be deleted if it has been ordered.
7. Inventory record is automatically created with quantity 0 when a new product is added.

---

## Sample Test Scenarios

### Scenario 1: Successful Order Flow
```
1. POST /api/products/         → Create "Brake Pad" at ₹500
2. PUT  /api/inventory/1/      → Set stock to 100
3. POST /api/dealers/          → Create "ABC Motors"
4. POST /api/orders/           → Create draft with 10 Brake Pads
5. POST /api/orders/1/confirm/ → Stock reduces to 90
6. POST /api/orders/1/deliver/ → Order complete
```

### Scenario 2: Insufficient Stock
```
1. Product has 5 units in stock
2. POST /api/orders/ with quantity 10
3. POST /api/orders/2/confirm/
→ Error: "Insufficient stock for 'Brake Pad'. Available: 5, Requested: 10."
```

### Scenario 3: Invalid Status Transition
```
POST /api/orders/1/confirm/  (order already confirmed)
→ Error: "Only Draft orders can be confirmed."
```
