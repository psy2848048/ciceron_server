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

    def test_individualPromotionCodeExecutor(self):
        self.paymentObj.individualPromotionCodeExecutor('admin@ciceron.me', 'abcde')

    def test_checkPoint(self):
        checked, current_point = self.paymentObj.checkPoint(1, 12)

    def test_alipayPayment(self):
        is_payment_ok, link = self.paymentObj.alipayPayment(False, 1, 'psy2848048@nate.com', 20.1
                , point_for_use=0
                , promo_type='null'
                , promo_code='null'
                )

        if is_payment_ok == False or link is None:
            raise Exception

    def test_paypalPayment(self):
        is_payment_ok, link = self.paymentObj.alipayPayment(False, 1, 'psy2848048@nate.com', 20.1
                , point_for_use=0
                , promo_type='null'
                , promo_code='null'
                )

        print("Link: %s" % link)
        if is_payment_ok == False or link is None:
            raise Exception

    def test_iamportPayment(self):
        payload = {
                "card_number": '1111-2222-3333-4444'
              , "expiry": '2016-11'
              , 'birth': '198805'
              , 'pwd_2digit': '55'
                }
        try:
            is_payment_ok, link = self.paymentObj.iamportPayment(False, 1, 'psy2848048@nate.com', 20.1
                    , point_for_use=0
                    , promo_type='null'
                    , promo_code='null'
                    , **payload
                    )

        except Exception:
            return

        if is_payment_ok == True or link is not None:
            raise Exception

    def test_pointPayment(self):
        is_payment_ok, link = self.paymentObj.pointPayment(False, 1, 'psy2848048@nate.com', 20.1
                , point_for_use=0
                , promo_type='null'
                , promo_code='null'
                )

        if not (is_payment_ok == True and link is not None):
            raise Exception

    def test_postProcess(self):
        is_ok = self.paymentObj.postProcess(
                  user_email='psy2848048@nate.com'
                , request_id=360
                , pay_via='alipay'
                , pay_by='web'
                , is_succeeded=True
                , amount=10
                , use_point=0
                , promo_type=None
                , promo_code=None
                , is_additional=None
                , is_groupRequest='true'
                , is_public='true'
                , paymentId=None
                , PayerID=None
                , ciceron_order_id=None)

        self.assertEqual(is_ok, True)
