# -*- coding: utf-8 -*-
import xmltodict, json, csv, io


class I18nHandler(object):

    def __init__(self, conn):
        self.conn = conn

    def __getCountryNameById(self, lang_id):
        query = "SELECT text FROM CICERON.D_LANGUAGES WHERE id = %s"
        cursor = self.conn.cursor()

        cursor.execute(query, (lang_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return "null"
        else:
            return res[0]

    def __getCountryCodeById(self, lang_id):
        query = "SELECT google_code FROM CICERON.D_LANGUAGES WHERE id = %s"
        cursor = self.conn.cursor()

        cursor.execute(query, (lang_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return "null"
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

    def __insertToDB(self, request_id, variable_id, source_lang_id, target_lang_id, paragraph_seq, sentence_seq, text):
        cursor = self.conn.cursor()
        query = """
            INSERT INTO CICERON.D_I18N_REQUESTS
                (id, request_id, variable_id, %(source_id)s, %(target_lang_id)s, paragraph_seq, sentence_seq, text)"""

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

    def _iosToDict(self, iosText):
        pass

    def _androidToDict(self, andrText):
        pass

    def _unityToDict(self, unityText):
        pass

    def _xamarinToDict(self, xamText):
        pass

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

