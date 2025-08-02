from psycopg import Cursor


class Order:
    @staticmethod
    def get_all_orders(
        cur: Cursor,
        has_external_id: bool = None,
        status: str = None,
        market_code: str = None,
    ):
        sql_query = """
        SELECT o.id AS id,
            o.amount AS amount,
            o.price AS price,
            o.type AS type,
            o.note AS note,
            o.status AS status,
            o.filled_amount AS filled_amount,
            o."comment" AS comment,
            o.side AS side,
            o.market_code AS market_code,
            o.external_order_id as external_order_id,
            o.created_on AS created_on,
            o.updated_on AS updated_on,
            c.code AS coin_code,
            s.value AS value
        FROM moolah."order" o
        JOIN moolah.signal_order so ON so.order_id = o.id 
        JOIN moolah.signal s ON s.id = so.signal_id 
        JOIN moolah.coin c ON s.coin_id = c.id
        """

        conditions: list[str] = []
        params: list[str] = []

        if has_external_id is not None:
            if has_external_id:
                conditions.append("o.external_order_id IS NOT NULL AND o.external_order_id != ''")
            else:
                conditions.append("(o.external_order_id IS NULL OR o.external_order_id = '')")

        if status is not None:
            conditions.append("o.status = %s")
            params.append(status)

        if market_code is not None:
            conditions.append("o.market_code = %s")
            params.append(market_code)

        if conditions:
            sql_query += " WHERE " + " AND ".join(conditions)
        sql_query += ";"
        cur.execute(sql_query, params)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        results = [dict(zip(columns, row, strict=False)) for row in rows]

        return results

    def get_order_by_external_order_id(
        cur: Cursor,
        external_order_id: str,
    ):
        query = """
        SELECT *
        FROM moolah."order" o
        WHERE external_order_id = %s
        """

        cur.execute(
            query,
            (external_order_id,),
        )

        row = cur.fetchone()
        columns = [desc[0] for desc in cur.description]
        result = dict(zip(columns, row, strict=False)) if row else None

        return result

    @staticmethod
    def update_order_by_id(
        cur: Cursor,
        filled_amount: float,
        status: str,
        external_order_id: int,
        id: int,
    ):
        query = """
            UPDATE moolah."order"
            SET filled_amount = %s, status = %s, external_order_id = %s
            WHERE id = %s
        """
        params = [filled_amount, status, external_order_id, id]

        cur.execute(query, params)

    @staticmethod
    def update_order_by_external_order_id(
        cur: Cursor,
        filled_amount: float,
        status: str,
        external_order_id: int,
    ):
        query = """
            UPDATE moolah."order" 
            SET filled_amount = %s, status = %s 
            WHERE external_order_id = %s
        """
        params = [filled_amount, status, external_order_id]
        cur.execute(query, params)


class Trade:
    @staticmethod
    def insert_trade_if_not_exists(cur: Cursor, trade_id, price, quantity, timestamp, market_id, order_id):
        cur.execute(
            """
            INSERT INTO moolah.trade (trade_id, price, quantity, "timestamp", market_id, order_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (trade_id) DO NOTHING
            RETURNING id;
            """,
            (trade_id, price, quantity, timestamp, market_id, order_id),
        )
