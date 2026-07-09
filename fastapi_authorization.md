# 🔐 FastAPI Authorization (Roles & Permissions)

---

## 1. Что такое Authorization

| Термин | Вопрос |
|---|---|
| **Authentication** | Кто ты? |
| **Authorization** | Что тебе разрешено делать? |

**Пример:**
```
Пользователь вошёл в систему  →  Authentication
Пользователь пытается удалить книгу  →  Authorization
```

---

## 2. Authentication vs Authorization

```
Authentication  →  Проверка личности пользователя
Authorization   →  Проверка прав пользователя
```

> JWT Token существует → Пользователь **аутентифицирован**
>
> Но удалять пользователей может только **ADMIN**

---

## 3. Добавляем роли

В модель `User` добавляют поле `role`:

```python
from sqlalchemy import String

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(50), default="user")
```

**Возможные роли:**

| Роль | Уровень |
|---|---|
| `user` | Обычный пользователь |
| `moderator` | Модератор |
| `admin` | Администратор |
| `superadmin` | Суперадминистратор |

---

## 4. Пример пользователей

| ID | Username | Role |
|---|---|---|
| 1 | Aziz | `user` |
| 2 | Hakim | `moderator` |
| 3 | Ali | `admin` |

---

## 5. Получение текущего пользователя

После JWT Authentication у нас уже есть `current_user`:

```python
@app.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return current_user
```

Теперь мы знаем: **кто** пользователь и **какая у него роль**.

---

## 6. Простая проверка роли

```python
from fastapi import HTTPException

def admin_required(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
```

**Использование:**

```python
@app.delete("/books/{book_id}")
def delete_book(
    book_id: int,
    current_user: User = Depends(get_current_user)
):
    admin_required(current_user)
    return {"message": "Book deleted"}
```

---

## 7. Dependency для проверки роли

Лучший вариант — использовать **Dependency**:

```python
from fastapi import Depends, HTTPException

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user
```

**Использование:**

```python
@app.delete("/books/{book_id}")
def delete_book(
    book_id: int,
    current_user: User = Depends(require_admin)
):
    return {"message": "Deleted"}
```

---

## 8. Универсальная проверка ролей

Иногда доступ разрешён **нескольким ролям** (например, `admin` и `moderator`):

```python
from fastapi import Depends, HTTPException

def require_roles(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Permission denied")
        return current_user
    return role_checker
```

**Использование:**

```python
@app.delete("/books/{book_id}")
def delete_book(
    book_id: int,
    current_user: User = Depends(require_roles(["admin", "moderator"]))
):
    return {"message": "Deleted"}
```

---

## 9. Role-Based Access Control (RBAC)

> Права назначаются **ролям**, а роли назначаются **пользователям**.

| Роль | Разрешения |
|---|---|
| `USER` | Читать книги |
| `MODERATOR` | Читать + изменять книги |
| `ADMIN` | Читать + изменять + удалять книги |

---

## 10. Permissions

Иногда ролей недостаточно — можно хранить конкретные **разрешения**:

```
create_book    update_book    delete_book
create_user    delete_user
```

**Пример пользователя:**
```
Aziz  →  create_book, update_book
```

---

## 11. Проверка Permission

```python
def require_permission(permission: str):
    def permission_checker(current_user: User = Depends(get_current_user)):
        if permission not in current_user.permissions:
            raise HTTPException(status_code=403, detail="Permission denied")
        return current_user
    return permission_checker
```

**Использование:**

```python
@app.delete("/books/{book_id}")
def delete_book(
    current_user: User = Depends(require_permission("delete_book"))
):
    pass
```

---

## 12. HTTP Status Codes

### 401 Unauthorized

> Пользователь **не вошёл** в систему.

```
Причины:
  • Authorization header missing
  • JWT отсутствует
  • JWT недействителен
```

### 403 Forbidden

> Пользователь вошёл, но **не имеет прав**.

```
Причина:
  Role = user, а endpoint требует admin
```

```json
{
  "detail": "Permission denied"
}
```

---

## 13. Практический пример

| Endpoint | USER | MODERATOR | ADMIN |
|---|:---:|:---:|:---:|
| `GET /books` | ✅ | ✅ | ✅ |
| `POST /books` | ❌ | ✅ | ✅ |
| `PUT /books/{id}` | ❌ | ✅ | ✅ |
| `DELETE /books/{id}` | ❌ | ❌ | ✅ |

---

## 14. Полная схема работы

```
1. Пользователь логинится
2. Backend выдаёт JWT
3. Клиент отправляет JWT
4. get_current_user() получает пользователя
5. Проверяется роль
6. Проверяются permissions
7. Если всё хорошо  →  доступ разрешён
8. Если прав нет    →  403 Forbidden
```

---

## 15. Authentication + Authorization: полный поток

```
Client
  │
  │  Login
  ▼
Backend  ──────────►  JWT
                        │
                        │  Bearer Token
                        ▼
                  get_current_user()
                        │
                        │  Authentication
                        ▼
                    User найден
                        │
                        │  Authorization
                        ▼
              Role / Permission проверены
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
        403 Forbidden      Endpoint выполнен
```

---

## Итог

| Концепция | Значение |
|---|---|
| **Authentication** | Кто пользователь? |
| **Authorization** | Что пользователь может делать? |
| **JWT** | Инструмент Authentication |
| **Roles + Permissions** | Инструменты Authorization |
| **401** | Не аутентифицирован |
| **403** | Нет прав доступа |


Oauth2PasswordBearer