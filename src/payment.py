

class Payment(object):
    def __init__(self, conn):
        self.conn = conn

    def alipayPayment(self, **kwargs):
        pass

    def iamportPayment(self, **kwargs):
        pass

    def paypalPayment(self, **kwargs):
        pass

    def pointPayment(self, **kwargs):
        pass

