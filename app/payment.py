# -*- coding: utf-8 -*-

import traceback
import random
from datetime import datetime, timedelta, tzinfo
import string
import logging

import paypalrestsdk
from iamport import Iamport
from alipay import Alipay

try:
    from . import ciceron_lib
except:
    import ciceron_lib
try:
    from .groupRequest import GroupRequest
except:
    from groupRequest import GroupRequest

try:
    from .requestResell import RequestResell
except:
    from requestResell import RequestResell

try:
    from ciceron_lib import login_required
except:
    from .ciceron_lib import login_required

ZERO = timedelta(0)

class UTC(tzinfo):
    def utcoffset(self, dt):
        return ZERO
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return ZERO

utc = UTC()

class Payment(object):
    def __init__(self, conn):
        self.conn = conn

    def _orderNoGenerator(self):
        """
        Iamport 방식으로 결제할 때에는 Iamport 단에서 주문번호를 만들어 주지 않기 때문에 우리가 직접 만들어야 한다.
        주문번호 형식은 YYYYMMDDxxxx (ex 20160716abcd) 방식으로 한다.
        """
        cursor = self.conn.cursor()
        order_no = None
    
        for _ in range(1000):
            order_no = datetime.strftime(datetime.now(), "%Y%m%d") + ciceron_lib.random_string_gen(size=4)
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
        # To Be Depricated
        cursor = self.conn.cursor()

        if is_additional == False:
            query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_paid = %s WHERE id = %s"
        else:
            query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_additional_points_paid = %s WHERE id = %s"
        cursor.execute(query_setToPaid, (True, request_id, ))

    def _paypalPaymentCheck(self, payment_id, payer_id):
        payment = paypalrestsdk.Payment.find(payment_id)
        payment.execute({"payer_id": payer_id})

    def _insertPaymentInfo(self, product, request_id, user_id, payment_platform, payment_id, amount):
        # Payment information update
        cursor = self.conn.cursor()
        payment_info_id = ciceron_lib.get_new_id(self.conn, "PAYMENT_INFO")
        query = """
            INSERT INTO CICERON.PAYMENT_INFO
                (id, product, request_id, client_id, payed_via, order_no, pay_amount, payed_time)
            VALUES
                (%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)"""

        cursor.execute(query,
                (  payment_info_id
                 , product
                 , request_id
                 , user_id
                 , payment_platform
                 , payment_id
                 , amount
                 , )
                )

    def _organizePostprocessApiAddress(self, product, request_id):
        endpoint = "api/v2/user/payment/postprocess"
        #return endpoint.format(
        #            product=product
        #          , request_id=request_id
        #       )
        return endpoint

    def _organizeMarkAsPaidApiAddress(self, product, request_id):
        endpoint = "api/v2/{product}/request/{request_id}/markAsPaid"
        return endpoint.format(
                    product=product
                  , request_id=request_id
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
        expireTime = ret[2]
    
        if expireTime < datetime.now(utc):
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
        expireTime = ret[1]
        isUsed = ret[2]
    
        if expireTime < datetime.now(utc):
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

    def alipayPayment2(self, is_prod_server, request_id, user_email, amount, product
            , point_for_use=0
            , promo_type=''
            , promo_code=''
            ):

        host_name = ""
        if is_prod_server == False:
            host_name = "http://ciceron.xyz:5000"
        else:
            host_name = "http://ciceron.me:5000"

        postprocess_endpoint = self._organizePostprocessApiAddress(product, request_id)
        postprocess_api = "{}/{}".format(host_name, postprocess_endpoint)

        order_no = self._orderNoGenerator()
        param_dict = {
                'payment_platform': 'alipay'
              , 'product': product
              , 'request_id': request_id
              , 'status': 'success'
              , 'user_email': user_email
              , 'amount': amount
              , 'point_for_use': point_for_use
              , 'promo_type': promo_type
              , 'promo_code': promo_code
              , 'ciceron_order_no': order_no
                }
        return_url = ciceron_lib.dictToUrlParam(postprocess_api, **param_dict)

        alipay_obj = Alipay(pid='2088021580332493', key='lksk5gkmbsj0w7ejmhziqmoq2gdda3jo', seller_email='contact@ciceron.me')
        params = {
            'subject': '诗谐论翻译'.decode('utf-8'),
            'out_trade_no': order_no,
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

    def iamportPayment2(self, is_prod_server, request_id, user_email, amount, product
            , point_for_use=0
            , promo_type=None
            , promo_code=None
            , **payload):
        """
        아임포트 No-ActiveX 결제 시스템이다.

        직접 카드번호 및 유효기간 등의 정보를 물러와서 결제를 바로 한다.
        그리고 이 자리에서 바로 결제를 하기 때문에 postprocessing 과정을 거쳐서 할 작업을 여기서 다 한다.
        """
        if is_prod_server == False:
            host_name = "http://ciceron.xyz"
        else:
            host_name = "http://ciceron.me"

        # Payload parameter check
        for item in ['card_number', 'expiry', 'birth', 'pwd_2digit']:
            if item not in payload:
                print("    Insufficient parameters. 'card_number', 'expiry', 'birth', 'pwd_2digit' are needed.")
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
            print(e.code)
            print(e.message)
            raise Exception

        postprocess_endpoint = self._organizePostprocessApiAddress(product, request_id)
        postprocess_api = "{}/{}".format(host_name, postprocess_endpoint)
        param_dict = {
                'payment_platform': 'iamport'
              , 'product': product
              , 'request_id': request_id
              , 'status': 'success'
              , 'user_email': user_email
              , 'amount': amount
              , 'point_for_use': point_for_use
              , 'promo_type': promo_type
              , 'promo_code': promo_code
              , 'ciceron_order_id': order_no
                }
        return_url = ciceron_lib.dictToUrlParam(postprocess_api, **param_dict)

        if double_check == False:
            print("    Iamport checkout abnormaly works!")
            return False, None
        else:
            return True, return_url

    def paypalPayment2(self, is_prod_server, request_id, user_email, amount, product
            , point_for_use=0
            , promo_type=''
            , promo_code=''):
        """
        페이팔은 그냥 모든 정보를 URL에 박아서 페이팔에 넘겨주면 된다.
        결제는 페이팔에서 한 후 콜백으로 postprocessing을 불러오기때문에, 여기서는 페이팔로의 링크만 제공해주면 된다.
        """
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

        postprocess_endpoint = self._organizePostprocessApiAddress(product, request_id)
        postprocess_api = "{}/{}".format(host_name, postprocess_endpoint)
        param_dict = {
                'payment_platform': 'paypal'
              , 'product': product
              , 'request_id': request_id
              , 'status': 'success'
              , 'user_email': user_email
              , 'amount': amount
              , 'use_point': point_for_use
              , 'promo_type': promo_type
              , 'promo_code': promo_code
                }
        return_url = ciceron_lib.dictToUrlParam(postprocess_api, **param_dict)

        param_dict['status'] = 'fail'
        cancel_url = ciceron_lib.dictToUrlParam(postprocess_api, **param_dict)

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

    def pointPayment2(self, is_prod_server, request_id, user_email, amount, product
            , point_for_use=0
            , promo_type=''
            , promo_code=''):
        """
        페이팔은 그냥 모든 정보를 URL에 박아서 페이팔에 넘겨주면 된다.
        결제는 페이팔에서 한 후 콜백으로 postprocessing을 불러오기때문에, 여기서는 페이팔로의 링크만 제공해주면 된다.
        """
        host_name = ""
        if is_prod_server == False:
            host_name = "http://ciceron.xyz"
        else:
            host_name = "http://ciceron.me"

        order_no = self._orderNoGenerator()
        postprocess_endpoint = self._organizePostprocessApiAddress(product, request_id)
        postprocess_api = "{}/{}".format(host_name, postprocess_endpoint)
        param_dict = {
                'payment_platform': 'point'
              , 'product': product
              , 'request_id': request_id
              , 'status': 'success'
              , 'user_email': user_email
              , 'amount': amount
              , 'point_for_use': point_for_use
              , 'promo_type': promo_type
              , 'promo_code': promo_code
              , 'ciceron_order_id': order_no
                }
        return_url = ciceron_lib.dictToUrlParam(postprocess_api, **param_dict)

        return True, return_url

    def postProcess2(self
            , user_email=None
            , product=None
            , request_id=None
            , payment_platform=None
            , is_succeeded=None
            , amount=0
            , point_for_use=0
            , promo_type=None
            , promo_code=None
            , paymentId=None
            , PayerID=None
            , ciceron_order_id=None):

        user_id = ciceron_lib.get_user_id(self.conn, user_email)

        if is_succeeded == False:
            return False, None

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
        if payment_platform == 'paypal' and is_succeeded == True:
            payment_id = paymentId
            payer_id = PayerID
            self._paypalPaymentCheck(payment_id, payer_id)

        elif payment_platform == 'alipay' and is_succeeded == True:
            payment_id = ciceron_order_id

        elif payment_platform == 'iamport' and is_succeeded == True:
            payment_id = ciceron_order_id

        elif payment_platform == 'point' and is_succeeded == True:
            payment_id = ciceron_order_id

        markAsPaid_api = self._organizePostprocessApiAddress(product, request_id)
        self._insertPaymentInfo(product, request_id, user_id, payment_platform, payment_id, amount)

        return True, markAsPaid_api

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

    #######################################################################################
    ############ BELOW FUNCTIONS ARE DEPRICATED AND WILL BE DELETED!!!!!! #################
    #######################################################################################

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
                print("    Insufficient parameters. 'card_number', 'expiry', 'birth', 'pwd_2digit' are needed.")
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
            print(e.code)
            print(e.message)
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
            print("    Iamport checkout abnormaly works!")
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

    #######################################################################################
    ############ ABOVE FUNCTIONS ARE DEPRICATED AND WILL BE DELETED!!!!!! #################
    #######################################################################################



class PaymentAPI(object):
    def __init__(self, app, endpoints):
        self.app = app
        self.endpoints = endpoints

        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in self.endpoints:
            self.app.add_url_rule('{}/user/payment/checkPromotionCode'.format(endpoint), view_func=self.checkPromotionCode, methods=["POST"])
            self.app.add_url_rule('{}/user/payment/start'.format(endpoint), view_func=self.payment, methods=["POST"])
            self.app.add_url_rule('{}/user/payment/postprocess'.format(endpoint), view_func=self.postprocess, methods=["GET"])

    @login_required
    def checkPromotionCode(self):
        """
        프로모션 코드 유효성 체크. 이 API에서는 체크만 하고 적용은 결제 API에서 이루어짐.

        **Parameters**
          **"promoCode"**: 프로모션 코드. 대소문자 가리지 않음.

        **Response**
          **200**
            .. code-block:: json
               :linenos:

               {
                 "promoType": "indiv", // or "common"
                 "point": 2, // 할인해주는 포인트
               }
               // "common" -> 누구나 적용하는 캠페인
               // "indiv" -> 개인한테만 제공

          **402**: 존재는 하나 조건이 맞지 않는 코드

          **405**: 존재하지 않는 코드

        """
        user_id = get_user_id(g.db, session['useremail'])
        parameters = parse_request(request)
        paymentObj = Payment(g.db)
    
        code = parameters['promoCode'].upper()
    
        isCommonCode, commonPoint, commonMessage = paymentObj.commonPromotionCodeChecker(user_id, code)
        isIndivCode, indivPoint, indivMessage = paymentObj.individualPromotionCodeChecker(user_id, code)
        if isCommonCode in [1, 2]:
            return make_response(json.jsonify(
                promoType=None, message=commonMessage, code=isCommonCode, point=0), 402)
        elif isIndivCode in [1, 2]:
            return make_response(json.jsonify(
                promoType=None, message=indivMessage, code=isIndivCode, point=0), 402)
    
        elif isCommonCode == 0:
            return make_response(json.jsonify(
                promoType='common', message=commonMessage, code=0, point=commonPoint), 200)
        elif isIndivCode == 0:
            return make_response(json.jsonify(
                promoType='indiv', message=indivMessage, code=0, point=indivPoint), 200)
    
        else:
            return make_response(json.jsonify(
                promoType=None, message="There is no promo code matched,", code=3, point=0), 405)
            
    @login_required
    def payment(self):
        """
        결제 진행 API

        **Parameters**
          **"payment_platform"**: 지불 플랫폼 ("alipay", "paypal", "iamport", "point")
          **"product"**: 구매한 내부 플랫폼 이름 ("l10n", "pretranslation", "groupRequest", "f2finterpreter")
          **"request_id"**: 각 플랫폼에서의 의뢰 번호
          **"amount"**: 지불 금액 (단위: USD)
          **"promo_type"**: 쿠폰 타입 ("indiv": 개인적용, "common": 마구 뿌린 프로모션)
          **"point_for_use"**: 결제시 사용할 포인트. 사용한 만큼 결제금에서 차감

          **"card_number"**: 카드번호 (iamport에서만 필요,"xxxx-xxxx-xxxx-xxxx" or "xxxx-xxxx-xxxx-xxx"[AMEX] )
          **"expiry"**: 유효기간 (iamport에서만 필요, "YYYY-MM")
          **"birth"**: [개인] 생년월일 "YYMMDD", [사업자] 사업자등록번호 "xxxxxxxxxx" (iamport 전용)
          **"pwd_2digit"**: 비밀번호 앞 2자리 (iamport 전용)
          **"buyer_name"**: 구매자 이름 (iamport 전용, OPTIONAL)
          **"buyer_email"**: 구매자 이메일 (iamport 전용, OPTIONAL)

        **Response**
          **200**
            .. code-block:: json
               :linenos:

               {
                 "link": "http://payment.paypalalipay.com/paymemnt/blahblah" // 리다이렉팅 할 주소
               }

          **410**: 포인트 보유량이 사용할 포인트보다 적음
          **411**: 유효하지 않은 쿠폰 번호
          **412**: 결제준비 실패

        """
        paymentObj = Payment(g.db)
        parameters = parse_request(request)

        email = session['useremail']
        payment_platform = parameters['payment_platform']
        product = float(parameters['product'])
        request_id = float(parameters['request_id'])
        amount = float(parameters['amount'])
        promo_type = parameters.get('promo_type', 'null')
        promo_code = parameters.get('promo_code', 'null')
        point_for_use = float(parameters.get('point_for_use', 0))

        user_id = ciceron_lib.get_user_id(g.db, email)

        # 아임포트 직접결제를 위한 파라미터
        payload = None
        if payment_platform == 'iamport':
            payload = {}

            payload['card_number'] = parameters['card_number']
            payload['expiry'] = parameters['expiry']
            payload['birth'] = parameters['birth']
            payload['pwd_2digit'] = parameters['pwd_2digit']
            payload['buyer_name'] = parameters.get('buyer_name', "Anonymous")
            payload['buyer_email'] = parameters.get('buyer_email', "anon@anon.com")

        # 결제금액 없으면 바로 지불처리
        if amount < 0.01:
            is_payment_ok, link = paymentObj.pointPayment2(is_prod, request_id, email, 0, product)
            if is_payment_ok == True:
                return make_response(json.jsonify(
                    link=link), 200)
            else:
                return make_response(json.jsonify(
                    link=link), 412)

        is_prod = False
        if os.environ.get('PURPOSE') == 'PROD':
            is_prod = True

        # Point test
        cur_amount = amount
        if point_for_use > 0.00001:
            is_point_usable, cur_amount = paymentObj.checkPoint(user_id, point_for_use)
            if cur_amount - point_for_use < -0.00001:
                return make_response(json.jsonify(
                    message="Fail"), 410)

        # Promo code test
        if promo_type != 'null':
            isCommonCode, commonPoint, commonMessage = paymentObj.commonPromotionCodeChecker(email, promo_code)
            isIndivCode, indivPoint, indivMessage = paymentObj.individualPromotionCodeChecker(email, promo_code)
            if isCommonCode == 0:
                cur_amount = cur_amount - commonPoint
            elif isIndivCode == 0:
                cur_amount = cur_amount - indivPoint
            else:
                return make_response(json.jsonify(
                    message="Fail"), 411)

        # Send payment request
        is_payment_ok, link = False, ""
        if payment_platform == 'alipay' and cur_amount > 0.0001:
            is_payment_ok, link = paymentObj.alipayPayment2(is_prod, request_id, email, cur_amount, product
                    , point_for_use=point_for_use
                    , promo_type=promo_type
                    , promo_code=promo_code
                    )

        elif payment_platform == 'paypal' and cur_amount > 0.0001:
            is_payment_ok, link = paymentObj.paypalPayment2(is_prod, request_id, email, cur_amount, product
                    , point_for_use=point_for_use
                    , promo_type=promo_type
                    , promo_code=promo_code
                    )

        elif payment_platform == 'iamport' and cur_amount > 0.0001:
            is_payment_ok, link = paymentObj.iamportPayment2(is_prod, request_id, email, cur_amount, product
                    , point_for_use=point_for_use
                    , promo_type=promo_type
                    , promo_code=promo_code
                    , **payload
                    )

        else:
            is_payment_ok, link = paymentObj.pointPayment2(is_prod, request_id, email, cur_amount, product
                    , point_for_use=point_for_use
                    , promo_type=promo_type
                    , promo_code=promo_code
                    )

        # Return
        if is_payment_ok:
            g.db.commit()
            return make_response(json.jsonify(
                link=link), 200)

        else:
            g.db.rollback()
            return make_response(json.jsonify(
                message="Fail"), 412)


    def postprocess(self):
        """
        결제 진행 이후 내부에서 결제 완료 처리하는 API.

        Paypal, Alipay같은 경우 결제 완료 후 Redirect할 주소를 넣어 결제 이후의 내부 쇼핑몰과 연결고리를 만들게 된다.

        Frontend에서 직접 call할 일은 없다.
        """
        paymentObj = Payment(g.db)

        payload = {
              'user_email': request.args['user_email']
            , 'product': request.args['product']
            , 'request_id': request.args['request_id']
            , 'payment_platform': request.args['payment_platform']
            , 'is_succeeded': True if request.args['status'] == "success" else False
            , 'amount': float(request.args.get('amount'))
            , 'point_for_use': float(request.args.get('point_for_use', 0))
            , 'promo_type': request.args.get('promo_type', None)
            , 'promo_code': request.args.get('promo_code', None)
            , 'paymentId': request.args.get('paymentId', None)
            , 'PayerID': request.args.get('PayerID', None)
            , 'ciceron_order_id': request.args.get('ciceron_order_id', None)
        }

        is_succeeded, redirect_address = paymentObj.postProcess2(**payload)

        if is_succeeded == True:
            g.db.commit()
            return redirect(redirect_address, code=302)

        else:
            g.db.rollback()
            return make_response(json.jsonify(message="Payment fail"), 410)
