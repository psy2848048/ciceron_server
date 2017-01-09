# -*- coding: utf-8 -*-
import os
import csv
import json
import io
from lxml import etree
import lxml.html
import tarfile
import zipfile
import traceback
from flask import request, send_file

try:
    from . import ciceron_lib
except:
    import ciceron_lib

class Localizer(object):
    """
        Localizer Module

          1) Hard coded된 Front-end 압축 파일을 받아 angular 등에서 널리 지원하는 template 형으로 변환해준다. (e.g. {{ index001 }} )
          2) Hard-coded된 텍스트를 추출하여 i18n.json 파일을 만든다.

          :file_name:
            파일 이름
          :file_bin:
            사용자가 업로드한 압축 파일 바이너리, 객체 내 open() 메소드가 있어야 한다. (zip, tar, tar.gz, tar.bz2 지원)

    """

    def __init__(self, file_name, file_bin):
        self.old_file_bin = None
        if file_name.endswith('.tar.gz') or file_name.endswith('.tar.bz2'):
            self.old_file_bin = tarfile.TarFile(file_bin, 'r')
            self.file_list = self.old_file_bin.getnames()
        elif file_name.endswith('.zip'):
            self.old_file_bin = zipfile.ZipFile(file_bin, 'r')
            self.file_list = self.old_file_bin.namelist()
        else:
            raise Exception('Compressed tar file of Zip are supported!')

        self.json_value = {}

        self.binary_obj = io.BytesIO()
        self.zip_obj = zipfile.ZipFile(self.binary_obj, 'w', zipfile.ZIP_DEFLATED)

        self.html_extensions = [
            "asp"
          , "aspx"
          , "html"
          , "htm"
          , "xhtml"
          , "jsp"
          , "jspx"
          , "do"
          , "php"
          , "php4"
          , "php3"
          , "html5"
        ]

    def _findKeyByBalue(self, filename, value_args):
        for key, value_dic in self.json_value.items():
            if value_args == value_dic and filename in key:
                return True, key

        else:
            return False, None

    def textExtractor(self, filename, htmlString):
        utf8_parser = etree.HTMLParser(encoding='utf-8')
        #utf8_parser = etree.HTMLParser()
        # <br> 태그를 제거하지 않으면 이 태그 이후의 텍스트를 텍스트로 인식하지 못하고
        # URL식으로 인코딩을 하기 때문에 일찍 처리해야 한다.
        replaced_html_string = htmlString.replace('<br>', '\n').\
                replace('<br/>', '\n').replace('<br />', '\n')
        #replaced_html_string = unicode(htmlString)
        root = etree.parse(io.StringIO(replaced_html_string), utf8_parser)

        idx = 1
        for tag in root.iter():
            if tag.tag == 'script' or tag.tag == 'style' or str(tag.tag) == "<built-in function Comment>":
                continue

            unit_string = tag.text
            if unit_string is not None and unit_string != "" and unit_string.strip() != "":
                unit_string = unit_string.strip()
                can_find, key = self._findKeyByBalue(filename, unit_string)

                if can_find == True:
                    tag.text = tag.text.replace(unit_string, "{{ %s }}" % key)

                elif can_find == False and not unit_string.strip().startswith("{") and not unit_string.strip().endswith("}"):
                    real_filename = ('.'.join(filename.split('.')[:-1])).split('/')[-1]
                    key = "%s%03d" % (real_filename, idx)
                    self.json_value[ key ] = unit_string.strip()
                    tag.text = tag.text.replace(unit_string, "{{ %s }}" % key)
                    idx += 1

                else:
                    continue

        return lxml.html.tostring(root.getroot(), pretty_print=True, method="html")

    def jsonWriter(self, target_lang):
        return_dict = {}
        return_dict[ target_lang ] = self.json_value
        return json.dumps(return_dict, indent=4)

    def compressFileOrganizer(self, filename, binary):
        self.zip_obj.writestr(filename, bytearray(binary.encode()))

    def run(self, target_lang):
        for filename in self.file_list:
            print(filename)
            file_binary = self.old_file_bin.read(filename)

            # 인코딩 처리
            try:
                file_binary = str(file_binary.decode('utf-8'))
            except UnicodeDecodeError:
                try:
                    file_binary = str(file_binary)
                except UnicodeDecodeError:
                    file_binary = file_binary

            if filename.split('.')[-1] in self.html_extensions:
                file_binary = self.textExtractor(filename, file_binary)
            self.compressFileOrganizer(filename, file_binary)

        jsonText = self.jsonWriter(target_lang)
        print(jsonText)
        self.compressFileOrganizer('i18n.json', jsonText)
        self.zip_obj.close()

        return self.binary_obj.getvalue()


ENDPOINTS = ['/api/v1', '/api/v2']


class LocalizerAPI(object):
    def __init__(self, app):
        self.app = app
        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in ENDPOINTS:
            self.app.add_url_rule('{}/user/localizer'.format(endpoint), view_func=self.localizer, methods=["POST"])

    @ciceron_lib.login_required
    def localizer(self):
        parameters = ciceron_lib.parse_request(request)
        file_binary = request.files['binary']
        file_name = file_binary.filename
        target_lang = parameters['target_lang']

        localizer = Localizer(file_name, file_binary)
        return_binary = localizer.run(target_lang)

        return send_file(io.BytesIO(return_binary), attachment_filename="{}_localized.zip".format(file_name))


if __name__ == "__main__":
    localizer = None
    result_binary = None

    with open('../test/testdata/ciceron_webclient.zip', 'r') as f:
        localizer = Localizer('ciceron_webclient.zip', f)
        result_binary = localizer.run('en')

    result_file = open('ciceron_webclient_replaced.zip', 'w')
    result_file.write(result_binary)
    result_file.close()
