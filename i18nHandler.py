# -*- coding: utf-8 -*-
import xmltodict, json, csv, io, hashlib, codecs, traceback
from nslocalized import StringTable
import ciceron_lib
import nltk.data


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
            return -1
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

    def __historyChecker(self, cursor, source_lang_id, target_lang_id, text):
        # MD5를 이용하여 원문 ID 검색
        hashed_text = self.__getMD5(text)
        query_textSearch = "SELECT id FROM CICERON.D_I18N_TEXTS WHERE md5_checksum = %s ORDER BY hit_count LIMIT 1"
        cursor.execute(query_textSearch, (hashed_text, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return False, None, None
        source_text_id = res[0]

        # 원문 ID와 언어를 이용하여 이전 번역기록 추출
        query_getAllRequests = "SELECT DISTINCT id FROM CICERON.F_REQUESTS WHERE original_lang_id = %s AND target_lang_id = %s AND status_id = 2"
        cursor.execute(query_getAllRequests, (source_lang_id, target_lang_id, ))
        res = cursor.fetchall()
        if res is None or len(res) == 0:
            return False, None, None

        # 번역 기록 이용하여 후보 단어 추출
        request_lists = ','.join([str(row[0]) for row in res])
        query_getAllTargetWords = "SELECT DISTINCT target_text_mapping_id FROM CICERON.F_I18N_VALUES WHERE request_id in (%s)"
        query_getAllTargetWords = query_getAllTargetWords % request_lists
        cursor.execute(query_getAllTargetWords)
        res = cursor.fetchall()
        if res is None or len(res) == 0:
            return False, None, None

        # 후보 단어 중 가장 추천 많이 된 것 골라줌
        target_text_id_lists = ','.join([str(row[0]) for row in res])
        query_getTopTextId = "SELECT id, text FROM CICERON.D_I18N_TEXTS WHERE id in (%s) ORDER BY hit_count LIMIT 1"
        query_getTopTextId = query_getTopTextId % target_text_id_lists
        cursor.execute(query_getTopTextId)
        res = cursor.fetchone()
        curated_text_id, curated_text = res[0]

        # 최종 후보 단어는 카운트 +1
        query_hitUp = "UPDATE CICERON.D_I18N_TEXTS SET hit_count = hit_count + 1 WHERE id = %s"
        cursor.execute(query_hitUp, (curated_text_id, ))

        return True, source_text_id, curated_text_id

    def __insertUnitText(self, cursor, text):
        text_id = ciceron_lib.get_new_id(self.conn, "D_I18N_TEXTS")
        md5_text = self.__getMD5(text)
        query_newText = """
            INSERT INTO CICERON.D_I18N_TEXTS
                (id, text, md5_checksum, hit_count)
            VALUES
                (%s, %s, %s, 0)
        """
        try:
            cursor.execute(query_newText, (text_id, text, md5_text, ))
        except Exception:
            self.conn.rollback()
            traceback.print_exc()
            return False, None

        return True, text_id

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
            UPDATE CIERON.D_I18N_VARIABLE_NAMES
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
            WHERE variabld_id = %s
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

    def _deleteVariableAndText(self, request_id, variable_id):
        cursor = self.conn.cursor()

        query_deleteVariable = """
            DELETE FROM CIERON.D_I18N_VARIABLE_NAMES
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
            cursor.execute(query_deleteVariable, (variable_id, ))
            cursor.execute(query_findMapping, (request_id, variable_id, ))
            res = cursor.fetchone()
            if res is not None and len(res) > 0:
                source_text_mapping_id = res[0]
                target_text_mapping_id = res[1]
                cursor.execute(query_deleteMapping, (source_text_mapping_id, ))
                cursor.execute(query_deleteMapping, (target_text_mapping_id, ))

            cursor.execute(query_deleteValue, (request_id, variable_id, ))

        except Exception:
            self.conn.rollback()
            traceback.print_exc()
            return False

        return True

    def _writeOneRecordToDB(self, cursor, request_id, variable_id, paragraph_seq, sentence_seq, partial_text):
        source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        is_exist_source, source_text_id, source_curated_text_id = self.__historyChecker(cursor, source_lang_id, target_lang_id, partial_text)
        is_exist_target, target_text_id, target_curated_text_id = self.__historyChecker(cursor, source_lang_id, target_lang_id, "")

        if is_exist_source == False:
            is_unitText_inserted, source_curated_text_id = self.__insertUnitText(cursor, partial_text)
            if is_unitText_inserted == False:
                raise Exception

        if is_exist_target == False:
            is_unitText_inserted, target_curated_text_id = self.__insertUnitText(cursor, "")
            if is_unitText_inserted == False:
                raise Exception

        is_source_mapping_inserted, source_mapping_id = self.__insertMapping(cursor, variable_id, source_lang_id, paragraph_seq, sentence_seq, source_curated_text_id, is_exist_source)
        is_target_mapping_inserted, target_mapping_id = self.__insertMapping(cursor, variable_id, target_lang_id, paragraph_seq, sentence_seq, target_curated_text_id, is_exist_target)

        is_value_inserted, value_id = self.__insertValue(cursor, request_id, variable_id, source_mapping_id, target_mapping_id)

        if      is_source_mapping_inserted == True \
            and is_target_mapping_inserted == True \
            and is_value_inserted == True:
            return True, value_id

        else:
            return False, None

    def _dictToDb(self, request_id, dictData):
        cursor = self.conn.cursor()

        for key, whole_text in sorted(dictData.iteritems()):
            whole_text_temp = whole_text.replace("\r", "").replace("\n  ", "\n\n")
            splited_text = whole_text_temp.split('\n\n')

            is_variable_inserted, variable_id = self.__insertVariable(cursor, key)
            if is_variable_inserted == False:
                self.conn.rollback()
                raise Exception

            for paragraph_seq, paragraph in enumerate(splited_text):
                parsed_sentences = self.sentence_detector.tokenize(paragraph.strip())

                for sentence_seq, sentence in enumerate(parsed_sentences):
                    is_sentence_inserted, value_id = self._writeOneRecordToDB(cursor, request_id, variable_id, paragraph_seq, sentence_seq, sentence)

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
                   target_text.text as target_sentence    -- 6

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

        source_obj = {}
        target_obj = {}

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

            if cur_variable != variable:
                source_obj[ cur_variable ] = source_paragraph_per_variable
                target_obj[ cur_variable ] = target_paragraph_per_variable
                cur_variable = variable

            if cur_paragraph_seq != paragraph_seq:
                source_paragraph_per_variable += '\n\n'
                target_paragraph_per_variable += '\n\n'
                cur_paragraph_seq = paragraph_seq

            if source_sentence != None:
                source_paragraph_per_variable += " " + source_sentence
            if target_sentence != None:
                target_paragraph_per_variable += " " + target_sentence

            if idx == len(res) - 1:
                source_obj[ cur_variable ] = source_paragraph_per_variable
                target_obj[ cur_variable ] = target_paragraph_per_variable

        return source_obj, target_obj

    def _jQueryToDict(self, jsonText, code):
        obj = json.loads(jsonText)
        return obj[code]

    def _jsonToDict(self, jsonText, code):
        obj = json.loads(jsonText)
        if code in obj:
            return obj[code]
        elif code.upper() in obj:
            return obj[code.upper()]
        else:
            return obj

    def _iosToDict(self, iosText):
        st = StringTable.read(iosText)
        return st

    def _androidToDict(self, andrText):
        parsedData = xmltodict.parse(andrText)
        result = {}

        for row in sorted(parsedData['resources']['string']):
            result[ row['@value'] ] = row['#text']

        return result

    def _unityToDict(self, unityText, language):
        result = {}
        items = csv.reader(unityText)

        marker = None
        for idx, row in enumerate(items):
            if idx == 0:
                for idx2, item in enumerate(row):
                    if item == language:
                        marker = idx2
                        break

            else:
                result[ row[0] ] = row[marker]

        return result

    def _xamarinToDict(self, xamText):
        parsedData = xmltodict.parse(xamText)
        result = {}

        for item in parsedData['root']['data']:
            result[ item['@value'] ] = item['#text']

        return result

    def _dictToIOs(self, iosDict):
        output = io.BytesIO()
        for key, text in sorted(iosDict.iteritems()):
            output.write(("\"%s\": \"%s\";\n" % (key, text)).encode('utf-16'))

        return ('Localizable.strings', output.getvalue())

    def _dictToAndroid(self, andrDict):
        wrappeddict = {}
        wrappeddict['resources'] = {}
        wrappeddict['resources']['string'] = []

        for key, text in sorted(andrDict.iteritems()):
            row = {}
            row['@value'] = key
            row['#text'] = text

            wrappeddict['resources']['string'].append(row)

        xmlResult = xmltodict.unparse(wrappeddict, pretty=True)
        return ('string.xml', xmlResult)

    def _dictToUnity(self, language, unityDict):
        result = []
        result.append(['KEY', language])

        for key, text in sorted(unityDict.iteritems()):
            result.append([key, text])

        output = io.BytesIO()
        writer = csv.writer(output)
        writer.writerows(result)

        unityResult = output.getvalue()

        return ('Localization.csv', unityResult)

    def _dictToXamarin(self, lang_code, xamDict):
        wrappeddict = {}
        wrappeddict['root'] = {}
        wrappeddict['root']['resheader'] = [
                  {'@name': 'resmimetype', 'value': 'text/microsoft-resx'}
                , {'@name': 'version', 'value': '2.0'}
                , {'@name': 'reader', 'value': 'System.Resources.ResXResourceReader, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=FillYours'}
                , {'@name': 'writer', 'value': 'System.Resources.ResXResourceWriter, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=FillYours'}
                ]

        wrappeddict['root']['data'] = []

        for key, text in sorted(xamDict.iteritems()):
            row = {}
            row['@xml:space'] = 'preserve'
            row['@name'] = key
            row['value'] = text

            wrappeddict['root']['data'].append(row)

        xamResult = xmltodict.unparse(wrappeddict, pretty=True)
        return ('AppResources.%s.resx' % lang_code, xamResult)

    def _dictToJson(self, lang_code, jsonDict):
        result = {}
        result[lang_code] = jsonDict
        return result

    def jsonResponse(self, request_id, is_restricted=True):
        # For web response
        source_obj, target_obj = self._dbToDict(request_id)

        result = []
        for key, value in source_obj.iteritems():
            row = {}
            row['variable'] = key
            row['source_sentence'] = value
            if is_restricted == False:
                row['translated_sentence'] = target_obj[key]
            else:
                row['translated_sentence'] = None

            result.append(row)

        return result

    def androidToDb(self, request_id, xml_text):
        dict_data = self._androidToDict(xml_text)
        self._dictToDb(request_id, dict_data)

    def jsonToDb(self, request_id, json_text):
        source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        source_lang = self.__getCountryCodeById(source_lang_id)
        dict_data = self._jsonToDict(json_text, source_lang)
        self._dictToDb(request_id, dict_data)

    def iosToDb(self, request_id, ios_text):
        dict_data = self._iosToDict(ios_text)
        self._dictToDb(request_id, dict_data)

    def xamarinToDb(self, request_id, xamText):
        dict_data = self._xamarinToDict(xamTet)
        self._dictToDb(request_id, dict_data)

    def unityToDb(self, request_id, unityText):
        source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        source_lang = self.__getCountryCodeById(source_lang_id)
        dict_data = self._unityToDict(request_id, unityText, source_lang)
        self._dictToDb(request_id, dict_data)

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
        is_deleted = self._deleteVariableAndText(request_id, variable_id)
        return is_deleted

    def updateText(self, request_id, variable_id, paragraph_seq, sentence_seq, new_text):
        cursor = self.conn.cursor()

        source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        is_mapping_exist, mapping_id = self.__getMappingIdFromVariable(cursor, variable_id, target_lang_id, paragraph_seq, sentence_seq)
        is_exist, source_text_id, curated_text_id = self.__historyChecker(cursor, source_lang_id, target_lang_id, new_text)
        if is_exist == False:
            is_unitText_inserted, new_text_id = self.__insertUnitText(cursor, new_text)
            is_mapping_updated = self.__updateMapping(cursor, mapping_id, new_text_id)
        else:
            is_mapping_updated = self.__updateMapping(cursor, mapping_id, curated_text_id)

        if is_mapping_updated == True:
            self.conn.commit()

    def exportIOs(self, request_id):
        dict_data = self._dbToDict(request_id)
        filename, ios_binary = self._dictToIOs(dict_data)
        return filename, ios_binary

    def exportAndroid(self, request_id):
        dict_data = self._dbToDict(request_id)
        filename, android_binary = self._dictToAndroid(dict_data)
        return filename, android_binary

    def exportUnity(self, request_id):
        dict_data = self._dbToDict(request_id)
        source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        target_lang = self.__getCountryCodeById(target_lang_id)
        filename, unity_binary = self._dictToUnity(target_lang, dict_data)
        return filename, unity_binary

    def exportJson(self, request_id):
        dict_data = self._dbToDict(request_id)
        source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        target_lang = self.__getCountryCodeById(target_lang_id)
        filename, json_binary = self._dictToJson(target_lang, dict_data)
        return filename, json_binary

    def exportXamarin(self, request_id):
        dict_data = self._dbToDict(request_id)
        source_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        target_lang = self.__getCountryCodeById(target_lang_id)
        filename, xamarin_binary = self._dictToXamarin(target_lang, dict_data)
        return filename, xamarin_binary

if __name__ == "__main__":
    import psycopg2
    import os
    if os.environ.get('PURPOSE') == 'PROD':
        DATABASE = "host=ciceronprod.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"
    else:
        DATABASE = "host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"

    conn = psycopg2.connect(DATABASE)

    i18nObj = I18nHandler(conn)

    dictData = {}
    f = open('testdata/string.xml', 'r')
    i18nObj.androidToDb(678, f.read())
    result = i18nObj.jsonResponse(678)
