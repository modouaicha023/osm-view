from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import Route, SessionLocal
from vrp_solver import solve_vrp

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/routes")
def get_routes(db: Session = Depends(get_db)):
    return db.query(Route).all()


@router.post("/generate_routes")
def generate_routes(db: Session = Depends(get_db)):
    data = solve_vrp()
    for route in data:
        db_route = Route(**route)
        db.add(db_route)
    db.commit()
    return {"message": "Routes generated"}
