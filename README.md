## Blacknight Admin

An inventory and order management web application for Blacknight
Merchandise, a startup based in Surulere, Lagos, specializing in
selling digital products within and outside Lagos.

## About

Blacknight Admin is a dashboard for managing inventory and orders.
Product stock counts are automatically kept in sync as orders move
through the system — no manual stock adjustments required for
normal order flow.

## Features

### Inventory management
- Supplier and Product records with full CRUD support

### Order management
- Order and OrderItem records with full CRUD support, enforcing
  business rules (e.g. items can only be modified on pending
  orders; shipped or delivered orders cannot be deleted)
- Order status transitions follow a defined state machine, which
  automatically keeps product stock counts in sync as orders move
  from pending through delivery or cancellation

### Order reports
- Reporting on order activity, including daily/weekly/monthly
  time-series data for order counts and revenue

### Returning order items
- Process returns for items in orders delivered within the past
  14 days

### Filtering and searching
- Search suppliers and products by name
- Filter products by supplier
- Filter orders by status and payment status
- Filter order items by order
- Search order items by product name