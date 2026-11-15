# Лабораторна робота №3

Тема: Прикладні бібліотеки Python для побудови вебзастосунків

Варіант: 3. Реєстр вразливостей робочих станцій

## Предметна область

Сервіс обліку знахідок перевірки робочих станцій.

- Категорія визначає тип програмного забезпечення: `os`, `browser`, `office`.
- `value` це навчальна оцінка небезпеки знахідки, число від 0 до 10 включно.
- Одиниця вимірювання: `score`. Умовний поріг уваги: 8.0.
- `status` описує стан опрацювання: `new`, `in_progress` або `done`.

## Структура

```
labs/lab03/
├── main.py          застосунок FastAPI і підключення маршрутів
├── database.py      з'єднання та виконання schema.sql
├── schema.sql       схема таблиць categories і records
├── repository.py    параметризовані SQL запити
├── schemas.py       Pydantic моделі запитів і відповідей
├── config.py        одиниця вимірювання, поріг, обмеження варіанта
├── seed.py          початкове заповнення з data/seed.json
├── routers/
│   ├── categories.py
│   └── records.py
└── data/
    ├── seed.json    навчальні дані варіанта
    └── lab3.sqlite3 створюється програмою, у Git не додається
```

## Встановлення

Усі команди виконуються з кореня репозиторію в активованому віртуальному середовищі.

```powershell
pip install -r requirements.txt
```

## Початкове заповнення бази

```powershell
python -m labs.lab03.seed
```

Створює 3 категорії та 8 записів однією транзакцією. Повторний запуск повідомляє,
що база вже містить дані, і нічого не змінює.

## Запуск API

```powershell
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs

OpenAPI схема: http://127.0.0.1:8000/openapi.json

## Приклади запитів

У Windows PowerShell використовуйте `curl.exe`, а не `curl`. Лапки в JSON зручніше
передавати через Swagger UI.

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/student"
curl -i "http://127.0.0.1:8000/categories"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"
```

Створення запису:

```bash
curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V03-TEST","title":"Навчальна знахідка","category_id":1,"value":7.5,"status":"new"}'
```

Перевірка скасування пакета, коли V03-01 уже є в базі:

```bash
curl -i -X POST "http://127.0.0.1:8000/records/bulk" \
  -H "Content-Type: application/json" \
  -d '[{"code":"V03-ROLLBACK","title":"Перший елемент","category_id":1,"value":4.0,"status":"new"},{"code":"V03-01","title":"Дублікат коду","category_id":2,"value":5.0,"status":"new"}]'
```

Очікується 409, запис V03-ROLLBACK не зберігається.

## Основні маршрути

| Метод і шлях | Призначення | Успіх |
|---|---|---|
| GET /ping | перевірка доступності | 200 |
| GET /student | дані студента | 200 |
| GET /categories | список категорій | 200 |
| POST /categories | створення категорії | 201 |
| DELETE /categories/{category_id} | видалення порожньої категорії | 204 |
| GET /records | список із фільтрами | 200 |
| GET /records/{record_id} | один запис | 200 |
| POST /records | створення запису | 201 |
| PUT /records/{record_id} | повна заміна полів | 200 |
| DELETE /records/{record_id} | видалення запису | 204 |
| POST /records/bulk | пакетне створення | 201 |

Помилки: 404 запис чи категорію не знайдено, 409 дублікат або непорожня категорія,
422 некоректні дані.
