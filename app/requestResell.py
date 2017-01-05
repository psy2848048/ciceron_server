# -*- coding: utf-8 -*-
try:
    from .ciceron_lib import *
except:
    from ciceron_lib import *


class RequestResell(object):
    def __init__(self, conn):
        self.conn = conn

    def getListRandomPick(self):
        cursor = self.conn.cursor()
        query = """
                WITH public_requests AS
                (
                    SELECT * FROM CICERON.V_REQUESTS
                    WHERE status_id = 2
                      AND is_public = true
                    ORDER BY submitted_time DESC
                )

               SELECT * FROM public_requests
               OFFSET FLOOR(RANDOM() * (SELECT COUNT(*) FROM public_requests))
               LIMIT 20
            """
        cursor.execute(query)
        res = cursor.fetchall()
        return res

    def getList(self, page=1):
        cursor = self.conn.cursor()
        query = """
               SELECT * FROM CICERON.V_REQUESTS
               WHERE status_id = 2
                 AND is_public = true
               ORDER BY submitted_time DESC
               LIMIT 20 OFFSET 20 * (%s - 1)
            """

        cursor.execute(query, (page, ))
        res = cursor.fetchall()
        return res

    def getOneTicket(self, request_id):
        cursor = self.conn.cursor()
        query = """
               SELECT * FROM CICERON.V_REQUESTS
               WHERE request_id = %s
                 AND status_id = 2
                 AND is_public = true
            """

        cursor.execute(query, (request_id, ))
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

    def confirmCopyright(self, request_id):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_PUBLIC_REQUESTS_COPYRIGHT_CHECK
            SET is_confirmed = true
            WHERE request_id = %s
        """
        try:
            cursor.execute(query, (request_id, ))
            return True

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False

    def rejectCopyright(self, request_id):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_PUBLIC_REQUESTS_COPYRIGHT_CHECK
            SET is_confirmed = false
            WHERE request_id = %s
        """
        try:
            cursor.execute(query, (request_id, ))
            return True

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False

    def assignToGroup(self, request_id, user_id, group_id):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_READ_PUBLIC_REQUESTS_USERS
            SET complete_client_group_id = %s
            WHERE request_id = %s
              AND user_id = %s
        """
        cursor.execute(query, (group_id, request_id, user_id, ))

    def insertTitle(self, request_id, user_id, title_id):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_READ_PUBLIC_REQUESTS_USERS
            SET complete_client_title_id = %s
            WHERE request_id = %s
              AND user_id = %s
        """
        cursor.execute(query, (title_id, request_id, user_id, ))

