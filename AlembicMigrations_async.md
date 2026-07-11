
## 1. Устанавливаем Alembic и зависимости

```bash
pip install alembic asyncpg sqlalchemy
```

`asyncpg` — асинхронный драйвер для PostgreSQL, без него async-подключение работать не будет.

## 2. Создаём папку миграций

```bash
alembic init -t async alembic
```

Обрати внимание: используем шаблон `-t async` — Alembic сразу сгенерирует `env.py`, заточенный под асинхронный движок.

После этого увидим:

```text
alembic/
    versions/
    env.py
alembic.ini
```

## 3. Проверяем `database.py`

Пример:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/dbname"


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
```

## 4. Пример модели

`models.py`

```python
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
```

## 5. Настраиваем `alembic.ini`

Находим строку:

```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

Заменяем на:

```ini
sqlalchemy.url = postgresql+asyncpg://user:password@localhost:5432/dbname
```

Если пароль или логин содержат спецсимволы, лучше вообще убрать эту строку из `alembic.ini` и задавать URL программно в `env.py` (см. ниже) — например, через переменные окружения, чтобы не хранить креды в файле.

## 6. Настраиваем `alembic/env.py`

В начале файла добавляем:

```python
import os
import sys
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import Base, DATABASE_URL
import models
```

Затем находим:

```python
target_metadata = None
```

Заменяем на:

```python
target_metadata = Base.metadata
```

Прописываем URL из `database.py`, чтобы не дублировать его в `alembic.ini`:

```python
config.set_main_option("sqlalchemy.url", DATABASE_URL)
```

Ключевая часть — асинхронный `run_migrations_online()`. Он выглядит так:

```python
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=False,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())
```

Обрати внимание на два отличия от синхронного варианта:

- Используется `async_engine_from_config` вместо `engine_from_config`.
- `render_as_batch=True` больше не нужен — это было решение специально для SQLite (там таблицы пересоздаются batch-режимом). Для PostgreSQL используем `render_as_batch=False` (или просто не указываем параметр), так как PostgreSQL нормально поддерживает `ALTER TABLE`. ([Alembic][2])

`run_migrations_offline()` (генерация SQL-скрипта без подключения к базе) можно оставить как есть — она не требует изменений под async.

## 7. Создаём первую миграцию

```bash
alembic revision --autogenerate -m "create users table"
```

После этого в:

```text
alembic/versions/
```

появится файл. Открываем и проверяем, что там есть что-то вроде:

```python
op.create_table(
    'users',
    ...
)
```

## 8. Применяем миграцию

```bash
alembic upgrade head
```

После этого в базе PostgreSQL появится таблица `users`.

## 9. Если изменили модель

Например, добавили новое поле:

```python
role: Mapped[str] = mapped_column(
    String(20),
    default="user"
)
```

Создаём новую миграцию:

```bash
alembic revision --autogenerate -m "add role to users"
```

Применяем:

```bash
alembic upgrade head
```

## Важно

Если миграция генерируется пустой, проблема почти всегда здесь:

```python
import models
target_metadata = Base.metadata
```

Это значит, что Alembic не видит наши модели.

Если моделей несколько файлов, например:

```text
models/user.py
models/post.py
models/comment.py
```

то в `env.py` нужно импортировать их все:

```python
from models import user, post, comment
```

или импортировать один общий файл, где они уже все собраны.

Ещё частые причины проблем именно с async-подключением:

- **Неверный драйвер в URL.** Строка должна начинаться с `postgresql+asyncpg://`, а не просто `postgresql://` — иначе SQLAlchemy попытается использовать синхронный psycopg2 и упадёт с ошибкой.
- **Использование обычного `create_engine` вместо `create_async_engine`** где-то в коде приложения — тогда часть кода будет асинхронной, а часть нет, и это приведёт к рассинхронизации.
- **Забыли `await connectable.dispose()`** — соединения могут "зависать" при повторных запусках миграций в тестах.
- **PostgreSQL должен быть уже поднят и доступен** (например, через Docker) до запуска `alembic upgrade head` — в отличие от SQLite, база не создаётся автоматически на лету.

Правильная команда для создания миграции:

```bash
alembic revision --autogenerate -m "migration name"
```

Правильная команда для применения:

```bash
alembic upgrade head
```

[1]: https://alembic.sqlalchemy.org/en/latest/autogenerate.html?utm_source=chatgpt.com "Auto Generating Migrations - Alembic's documentation!"
[2]: https://alembic.sqlalchemy.org/en/latest/batch.html?utm_source=chatgpt.com "Running “Batch” Migrations for SQLite and Other Databases"
