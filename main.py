import csv
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from decimal import Decimal
from io import StringIO
from datetime import datetime
from database import get_db
import database
import models
import schemas
import crud
import os
import uvicorn


app = FastAPI()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Obtiene el puerto de Railway o usa 8000 por defecto
    uvicorn.run("main:app", host="0.0.0.0", port=port)

# Crea las tablas en la BD si no existen
models.Base.metadata.create_all(bind=database.engine)

@app.get("/employees/hired-per-quarter", response_class=HTMLResponse)
def hired_per_quarter(db: Session = Depends(get_db)):
    query = text("""
        SELECT 
            d.department AS department,
            j.job AS job,
            SUM(CASE WHEN QUARTER(he.datatime) = 1 THEN 1 ELSE 0 END) AS Q1,
            SUM(CASE WHEN QUARTER(he.datatime) = 2 THEN 1 ELSE 0 END) AS Q2,
            SUM(CASE WHEN QUARTER(he.datatime) = 3 THEN 1 ELSE 0 END) AS Q3,
            SUM(CASE WHEN QUARTER(he.datatime) = 4 THEN 1 ELSE 0 END) AS Q4
        FROM hired_employees he
        JOIN departments d ON he.department_id = d.id
        JOIN jobs j ON he.job_id = j.id
        WHERE YEAR(he.datatime) = 2021
        GROUP BY d.department, j.job
        ORDER BY d.department ASC, j.job ASC;
    """)

    try:
        result = db.execute(query).fetchall()
        
        # tabla HTML
        table_html = """
        <html>
        <head>
            <style>
                table { width: 80%%; margin: auto; border-collapse: collapse; font-family: Arial, sans-serif; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h2 style="text-align:center;">Employees Hired Per Quarter (2021)</h2>
            <table>
                <tr>
                    <th>department</th>
                    <th>job</th>
                    <th>Q1</th>
                    <th>Q2</th>
                    <th>Q3</th>
                    <th>Q4</th>
                </tr>
        """

        for row in result:
            table_html += "<tr>"
            for value in row:
                if isinstance(value, Decimal):
                    value = int(value)
                table_html += f"<td>{value}</td>"
            table_html += "</tr>"

        table_html += "</table></body></html>"

        return HTMLResponse(content=table_html)
    except Exception as e:
        return HTMLResponse(content=f"<h3>Error: {str(e)}</h3>", status_code=500)
    

@app.get("/departments/above-average-hired", response_class=HTMLResponse)
def departments_above_avg_hired(db: Session = Depends(get_db)):
    query = text("""
        SELECT 
            d.id AS id,
            d.department AS department,
            COUNT(he.id) AS hired
        FROM hired_employees he
        JOIN departments d ON he.department_id = d.id
        WHERE YEAR(he.datatime) = 2021
        GROUP BY d.id, d.department
        HAVING COUNT(he.id) > (
            SELECT AVG(hired_count) FROM (
                SELECT COUNT(id) AS hired_count 
                FROM hired_employees 
                WHERE YEAR(datatime) = 2021 
                GROUP BY department_id
            ) AS department_avg
        )
        ORDER BY hired DESC;
    """)

    try:
        result = db.execute(query).fetchall()
        
        # tabla HTML
        table_html = """
        <html>
        <head>
            <style>
                table { width: 60%%; margin: auto; border-collapse: collapse; font-family: Arial, sans-serif; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #3498db; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h2 style="text-align:center;">Departments Above Average Hires (2021)</h2>
            <table>
                <tr>
                    <th>id</th>
                    <th>department</th>
                    <th>hired</th>
                </tr>
        """

        for row in result:
            table_html += "<tr>"
            for value in row:
                if isinstance(value, Decimal):
                    value = int(value) 
                table_html += f"<td>{value}</td>"
            table_html += "</tr>"

        table_html += "</table></body></html>"

        return HTMLResponse(content=table_html)
    except Exception as e:
        return HTMLResponse(content=f"<h3>Error: {str(e)}</h3>", status_code=500)


# Función para cargar los datos de jobs
def load_jobs(file_content: str, db: Session):
    csv_reader = csv.reader(StringIO(file_content))
    for row in csv_reader:
        try:
            # Asegurarse de que la columna "job" esté presente en la fila (no vacía)
            if row:  # Verifica si la fila no está vacía
                job_name = row[1]  
                if not job_name:
                    raise ValueError("Job name cannot be empty")
                job = models.Job(job=job_name)
                db.add(job)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing job: {str(e)}")
    db.commit()

# Función para cargar los datos de departments
def load_departments(file_content: str, db: Session):
    csv_reader = csv.reader(StringIO(file_content))
    for row in csv_reader:
        try:
            # Asegurarse de que la columna "department" esté presente en la fila (no vacía)
            if row:  
                department_name = row[1]  
                if not department_name:
                    raise ValueError("Department name cannot be empty")
                department = models.Department(department=department_name)
                db.add(department)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing department: {str(e)}")
    db.commit()

# Función para cargar los datos de hired_employees
def load_hired_employees(file_content: str, db: Session):
    csv_reader = csv.reader(StringIO(file_content))
    errors = []  # Lista para almacenar errores 
    
    for index, row in enumerate(csv_reader, start=1):  
        try:
            employee_id = int(row[0])  
            name = row[1]
            hire_date = row[2].strip()  
            department_id = int(row[3])
            job_id = int(row[4])
            
            # Validar si la fecha está vacía
            if not hire_date:
                raise ValueError("Fecha de ingreso vacía")

            hire_datetime = datetime.fromisoformat(hire_date)  # Convertir a datetime

            employee = models.HiredEmployee(
                id=employee_id,
                name=name,
                datatime=hire_datetime,
                department_id=department_id,
                job_id=job_id
            )
            db.add(employee)

        except Exception as e:
            errors.append(f"Fila {index}: Error {str(e)}")  # Guardar error en la lista

    db.commit()  # commit después de procesar todas las filas
    
    if errors:
        print("Errores encontrados:")
        for error in errors:
           with open("error_log.txt", "a") as f:
                for error in errors:
                    f.write(error + "\n")



# Endpoint para cargar los tres archivos CSV
@app.post("/upload-csv/")
async def upload_csv(
    jobs_file: UploadFile = File(...),
    departments_file: UploadFile = File(...),
    employees_file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    try:
        # Lee el contenido de los archivos
        jobs_content = await jobs_file.read()
        departments_content = await departments_file.read()
        employees_content = await employees_file.read()

        # Cargar los datos en las tablas respectivas
        load_jobs(jobs_content.decode("utf-8"), db)
        load_departments(departments_content.decode("utf-8"), db)
        load_hired_employees(employees_content.decode("utf-8"), db)

        return {"status": "success", "message": "CSV files processed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV files: {str(e)}")