from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://admin:passer@localhost/tour_optimization"

Base = declarative_base()


class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer)
    stop_number = Column(Integer)
    lat = Column(Float)
    lon = Column(Float)
    passengers = Column(Integer)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def create_db():
    Base.metadata.create_all(bind=engine)
