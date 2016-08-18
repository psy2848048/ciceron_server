# -*- coding: utf-8 -*-
import ciceron_lib


class RequestResell(object):
    def __init__(self, conn):
        self.conn = conn

    def getList(self):
        cursor = self.conn.cursor()
        query = """
                WITH public_requests AS
                (
                    SELECT * FROM CICERON.V_REQUESTS
                    WHERE status_id = 2
                      AND is_public = true
                    ORDER BY request_id DESC
                )

               SELECT * FROM public_requests
               OFFSET FLOOR(RANDOM() * (SELECT COUNT(*) FROM public_requests))
               LIMIT 20
            """
        cursor.execute(query)
        res = cursor.fetchall()
        return res

    def setReadPermission(self, request_id, user_id):
        cursor = self.conn.cursor()

        new_id = ciceron_lib.get_new_id(self.conn, "F_READ_PUBLIC_REQUESTS_USERS")
        query = """
            INSERT INTO CICERON.F_READ_PUBLIC_REQUESTS_USERS
            (id, request_id, user_id, is_paid)
            VALUES
            (%s, %s, %s, false)
            """

        cursor.execute(query, (new_id, request_id, user_id, ))

    def setToPaid(self, request_id, user_id, payment_platform, transaction_id):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_READ_PUBLIC_REQUESTS_USERS
            SET   is_paid = true
                , payment_platform = %s
                , transaction_id = %s
            WHERE request_id = %s
              AND user_id = %s
              AND is_paid = false
            """

        cursor.execute(query, (payment_platform, transaction_id, request_id, user_id, ))
