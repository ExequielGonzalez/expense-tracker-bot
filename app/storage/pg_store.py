from typing import Dict, Optional
import psycopg


class PostgresStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._ensure_table()

    def _ensure_table(self) -> None:
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS expenses (
                        id SERIAL PRIMARY KEY,
                        date DATE NOT NULL,
                        amount NUMERIC(10,2) NOT NULL,
                        category TEXT NOT NULL,
                        payer TEXT NOT NULL,
                        telegram_user TEXT,
                        chat_id BIGINT,
                        message_id BIGINT,
                        processed_at TIMESTAMP NOT NULL,
                        source TEXT NOT NULL,
                        receipt_path TEXT,
                        receipt_file_id TEXT,
                        title TEXT,
                        model TEXT,
                        overall_confidence NUMERIC(5,2)
                    )
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_payer ON expenses(payer)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_chat_id ON expenses(chat_id)")
            conn.commit()

    def save_expense(self, expense: Dict[str, object]) -> None:
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO expenses (
                        date,
                        amount,
                        category,
                        payer,
                        telegram_user,
                        chat_id,
                        message_id,
                        processed_at,
                        source,
                        receipt_path,
                        receipt_file_id,
                        title,
                        model,
                        overall_confidence
                    ) VALUES (
                        %(date)s,
                        %(amount)s,
                        %(category)s,
                        %(payer)s,
                        %(telegram_user)s,
                        %(chat_id)s,
                        %(message_id)s,
                        %(processed_at)s,
                        %(source)s,
                        %(receipt_path)s,
                        %(receipt_file_id)s,
                        %(title)s,
                        %(model)s,
                        %(overall_confidence)s
                    )
                    """,
                    expense
                )
            conn.commit()


def build_postgres_store(database_url: Optional[str]) -> Optional[PostgresStore]:
    if not database_url:
        return None
    return PostgresStore(database_url)
