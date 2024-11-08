# Neo Challenge - Data Engineering Project

## Quick Start 🚀

### 1. Clone and Setup
Clone repository
```bash
git clone https://github.com/TalalBadreddine/neo_tech_challange
cd neo_challenge
```
Copy environment file
```bash
cp .env.example .env
```
### 2. Start with Docker
Build and start containers
```bash
docker-compose up --build
```

### The application will be running at:
- API: http://localhost:8000/api/
- Admin Dashboard: http://localhost:8000/admin/
- API Documentation: http://localhost:8000/swagger/

### Default admin credentials:
- Username: admin
- Password: adminpass123

## ETL Process 🔄

### 1. Prepare Data Files
Place your data files in the `data/` directory:
- clients.csv
- transactions.csv

### 2. Run ETL Process
The ETL process can be run in two modes: Bulk Processing (default) or Single-Row Processing.

#### 1. Bulk Processing
- Faster performance
- Uses database transactions
- Better for large datasets
- Less memory usage
- Recommended for clean data

```bash
docker-compose exec web python manage.py run_etl \
    --clients-file=data/clients.csv \
    --transactions-file=data/transactions.xlsx
```


#### 2. Single-Row Processing
- Processes one record at a time
- Better error handling per record
- Easier to track problematic records
- Slower performance
- Recommended for data that needs validation

```bash
docker-compose exec web python manage.py run_etl \
    --clients-file=data/clients.csv \
    --transactions-file=data/transactions.xlsx \
    --single-row-processing
```

### 3. Monitor ETL Jobs
1. Via Admin Dashboard:
   - Visit http://localhost:8000/admin/core/etljob/
   - Login with admin credentials
   - View all ETL jobs and their status

2. Via API:
bash
List all jobs
curl http://localhost:8000/api/etl/jobs/
Check specific job
curl http://localhost:8000/api/etl/jobs/<job_id>/


## API Authentication 🔑

### 1. Create User
1. Open Swagger UI: http://localhost:8000/swagger/
2. Navigate to "Users" section
3. Find POST `/api/auth/register` endpoint
4. Click "Try it out"
5. Input user data in the request body:
```json
{
  "username": "user",
  "password": "12345678"
}
```
6. Click "Execute"
7. You should receive a 201 Created response

### 2. Get Authentication Token
1. In Swagger UI, find POST `/api/auth/login/`
2. Click "Try it out"
3. Input credentials:
```json
{
  "username": "user",
  "password": "12345678"
}
```
4. Click "Execute"
5. Copy the `token` from the response:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "username": "user"
  }
}
```
### 3. Use Token in API Requests
1. For any authenticated endpoint in Swagger UI
2. Click "Try it out"
3. In the "Authorization" section:
   - Add Value: `Token <your-access-token>`
   - Example: `Token eyJ0eXAiOiJKV1QiLCJhbGc...`
4. Click "Execute"

### 4. Test Authorization
1. Try GET `/api/clients/<client_id>/transactions/`
2. Add in the Authorization section: `Token <your-access-token>`
3. Add in the client_id in the path params: `412ebc1-f3e2-400b-a1c3-51860cb45c5d`
4. You can add other params to filter the transactions:
- start_date: `2023-01-01`
- end_date: `2024-12-31`

## Troubleshooting 🔧

### ETL Issues

Check file permissions
```bash
docker-compose exec web ls -l /app/data/
```

View ETL job logs
```bash
docker-compose exec web python manage.py shell
>>> from core.models import ETLJob
>>> ETLJob.objects.latest('created_at').error_message
```


## Need Help? 🤔
- Check the logs: `docker-compose logs`
- Visit the admin dashboard
- Review API documentation at `/swagger/`
- Open an issue on GitHub: [Neo Challenge](https://github.com/TalalBadreddine/neo_tech_challange/issues)