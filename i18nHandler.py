# -*- coding: utf-8 -*-
import xmltodict, json, csv, io


class I18nHandler(object):

    def __init__(self, conn):
        self.conn = conn

    def __insertToDB(self, request_id, variable_id, source_lang_id, target_lang_id, paragraph_seq, sentence_seq, text):
        pass

    def __updateText(self, request_id, variable_id, source_lang_id, target_lang_id, paragraph_seq, sentence_seq, text):
        pass

    def __deleteLine(self, request_id, variable_id, source_lang_id, target_lang_id, paragraph_seq, sentence_seq):
        pass

    def __dictToDb(self, request_id, dictData):
        pass

    def __dbToDict(self, request_id):
        pass

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

