# -*- coding: utf-8 -*-
import psycopg2
from detourserverConnector import Connector

DATABASE = None
if os.environ.get('PURPOSE') == 'PROD':
    DATABASE = "host=ciceronprod.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"
else:
    DATABASE = "host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"

class TranslationAgent:

    def __init__(self):
        self.conn = psycopg2.connect(DATEBASE)

    def getOneRawData(self):
        print "blahblah"
