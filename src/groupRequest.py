# -*- coding: utf-8 -*-

import psycopg2
import os
import traceback

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
            SELECT count(*) FROM CICERON.F_GROUP_REQUESTS_USERS
        """
        cursor.execute(query, (request_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return 0

        return res[0]

    def _checkNumberOfGroupMembers(self, request_id):
        pass

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
        pass

    def addUserToGroup(self, request_id, user_id):
        pass

    def deleteUserFromGroup(self, request_id, user_id):
        pass

    def confirmCopyright(self, request_id):
        pass

    def rejectCopyright(self, request_id):
        pass

    def cancelGroupRequest(self, request_id):
        pass

