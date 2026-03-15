# API-сервис сокращения ссылок

Сервис для создания коротких ссылок, редиректа по короткому коду, просмотра статистики и управления ссылками.

## Функциональность

- регистрация и авторизация пользователей
- создание короткой ссылки
- создание короткой ссылки с кастомным alias
- редирект по короткой ссылке
- получение информации о ссылке
- обновление оригинального URL
- удаление ссылки
- просмотр статистики по ссылке
- поиск ссылки по оригинальному URL
- поддержка времени жизни ссылки (`expires_at`)
- автоматическое удаление истекших ссылок
- история истекших ссылок
- PostgreSQL как основное хранилище
- Redis для кэширования

## API

### Auth

- `POST /auth/register` — регистрация пользователя
- `POST /auth/login` — авторизация пользователя

### Links

- `POST /links/shorten` — создание короткой ссылки
- `GET /{short_code}` — редирект на оригинальный URL
- `GET /links/{short_code}` — получение информации о ссылке
- `PUT /links/{short_code}` — обновление ссылки
- `DELETE /links/{short_code}` — удаление ссылки
- `GET /links/{short_code}/stats` — статистика по ссылке
- `GET /links/search?original_url={url}` — поиск ссылки по оригинальному URL
- `GET /links/expired/history` — история истекших ссылок

## Примеры запросов

### Регистрация

```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "12345678"
  }'
````

### Авторизация

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=12345678"
```

### Создание ссылки

```bash
curl -X POST "http://127.0.0.1:8000/links/shorten" \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://www.python.org",
    "custom_alias": "python-link"
  }'
```

### Создание ссылки с временем жизни

```bash
curl -X POST "http://127.0.0.1:8000/links/shorten" \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://www.python.org",
    "custom_alias": "expire-test",
    "expires_at": "2026-03-20T18:30:00"
  }'
```

### Получение информации о ссылке

```bash
curl -X GET "http://127.0.0.1:8000/links/python-link"
```

### Редирект

```bash
curl -L "http://127.0.0.1:8000/python-link"
```

### Поиск по оригинальному URL

```bash
curl -X GET "http://127.0.0.1:8000/links/search?original_url=https://www.python.org"
```

### Получение статистики

```bash
curl -X GET "http://127.0.0.1:8000/links/python-link/stats"
```

### Обновление ссылки

```bash
curl -X PUT "http://127.0.0.1:8000/links/python-link" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "original_url": "https://docs.python.org"
  }'
```

### Удаление ссылки

```bash
curl -X DELETE "http://127.0.0.1:8000/links/python-link" \
  -H "Authorization: Bearer <TOKEN>"
```

## Запуск проекта

### Через Docker Compose

```bash
git clone https://github.com/npoisoned/fastapi_project.git
cd fastapi_project
docker compose up --build
```

Документация Swagger:

```text
http://127.0.0.1:8000/docs
```

Проверка health endpoint:

```text
http://127.0.0.1:8000/health
```

## База данных

Используются таблицы:

### `users`

* `id`
* `email`
* `password_hash`
* `created_at`

### `links`

* `id`
* `short_code`
* `original_url`
* `custom_alias`
* `user_id`
* `created_by_authenticated`
* `click_count`
* `created_at`
* `updated_at`
* `last_accessed_at`
* `expires_at`
* `is_active`

### `expired_links_history`

* `id`
* `short_code`
* `original_url`
* `user_id`
* `created_at`
* `expired_at`
* `click_count`
* `last_accessed_at`
* `reason`

## Ограничения доступа

* создание ссылки и переход по ссылке доступны всем
* изменение и удаление ссылки доступны только зарегистрированному пользователю
* изменение и удаление доступны только владельцу ссылки

```
```
