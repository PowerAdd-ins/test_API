from fastapi import FastAPI
from database import SessionLocal, Employee

app = FastAPI()

@app.post("/insert_transactions/")
def insert_transactions(employees: list[dict]):
    session = SessionLocal()
    for emp in employees:
        employee = Employee(
            id=emp['id'], name=emp['name'], datetime=emp['datetime'],
            department_id=emp['department_id'], job_id=emp['job_id']
        )
        session.add(employee)
    session.commit()
    session.close()
    return {"message": "Transactions inserted successfully"}