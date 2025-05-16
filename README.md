# Итоговый проект Foodgram

## Описание

**Foodgram** — сайт, на котором пользователи публикуют рецепты, добавляют их в избранное и формируют список покупок. Также реализована возможность подписки на других авторов.

## Платформа позволяет:
- Публиковать и редактировать рецепты;
- Добавлять рецепты в избранное;
- Подписываться на других пользователей;
- Формировать и скачивать список необходимых ингредиентов;
- Искать рецепты и ингредиенты;
- Управлять подписками и избранным из личного профиля.

## Страницы проекта
- главная,
- страница входа,
- страница регистрации,
- страница рецепта,
- страница пользователя,
- страница подписок,
- избранное,
- список покупок,
- создание и редактирование рецепта,
- страница смены пароля,
- статические страницы «О проекте» и «Технологии».

## Разграничение прав доступа

| Роль | Возможности |
|------|-------------|
| Гость | Просмотр рецептов и страниц |
| Аутентифицированный | Добавление рецептов, подписки, покупки |
| Администратор | Полный доступ, в том числе к админ-панели |

## Stack
- **Python** 3.10+
- **Django** 4.2 — основной веб-фреймворк
- **Django REST Framework** ≥3.14 — создание REST API
- **Djoser** ≥2.1.0 — регистрация и аутентификация
- **django-filter** ≥23.1 — фильтрация запросов
- **drf-extra-fields** — дополнительные поля сериализации
- **Django Extensions** — отладочные и служебные инструменты
- **Pillow** 10.3.0 — работа с изображениями
- **psycopg2-binary** ≥2.9.9 — драйвер PostgreSQL
- **python-dotenv** ≥0.21.0 — работа с `.env`-файлами
- **gunicorn** 22.0.0 — WSGI HTTP-сервер
- **PostgreSQL** — реляционная база данных
- **Docker / Docker Compose** — контейнеризация приложения
- **Nginx** — прокси-сервер и сервер статики

## Как запустить

### 1. Склонируйте репозиторий

```sh
git clone https://github.com/LeakMachine/foodgram-st.git
cd foodgram-st
```

### 2. Создайте переменные окружения .env в корне проекта


```env
POSTGRES_DB=foodgram_database
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=user_password
DATABASE_URL=postgresql://foodgram_user:pass@db:5432/foodgram_database
DB_HOST=db
DB_PORT=5432
```

### 3. Соберите и запустите контейнеры на Docker Hub

```sh
docker-compose up -d --build
```

### 4. Выполните миграции, создайте админа

```sh
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

### 5. Загрузите ингредиенты в БД

```sh
docker-compose exec backend python manage.py db_import
```

### 6. При необходимости перезапуска

```sh
docker-compose down -v
```


## Проект доступен по адресу http://localhost

## Для тестирования запросов используйте коллекцию Postman в каталоге postman_collection/foodgram.postman_collection.json


