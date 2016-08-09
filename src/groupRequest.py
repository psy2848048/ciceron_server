# -*- coding: utf-8 -*-

import psycopg2
import os
import traceback
import ciceron_lib

class GroupRequest(object):
    def __init__(self, conn):
        self.conn = conn

    def __getNumberOfGroupMember(self, request_id):
        cursor = self.conn.cursor()

        query = """
            SELECT number_of_member_in_group FROM CICERON.F_REQUESTS
            WHERE id = %s AND is_splitTrans = true
        """
        cusor.exeucte(query, (request_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return 1

        return res[0]

    def __checkParticipatedMemberInRequest(self, request_id):
        cursor = self.conn.cursor()

        query = """
            SELECT user_id, is_paid, payment_platform, transaction_id 
            FROM CICERON.F_GROUP_REQUESTS_USERS
            WHERE request_id = %s AND is_paid = true
        """
        cusor.exeucte(query, (request_id, ))
        res = cursor.fetchall()
        return res

    def __checkUnpaidMemberInRequest(self, request_id):
        cursor = self.conn.cursor()

        query = """
            SELECT user_id, is_paid, payment_platform, transaction_id 
            FROM CICERON.F_GROUP_REQUESTS_USERS
            WHERE request_id = %s AND is_paid = false
        """
        cusor.exeucte(query, (request_id, ))
        res = cursor.fetchall()
        return res

    def __checkNumberOfParticipatedMemberInRequest(self, request_id):
        cursor = self.conn.cursor()

        query = """
            SELECT count(*) FROM CICERON.F_GROUP_REQUESTS_USERS
            WHERE request_id = %s AND is_paid = true
        """
        cursor.execute(query, (request_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return 0

        return res[0]

    def _checkNumberOfGroupMembers(self, request_id):
        cursor = self.conn.cursor()

        query = """
            SELECT number_of_member_in_group FROM CICERON.F_REQUESTS
            WHERE id = %s
        """
        cursor.execute(query, (request_id, ))
        res = cursor.fetchone()
        if res is None or len(rs) == 0:
            return 0

        return res[0]

    def getGroupRequestList(self):
        cursor = self.conn.cursor()

        query = """
            SELECT * FROM CICERON.V_REQUESTS
            WHERE is_splitTrans = true AND is_paid = true
              AND number_of_member_in_group > requested_member
            ORDER BY registered_time
        """
        cursor.execute(query)
        ret = cursor.fetchall()
        return ret

    def checkGroupMembers(self, request_id):
        result = self.__checkParticipatedMemberInRequest(request_id)
        return result

    def checkUnpaidMembers(self, request_id):
        result = self.__checkUnpaidMemberInRequest(request_id)
        return result

    def addUserToGroup(self, request_id, user_id):
        cursor = self.conn.cursor()
        seq = ciceron_lib.get_new_id(self.conn, "F_GROUP_REQUESTS_USERS")

        query = """
            INSERT INTO CICERON.F_GROUP_REQUESTS_USERS
            (id, request_id, user_id, is_paid)
            VALUES
            (%s, %s, %s, false)
        """
        try:
            cursor.execute(query, (seq, request_id, user_id, ))
            return True

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False

    def updatePaymentInfo(self, request_id, user_id, payment_platform, transaction_id):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_GROUP_REQUESTS_USERS
            SET is_paid = true,
                payment_platform = %s,
                transaction_id = %s
            WHERE request_id = %s AND user_id = %s
        """
        try:
            cursor.execute(query, (payment_platform, transaction_id, request_id, user_id, ))
            return True

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False

    def deleteUserFromGroup(self, request_id, user_id):
        cursor = self.conn.cursor()

        query = """
            DELETE FROM CICERON.F_GROUP_REQUESTS_USERS
            WHERE request_id = %s AND user_id = %s
        """
        try:
            cursor.execute(query, (request_id, user_id, ))
            return True

        except Exception:
            tracaback.print_exc()
            self.conn.rollback()
            return False

    def confirmCopyright(self, request_id):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_GROUP_REQUESTS_COPYRIGHT_CHECK
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
            UPDATE CICERON.F_GROUP_REQUESTS_COPYRIGHT_CHECK
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

    def cancelGroupRequest(self, request_id):
        # Use normal DELETE request
        pass
