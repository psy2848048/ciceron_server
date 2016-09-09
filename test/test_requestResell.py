# -*- coding: utf-8 -*-

import psycopg2
from unittest import TestCase
import sys

from requestResell import RequestResell

class RequestResellTestCase(TestCase):
    def setUp(self):
        self.conn = psycopg2.connect("host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!")
        self.requestResellObj = RequestResell(self.conn)

    def tearDown(self):
        self.conn.rollback()
        self.conn.close()

    def test_getListRandomPick(self):
        res = self.requestResellObj.getListRandomPick()
        self.assertEqual(len(res), 0)

    def test_getList(self):
        res = self.requestResellObj.getList()
        self.assertEqual(len(res), 0)

    def test_getOneTicket(self):
        res = self.requestResellObj.getOneTicket(360)
        self.assertEqual(len(res), 0)

    def test_setReadPermission(self):
        self.requestResellObj.setReadPermission(360, 1)

    def test_setToPaid(self):
        self.requestResellObj.setToPaid(360, 1, 'alipay', '12345')

    def test_confirmCopyright(self):
        res = self.requestResellObj.confirmCopyright(360)
        self.assertEqual(res, True)

    def test_rejectCopyright(self):
        res = self.requestResellObj.rejectCopyright(360)
        self.assertEqual(res, True)

    def test_assignToGroup(self):
        self.requestResellObj.assignToGroup(360, 1, 1)

    def test_insertTitle(self):
        self.requestResellObj.insertTitle(360, 1, 1)
