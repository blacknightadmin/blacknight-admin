## Blacknight Admin

An inventory and order management web application for Blacknight
Merchandise, a Surulere, Lagos-based bussiness specializing in
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

## Setting up locally

**Prerequisites:** Python 3.12+, Docker, `uv`, `pip`

1. Clone the repo
```bash
   git clone https://github.com/blacknightadmin/blacknight-admin.git
   cd blacknight-admin
```

2. Install dependencies
```bash
   pip install -r requirements.txt
```

3. Start Postgres and pgAdmin
```bash
   docker compose up -d
```

4. Open `127.0.0.1:8080` and log in with the `PGADMIN_DEFAULT_EMAIL` /
   `PGADMIN_DEFAULT_PASSWORD` values from `docker-compose.yml`.

5. Register the Postgres server in pgAdmin:
   - Right-click **Servers** → **Register** → **Server**
   - **General** tab → Name: `db`
   - **Connection** tab → Host: `db`, Username: `postgres`, Password:
     `POSTGRES_PASSWORD` from `docker-compose.yml`

6. Create a dedicated app user:
   - Expand **Servers** dropdown
   - Right-click **db** → **Login/Group Roles** → **Create** → **Login/Group Role**
   - **General** tab → Name: `blacknight`
   - **Definition** tab → Password: your choice
   - **Privileges** tab → check **Can login?** and **Inherit rights from
     the parent roles?**
   - Save

7. Create the app database:
   - Expand **db** dropdown
   - Right-click **Databases** → **Create** → **Database**
   - Name: `blacknight`, Owner: `postgres`
   - Save

8. Grant the app user access:
   - Navigate to **Databases → blacknight → Schemas → public**
   - Right-click → **Properties** → **Security** tab
   - Click + in the **Privileges** tab
   - Add the `blacknight` role as grantee, check **ALL**, Save

9. Create `.env` in the project root:
```env
   DATABASE_URL=postgresql+psycopg2://blacknight:<your_password>@localhost:5433/blacknight
   ADMIN_USERNAME=<your_choice>
   ADMIN_PASSWORD=<your_choice>
   SECRET_KEY=<your_choice>
   SESSION_COOKIE_AGE=300  # seconds before re-login is required
```

10. Run migrations
    ```bash
    alembic upgrade head
    ```

11. Run tests *(optional)*
    ```bash
    pytest test/

12. Run the app
```bash
    uv run fastapi dev
```
