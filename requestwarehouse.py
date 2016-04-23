# -*- coding: utf-8 -*-
from translator import Translator
from ciceron_lib import get_new_id
import nltk.data


class Warehousing:

    def __init__(self, conn):
        self.conn = conn
        self.sentence_detector = nltk.data.load('tokenizers/punkt/english.pickle')

    def __parseParagragh(self, strings):
        return strings.split('\n')

    def __parseSentence(self, strings):
        return self.sentence_detector.tokenize(strings.strip())

    def __unitOriginalDataInsert(self, request_id, paragragh_id, sentence_id, path, text):
        cursor = self.conn.cursor()

        try:
            query = """INSERT INTO CICERON.D_REQUEST_TEXTS
                           (id, paragragh_seq, sentence_seq, path, text, is_sent_to_machine, hit)
                       VALUES
                           (%s, %s, %s, %s, %s, false, 0) """

            cursor.execute(query, (request_id, paragragh_id, sentence_id, path, text, ))
            self.conn.commit()
            return True
        except Exception as e:
            print e
            return False
