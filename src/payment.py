# -*- coding: utf-8 -*-

import traceback
import random
from datetime import datetime
import string
import logging

import paypalrestsdk
from iamport import Iamport
from alipay import Alipay

import ciceron_lib
from groupRequest import GroupRequest
from requestResell import RequestResell

class Payment(object):
    """
    결제모듈 담당
    """
    def __init__(self, conn):
        self.conn = conn

    def __random_string_gen(self, size=6, chars=string.letters + string.digits):
        """
        무작위 string 만들어줌. 길이 조절도 가능함
        """
        gened_string = ''.join(random.choice(chars) for _ in range(size))
        gened_string = gened_string.encode('utf-8')
        return gened_string

    def _orderNoGenerator(self):
        """
        Iamport 방식으로 결제할 때에는 Iamport 단에서 주문번호를 만들어 주지 않기 때문에 우리가 직접 만들어야 한다.
        주문번호 형식은 YYYYMMDDxxxx (ex 20160716abcd) 방식으로 한다.
        """
        cursor = self.conn.cursor()
        order_no = None
    
        for _ in xrange(1000):
            order_no = datetime.strftime(datetime.now(), "%Y%m%d") + self.__random_string_gen(size=4)
            cursor.execute("SELECT count(*) FROM CICERON.PAYMENT_INFO WHERE order_no = %s", (order_no, ))
            cnt = cursor.fetchone()[0]
    
            if cnt == 0:
                break
            else:
                continue

        return order_no

    def _pointDeduction(self, user_email, point_for_use):
        cursor = self.conn.cursor()
        user_id = ciceron_lib.get_user_id(self.conn, user_email)

        if point_for_use > 0:
            cursor.execute("""
                    UPDATE CICERON.return_point
                    SET amount = amount - %s
                    WHERE id = %s
                    """, 
                (point_for_use, user_id, )
                    )

    def _markAsPaid(self, request_id, is_additional=False):
        cursor = self.conn.cursor()

        if is_additional == False:
            query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_paid = %s WHERE id = %s"
        else:
            query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_additional_points_paid = %s WHERE id = %s"
        cursor.execute(query_setToPaid, (True, request_id, ))

    def _paypalPaymentCheck(self, payment_id, payer_id):
        payment = paypalrestsdk.Payment.find(payment_id)
        payment.execute({"payer_id": payer_id})

    def _insertPaymentInfo(self, request_id, user_id, payment_platform, payment_id, amount):
        # Payment information update
        cursor = self.conn.cursor()
        payment_info_id = ciceron_lib.get_new_id(self.conn, "PAYMENT_INFO")
        query = """
            INSERT INTO CICERON.PAYMENT_INFO
                (id, request_id, client_id, payed_via, order_no, pay_amount, payed_time)
            VALUES
                (%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)"""

        cursor.execute(query,
                (  payment_info_id
                 , request_id
                 , user_id
                 , payment_platform
                 , payment_id
                 , amount
                 , )
                )

    def commonPromotionCodeChecker(self, user_id, code):
        # return: (val1, val2, message)
        #          val1: is valid code? (codeType)
        #          val2: How much?
        #          message: Message
        """
        공용 프로모션 코드 validator이다.
        코드는 유효한지, 유효한 코드지만 이미 사용한 코드인지 등등을 체크한다.
        """
        cursor = self.conn.cursor()
        query_commonPromotionCode= """
            SELECT id, benefitPoint, expireTime FROM CICERON.PROMOTIONCODES_COMMON WHERE text = UPPER(%s) """
        cursor.execute(query_commonPromotionCode, (code.upper(), ))
        ret = cursor.fetchone()
    
        if ret is None or len(ret) == 0:
            return (3, 0, "There is no promo code matched.")
    
        code_id = ret[0]
        benefitPoint = ret[1]
        expireTime = string2Date(ret[2])
    
        if expireTime < datetime.now():
            return (2, 0, "This promo code is expired.")
    
        query_userCheck = """
            SELECT count(*) FROM CICERON.USEDPROMOTION_COMMON WHERE id = %s AND user_id = %s """
    
        cursor.execute(query_userCheck, (code_id, user_id))
        cnt = cursor.fetchone()[0]
    
        if cnt > 0:
            return (1, 0, "You've already used this code.")
    
        else:
            return (0, benefitPoint, "You may use this code.")

    def commonPromotionCodeExecutor(self, user_email, code):
        """
        프로모션 코드를 적용한다.
        """
        cursor = self.conn.cursor()

        user_id = ciceron_lib.get_user_id(self.conn, user_email)
        query_searchPromoCodeId = """
            SELECT id FROM CICERON.PROMOTIONCODES_COMMON WHERE text = UPPER(%s)
            """
        cursor.execute(query_searchPromoCodeId, (code.upper(), ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            raise Exception("Promo code '%s' doesn't exist!" % code)

        code_id = ret[0]
        query_commonPromotionCodeExeutor = """
            INSERT INTO CICERON.USEDPROMOTION_COMMON VALUES (%s,%s)
            """
        cursor.execute(query_commonPromotionCodeExeutor, (code_id, user_id, ))

    def individualPromotionCodeChecker(self, user_id, code):
        # return: (val1, val2)
        #          val1: is valid code?
        #          val2: How much?
        """
        개인 프로모션 코드 validator이다.
        그 밖의 기능은 위와 같다.
        """
        cursor = self.conn.cursor()
        query_individualPromotionCode= """
            SELECT benefitPoint, expireTime, is_used
            FROM CICERON.PROMOTIONCODES_USER
            WHERE user_id = %s AND text = UPPER(%s)
            """
        cursor.execute(query_individualPromotionCode, (user_id, code.upper(), ))
        ret = cursor.fetchone()
    
        if ret is None or len(ret) == 0:
            return (3, 0, "There is no promo code matched.")
    
        benefitPoint = ret[0]
        expireTime = string2Date(ret[1])
        isUsed = ret[2]
    
        if expireTime < datetime.now():
            return (2, 0, "This promo code is expired.")
    
        if isUsed == 1:
            return (1, 0, "You've already used this code.")
    
        else:
            return (0, benefitPoint, "You may use this code.")

    def individualPromotionCodeExecutor(self, user_email, code):
        """
        개인용 프로모션 코드 적용기이다.
        """
        cursor = self.conn.cursor()
        user_id = ciceron_lib.get_user_id(self.conn, user_email)
        query_commonPromotionCodeExeutor = """
            UPDATE CICERON.PROMOTIONCODES_USER
            SET is_used = true 
            WHERE user_id = %s AND text = UPPER(%s)
            """
        cursor.execute(query_commonPromotionCodeExeutor, (user_id, code.upper(), ))

    def checkPoint(self, user_id, point_for_use):
        """
        포인트 조회 함수
        """
        cursor = self.conn.cursor()
    
        try:
            cursor.execute("SELECT amount FROM CICERON.RETURN_POINT WHERE id = %s", (user_id, ))
            current_point = float(cursor.fetchall()[0][0])
            if current_point - point_for_use < -0.00001:
                return False, current_point
    
            else:
                return True, current_point
            
        except Exception:
            traceback.print_exc()
            return False, None

    def alipayPayment(self, is_prod_server, request_id, user_email, amount
            , point_for_use=0
            , promo_type=''
            , promo_code=''
            , is_additional=False
            , is_groupRequest=False
            , is_public=False):

        host_name = ""
        if is_prod_server == False:
            host_name = "http://ciceron.xyz:5000"
        else:
            host_name = "http://ciceron.me:5000"
        pay_by = "web"

        postprocess_api = "%s/%s" % (host_name, 'api/user/requests/%d/payment/postprocess' % request_id)

        order_no = self._orderNoGenerator()
        param_dict = {
                'pay_via': 'alipay'
              , 'status': 'success'
              , 'user_id': user_email
              , 'pay_amt': amount
              , 'pay_by': pay_by
              , 'use_point': point_for_use
              , 'promo_type': promo_type
              , 'promo_code': promo_code
              , 'ciceron_order_no': order_no
              , 'is_additional': 'false' if is_additional == False else 'true'
              , 'is_groupRequest': 'false' if is_groupRequest == False else 'true'
              , 'is_public': 'false' if is_public == False else 'true'
                }
        return_url = ciceron_lib.apiURLOrganizer(postprocess_api, **param_dict)

        alipay_obj = Alipay(pid='2088021580332493', key='lksk5gkmbsj0w7ejmhziqmoq2gdda3jo', seller_email='contact@ciceron.me')
        params = {
            'subject': '诗谐论翻译'.decode('utf-8'),
            'out_trade_no': order_no,
            #'subject': 'TEST',
            'total_fee': '%.2f' % amount,
            'currency': 'USD',
            'quantity': '1',
            'return_url': return_url
            }

        provided_link = None
        try:
            if pay_by == 'web':
                provided_link = alipay_obj.create_forex_trade_url(**params)
            elif pay_by == 'mobile':
                provided_link = alipay_obj.create_forex_trade_wap_url(**params)
        except:
            return False, None

        return True, provided_link

    def iamportPayment(self, is_prod_server, request_id, user_email, amount
            , point_for_use=0
            , promo_type=None
            , promo_code=None
            , is_additional=False
            , is_groupRequest=False
            , is_public=False
            , **payload):
        """
        아임포트 No-ActiveX 결제 시스템이다.

        직접 카드번호 및 유효기간 등의 정보를 물러와서 결제를 바로 한다.
        그리고 이 자리에서 바로 결제를 하기 때문에 postprocessing 과정을 거쳐서 할 작업을 여기서 다 한다.
        """
        pay_by = "web"
        if is_prod_server == False:
            host_name = "http://ciceron.xyz"
        else:
            host_name = "http://ciceron.me"

        # Payload parameter check
        for item in ['card_number', 'expiry', 'birth', 'pwd_2digit']:
            if item not in payload:
                print "    Insufficient parameters. 'card_number', 'expiry', 'birth', 'pwd_2digit' are needed."
                return False, None

        new_payload = payload
        order_no = self._orderNoGenerator()
        # Should check USD->KRW currency
        # Hard coded: 1200
        kor_amount = int(amount * 1160)

        new_payload['merchant_uid'] = order_no
        new_payload['amount'] = kor_amount

        pay_module = Iamport(imp_key=2311212273535904, imp_secret='jZM7opWBO5K2cZfVoMgYJhsnSw4TiSmBR8JgyGRnLCpYCFT0raZbsrylYDehvBSnKCDjivG4862KLWLd')

        try:
            payment_result = pay_module.pay_onetime(**new_payload)
            double_check = pay_module.is_paid(**payment_result)
        except Iamport.ResponseError as e:
            print e.code
            print e.message
            raise Exception

        postprocess_api = "%s/%s" % (host_name, 'api/user/requests/%d/payment/postprocess' % request_id)
        param_dict = {
                'pay_via': 'iamport'
              , 'status': 'success'
              , 'user_id': user_email
              , 'pay_amt': amount
              , 'pay_by': pay_by
              , 'use_point': point_for_use
              , 'promo_type': promo_type
              , 'promo_code': promo_code
              , 'is_additional': 'false' if is_additional == False else 'true'
              , 'is_groupRequest': 'false' if is_groupRequest == False else 'true'
              , 'is_public': 'false' if is_public == False else 'true'
              , 'ciceron_order_id': order_no
                }
        return_url = ciceron_lib.apiURLOrganizer(postprocess_api, **param_dict)

        if double_check == False:
            print "    Iamport checkout abnormaly works!"
            return False, None
        else:
            return True, return_url

    def paypalPayment(self, is_prod_server, request_id, user_email, amount
            , point_for_use=0
            , promo_type=''
            , promo_code=''
            , is_additional=False
            , is_groupRequest=False
            , is_public=False):
        """
        페이팔은 그냥 모든 정보를 URL에 박아서 페이팔에 넘겨주면 된다.
        결제는 페이팔에서 한 후 콜백으로 postprocessing을 불러오기때문에, 여기서는 페이팔로의 링크만 제공해주면 된다.
        """
        pay_by = "web"
        host_name = ""
        # SANDBOX
        if is_prod_server == False:
            host_name = "http://ciceron.xyz"
            paypalrestsdk.configure(
                    mode="sandbox",
                    client_id="AQX4nD2IQ4xQ03Rm775wQ0SptsSe6-WBdMLldyktgJG0LPhdGwBf90C7swX2ymaSJ-PuxYKicVXg12GT",
                    client_secret="EHUxNGZPZNGe_pPDrofV80ZKkSMbApS2koofwDYRZR6efArirYcJazG2ao8eFqqd8sX-8fUd2im9GzBG"
            )

        # LIVE
        else:
            host_name = "http://ciceron.me"
            paypalrestsdk.set_config(
                    mode="live",
                    client_id="AevAg0UyjlRVArPOUN6jjsRVQrlasLZVyqJrioOlnF271796_2taD1HOZFry9TjkAYSTZExpyFyJV5Tl",
                    client_secret="EJjp8RzEmFRH_qpwzOyJU7ftf9GxZM__vl5w2pqERkXrt3aI6nsVBj2MnbkfLsDzcZzX3KW8rgqTdSIR"
                    )

        logging.basicConfig(level=logging.INFO)
        logging.basicConfig(level=logging.ERROR)

        postprocess_api = "%s/%s" % (host_name, 'api/user/requests/%d/payment/postprocess' % request_id)
        param_dict = {
                'pay_via': 'paypal'
              , 'status': 'success'
              , 'user_id': user_email
              , 'pay_amt': amount
              , 'pay_by': pay_by
              , 'use_point': point_for_use
              , 'promo_type': promo_type
              , 'promo_code': promo_code
              , 'is_additional': 'false' if is_additional == False else 'true'
              , 'is_groupRequest': 'false' if is_groupRequest == False else 'true'
              , 'is_public': 'false' if is_public == False else 'true'
                }
        return_url = ciceron_lib.apiURLOrganizer(postprocess_api, **param_dict)

        param_dict['status'] = 'fail'
        cancel_url = ciceron_lib.apiURLOrganizer(postprocess_api, **param_dict)

        payment = paypalrestsdk.Payment({
          "intent": "sale",
          "payer": {
            "payment_method": "paypal"},
          "redirect_urls":{
            "return_url": return_url,
            "cancel_url": cancel_url
            },
          "transactions": [{
            "amount": {
                "total": "%.2f" % amount,
                "currency": "USD",
            },
          "description": "Ciceron translation request fee USD: %f" % amount }]})
        rs = payment.create()  # return True or False
        paypal_link = None
        for item in payment.links:
            if item['method'] == 'REDIRECT':
                paypal_link = item['href']
                break

        if bool(rs) is True:
            return True, paypal_link

        else:
            return False, None

    def pointPayment(self, is_prod_server, request_id, user_email, amount
            , point_for_use=0
            , promo_type=''
            , promo_code=''
            , is_additional=False
            , is_groupRequest=False
            , is_public=False):
        """
        페이팔은 그냥 모든 정보를 URL에 박아서 페이팔에 넘겨주면 된다.
        결제는 페이팔에서 한 후 콜백으로 postprocessing을 불러오기때문에, 여기서는 페이팔로의 링크만 제공해주면 된다.
        """
        pay_by = "web"
        host_name = ""
        if is_prod_server == False:
            host_name = "http://ciceron.xyz"
        else:
            host_name = "http://ciceron.me"

        order_no = self._orderNoGenerator()
        postprocess_api = "%s/%s" % (host_name, 'api/user/requests/%d/payment/postprocess' % request_id)
        param_dict = {
                'pay_via': 'point'
              , 'status': 'success'
              , 'user_id': user_email
              , 'pay_amt': amount
              , 'pay_by': pay_by
              , 'use_point': point_for_use
              , 'promo_type': promo_type
              , 'promo_code': promo_code
              , 'is_additional': 'false' if is_additional == False else 'true'
              , 'is_groupRequest': 'false' if is_groupRequest == False else 'true'
              , 'is_public': 'false' if is_public == False else 'true'
              , 'ciceron_order_id': order_no
                }
        return_url = ciceron_lib.apiURLOrganizer(postprocess_api, **param_dict)

        return True, return_url

    def postProcess(self
            , user_email=None
            , request_id=None
            , pay_via=None
            , pay_by=None
            , is_succeeded=None
            , amount=0
            , use_point=0
            , promo_type=None
            , promo_code=None
            , is_additional=None
            , is_groupRequest=None
            , is_public=None
            , paymentId=None
            , PayerID=None
            , ciceron_order_id=None):

        user_id = ciceron_lib.get_user_id(self.conn, user_email)

        if is_succeeded == False:
            return False

        # Point deduction
        if use_point > 0:
            self._pointDeduction(user_id, use_point)

        # Use promo code
        if promo_type == 'common':
            self.commonPromotionCodeExecutor(user_email, promo_code)
        elif promo_type == 'indiv':
            self.individualPromotionCodeExecutor(user_email, promo_code)

        # Check payment in each payment platform
        payment_id = ""
        if pay_via == 'paypal' and is_succeeded == True:
            payment_id = paymentId
            payer_id = PayerID
            self._paypalPaymentCheck(payment_id, payer_id)

        elif pay_via == 'alipay' and is_succeeded == True:
            payment_id = ciceron_order_id

        elif pay_via == 'iamport' and is_succeeded == True:
            payment_id = ciceron_order_id

        elif pay_via == 'point' and is_succeeded == True:
            payment_id = ciceron_order_id

        # Set to 'paid'
        self._markAsPaid(request_id, is_additional)

        # Group request processing
        if is_groupRequest == 'true':
            groupRequestObj = GroupRequest(self.conn)
            groupRequestObj.updatePaymentInfo(request_id, user_id, pay_via, payment_id)

        if is_public == 'true':
            requestResellObj = RequestResell(self.conn)
            requestResellObj.setToPaid(request_id, user_id, pay_via, payment_id)

        # Insert payment info
        self._insertPaymentInfo(request_id, user_id, pay_via, payment_id, amount)

        return True

    def refundByPoint(self, user_id, points):
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                    UPDATE CICERON.REVENUE 
                    SET amount = amount + %s 
                    WHERE id = %s
                """, (points, user_id, ))

            return True

        except Exception:
            traceback.print_exc()
            return False
