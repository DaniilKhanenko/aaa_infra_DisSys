from dataclasses import dataclass

import asyncpg


@dataclass
class ItemEntry:
    item_id: int
    user_id: int
    title: str
    description: str


class ItemStorage:
    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        # We initialize client here, because we need to connect it,
        # __init__ method doesn't support awaits.
        #
        # Pool will be configured using env variables.
        self._pool = await asyncpg.create_pool()

    async def disconnect(self) -> None:
        # Connections should be gracefully closed on app exit to avoid
        # resource leaks.
        await self._pool.close()

    async def create_tables_structure(self) -> None:
        """
        Создайте таблицу items со следующими колонками:
         item_id (int) - обязательное поле, значения должны быть уникальными
         user_id (int) - обязательное поле
         title (str) - обязательное поле
         description (str) - обязательное поле
        """
        # In production environment we will use migration tool
        # like https://github.com/pressly/goose
        table = """
        CREATE TABLE IF NOT EXISTS items(
            item_id bigint primary key,
            user_id integer not null,
            title text not null,
            description text not null
        );

        """
        async with self._pool.acquire() as connection:
            await connection.execute(table)

    async def save_items(self, items: list[ItemEntry]) -> None:
        """
        Напишите код для вставки записей в таблицу items одним запросом, цикл
        использовать нельзя.
        """
        # Don't use str-formatting, query args should be escaped to avoid
        # sql injections https://habr.com/ru/articles/148151/.
        query = """
            insert into items
            (item_id, user_id, title, description) 
            values ($1, $2, $3, $4)
        """
        records = [
            (item.item_id, item.user_id, item.title, item.description) for item in items
        ]
        async with self._pool.acquire() as connection:
            await connection.executemany(query, records)

    async def find_similar_items(
        self, user_id: int, title: str, description: str
    ) -> list[ItemEntry]:
        """
        Напишите код для поиска записей, имеющих указанные user_id, title и description.
        """
        query = """
            select item_id, user_id, title, description from items
            where
                user_id = $1
                and title = $2
                and description = $3
        """
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, user_id, title, description)
            return [ItemEntry(**dict(row)) for row in rows]
