from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

class DepartmentBase(BaseModel):
    name: str
    code: str
    manager_name: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentOut(DepartmentBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    employee_id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    designation: Optional[str] = "Staff"
    role: Optional[str] = "employee"
    department_id: Optional[int] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: Optional[str] = "Welcome@123"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None

class UserOut(UserBase):
    id: int
    avatar_path: Optional[str] = None
    has_biometric: bool = False
    created_at: datetime
    department: Optional[DepartmentOut] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
