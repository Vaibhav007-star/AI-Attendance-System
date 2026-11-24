from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.core.security import get_password_hash
from app.models.user import User
from app.models.department import Department
from app.schemas.user import UserCreate, UserUpdate, UserOut, DepartmentCreate, DepartmentOut

router = APIRouter(prefix="/users", tags=["Users & Departments"])

@router.get("/departments", response_model=List[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    return db.query(Department).order_by(Department.name).all()

@router.post("/departments", response_model=DepartmentOut)
def create_department(dept: DepartmentCreate, db: Session = Depends(get_db)):
    existing = db.query(Department).filter(Department.name == dept.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department already exists")
    db_dept = Department(name=dept.name, code=dept.code.upper(), manager_name=dept.manager_name)
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept

@router.get("", response_model=List[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_term)) |
            (User.employee_id.ilike(search_term)) |
            (User.email.ilike(search_term))
        )
    if department_id:
        query = query.filter(User.department_id == department_id)

    users = query.offset(skip).limit(limit).all()
    for u in users:
        u.has_biometric = u.biometric_profile is not None
    return users

@router.post("", response_model=UserOut)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.employee_id == user_in.employee_id).first():
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    pwd_hash = get_password_hash(user_in.password or "Welcome@123")
    user = User(
        employee_id=user_in.employee_id,
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=pwd_hash,
        phone=user_in.phone,
        designation=user_in.designation,
        role=user_in.role or "employee",
        department_id=user_in.department_id,
        is_active=user_in.is_active
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user.has_biometric = False
    return user

@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.has_biometric = user.biometric_profile is not None
    return user

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, val in user_in.dict(exclude_unset=True).items():
        setattr(user, field, val)

    db.commit()
    db.refresh(user)
    user.has_biometric = user.biometric_profile is not None
    return user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
