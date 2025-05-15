# Transactional Outbox и Debezium #

Реализация паттерна Transactional Outbox с использованием:
- PostgreSQL
- Debezium для отслеживания изменений
- Kafka в качестве брокера сообщений
- Python (FastAPI) для основного приложения

Поток данных:
[Python App] → [PostgreSQL (outbox_message)] → [Debezium] → [Kafka] → [Consumer]

1. После запуска инфраструктуры (docker-compose up -d), создаем коннектор:

```
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" \
http://localhost:8083/connectors/outbox-connector/config -d @- <<EOF
{
  "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
  "database.hostname": "postgres",
  "database.port": "5432",
  "database.user": "postgres",
  "database.password": "postgres",
  "database.dbname": "outbox_db",
  "database.server.name": "outbox-server",
  "table.include.list": "outbox.outbox_message",
  "plugin.name": "pgoutput",
  "tombstones.on.delete": "false",
  "transforms": "outbox",
  "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
  "transforms.outbox.route.by.field": "aggregate_type",
  "transforms.outbox.route.topic.replacement": "outbox.events.\${routedByValue}",
  "transforms.outbox.table.field.event.id": "id",
  "transforms.outbox.table.field.event.key": "aggregate_id",
  "transforms.outbox.table.field.event.type": "event_type",
  "transforms.outbox.table.field.event.payload": "payload",
  "transforms.outbox.field.event.timestamp": "created_at",
  "transforms.outbox.field.event.timestamp.encoding": "string",
  "transforms.outbox.field.event.timestamp.format": "ISO_DATE_TIME",
  "transforms.outbox.table.fields.additional.placement": "event_type:header:event_type",
  "transforms.outbox.route.by.field": "aggregate_type"
}
EOF
```

2. Устанавливаем зависимости `pip install -r requirements.txt`

2. Запускаем приложение:
`uvicorn app.main:app --reload`

3. Создаем заказ:
```
curl -X POST "http://localhost:8000/orders/" \
-H "Content-Type: application/json" \
-d '{"customer_id": 1, "product_id": 101, "quantity": 2}'
```
4. Запускаем консьюмера:
`python consumer.py`

---

Как это работает:
* Приложение получает запрос на создание заказа
* В одной транзакции:
  - (В реальном приложении) сохраняются данные заказа
  - Сохраняется событие в outbox таблицу
* Debezium обнаруживает изменение в outbox таблице
* Трансформация EventRouter преобразует запись в формат события
* Событие публикуется в Kafka топик outbox.events.order
* Потребитель получает и обрабатывает событие


Преимущества паттерна Transaction Outbox:

- Гарантированная доставка: Событие не потеряется, даже если Kafka временно недоступна
- Транзакционность: Данные и событие сохраняются атомарно
- Масштабируемость: Можно добавлять новые потребители без изменения основного приложения
- Гибкость: Схема событий может изменяться независимо от основной БД

---

Доп. команды, если что-то пошло не так:
- Проверить статус коннектора `curl -s http://localhost:8083/connectors/outbox-connector/status | jq`
- Удалить коннектор `curl -X DELETE http://localhost:8083/connectors/outbox-connector`
- Перезапустить коннектор - `curl -X POST http://localhost:8083/connectors/outbox-connector/restart`
- Проверить слот репликации - `SELECT * FROM pg_replication_slots;`
- Принудительно обновить слот - `SELECT pg_replication_slot_advance('your_slot_name', pg_current_wal_lsn());`
- Если слот неактивен - `SELECT pg_drop_replication_slot('your_slot_name');`