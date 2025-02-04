from sqlalchemy.orm import Session
import models
import schemas

def create_hired_employee(db: Session, employee: schemas.HiredEmployeeCreate):
    db_employee = models.HiredEmployee(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee
