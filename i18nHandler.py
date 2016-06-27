# -*- coding: utf-8 -*-
import xmltodict, json, csv, io, hashlib
from requestwarehouse import Warehousing
from nslocalized import StringTable


class I18nHandler(object):

    def __init__(self, conn):
        self.conn = conn
        self.warehouser = Warehousing(conn)

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
        hash_maker.update(text)
        return hash_maker.hexdigest()

    def __historyChecker(self, request_id, source_lang_id, target_lang_id, text):
        cursor = self.conn.cursor()

        # MD5를 이용하여 원문 ID 검색
        original_lang_id, target_lang_id = self.__getLangCodesByRequestId(request_id)
        hashed_text = self.__getMD5(text)
        query_textSearch = "SELECT id FROM CICERON.D_I18N_TEXTS WHERE md5_shecksum = %s ORDER BY hit_count LIMIT 1"
        cursor.execute(query_textSearch, (hashed_text, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return False, None
        source_text_id = res[0]

        # 원문 ID와 언어를 이용하여 이전 번역기록 추출
        query_getAllRequests = "SELECT DISTINCT id FROM CICERON.F_REQUESTS WHERE original_lang_id = %s AND target_lang_id = %s"
        cursor.execute(query_getAllRequests, (original_lang_id, target_lang_id, ))
        res = cursor.fetchall()
        if res is None or len(res) == 0:
            return False, None

        # 번역 기록 이용하여 후보 단어 추출
        request_lists = ','.join([row[0] for row in res])
        query_getAllTargetWords = "SELECT DISTINCT target_text_id FROM CICERON.F_I18N_VALUES WHERE request_id in (%s)"
        query_getAllTargetWords = query_getAllTargetWords % request_lists
        cursor.execute(query_getAllTargetWords)
        res = cursor.fetchall()
        if res in None or len(res) == 0:
            return False, None

        # 후보 단어 중 가장 추천 많이 된 것 골라줌
        target_text_id_lists = ','.join([row[0] for row in res])
        query_getTopTextId = "SELECT id, text FROM CICERON.D_I18N_TEXTS WHERE id in (%s) ORDER BY hit_count LIMIT 1"
        query_getTopTextId = query_getTopTextId % target_text_id_lists
        cursor.execute(query_getTopTextId)
        res = cursor.fetchone()
        curated_text_id, curated_text = res[0]

        # 최종 후보 단어는 카운트 +1
        query_hitUp = "UPDATE CICERON.D_I18N_TEXTS SET hit_count = hit_count + 1 WHERE id = %s"
        cursor.execute(query_hitUp, (curated_text_id, ))
        self.conn.commit()

        return True, curated_text

    def __updateText(self, request_id, variable_id, source_lang_id, target_lang_id, paragraph_seq, sentence_seq, text):
        pass

    def __updateVariable(self, request_id, variable_id, source_lang_id, target_lang_id, paragraph_seq, sentence_seq, new_variable):
        pass

    def __deleteLine(self, request_id, variable_id, source_lang_id, target_lang_id, paragraph_seq, sentence_seq):
        pass

    def __dictToDb(self, request_id, dictData):
        for key, text in iteritems(dictData):
            self.__insertToDB(request_id, key)

    def __dbToDict(self, request_id):
        query_db = "SELECT ..."

        self.conn.execute(query_db, (request_id, ))
        res = self.conn.fetchall()

        dictObj = []
        for key, text in res:
            row = {}
            row[key] = text
            dictObj.append(row)

        return dictObj

    def _writeOneRecordToDB(self, request_id, variable_id, source_lang_id, target_lang_id, paragraph_seq, sentence_seq, text):
        cursor = self.conn.cursor()
        query = """
            INSERT INTO CICERON.D_I18N_VALUES
                (id, request_id, variable_id, source_text_id, target_text_id)
            VALUES
                (%s, %s, %s, %s, %s)
                """

    def _jQueryToDict(self, jsonText, code):
        obj = json.loads(jsonText)
        return obj[code]

    def _railsToDict(self, jsonText, code):
        obj = json.loads(jsonText)
        return obj[code.upper()]

    def _iosToDict(self, iosText):
        st = StringTable.read(iosText)
        return st

    def _androidToDict(self, andrText):
        parsedData = xmltodict.parse(andrText)
        result = []

        for row in parsedData['resources']:
            temp_row = {}
            temp_row[ row['@value'] ] = row['#text']

            result.append(temp_row)

        return result

    def _unityToDict(self, unityText, language):
        result = []
        items = csv.reader(unityText)

        marker = None
        for idx, row in enumerate(items):
            if idx == 0:
                for idx2, item in enumerate(row):
                    if item == language:
                        marker = idx2
                        break

            else:
                temp_row = {}
                temp_row[ row[0] ] = row[marker]

                result.append(temp_row)

        return result

    def _xamarinToDict(self, xamText):
        parsedData = xmltodict.parse(xamText)
        result = []

        for item in parsedData['root']['data']:
            temp_row = {}
            temp_row[ item['@value'] ] = item['#text']

            result.append(temp_row)

        return result

    def _dictToIOs(self, iosDict):
        output = io.BytesIO()
        for key, text in iteritems(iosDict):
            output.write("\"%s\": \"%s\";" % (key, text))

        return ('Localizable.strings', output.getvalue())

    def _dictToAndroid(self, andrDict):
        wrappeddict = {}
        wrappeddict['resources'] = {}
        wrappeddict['resources']['string'] = []

        for key, text in iteritems(andrDict):
            row = {}
            row['@value'] = key
            row['#text'] = text

            wrappeddict['resources']['string'].append(row)

        xmlResult = xmltodict.unparse(wrappeddict)
        return ('string.xml', xmlResult)

    def _dictToUnity(self, language, unityDict):
        result = []
        result.append(['KEY', language])

        for key, text in iteritems(unityDict):
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

        for key, text in iteritems(xamDict):
            row = {}
            row['@xml:space'] = 'preserve'
            row['@name'] = key
            row['value'] = text

            wrappeddict['root']['data'].append(row)

        xamResult = xmltodict.unparse(wrappeddict)
        return ('AppResources.%s.resx' % lang_code, xamResult)

    def _dictToRails(self, lang_code, jsonDict):
        result = {}
        result[lang_code] = jsonDict
        return result
