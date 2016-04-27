# -*- coding: utf-8 -*-
import psycopg2
from detourserverConnector import Connector
import random, argparse, traceback, os, sys


DATABASE = None
if os.environ.get('PURPOSE') == 'PROD':
    DATABASE = "host=ciceronprod.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=%s"
else:
    DATABASE = "host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=%s"

class TranslationAgent:

    def __init__(self, dbInfo):
        self.conn = psycopg2.connect(dbInfo)
        self.connector = Connector()

    def getOneRawData(self):
        cursor = self.conn.cursor()

        query = """SELECT paragragh_seq, sentence_seq, text,
                      translation_id, original_lang_id, target_lang_id
                   FROM CICERON.D_REQUEST_TEXTS
                   WHERE is_sent_to_machine != true LIMIT 1"""

        cursor.execute(query)
        result = cursor.fetchone()

        if result is None or len(result) == 0:
            return False, None
        else:
            return True, result

    def fillInitialTranslatedData(self, paragragh_seq, sentence_seq, sentence, translation_id, original_lang_id, target_lang_id):
        cursor = self.conn.cursor()

        try:
            # Get translated data from detour server
            data = self.connector.getTranslatedData(sentence, original_lang_id, target_lang_id)
            query_fillTranslatedData = """
                INSERT INTO CICERON.D_TRANSLATED_TEXT (id, paragragh_seq, sentence_seq, google_result, yandex_result, bing_result)
                  VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(query_fillTranslatedData,
                    (translation_id, paragragh_seq, sentence_seq
                    , data['google'], data['yandex'], data['bing'], ) )

            # Show randomly selected data amaong google, bing, and yandex result as initial translation
            ran_num = random.randint(1, 3)
            query_setInitTranslation = None
            if ran_num == 1:
                query_setInitTranslation = """
                    UPDATE CICERON.D_TRANSLATED_TEXT
                      SET text = google_result
                      WHERE id=%s AND paragragh_seq=%s AND sentence_seq=%s"""
            elif ran_num == 2:
                query_setInitTranslation = """
                    UPDATE CICERON.D_TRANSLATED_TEXT
                      SET text = yandex_result
                      WHERE id=%s AND paragragh_seq=%s AND sentence_seq=%s"""
            elif ran_num == 3:
                query_setInitTranslation = """
                    UPDATE CICERON.D_TRANSLATED_TEXT
                      SET text = bing_result
                      WHERE id=%s AND paragragh_seq=%s AND sentence_seq=%s"""
            cursor.execute(query_setInitTranslation, (translation_id, paragragh_seq, sentence_seq, ))

            # Mark as complete initial translation by machine
            query_markAsComplete = "UPDATE CICERON.D_REQUEST_TEXTS SET is_sent_to_machine = true WHERE translation_id=%s AND paragragh_seq=%s AND sentence_seq=%s"
            cursor.execute(query_markAsComplete, (translation_id, paragragh_seq, sentence_seq, ))

            self.conn.commit()

            return True

        except Exception:
            print str(data)
            traceback.print_exc()
            self.conn.rollback()

            return False

    def run(self):
        while True:
            is_need_initTrans, data = self.getOneRawData()
            if is_need_initTrans == False:
                break

            is_ok = self.fillInitialTranslatedData(data[0], data[1], data[2], data[3], data[4], data[5])
            if is_ok == False:
                sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Translation agent')
    parser.add_argument('--dbpass', dest='dbpass', help='DB password')
    parser.add_argument('--check', dest='check', default='false', help='Just for check')
    args = parser.parse_args()

    dbInfo = DATABASE % args.dbpass
    agent = TranslationAgent(dbInfo)

    if args.check == 'false':
        agent.run()
    else:
        checker, _ = agent.getOneRawData()
        if checker == True:
            f = open('/tmp/translation.log', 'w')
            f.close()
