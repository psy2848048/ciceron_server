# -*- coding: utf-8 -*-

import psycopg2
from unittest import TestCase
import sys
sys.path.append('./src')

from payment import Payment

class PaymentTestCase(TestCase):
    def setUp(self):
        self.conn = psycopg2.connect("host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!")
        self.paymentObj = Payment(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_assert(self):
        self.assertEqual(True, True)

    def test_commonPromotionCodeChecker(self):
        code, point, message = self.paymentObj.commonPromotionCodeChecker(1, 'abcde')
        self.assertEqual((code, point), (3, 0))

    def test_commonPromotionCodeExecutor(self):
        try:
            self.paymentObj.commonPromotionCodeExecutor('admin@ciceron.me', 'abcde')
        except Exception:
            return

        raise Exception

    def test_individualPromotionCodeChecker(self):
        code, point, message = self.paymentObj.individualPromotionCodeChecker(1, 'abcde')
        self.assertEqual((code, point), (3, 0))
