# curd/write_main_data.py
from sqlalchemy import delete
from sqlalchemy.orm import Session

def delete_processed_orders(session: Session, order_ids: list[int]):
    pass