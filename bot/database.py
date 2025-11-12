from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import aiosqlite


@dataclass
class User:
    user_id: int
    first_name: str | None
    language: str
    ton_wallet: str | None
    rub_wallet: str | None
    ton_balance: float
    rub_balance: float
    ref_code: str
    invited_by: int | None


@dataclass
class Deal:
    id: int
    seller_id: int
    currency: str
    amount: float
    description: str
    status: str
    link_token: str
    buyer_id: int | None


class Database:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._path)
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.execute("PRAGMA journal_mode = WAL")
        await self._conn.execute("PRAGMA synchronous = NORMAL")
        await self._conn.execute("PRAGMA cache_size = -64000")
        self._conn.row_factory = aiosqlite.Row

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def setup(self) -> None:
        if self._conn is None:
            raise RuntimeError("Database is not connected")
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                language TEXT NOT NULL DEFAULT 'ru',
                ton_wallet TEXT,
                rub_wallet TEXT,
                ton_balance REAL NOT NULL DEFAULT 0,
                rub_balance REAL NOT NULL DEFAULT 0,
                ref_code TEXT NOT NULL UNIQUE,
                invited_by INTEGER,
                FOREIGN KEY(invited_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                currency TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                link_token TEXT NOT NULL UNIQUE,
                buyer_id INTEGER,
                FOREIGN KEY(seller_id) REFERENCES users(user_id),
                FOREIGN KEY(buyer_id) REFERENCES users(user_id)
            );
            """
        )
        await self._conn.commit()

    async def ensure_user(self, user_id: int, first_name: Optional[str], ref_code: str, invited_by: Optional[int]) -> User:
        async with self._lock:
            assert self._conn is not None
            row = await (await self._conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            )).fetchone()
            if row is None:
                await self._conn.execute(
                    "INSERT INTO users (user_id, first_name, ref_code, invited_by) VALUES (?, ?, ?, ?)",
                    (user_id, first_name, ref_code, invited_by),
                )
                await self._conn.commit()
                row = await (await self._conn.execute(
                    "SELECT * FROM users WHERE user_id = ?",
                    (user_id,),
                )).fetchone()
            return self._row_to_user(row)

    async def update_language(self, user_id: int, language: str) -> None:
        async with self._lock:
            assert self._conn is not None
            await self._conn.execute(
                "UPDATE users SET language = ? WHERE user_id = ?",
                (language, user_id),
            )
            await self._conn.commit()

    async def update_wallet(self, user_id: int, currency: str, value: str) -> None:
        column = "ton_wallet" if currency == "ton" else "rub_wallet"
        async with self._lock:
            assert self._conn is not None
            await self._conn.execute(
                f"UPDATE users SET {column} = ? WHERE user_id = ?",
                (value, user_id),
            )
            await self._conn.commit()

    async def fetch_user(self, user_id: int) -> Optional[User]:
        assert self._conn is not None
        row = await (await self._conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )).fetchone()
        if row is None:
            return None
        return self._row_to_user(row)

    async def fetch_referrer(self, ref_code: str) -> Optional[int]:
        assert self._conn is not None
        row = await (await self._conn.execute(
            "SELECT user_id FROM users WHERE ref_code = ?",
            (ref_code,),
        )).fetchone()
        if row is None:
            return None
        return int(row["user_id"])

    async def generate_ref_code(self) -> str:
        assert self._conn is not None
        while True:
            candidate = secrets.token_urlsafe(4)
            row = await (await self._conn.execute(
                "SELECT 1 FROM users WHERE ref_code = ?",
                (candidate,),
            )).fetchone()
            if row is None:
                return candidate

    async def stats_referrals(self, user_id: int) -> int:
        assert self._conn is not None
        row = await (await self._conn.execute(
            "SELECT COUNT(*) AS total FROM users WHERE invited_by = ?",
            (user_id,),
        )).fetchone()
        return int(row["total"]) if row else 0

    async def create_deal(
        self, seller_id: int, currency: str, amount: float, description: str
    ) -> Deal:
        assert self._conn is not None
        link_token = secrets.token_urlsafe(8)
        async with self._lock:
            await self._conn.execute(
                """
                INSERT INTO deals (seller_id, currency, amount, description, status, link_token)
                VALUES (?, ?, ?, ?, 'created', ?)
                """,
                (seller_id, currency, amount, description, link_token),
            )
            await self._conn.commit()
            row = await (await self._conn.execute(
                "SELECT * FROM deals WHERE link_token = ?",
                (link_token,),
            )).fetchone()
        return self._row_to_deal(row)

    async def update_deal_status(self, deal_id: int, status: str) -> None:
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(
                "UPDATE deals SET status = ? WHERE id = ?",
                (status, deal_id),
            )
            await self._conn.commit()

    async def assign_buyer(self, deal_id: int, buyer_id: int) -> None:
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(
                "UPDATE deals SET buyer_id = ? WHERE id = ?",
                (buyer_id, deal_id),
            )
            await self._conn.commit()

    async def fetch_deal_by_token(self, token: str) -> Optional[Deal]:
        assert self._conn is not None
        row = await (await self._conn.execute(
            "SELECT * FROM deals WHERE link_token = ?",
            (token,),
        )).fetchone()
        if row is None:
            return None
        return self._row_to_deal(row)

    async def adjust_balances(
        self, *,
        payer_id: int,
        seller_id: int,
        currency: str,
        amount: float,
    ) -> bool:
        assert self._conn is not None
        column = "ton_balance" if currency == "ton" else "rub_balance"
        async with self._lock:
            payer_row = await (await self._conn.execute(
                f"SELECT {column} FROM users WHERE user_id = ?",
                (payer_id,),
            )).fetchone()
            seller_row = await (await self._conn.execute(
                f"SELECT {column} FROM users WHERE user_id = ?",
                (seller_id,),
            )).fetchone()
            if payer_row is None or seller_row is None:
                return False
            payer_balance = float(payer_row[column])
            if payer_balance < amount:
                return False
            new_payer_balance = payer_balance - amount
            seller_balance = float(seller_row[column])
            new_seller_balance = seller_balance + amount
            await self._conn.execute(
                f"UPDATE users SET {column} = ? WHERE user_id = ?",
                (new_payer_balance, payer_id),
            )
            await self._conn.execute(
                f"UPDATE users SET {column} = ? WHERE user_id = ?",
                (new_seller_balance, seller_id),
            )
            await self._conn.commit()
            return True

    def _row_to_user(self, row: aiosqlite.Row) -> User:
        return User(
            user_id=int(row["user_id"]),
            first_name=row["first_name"],
            language=row["language"],
            ton_wallet=row["ton_wallet"],
            rub_wallet=row["rub_wallet"],
            ton_balance=float(row["ton_balance"] or 0),
            rub_balance=float(row["rub_balance"] or 0),
            ref_code=row["ref_code"],
            invited_by=row["invited_by"],
        )

    def _row_to_deal(self, row: aiosqlite.Row) -> Deal:
        return Deal(
            id=int(row["id"]),
            seller_id=int(row["seller_id"]),
            currency=row["currency"],
            amount=float(row["amount"]),
            description=row["description"],
            status=row["status"],
            link_token=row["link_token"],
            buyer_id=row["buyer_id"],
        )
