# -*- coding: utf-8 -*-
import xmltodict
import json
import csv
import io
import hashlib
import codecs
import traceback
import os
import re
import tempfile
from collections import OrderedDict

from nslocalized import StringTable
import nltk.data
try:
    from . import ciceron_lib
except:
    import ciceron_lib


class I18nHandler(object):

    def __init__(self, conn):
        self.conn = conn
        self.sentence_detector = nltk.data.load('tokenizers/punkt/english.pickle')

    def __getCountryNameById(self, lang_id):
        query = "SELECT text FROM CICERON.D_LANGUAGES WHERE id = %s"
        cursor = self.conn.cursor()

        cursor.execute(query, (lang_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return "!null!"
        else:
            return res[0]

    def __getCountryCodeById(self, lang_id):
        query = "SELECT google_code FROM CICERON.D_LANGUAGES WHERE id = %s"
        cursor = self.conn.cursor()

        cursor.execute(query, (lang_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return "!null!"
        else:
            return res[0]

    def __getIdByCountryName(self, country_name):
        query = "SELECT id FROM CICERON.D_LANGUAGES WHERE text = %s"
        cursor = self.conn.cursor()

        cursor.execute(query, (country_name, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return -1
        else:
            return res[0]

    def __getIdByCountryCode(self, country_code):
        query = "SELECT id FROM CICERON.D_LANGUAGES WHERE google_code = %s"
        cursor = self.conn.cursor()

        cursor.execute(query, (country_code, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return -1
        else:
            return res[0]

    def __getLangCodesByRequestId(self, request_id):
        query = """
            SELECT original_lang_id, target_lang_id
              FROM CICERON.F_REQUESTS
              WHERE id = %s"""
        cursor = self.conn.cursor()
        cursor.execute(query, (request_id, ))
        res = cursor.fetchone()

        if res is None or len(res) == 0:
            return (-1, None)
        else:
            return (res[0], res[1])

    # 각 UX별 서버 작업
    # 1. 새로 받아올 때
    #   1) Parsing / MD5 Hashing (Done)
    #   2) Dict to DB
    #   3) History 검색 / 초벌번역 진행
    #
    # 2. 번역가에게 보여줄 때
    #   1) DB to dict
    #   2) Dict to web JSON
    #
    # 3. 의뢰인이 Variable 통으로 날릴 때
    #   1) F_I18N_TEXT_MAPPINGS / D_I18N_VARIABLE_NAMES / F_I18N_VALUES 레코드 삭제
    #
    # 4. 의뢰인이 Variable 이름 수정할 때
    #   1) D_I18N_VARIABLE_NAMES 업데이트
    #
    # 5. 번역가가 번역 입력할 때
    #   1) History 검색 -> 중복자료 있으면 ID 사용, 없으면 새로 ID 땀
    #
    # 6. 번역가가 문단견해 / 문장 코멘트 입력
    #   1) 문단 / 문장번호 받아서 테이블에 입력 (기존 라이브러리 활용)

    # 필요한 메소드
    # 1. 각 형식 Parsing
    #   1) 문단/문장분해
    #   2) DB입력
    # 2. MD5 hasher
    # 3. 번역 History 검색
    #   1) 의뢰의 원문언어, 타겟언어 가져옴
    #   2) 원문 MD5 검색 -> Text ID 가져옴, Hit counter +1
    #   3) Text ID를 이용하여 해당 Text ID를 사용했던 Mapping ID 모두 가져옴
    #   4) 의뢰 언어의 Mapping ID들과, 그것의 Request id를 이용하여 원문언어 타겟언어 일치하는 Request ID 필터링하여 Mapping ID 수 줄이기 (번역이 완료된 의뢰 중 검색)
    #   5) 주어진 Mapping ID 이용하여 text id 추출, 그리고 text 추출
    #   6) text가 없으면 번역기 갔다오고 ID 새로 따서 삽입, is_curated = false
    # 4. Variable 삭제
    #   1) 해당 ID 삭제
    #   2) Variable과 연결된 텍스트 모두 삭제
    # 5. Variable 이름 번경
    # 6. 번역 입력: 3번의 1)~5) 수행 후 텍스트 검색되면 해당 text 제공 is_curated=True, 검색 안되면 새 text ID 딴 후 새 Mapping 넣음, is_curated=False
    # 7. 각종 코멘트 입력

    def __getMD5(self, text):
        hash_maker = hashlib.md5()
        hash_maker.update(text.encode('utf-8'))
        return hash_maker.hexdigest()

    def __getTextId(self, cursor, text):
        hashed_text = self.__getMD5(text)
        query_textSearch = "SELECT id FROM CICERON.D_I18N_TEXTS WHERE md5_checksum = %s ORDER BY hit_count LIMIT 1"
        cursor.execute(query_textSearch, (hashed_text, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return False, None
        else:
            return True, res[0]

    def __historyChecker(self, cursor, source_lang_id, target_lang_id, text):
        # MD5를 이용하여 원문 ID 검색
        is_exist, source_text_id = self.__getTextId(cursor, text)
        if is_exist is False:
            return False, None, None

        # 해당 Text_id를 사용하는 TEXT_MAPPING 추출
        query_getTextMapping = "SELECT DISTINCT id FROM CICERON.F_I18N_TEXT_MAPPINGS WHERE text_id = %s"
        cursor.execute(query_getTextMapping, (source_text_id, ))
        res = cursor.fetchall()
        if res is None or len(res) == 0:
            return False, None, None

        ###### Source: source_lang_id / Target: target_lang_id ###
        # source가 주어진 text_id였을 때 target_id 추출
        source_nothing = False
        source_mapping_lists = ','.join([str(row[0]) for row in res if row[0] != None ])
        query_getAllTargetMappings = "SELECT DISTINCT target_text_mapping_id FROM CICERON.F_I18N_VALUES WHERE source_text_mapping_id in ({0})".format(source_mapping_lists)
        cursor.execute(query_getAllTargetMappings)
        res2 = cursor.fetchall()
        if res2 is None or len(res2) == 0:
            source_nothing = True

        # Mapping 찾기
        if source_nothing == False:
            target_mapping_id_lists = ','.join([str(row[0]) for row in res2 if row[0] != None ])
            query_getTargetTextId = "SELECT DISTINCT text_id FROM CICERON.F_I18N_TEXT_MAPPINGS WHERE id in ({0}) AND lang_id = {1}".format(target_mapping_id_lists, target_lang_id)
            cursor.execute(query_getTargetTextId)
            res3 = cursor.fetchall()
            if res3 is None or len(res3) == 0:
                source_nothing = True

        # Hit수 높은 텍스트 1 선정
        if source_nothing == False:
            target_text_id_lists = ','.join([str(row[0]) for row in res3 if row[0] != None ])
            query_getTargetText = "SELECT id, text, hit_count FROM CICERON.D_I18N_TEXTS WHERE id in ({0}) ORDER BY hit_count DESC LIMIT 1".format(target_text_id_lists)
            cursor.execute(query_getTargetText)
            res4 = cursor.fetchone()
            targetSide_textId = res4[0]
            targetSide_text = res4[1]
            targetSide_hitCount = res4[2]
        #########################################################

        ###### Source: target_lang_id / Target: source_lang_id ###
        # source가 주어진 text_id였을 때 source_id 추출
        target_nothing = False
        target_mapping_lists = ','.join([str(row[0]) for row in res if row[0] != None ])
        query_getAllSourceMappings = "SELECT DISTINCT source_text_mapping_id FROM CICERON.F_I18N_VALUES WHERE target_text_mapping_id in ({0})".format(target_mapping_lists)
        cursor.execute(query_getAllSourceMappings)
        res5 = cursor.fetchall()
        if res5 is None or len(res5) == 0:
            target_nothing = True

        # Mapping 찾기
        if target_nothing == False:
            source_mapping_id_lists = ','.join([str(row[0]) for row in res5 if row[0] != None ])
            query_getSourceTextId = "SELECT DISTINCT text_id FROM CICERON.F_I18N_TEXT_MAPPINGS WHERE id in ({0})".format(source_mapping_id_lists)
            cursor.execute(query_getSourceTextId)
            res6 = cursor.fetchall()
            if res6 is None or len(res6) == 0:
                target_nothing = True

        # Hit수 높은 텍스트 1 선정
        if target_nothing == False:
            source_text_id_lists = ','.join([str(row[0]) for row in res6 if row[0] != None ])
            query_getSourceText = "SELECT id, text, hit_count FROM CICERON.D_I18N_TEXTS WHERE id in ({0}) ORDER BY hit_count DESC LIMIT 1".format(source_text_id_lists)
            cursor.execute(query_getSourceText)
            res7 = cursor.fetchone()
            sourceSide_textId = res7[0]
            sourceSide_text = res7[1]
            sourceSide_hitCount = res7[2]
        ########################################################

        # 두 후보 중 택1
        curated_text_id = 0
        curated_text = ""
        if target_nothing == True and source_nothing == True:
            return False, None, None
        elif target_nothing == True and source_nothing == False:
            curated_text_id = targetSide_textId
            curated_text = targetSide_text
        elif target_nothing == False and source_nothing == True:
            curated_text_id = sourceSide_textId
            curated_text = sourceSide_text
        elif sourceSide_hitCount <= targetSide_hitCount:
            curated_text_id = sourceSide_textId
            curated_text = sourceSide_text
        else:
            curated_text_id = targetSide_textId
            curated_text = targetSide_text

        # 최종 후보 단어는 카운트 +1
        query_hitUp = "UPDATE CICERON.D_I18N_TEXTS SET hit_count = hit_count + 1 WHERE id = %s"
        cursor.execute(query_hitUp, (curated_text_id, ))

        return True, curated_text, curated_text_id

    def __insertUnitText(self, cursor, text):
        md5_text = self.__getMD5(text)
        is_duplicated, duplicated_text_id = self.__getTextId(cursor, text)

        try:
            if is_duplicated == False:
                query_newText = """
                    INSERT INTO CICERON.D_I18N_TEXTS
                        (id, text, md5_checksum, hit_count)
                    VALUES
                        (%s, %s, %s, 0)
                """
                text_id = ciceron_lib.get_new_id(self.conn, "D_I18N_TEXTS")
                cursor.execute(query_newText, (text_id, text, md5_text, ))

        except Exception:
            self.conn.rollback()
            traceback.print_exc()
            return False, None

        if is_duplicated == False:
            return True, text_id
        else:
            return True, duplicated_text_id

    def __updateUnitText(self, cursor, text_id, text):
        md5_text = self.__getMD5(text)
        query_updateText = """
            UPDATE CICERON.D_I18N_TEXTS
            SET text = %s, md5_checksum = %s
            WHERE id = %s
        """
        try:
            cursor.execute(query_updateText, (text, md5_text, text_id, ))
        except Exception:
            self.conn.rollback()
            traceback.print_exc()
            return False

        return True

    def __updateVariable(self, cursor, variable_id, text):
        query_updateVariable = """
            UPDATE CICERON.D_I18N_VARIABLE_NAMES
            SET text = %s
            WHERE id = %s
        """
        try:
            cursor.execute(query_updateVariable, (text, variable_id, ))
        except Exception:
            self.conn.rollback()
            traceback.print_exc()
            return False

        return True

    def __insertVariable(self, cursor, text):
        variable_id = ciceron_lib.get_new_id(self.conn, "D_I18N_VARIABLE_NAMES")
        query_newVariable = """
            INSERT INTO CICERON.D_I18N_VARIABLE_NAMES
                (id, text)
            VALUES
                (%s, %s)
        """
        try:
            cursor.execute(query_newVariable, (variable_id, text, ))

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False, None

        return True, variable_id

    def __insertMapping(self, cursor, variable_id, lang_id, paragraph_seq, sentence_seq, text_id, is_curated):
        mapping_id = ciceron_lib.get_new_id(self.conn, "F_I18N_TEXT_MAPPINGS")
        query_newMapping = """
            INSERT INTO CICERON.F_I18N_TEXT_MAPPINGS
                (id, variable_id, lang_id, paragraph_seq, sentence_seq, text_id, is_curated, is_init_translated)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, false)
        """
        try:
            cursor.execute(query_newMapping, (mapping_id, variable_id, lang_id, paragraph_seq, sentence_seq, text_id, is_curated, ))

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False, None

        return True, mapping_id

    def __getMappingIdFromVariable(self, cursor, variable_id, lang_id, paragraph_seq, sentence_seq):
        query_getMapping = """
            SELECT id FROM CICERON.F_I18N_TEXT_MAPPINGS
            WHERE variable_id = %s
              AND paragraph_seq = %s
              AND sentence_seq = %s
              AND lang_id = %s
        """
        cursor.execute(query_getMapping, (variable_id, paragraph_seq, sentence_seq, lang_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return False, None

        else:
            return True, res[0]

    def __updateMapping(self, cursor, mapping_id, new_text_id):
        query_updateMapping = """
            UPDATE CICERON.F_I18N_TEXT_MAPPINGS
                SET text_id = %s
            WHERE id = %s
        """
        try:
            cursor.execute(query_updateMapping, (new_text_id, mapping_id, ))
        except Exception:
            tracevack.print_exc()
            self.conn.rollback()
            return False

        return True

    def __insertValue(self, cursor, request_id, variable_id, source_text_mapping_id, target_text_mapping_id):
        value_id = ciceron_lib.get_new_id(self.conn, "F_I18N_VALUES")
        query_newValue = """
            INSERT INTO CICERON.F_I18N_VALUES
                (id, request_id, variable_id, source_text_mapping_id, target_text_mapping_id)
            VALUES
                (%s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query_newValue, (value_id, request_id, variable_id, source_text_mapping_id, target_text_mapping_id, ))

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False, None

        return True, value_id

    def _deleteVariableAndText(self, cursor, request_id, variable_id):
        query_deleteVariable = """
            DELETE FROM CICERON.D_I18N_VARIABLE_NAMES
            WHERE id = %s
        """
        query_findMapping = """
            SELECT source_text_mapping_id, target_text_mapping_id
            FROM CICERON.F_I18N_VALUES
            WHERE request_id = %s
              AND variable_id = %s
        """
        query_deleteMapping = """
            DELETE FROM CICERON.F_I18N_TEXT_MAPPINGS
            WHERE id = %s
        """
        query_deleteValue = """
            DELETE FROM CICERON.F_I18N_VALUES
            WHERE request_id = %s
              AND variable_id = %s
        """

        try:
            cursor.execute(query_findMapping, (request_id, variable_id, ))
            res = cursor.fetchall()

            cursor.execute(query_deleteValue, (request_id, variable_id, ))
            if res is not None and len(res) > 0:
                for row in res:
                    source_text_mapping_id = row[0]
                    target_text_mapping_id = row[1]
                    cursor.execute(query_deleteMapping, (source_text_mapping_id, ))
                    cursor.execute(query_deleteMapping, (target_text_mapping_id, ))

            cursor.execute(query_deleteVariable, (variable_id, ))

        except Exception:
            self.conn.rollback()
            traceback.print_exc()
            return False

        return True

    def _writeOneRecordToDB(self, cursor, request_id, variable_id, paragraph_seq, sentence_seq, partial_text, source_lang_id=None, target_lang_id=None):
        if source_lang_id is None or target_lang_id is None:
            source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        # 원문은 똑같은 텍스트 있나 살펴보는 정도
        is_exist_source, source_text_id = self.__getTextId(cursor, partial_text)
        # 원문 텍스트 이용하여 기존 번역 있는지 검색
        is_exist_target, target_curated_text, target_curated_text_id = self.__historyChecker(cursor, source_lang_id, target_lang_id, partial_text)

        if is_exist_source == False:
            # 원문 부분은 기존 데이터 없을 시 원문 문장 삽입
            is_unitText_inserted, source_text_id = self.__insertUnitText(cursor, partial_text)
            if is_unitText_inserted == False:
                raise Exception

        if is_exist_target == False:
            # 번역 결과 부분은 기존 데이터 없으면 빈 줄 삽입
            is_dummy_exist, target_curated_text_id = self.__getTextId(cursor, "")
            if is_dummy_exist == False:
                is_unitText_inserted, target_curated_text_id = self.__insertUnitText(cursor, "")
                if is_unitText_inserted == False:
                    raise Exception

        is_source_mapping_inserted, source_mapping_id = self.__insertMapping(cursor, variable_id, source_lang_id, paragraph_seq, sentence_seq, source_text_id, is_exist_source)
        is_target_mapping_inserted, target_mapping_id = self.__insertMapping(cursor, variable_id, target_lang_id, paragraph_seq, sentence_seq, target_curated_text_id, is_exist_target)

        is_value_inserted, value_id = self.__insertValue(cursor, request_id, variable_id, source_mapping_id, target_mapping_id)

        if      is_source_mapping_inserted == True \
            and is_target_mapping_inserted == True \
            and is_value_inserted == True:
            return True, value_id

        else:
            return False, None

    def _dictToDb(self, request_id, source_lang_id, target_lang_id, dictData):
        cursor = self.conn.cursor()

        for key, whole_text in dictData.items():
            whole_text_temp = whole_text.replace("\r", "").replace("\n  ", "\n\n")
            splited_text = whole_text_temp.split('\n\n')

            is_variable_inserted, variable_id = self.__insertVariable(cursor, key)
            if is_variable_inserted == False:
                self.conn.rollback()
                raise Exception

            for paragraph_seq, paragraph in enumerate(splited_text):
                parsed_sentences = self.sentence_detector.tokenize(paragraph.strip())

                for sentence_seq, sentence in enumerate(parsed_sentences):
                    is_sentence_inserted, value_id = self._writeOneRecordToDB(cursor, request_id, variable_id, paragraph_seq, sentence_seq, sentence, source_lang_id=source_lang_id, target_lang_id=target_lang_id)

                    if is_sentence_inserted == False:
                        self.conn.rollback()
                        raise Exception

        # 입력 모두 끝나면 Commit
        self.conn.commit()

    def _dbToDict(self, request_id):
        cursor = self.conn.cursor()
        query_db = """
            SELECT f_values.request_id,                   -- 0
                   variable.id as variable_id,            -- 1
                   variable.text as variable,             -- 2
                   source_mapping.paragraph_seq,          -- 3
                   source_mapping.sentence_seq,           -- 4
                   source_text.text as source_sentence,   -- 5
                   target_text.text as target_sentence,   -- 6
                   variable.comment_string as comment     -- 7

            FROM CICERON.F_I18N_VALUES f_values
            JOIN CICERON.D_I18N_VARIABLE_NAMES variable ON f_values.variable_id = variable.id
            LEFT OUTER JOIN CICERON.F_I18N_TEXT_MAPPINGS source_mapping ON f_values.source_text_mapping_id = source_mapping.id
            LEFT OUTER JOIN CICERON.F_I18N_TEXT_MAPPINGS target_mapping ON f_values.target_text_mapping_id = target_mapping.id
            LEFT OUTER JOIN CICERON.D_I18N_TEXTS source_text ON source_mapping.text_id = source_text.id
            LEFT OUTER JOIN CICERON.D_I18N_TEXTS target_text ON target_mapping.text_id = target_text.id
            WHERE request_id = %s
            ORDER BY variable_id, paragraph_seq, sentence_seq 
        """

        cursor.execute(query_db, (request_id, ))
        res = cursor.fetchall()

        source_obj = OrderedDict()
        target_obj = OrderedDict()

        cur_variable = ""
        cur_paragraph_seq = -1
        source_paragraph_per_variable = ""
        target_paragraph_per_variable = ""

        for idx, row in enumerate(res):
            variable = row[2]
            paragraph_seq = row[3]
            sentence_seq = row[4]
            source_sentence = row[5]
            target_sentence = row[6]

            #
            if cur_variable != variable and idx > 0:
                source_obj[ cur_variable ] = source_paragraph_per_variable.replace('\r\n', '\n').lstrip('\n').rstrip('\n')
                target_obj[ cur_variable ] = target_paragraph_per_variable.replace('\r\n', '\n').lstrip('\n').rstrip('\n')
                cur_variable = variable

                source_paragraph_per_variable = ""
                target_paragraph_per_variable = ""

            elif cur_variable != variable and idx == 0:
                cur_variable = variable

            #
            if cur_paragraph_seq != paragraph_seq:
                if paragraph_seq > 0:
                    source_paragraph_per_variable += '\n\n'
                    target_paragraph_per_variable += '\n\n'
                cur_paragraph_seq = paragraph_seq

            if source_sentence != None:
                if sentence_seq > 0:
                    source_paragraph_per_variable += " " + source_sentence
                else:
                    source_paragraph_per_variable += source_sentence

            if target_sentence != None:
                if sentence_seq > 0:
                    target_paragraph_per_variable += " " + target_sentence
                else:
                    target_paragraph_per_variable += target_sentence

            if idx == len(res) - 1:
                source_obj[ cur_variable ] = source_paragraph_per_variable.replace('\r\n', '\n').lstrip('\n').rstrip('\n')
                target_obj[ cur_variable ] = target_paragraph_per_variable.replace('\r\n', '\n').lstrip('\n').rstrip('\n')

        return source_obj, target_obj

    def _dbToJsonResponse(self, request_id, is_restricted=True):
        cursor = self.conn.cursor()
        query_db = """
            SELECT f_values.request_id,                   -- 0
                   variable.id as variable_id,            -- 1
                   variable.text as variable,             -- 2
                   source_mapping.paragraph_seq,          -- 3
                   source_mapping.sentence_seq,           -- 4
                   source_text.text as source_sentence,   -- 5
                   target_text.text as target_sentence,   -- 6
                   variable.comment_string as comment     -- 7

            FROM CICERON.F_I18N_VALUES f_values
            JOIN CICERON.D_I18N_VARIABLE_NAMES variable ON f_values.variable_id = variable.id
            LEFT OUTER JOIN CICERON.F_I18N_TEXT_MAPPINGS source_mapping ON f_values.source_text_mapping_id = source_mapping.id
            LEFT OUTER JOIN CICERON.F_I18N_TEXT_MAPPINGS target_mapping ON f_values.target_text_mapping_id = target_mapping.id
            LEFT OUTER JOIN CICERON.D_I18N_TEXTS source_text ON source_mapping.text_id = source_text.id
            LEFT OUTER JOIN CICERON.D_I18N_TEXTS target_text ON target_mapping.text_id = target_text.id
            WHERE request_id = %s
            ORDER BY variable_id, paragraph_seq, sentence_seq 
        """

        cursor.execute(query_db, (request_id, ))
        res = cursor.fetchall()

        result_obj = OrderedDict()

        cur_variable = ""
        cur_variable_id = 0
        cur_paragraph_seq = -1
        cur_comment_string = ""
        paragraph_per_variable = []

        for idx, row in enumerate(res):
            variable_id = row[1]
            variable = row[2]
            paragraph_seq = row[3]
            sentence_seq = row[4]
            source_sentence = row[5]
            target_sentence = row[6]
            comment_string = row[7]

            if cur_variable != variable and idx > 0:
                result_obj[ cur_variable ] = {
                        "variable_id": cur_variable_id,
                        "comment": cur_comment_string,
                        "texts": paragraph_per_variable
                        }

                cur_variable = variable
                cur_variable_id = variable_id
                cur_comment_string = comment_string

                paragraph_per_variable = []

            elif cur_variable != variable and idx == 0:
                cur_variable = variable
                cur_variable_id = variable_id

            unit_row = {}

            unit_row['paragraph_seq'] = paragraph_seq
            unit_row['sentence_seq'] = sentence_seq
            unit_row['sentence'] = source_sentence
            if is_restricted == False:
                unit_row["translations"] = target_sentence
            else:
                unit_row["translations"] = None

            paragraph_per_variable.append(unit_row)

            if idx == len(res) - 1:
                result_obj[ cur_variable ] = {
                        "variable_id": variable_id,
                        "comment": comment_string,
                        "texts": paragraph_per_variable
                        }

        return result_obj

    def _jQueryToDict(self, jsonText, code):
        obj = json.loads(jsonText, object_pairs_hook=OrderedDict)
        return obj[code]

    def _jsonToDict(self, jsonText, code):
        obj = json.loads(jsonText, object_pairs_hook=OrderedDict)
        if code in obj:
            return obj[code]
        elif code.upper() in obj:
            return obj[code.upper()]
        else:
            return obj

    def _iosToDict(self, iosText):
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(iosText)
        f.close()
        st = StringTable.read(f.name)
        os.unlink(f.name)

        result = {}
        for key, value in st.strings.items():
            result[key] = value.target

        return result

    def _androidToDict(self, andrText):
        parsedData = xmltodict.parse(andrText)
        result = OrderedDict()

        for row in parsedData['resources']['string']:
            try:
                result[ row['@value'] ] = row['#text']

            except KeyError:
                if '@value' not in row:
                    continue
                elif '#text' not in row:
                    result[ row['@value'] ] = ""

        return result

    def _unityToDict(self, unityText, source_lang_key):
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(unityText)
        f.close()

        f2 = open(f.name)
        items = csv.reader(f2)

        result = OrderedDict()
        lang_key_idx = 1
        for idx, row in enumerate(items):
            if idx == 0:
                for idx2, lang_key in enumerate(row):
                    if lang_key.upper() == source_lang_key.upper():
                        print("Detected in {0}".format(idx2))
                        lang_key_idx = idx2
                        break
                else:
                    print("Default 0")

            else:
                result[ row[0] ] = row[1].decode('utf-8')

        f2.close()
        os.unlink(f.name)
        return result

    def _xamarinToDict(self, xamText):
        parsedData = xmltodict.parse(xamText)
        result = OrderedDict()

        for item in parsedData['root']['data']:
            try:
                result[ item['@name'] ] = item['value'] if item['value'] != None else ""
            except KeyError:
                if '@name' not in item:
                    continue
                elif 'value' not in item or item['value'] == None:
                    result[ item['@name'] ] = ""

        return result

    def _phpToDict(self, phpText):
        result = OrderedDict()
        for line in phpText.split('\n'):
            temp_result = re.search(r"\w\['([a-z0-9\_]+)'\][\s]+=[\s]+'(.*?)';", line)
            if temp_result is None:
                continue

            key = temp_result.group(1)
            value = temp_result.group(2)

            result[ key ] = value

        return result

    def _dictToIOs(self, iosDict):
        output = io.StringIO()
        for key, text in iosDict.items():
            output.write(("\"%s\" = \"%s\";\n" % (key, text)))

        return ('Localizable.strings', bytearray(output.getvalue().encode('utf-8')))

    def _dictToAndroid(self, andrDict):
        wrappeddict = OrderedDict()
        wrappeddict['resources'] = OrderedDict()
        wrappeddict['resources']['string'] = []

        for key, text in andrDict.items():
            row = {}
            row['@value'] = key
            row['#text'] = text

            wrappeddict['resources']['string'].append(row)

        xmlResult = xmltodict.unparse(wrappeddict, pretty=True)
        output = io.StringIO()
        output.write(xmlResult)
        result = output.getvalue()
        return ('string.xml', bytearray(result.encode('utf-8')))

    def _dictToUnity(self, language, unityDict):
        counter = 0

        result = []
        cur_sentences = []

        result.append(['KEY', language])

        for key, text in unityDict.items():
            result.append([key, text])
            counter += len(text.split(' '))
            cur_sentences.append(text)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerows(result)

        unityResult = output.getvalue()

        return ('Localization.csv', unityResult, counter, cur_sentences)

    def _dictToXamarin(self, lang_code, xamDict):
        wrappeddict = OrderedDict()
        wrappeddict['root'] = OrderedDict()
        wrappeddict['root']['resheader'] = [
                  {'@name': 'resmimetype', 'value': 'text/microsoft-resx'}
                , {'@name': 'version', 'value': '2.0'}
                , {'@name': 'reader', 'value': 'System.Resources.ResXResourceReader, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=FillYours'}
                , {'@name': 'writer', 'value': 'System.Resources.ResXResourceWriter, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=FillYours'}
                ]

        wrappeddict['root']['data'] = []

        for key, text in xamDict.items():
            row = {}
            row['@name'] = key
            row['@xml:space'] = 'preserve'
            row['value'] = text

            wrappeddict['root']['data'].append(row)

        xamResult = bytearray(xmltodict.unparse(wrappeddict, pretty=True, encoding='utf-8').encode('utf-8'))
        return ('AppResources.%s.resx' % lang_code, xamResult)

    def _dictToJson(self, lang_code, jsonDict):
        result = OrderedDict()
        result[lang_code] = jsonDict
        return ('i18n.json', bytearray(json.dumps(result, indent=4, encoding='utf-8', sort_keys=False)))

    def _dictToPhp(self, phpDict):
        output = io.BytesIO()
        output.write("<?php\n".encode('utf-8'))
        for key, value in phpDict.items():
            output.write("$_['{}'] = '{}';\n".format(key, value).encode('utf-8'))

        return ('translated.php', output.getvalue())

    def _updateComment(self, cursor, variable_id, comment):
        query = """
            UPDATE CICERON.D_I18N_VARIABLE_NAMES
              SET comment_string = %s
            WHERE id = %s
        """
        try:
            cursor.execute(query, (comment, variable_id, ))
        except Exception:
            self.conn.rollback()
            traceback.print_exc()
            raise Exception

    def jsonResponse(self, request_id, is_restricted=True):
        # For web response
        result = self._dbToJsonResponse(request_id, is_restricted)
        return result

    def androidToDb(self, request_id, source_lang_id, target_lang_id, xml_text):
        dict_data = self._androidToDict(xml_text)
        self._dictToDb(request_id, source_lang_id, target_lang_id, dict_data)

    def jsonToDb(self, request_id, source_lang_key, source_lang_id, target_lang_id, json_text):
        dict_data = self._jsonToDict(json_text, source_lang_key)
        self._dictToDb(request_id, source_lang_id, target_lang_id, dict_data)

    def iosToDb(self, request_id, source_lang_id, target_lang_id, ios_text):
        dict_data = self._iosToDict(ios_text)
        self._dictToDb(request_id, source_lang_id, target_lang_id, dict_data)

    def xamarinToDb(self, request_id, source_lang_id, target_lang_id, xamText):
        dict_data = self._xamarinToDict(xamText)
        self._dictToDb(request_id, source_lang_id, target_lang_id, dict_data)

    def unityToDb(self, request_id, source_lang_key, source_lang_id, target_lang_id, unityText):
        dict_data = self._unityToDict(unityText, source_lang_key)
        self._dictToDb(request_id, source_lang_id, target_lang_id, dict_data)

    def phpToDb(self, request_id, source_lang_key, source_lang_id, target_lang_id, phpText):
        dict_data = self._phpToDict(unityText)
        self._dictToDb(request_id, source_lang_id, target_lang_id, dict_data)

    def updateVariableName(self, request_id, variable_id, text):
        cursor = self.conn.cursor()
        is_updated = self.__updateVariable(cursor, variable_id, text)
        if is_updated == True:
            self.conn.commit()
        else:
            self.conn.rollback()

    def insertVariable(self, request_id, text):
        cursor = self.conn.cursor()

        is_inserted_variable, variable_id = self.__insertVariable(cursor, text)
        is_inserted_text, value_id = self._writeOneRecordToDB(cursor, request_id, variable_id, 0, 0, "")

        if is_inserted_variable == True and is_inserted_text == True:
            self.conn.commit()
            return value_id
        else:
            self.conn.rollback()
            return None

    def deleteVariable(self, request_id, variable_id):
        cursor = self.conn.cursor()

        is_deleted = self._deleteVariableAndText(cursor, request_id, variable_id)
        if is_deleted == True:
            self.conn.commit()

        return is_deleted

    def updateTranslation(self, request_id, variable_id, paragraph_seq, sentence_seq, new_text):
        cursor = self.conn.cursor()

        source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        is_mapping_exist, mapping_id = self.__getMappingIdFromVariable(cursor, variable_id, target_lang_id, paragraph_seq, sentence_seq)
        is_exist, curated_text_id = self.__getTextId(cursor, new_text)
        if is_exist == False:
            is_unitText_inserted, new_text_id = self.__insertUnitText(cursor, new_text)
            is_mapping_updated = self.__updateMapping(cursor, mapping_id, new_text_id)
        else:
            is_mapping_updated = self.__updateMapping(cursor, mapping_id, curated_text_id)

        if is_mapping_updated == True:
            self.conn.commit()
        else:
            self.conn.rollback()
            raise Exception

    def updateComment(self, request_id, variable_id, comment):
        cursor = self.conn.cursor()
        self._updateComment(cursor, variable_id, comment)
        self.conn.commit()

    def exportIOs(self, request_id):
        source_dict_data, target_dict_data = self._dbToDict(request_id)
        filename, ios_binary = self._dictToIOs(target_dict_data)
        return filename, ios_binary

    def exportAndroid(self, request_id):
        source_dict_data, target_dict_data = self._dbToDict(request_id)
        filename, android_binary = self._dictToAndroid(target_dict_data)
        return filename, android_binary

    def exportUnity(self, request_id):
        source_dict_data, target_dict_data = self._dbToDict(request_id)
        source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        target_lang = self.__getCountryCodeById(target_lang_id)
        filename, unity_binary = self._dictToUnity(target_lang, target_dict_data)
        return filename, unity_binary

    def exportJson(self, request_id):
        source_dict_data, target_dict_data = self._dbToDict(request_id)
        source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        target_lang = self.__getCountryCodeById(target_lang_id)
        filename, json_binary = self._dictToJson(target_lang, target_dict_data)
        return filename, json_binary

    def exportXamarin(self, request_id):
        source_dict_data, target_dict_data = self._dbToDict(request_id)
        source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        target_lang = self.__getCountryCodeById(target_lang_id)
        filename, xamarin_binary = self._dictToXamarin(target_lang, target_dict_data)
        return filename, xamarin_binary

    def exportPhp(self, request_id):
        source_dict_data, target_dict_data = self._dbToDict(request_id)
        filename, php_binary = self._dictToPhp(target_dict_data)
        return filename, php_binary

if __name__ == "__main__":
    import psycopg2
    import os
    if os.environ.get('PURPOSE') == 'PROD':
        DATABASE = "host=ciceronprod.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"
    else:
        DATABASE = "host=ciceron.xyz port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"

    conn = psycopg2.connect(DATABASE)

    i18nObj = I18nHandler(conn)

    # 불러오고 각 포멧으로 Export하는 테스트
    #from collections import OrderedDict
    #dictData = OrderedDict()
    #f = open('../test/testdata/peer_gynt/xmlReady.csv', 'r')
    #csvReader = csv.reader(f)
    #for key, value in csvReader:
    #    dictData[key] = value
    #f.close()

    #filename, binary = i18nObj._dictToAndroid(dictData)
    #f = open('../test/testdata/peer_gynt/string.xml', 'w')
    #f.write(binary)
    #f.close()

    #filename, binary = i18nObj._dictToJson('ko', dictData)
    #f = open('../test/testdata/peer_gynt/%s' % filename, 'w')
    #f.write(binary)
    #f.close()

    #filename, binary = i18nObj._dictToUnity('Korean', dictData)
    #f = open('../test/testdata/peer_gynt/%s' % filename, 'w')
    #f.write(binary)
    #f.close()

    #filename, binary = i18nObj._dictToIOs(dictData)
    #f = open('../test/testdata/peer_gynt/%s' % filename, 'w')
    #f.write(binary)
    #f.close()

    #filename, binary = i18nObj._dictToXamarin('ko', dictData)
    #f = open('../test/testdata/peer_gynt/%s' % filename, 'w')
    #f.write(binary)
    #f.close()

    #filename_json, json_binary = i18nObj.exportJson(678)
    #filename_unity, unity_binary = i18nObj.exportUnity(678)
    #filename_xamarin, xamarin_binary = i18nObj.exportXamarin(678)
    #filename_android, android_binary = i18nObj.exportAndroid(678)
    #filename_ios, ios_binary = i18nObj.exportIOs(678)

    #f0 = open('testdata/%s' % filename_json, 'w')
    #f1 = open('testdata/%s' % filename_unity, 'w')
    #f2 = open('testdata/%s' % filename_xamarin, 'w')
    #f3 = open('testdata/%s' % "string2.xml", 'w')
    #f4 = open('testdata/%s' % filename_ios, 'w')

    #f0.write(json_binary)
    #f1.write(unity_binary)
    #f2.write(xamarin_binary)
    #f3.write(android_binary)
    #f4.write(ios_binary)

    #f0.close()
    #f1.close()
    #f2.close()
    #f3.close()
    #f4.close()

    # CRUD 테스트
    #i18nObj.updateText(678, 2781, 0, 0, u'음향 is 뭔들')
    #i18nObj.updateVariableName(678, 2772, 'credit0001')
    #i18nObj.insertVariable(678, 'credit_opening')
    #i18nObj.deleteVariable(678, 2781)

    #wordcounter = 0
    #total_sentences = []

    #for root, folders, files in os.walk('../test/testdata/funmeu_source'):
    #    for filename in files:
    #        if not filename.endswith('.php'):
    #            continue

    #        print(os.path.join(root, filename))
    #        f = open(os.path.join(root, filename), 'r')
    #        phpBinary = f.read()
    #        f.close()

    #        dictFromPhp = i18nObj._phpToDict(phpBinary)
    #        new_filename, new_binary, unit_file_counter, sentences = i18nObj._dictToUnity('EN', dictFromPhp)
    #        #wordcounter += unit_file_counter
    #        for sentence in sentences:
    #            if sentence not in total_sentences:
    #                total_sentences.append(sentence)

    #        f2 = open(os.path.join(root, filename + '.csv'), 'w')
    #        f2.write(new_binary)
    #        f2.close()

    #f3 = open("funmeu_request.csv", "w")
    #writer = csv.writer(f3)
    #for item in total_sentences:
    #    writer.writerow([item, None])

    #f3.close()

    #for item in total_sentences:
    #    wordcounter += len(item.split(' '))

    #print(wordcounter)
    import xlrd

    f1 = xlrd.open_workbook('funmeu_in.xlsx')
    f2 = xlrd.open_workbook('funmeu_th.xlsx')
    f3 = xlrd.open_workbook('funmeu_vn.xlsx')

    sheet_in = f1.sheet_by_index(0)
    sheet_th = f2.sheet_by_index(0)
    sheet_vn = f3.sheet_by_index(0)

    result_id = {}
    result_th = {}
    result_vn = {}

    for cell in sheet_in.get_rows():
        result_id[ cell[0].value ] = cell[1].value
        print(cell[0].value)

    for cell in sheet_th.get_rows():
        result_th[ cell[0].value ] = cell[1].value

    for cell in sheet_vn.get_rows():
        result_vn[ cell[0].value ] = cell[1].value

    for root, folders, files in os.walk('../test/testdata/funmeu_source_vn'):
        for filename in files:
            if not filename.endswith('.php'):
                continue

            print(os.path.join(root, filename))
            f = open(os.path.join(root, filename), 'r')
            phpBinary = f.read()
            f.close()

            dictFromPhp = i18nObj._phpToDict(phpBinary)

            result_this_vn = {}
            result_this_th = {}
            result_this_id = {}

            for key, value in dictFromPhp.items():
                if value in result_id.keys():
                    result_this_id[ key ] = result_id[ value ]

                if value in result_th.keys():
                    result_this_th[ key ] = result_th[ value ]

                if value in result_vn.keys():
                    result_this_vn[ key ] = result_vn[ value ]

            _, binary_vn = i18nObj._dictToPhp(result_this_vn)
            #_, binary_th = i18nObj._dictToPhp(result_this_th)
            #_, binary_id = i18nObj._dictToPhp(result_this_id)

            f1 = open(os.path.join(root, filename), 'w')
            #f2 = open(os.path.join(root, filename), 'w')
            #f3 = open(os.path.join(root, filename), 'w')

            f1.write(binary_vn.decode('utf-8'))
            #f2.write(binary_th.decode('utf-8'))
            #f3.write(binary_id.decode('utf-8'))

            f1.close()
            #f2.close()
            #f3.close()
