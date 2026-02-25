# Симулятор кейсов на Python + pywebview

Desktop-приложение для симуляции открытия кейсов с модульной архитектурой и более гибким управлением балансом.

## Что улучшено

- Проект разделён на модули (`simcase/app.py`, `simcase/api.py`, `simcase/service.py`, `simcase/models.py`, `simcase/ui.py`).
- Переработанная UI-структура: отдельный блок прогрессии игрока + более аккуратные вкладки.
- Добавлена система уровней и опыта (XP = число открытых кейсов).
- Параметры XP настраиваются: базовый XP и коэффициент роста уровня.
- Гибкое редактирование редкостей прямо в таблице (массовое сохранение).
- Быстрая авто-нормализация диапазонов редкостей по всему ролл-диапазону.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск

```bash
python app.py
```

## Архитектура

- `simcase/models.py` — модели домена.
- `simcase/service.py` — бизнес-логика и работа с JSON-хранилищем.
- `simcase/api.py` — интерфейс для `pywebview` JS API.
- `simcase/ui.py` — HTML/CSS/JS интерфейс.
- `simcase/app.py` — запуск desktop-окна.
