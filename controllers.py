from datetime import date

import pandas as pd
from sqlalchemy import cast, Date, func, or_, select

from database import SessionLocal, init_db
from models import Clinic, Invoice, Location, Payroll, Revenue


class AppController:
    def __init__(self):
        init_db()

    def _session(self):
        return SessionLocal()

    def get_locations(self):
        with self._session() as session:
            return session.scalars(select(Location).order_by(Location.name)).all()

    def get_clinics(self, location_id=None):
        with self._session() as session:
            query = select(Clinic)
            if location_id is not None:
                query = query.where(Clinic.location_id == location_id)
            return session.scalars(query.order_by(Clinic.name)).all()

    def get_invoices(self, clinic_id, start_date=None, end_date=None, search_text=None):
        return self._get_records(Invoice, clinic_id, start_date, end_date, search_text)

    def get_payrolls(self, clinic_id, start_date=None, end_date=None, search_text=None):
        return self._get_records(Payroll, clinic_id, start_date, end_date, search_text)

    def get_revenues(self, clinic_id, start_date=None, end_date=None, search_text=None):
        return self._get_records(Revenue, clinic_id, start_date, end_date, search_text)

    def _get_records(self, model, clinic_id, start_date, end_date, search_text):
        with self._session() as session:
            query = select(model).where(model.clinic_id == clinic_id)
            if start_date:
                query = query.where(model.date >= start_date)
            if end_date:
                query = query.where(model.date <= end_date)
            if search_text:
                search = f"%{search_text}%"
                if model is Invoice:
                    query = query.where(or_(model.number.ilike(search), model.item.ilike(search)))
                elif model is Payroll:
                    query = query.where(model.employee.ilike(search))
                elif model is Revenue:
                    query = query.where(model.company.ilike(search))
            return session.scalars(query.order_by(model.date.desc())).all()

    def _add_record(self, model, clinic_id, values):
        with self._session() as session:
            record = model(clinic_id=clinic_id, **values)
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def add_invoice(self, clinic_id, number, item, net_amount, gross_amount, date):
        return self._add_record(Invoice, clinic_id, {
            "number": number,
            "item": item,
            "net_amount": net_amount,
            "gross_amount": gross_amount,
            "date": date,
        })

    def add_payroll(self, clinic_id, employee, period, amount, date):
        return self._add_record(Payroll, clinic_id, {
            "employee": employee,
            "period": period,
            "amount": amount,
            "date": date,
        })

    def add_revenue(self, clinic_id, company, period, amount, date):
        return self._add_record(Revenue, clinic_id, {
            "company": company,
            "period": period,
            "amount": amount,
            "date": date,
        })

    def update_record(self, model, record_id, data):
        with self._session() as session:
            record = session.get(model, record_id)
            if record is None:
                return None
            for key, value in data.items():
                setattr(record, key, value)
            session.commit()
            session.refresh(record)
            return record

    def delete_record(self, model, record_id):
        with self._session() as session:
            record = session.get(model, record_id)
            if record:
                session.delete(record)
                session.commit()
                return True
            return False

    def get_financial_summary(self, location_id=None, clinic_id=None, start_date=None, end_date=None):
        with self._session() as session:
            invoice_stmt = select(func.coalesce(func.sum(Invoice.net_amount), 0), func.coalesce(func.sum(Invoice.gross_amount), 0))
            payroll_stmt = select(func.coalesce(func.sum(Payroll.amount), 0))
            revenue_stmt = select(func.coalesce(func.sum(Revenue.amount), 0))
            if clinic_id:
                invoice_stmt = invoice_stmt.where(Invoice.clinic_id == clinic_id)
                payroll_stmt = payroll_stmt.where(Payroll.clinic_id == clinic_id)
                revenue_stmt = revenue_stmt.where(Revenue.clinic_id == clinic_id)
            elif location_id:
                clinic_ids = session.scalars(select(Clinic.id).where(Clinic.location_id == location_id)).all()
                invoice_stmt = invoice_stmt.where(Invoice.clinic_id.in_(clinic_ids))
                payroll_stmt = payroll_stmt.where(Payroll.clinic_id.in_(clinic_ids))
                revenue_stmt = revenue_stmt.where(Revenue.clinic_id.in_(clinic_ids))
            if start_date:
                invoice_stmt = invoice_stmt.where(Invoice.date >= start_date)
                payroll_stmt = payroll_stmt.where(Payroll.date >= start_date)
                revenue_stmt = revenue_stmt.where(Revenue.date >= start_date)
            if end_date:
                invoice_stmt = invoice_stmt.where(Invoice.date <= end_date)
                payroll_stmt = payroll_stmt.where(Payroll.date <= end_date)
                revenue_stmt = revenue_stmt.where(Revenue.date <= end_date)
            net_sum, gross_sum = session.execute(invoice_stmt).one()
            payroll_sum = session.execute(payroll_stmt).scalar_one()
            revenue_sum = session.execute(revenue_stmt).scalar_one()
            profit = revenue_sum - payroll_sum - net_sum
            return {
                "invoice_net": float(net_sum),
                "invoice_gross": float(gross_sum),
                "payroll": float(payroll_sum),
                "revenue": float(revenue_sum),
                "profit": float(profit),
            }

    def export_to_excel(self, items, filename):
        df = pd.DataFrame(items)
        if df.empty:
            df = pd.DataFrame(columns=["ID", "Clinic", "Type", "Value"])
        df.to_excel(filename, index=False, engine="openpyxl")

    def get_location_by_name(self, location_name):
        with self._session() as session:
            return session.scalar(select(Location).where(Location.name == location_name))

    def get_clinic_by_name(self, location_id, clinic_name):
        with self._session() as session:
            return session.scalar(select(Clinic).where(Clinic.location_id == location_id, Clinic.name == clinic_name))
