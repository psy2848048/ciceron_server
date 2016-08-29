# -*- coding: utf-8 -*-
from translator import Translator
import nltk.data
import traceback


class Warehousing:

    def __init__(self, conn):
        self.conn = conn
        self.sentence_detector = nltk.data.load('tokenizers/punkt/english.pickle')

    def __parseParagragh(self, strings):
        result = strings.replace("\r", "").replace("\n  ", "\n\n")
        return result.split('\n\n')

    def __parseSentence(self, strings):
        return self.sentence_detector.tokenize(strings.strip())

    def _unitOriginalDataInsert(self, request_id, paragraph_id, sentence_id, path, text, new_translation_id, original_lang_id, target_lang_id):
        cursor = self.conn.cursor()

        query = """INSERT INTO CICERON.D_REQUEST_TEXTS
                       (id, paragraph_seq, sentence_seq, path, text, is_sent_to_machine, hit, translation_id, original_lang_id, target_lang_id)
                   VALUES
                       (%s, %s, %s, %s, %s, false, 0, %s, %s, %s) """

        cursor.execute(query, (request_id, paragraph_id, sentence_id, path, text, new_translation_id, original_lang_id, target_lang_id, ))
        self.conn.commit()

    def store(self, request_id, path, whole_texts, new_translation_id, original_lang_id, target_lang_id):
        paragraphs = self.__parseParagragh(whole_texts)
        for paragraph_seq, paragraph in enumerate(paragraphs, start=1):
            sentences = self.__parseSentence(paragraph)
            for sentence_seq, sentence in enumerate(sentences, start=1):
                self._unitOriginalDataInsert(request_id, paragraph_seq, sentence_seq, path, sentence, new_translation_id, original_lang_id, target_lang_id)

    def parseSentence(self, strings):
        sentences = strings.strip().replace('\r\n', '\n').split('\n')
        result = []
        for sentence in sentences:
            result.extend(self.sentence_detector.tokenize(strings.strip()))

        return result

    def _restore_string(self, request_id, source):
        cursor = self.conn.cursor()

        query_getRequestText = "SELECT text_id, translatedText_id FROM CICERON.F_REQUESTS WHERE id = %s"
        cursor.execute(query_getRequestText, (request_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return None

        request_text_id = res[0]
        translated_text_id = res[1]

        if source == 'requested_text':
            query_text = "SELECT paragraph_seq, sentence_seq, text FROM CICERON.D_REQUEST_TEXTS WHERE id = %s ORDER BY paragraph_seq, sentence_seq"
            cursor.execute(query_text, (request_text_id, ))
        elif source == 'translated_text':
            query_text = "SELECT paragraph_seq, sentence_seq, text FROM CICERON.D_TRANSLATED_TEXT WHERE id = %s ORDER BY paragraph_seq, sentence_seq"
            cursor.execute(query_text, (translated_text_id, ))

        fetched_array = cursor.fetchall()

        cur_paragraph_id = 1
        result_string = ""
        for idx, item in enumerate(fetched_array):
            paragraph_id = item[0]
            sentence_id = item[1]
            text = item[2]

            if paragraph_id != cur_paragraph_id:
                cur_paragraph_id = paragraph_id
                result_string += '\n' + text
            elif paragraph_id == cur_paragraph_id and idx != 0:
                result_string += ' ' + text

            else:
                result_string += text

        return result_string

    def _restore_array(self, request_id, source=None):
        cursor = self.conn.cursor()

        query_getRequestText = "SELECT text_id, translatedText_id FROM CICERON.F_REQUESTS WHERE id = %s"
        cursor.execute(query_getRequestText, (request_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return None

        request_text_id = res[0]
        translated_text_id = res[1] if res[1] != None else -1 # -1: Dummy

        inter_array_request = None
        inter_array_translation = None

        if source == 'requested_text' or source is None:
            query_text = """
                SELECT texts.paragraph_seq, texts.sentence_seq, texts.text, comm.comment_string
                FROM CICERON.F_REQUESTS req
                JOIN CICERON.D_REQUEST_TEXTS texts
                  ON req.text_id = texts.id
                LEFT OUTER JOIN CICERON.COMMENT_SENTENCE comm
                  ON req.id = comm.request_id
                    AND texts.paragraph_seq = comm.paragraph_seq                             
                    AND texts.sentence_seq = comm.sentence_seq                            
                WHERE req.id = %s
                ORDER BY texts.paragraph_seq, texts.sentence_seq 
            """
            cursor.execute(query_text, (request_id, ))
            inter_array_request = cursor.fetchall()

        if source == 'translated_text' or source is None:
            query_text = """
                SELECT texts.paragraph_seq, texts.sentence_seq, texts.text, comm.comment_string
                FROM CICERON.F_REQUESTS req
                JOIN CICERON.D_TRANSLATED_TEXT texts
                  ON req.translatedText_id = texts.id
                LEFT OUTER JOIN CICERON.COMMENT_SENTENCE comm
                  ON req.id = comm.request_id
                    AND texts.paragraph_seq = comm.paragraph_seq                             
                    AND texts.sentence_seq = comm.sentence_seq                            
                WHERE req.id = %s
                ORDER BY texts.paragraph_seq, texts.sentence_seq
            """
            cursor.execute(query_text, (request_id, ))
            inter_array_translation = cursor.fetchall()

        inter_array = zip(inter_array_request, inter_array_translation)

        query_paragraphComment = """
            SELECT texts.paragraph_seq, texts.text, comm.comment_string
                FROM CICERON.F_REQUESTS req
                JOIN CICERON.D_TRANSLATED_TEXT texts
                  ON req.translatedText_id = texts.id
                LEFT OUTER JOIN CICERON.COMMENT_PARAGRAPH comm
                  ON req.id = comm.request_id
                    AND texts.paragraph_seq = comm.paragraph_seq AND texts.sentence_seq = 1
                WHERE req.id = %s
                ORDER BY texts.paragraph_seq
        """
        cursor.execute(query_paragraphComment, (request_id, ))
        paragaphcomment_array = cursor.fetchall()

        result_array = []
        cur_paragraph_no = 0
        item = {}
        for idx, row in enumerate(inter_array):
            paragraph_seq = row[0][0]
            sentence_seq = row[0][1]
            original_text = row[0][2]
            translated_text = row[1][2]
            sentence_comment = row[0][3]

            if cur_paragraph_no != paragraph_seq:
                if idx != 0:
                    result_array.append(item)

                item = {}
                item['paragraph_seq'] = paragraph_seq
                item['paragraph_comment'] = paragaphcomment_array[ idx - 1 ][2]
                item['sentences'] = []

                cur_paragraph_no = paragraph_seq

            sentence_item = {}
            sentence_item['sentence_seq'] = sentence_seq
            sentence_item['original_text'] = original_text
            sentence_item['translated_text'] = translated_text
            sentence_item['sentence_comment'] = sentence_comment

            item['sentences'].append(sentence_item)

            if idx == len(inter_array) - 1:
                result_array.append(item)

        return result_array

    def restoreRequestByString(self, request_id):
        return self._restore_string(request_id, 'requested_text')

    def restoreTranslationByString(self, request_id):
        return self._restore_string(request_id, 'translated_text')

    def restoreArray(self, request_id):
        return self._restore_array(request_id)

    def updateTranslationOneLine(self, request_id, paragraph_id, sentence_id, text):
        cursor = self.conn.cursor()

        try:
            query_getRequestText = "SELECT translatedText_id FROM CICERON.F_REQUESTS WHERE id = %s"
            cursor.execute(query_getRequestText, (request_id, ))
            translated_text_id = None
            res = cursor.fetchone()
            if res is None or len(res) == 0:
                return False

            translated_text_id = res[0]

            query_update = """
                UPDATE CICERON.D_TRANSLATED_TEXT
                  SET text = %s
                  WHERE id=%s AND paragraph_seq=%s AND sentence_seq=%s"""
            cursor.execute(query_update, (text, translated_text_id, paragraph_id, sentence_id, ))
            self.conn.commit()
            return True

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False

    def getTranslationOneLine(self, request_id, paragraph_id, sentence_id):
        cursor = self.conn.cursor()

        query_getRequestText = "SELECT translatedText_id FROM CICERON.F_REQUESTS WHERE id = %s"
        cursor.execute(query_getRequestText, (request_id, ))
        translated_text_id = None
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return False, None

        translated_text_id = res[0]

        query_update = """
            SELECT text
              FROM CICERON.D_TRANSLATED_TEXT
              WHERE id=%s AND paragraph_seq=%s AND sentence_seq=%s"""
        cursor.execute(query_update, (translated_text_id, paragraph_id, sentence_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return False, None

        return_text = res[0]
        return True, return_text

    def updateSentenceComment(self, request_id, paragraph_id, sentence_id, comment_string):
        cursor = self.conn.cursor()

        query_count = """
            SELECT count(*) FROM CICERON.COMMENT_SENTENCE
            WHERE request_id = %s AND paragraph_seq = %s AND sentence_seq = %s
        """
        query_insert = """
            INSERT INTO CICERON.COMMENT_SENTENCE
              (request_id, paragraph_seq, sentence_seq, comment_string)
            VALUES (%s, %s, %s, %s)
        """
        query_update = """
            UPDATE CICERON.COMMENT_SENTENCE
              SET comment_string = %s
            WHERE request_id = %s AND paragraph_seq = %s AND sentence_seq = %s
        """

        try:
            cursor.execute(query_count, (request_id, paragraph_id, sentence_id, ))
            count = cursor.fetchone()[0]

            if count == 0:
                cursor.execute(query_insert,
                        (request_id, paragraph_id, sentence_id, comment_string, ))
            else:
                cursor.execute(query_update,
                        (comment_string, request_id, paragraph_id, sentence_id, ))
            self.conn.commit()

        except Exception:
            self.conn.rollback()
            traceback.print_exc()
            return False

        return True

    def updateParagraphComment(self, request_id, paragraph_id, comment_string):
        cursor = self.conn.cursor()

        query_count = """
            SELECT count(*) FROM CICERON.COMMENT_PARAGRAPH
            WHERE request_id = %s AND paragraph_seq = %s
        """
        query_insert = """
            INSERT INTO CICERON.COMMENT_PARAGRAPH
              (request_id, paragraph_seq, comment_string)
            VALUES (%s, %s, %s)
        """
        query_update = """
            UPDATE CICERON.COMMENT_PARAGRAPH
              SET comment_string = %s
            WHERE request_id = %s AND paragraph_seq = %s
        """

        try:
            cursor.execute(query_count, (request_id, paragraph_id, ))
            count = cursor.fetchone()[0]

            if count == 0:
                cursor.execute(query_insert,
                        (request_id, paragraph_id, comment_string, ))
            else:
                cursor.execute(query_update,
                        (comment_string, request_id, paragraph_id, ))
            self.conn.commit()

        except Exception:
            self.conn.rollback()
            traceback.print_exc()
            return False

        return True

    @classmethod
    def initTest(cls, name, method):
        setattr(cls, name, method)

if __name__ == "__main__":
    # Test purpose

    def _unitOriginalDataInsert(self, request_id, paragraph_id, sentence_id, path, text, new_translation_id, original_lang_id, target_lang_id):
        print "%s | %s | %s | %s | %s | %s | %s" % (request_id, paragraph_id, sentence_id, path, text, original_lang_id, target_lang_id)

    conn = None
    Warehousing.initTest('_unitOriginalDataInsert', _unitOriginalDataInsert)
    warehousing = Warehousing(conn)
    #warehousing.__unitOriginalDataInsert = __unitOriginalDataInsert

    request_id = 1
    path = "fake/path"
    whole_text = u"""논문의 평균 분량은 분야마다 다 다르다. 수학 같은 경우는 정말 A4용지 반 장 분량(…)의 논문이라고 하더라도 그 내용이 어떠한가에 따라서 세계를 발칵 뒤집는 불후의 논문이 될 수도 있다.[2] 사회과학은 그보다는 좀 더 길어진다. 대개의 심리학 논문은 20~30장 선에서 어지간하면 글이 끝나고, 정치학은 비슷하거나 그보다는 좀 더 긴 편이다. 논문의 방대함으로는 (연구주제에 따라서는) 행정학이 유명한데, 이 분야는 나랏님 하시는 일을 다루는지라 일단 데이터 양부터가 장난이 아니다. 오죽하면 행정학자들끼리 "우리는 학회를 한번 갔다오면 왜 연구실에 전화번호부 두께의 학회지가 너댓 편씩 쌓이지?"(…) 같은 농담을 주고받을 정도이니...[3]
그 외에도 논문 분량이 당연히 백여 페이지를 한참 넘을 것으로 기대되는 분야들은 꽤 있다. 단, 학술지 논문에 비해 우리 위키러들이 정말로 궁금할 학위논문의 경우 분량이 그 5~10배 가량 육박하는 경우가 많으니 참고. 일부 박사논문은 납본되는 걸 보면 정말로 책 한 권이 나온다.(...)  좀 심하게 말하면, 어떤 학술적인 글을 쓰는데 분량을 신경쓰는 것은 레포트 쓰는 학부생들의 수준에서 바라보는 시각일 수 있다. (굳이 좋게 평하자면, 최소한의 논문다운 논문을 쓰기 위한 휴리스틱이다.) 학계에서 논문의 가치는 그 논문의 양이 얼마나 방대한지는 전혀 상관없다. 일부 사회과학 분야 논문들은 가설을 한번에 30개 이상씩(!) 검증하기도 하나, 그런 논문이 가설 하나 검증하는 논문, 아니 아무도 신경쓰지 않은 문제를 최초로 제기하느라 가설은 아예 검증하지도 못하고 제안하기만 한 논문보다 우월하다고 취급되지는 않는다.
가설을 많이 검증한다고 해도 그 검증과정이나 논리적 차원에서 결함이나 비약이 있다면 가차없이 탈탈 털릴 뿐이다. 원론적으로, 인문학이나 예술분야라고 해도 자신의 독창적 생각을 타인에게 설득력 있게 전달하는 과정이 중요하게 취급되는 것은 당연하다.  공연히 분량을 늘린답시고 논문에서 논거를 질질 끌거나 쓸데없는 데이터를 넣거나 하면 당연히 또 탈탈 털린다. 애초에 학계라는 곳은 타인의 언급을 인용하는 것조차도 논리적 전개에 불필요해 보인다 싶으면 가차없이 불벼락을 내리는 바닥이다.[4] 필요한 말을 안 써서 까이기도 하지만, 쓸데없는 말이 너무 많다고 까이기도 하니, 논문을 준비하는 연구자는 이래저래 피곤하다. 게다가 교수들도 긴 글 읽기는 싫어하는 경우가 많다.(…)[5] """

    warehousing.store(request_id, path, whole_text, 1, 0, 0)
