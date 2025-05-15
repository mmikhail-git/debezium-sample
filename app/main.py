import uuid
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()


# Модели данных
class OrderCreate(BaseModel):
    customer_id: int
    product_id: int
    quantity: int


class OrderOutboxMessage(BaseModel):
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: dict


# Подключение к БД
def get_db_connection():
    return psycopg2.connect(
        dbname="outbox_db",
        user="postgres",
        password="postgres",
        host="localhost",
        cursor_factory=RealDictCursor
    )


@app.post("/orders/")
def create_order(order: OrderCreate):
    # Генерируем ID заказа
    order_id = str(uuid.uuid4())

    # Создаем событие для outbox
    outbox_message = OrderOutboxMessage(
        aggregate_type="order",
        aggregate_id=order_id,
        event_type="OrderCreated",
        payload={
            "customer_id": order.customer_id,
            "product_id": order.product_id,
            "quantity": order.quantity,
            "order_id": order_id,
            "created_at": datetime.utcnow().isoformat()
        }
    )

    # Сохраняем в транзакции
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # В реальном приложении здесь была бы вставка в таблицу orders
        # cur.execute("INSERT INTO orders (...) VALUES (...)")

        # Вставка в outbox
        cur.execute(
            "INSERT INTO outbox.outbox_message (id, aggregate_type, aggregate_id, event_type, payload) "
            "VALUES (%s, %s, %s, %s, %s)",
            (str(uuid.uuid4()), outbox_message.aggregate_type, outbox_message.aggregate_id,
             outbox_message.event_type, json.dumps(outbox_message.payload)))

        conn.commit()
        return {"message": "Order created", "order_id": order_id}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


@app.get("/outbox/")
def get_outbox_messages():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM outbox.outbox_message ORDER BY created_at DESC")
        return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()