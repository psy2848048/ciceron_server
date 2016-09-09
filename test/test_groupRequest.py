# -*- coding: utf-8 -*-

import psycopg2
from unittest import TestCase
import sys
sys.path.append('./src')

from groupRequest import GroupRequest

class GroupRequestTestCase(TestCase):
    def setUp(self):
        self.conn = psycopg2.connect("host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!")
        self.groupRequestObj = GroupRequest(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_assert(self):
        self.assertEqual(True, True)

    def test__checkNumberOfGroupMembers(self):
        res = self.groupRequestObj._checkNumberOfGroupMembers(360)
        self.assertEqual(res, None)

    def test_getGroupRequestList(self):
        res = self.groupRequestObj.getGroupRequestList()
        self.assertEqual(len(res), 0)

    def test_getGroupRequestListDiffPage(self):
        res = self.groupRequestObj.getGroupRequestList(page=2)
        self.assertEqual(len(res), 0)

    def test_getOneGroupRequest(self):
        res = self.groupRequestObj.getOneGroupRequest(360)
        self.assertEqual(len(res), 0)

    def test_checkGroupMembers(self):
        res = self.groupRequestObj.checkGroupMembers(360)
        self.assertEqual(len(res), 0)

    def test_checkUnpaidMembers(self):
        res = self.groupRequestObj.checkUnpaidMembers(360)
        self.assertEqual(len(res), 0)

    def test_addUserToGroup(self):
        res = self.groupRequestObj.addUserToGroup(360, 1)
        self.assertEqual(res, True)
        self.conn.rollback()

    def test_updatePaymentInfo(self):
        res = self.groupRequestObj.updatePaymentInfo(360, 1, 'alipay', '12345')
        self.assertEqual(res, True)
        self.conn.rollback()

    def test_deleteUserFromGroup(self):
        res = self.groupRequestObj.deleteUserFromGroup(360, 1)
        self.assertEqual(res, True)
        self.conn.rollback()

    def test_assignToGroup(self):
        self.groupRequestObj.assignToGroup(360, 1, 1)
        self.conn.rollback()

    def test_insertTitle(self):
        self.groupRequestObj.insertTitle(360, 1, 1)
        self.conn.rollback()
