from pydantic import BaseModel
from datetime import datetime

class HiredEmployeeCreate(BaseModel):
    id: int
    name: str
    datatime: datetime
    department_id: int
    job_id: int

class DepartmentCreate(BaseModel):
    id: int
    department: str

class JobCreate(BaseModel):
    id: int
    job: str
