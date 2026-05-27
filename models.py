from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)
    clinics = relationship("Clinic", back_populates="location")


class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    name = Column(String(120), nullable=False)
    location = relationship("Location", back_populates="clinics")
    invoices = relationship("Invoice", back_populates="clinic", cascade="all, delete-orphan")
    payrolls = relationship("Payroll", back_populates="clinic", cascade="all, delete-orphan")
    revenues = relationship("Revenue", back_populates="clinic", cascade="all, delete-orphan")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    number = Column(String(80), nullable=False)
    item = Column(String(180), nullable=False)
    net_amount = Column(Numeric(10, 2), nullable=False)
    gross_amount = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False)
    clinic = relationship("Clinic", back_populates="invoices")


class Payroll(Base):
    __tablename__ = "payrolls"

    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    employee = Column(String(120), nullable=False)
    period = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False)
    clinic = relationship("Clinic", back_populates="payrolls")


class Revenue(Base):
    __tablename__ = "revenues"

    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    company = Column(String(140), nullable=False)
    period = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False)
    clinic = relationship("Clinic", back_populates="revenues")
