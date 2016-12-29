# -*- coding: utf-8 -*-
import os
import csv
from bs4 import BeautifulSoup
from tarfile import TarFile
from zipfile import ZipFile
import json
import io


class Localizer(object):

    def __init__(self, file_name, file_bin):
        self.old_file_bin = None
        if file_name.endswith('.tar.gz') or file_name.endswith('.tar.bz2'):
            self.old_file_bin = TarFile(file_bin, 'r')
            self.file_list = self.old_file_bin.getnames()
        elif file_name.endswith('.zip'):
            self.old_file_bin = ZipFile(file_bin, 'r')
            self.file_list = self.old_file_bin.namelist()
        else:
            raise Exception('Compressed tar file of Zip are supported!')

        self.json_value = {}

        self.binary_obj = io.BytesIO()
        self.zip_obj = ZipFile(self.binary_obj, 'w')

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
        for key, value_dic in self.json_value.iteritems():
            if value_args == value_dic and filename in key:
                return True, key

        else:
            return False, None

    def textExtractor(self, filename, htmlString):
        soup = BeautifulSoup(htmlString, "html.parser")

        idx = 1
        for tag in soup.find_all(True):
            if tag is not None and ( '<script>' in tag or '<style>' in tag ):
                # Skip for script of style code
                continue

            strings = tag.strings
            for unit_string in list(strings):
                if unit_string != None and unit_string != '':
                    can_find, key = self._findKeyByBalue(filename, unit_string.encode('utf-8'))
                    if can_find == True:
                        unit_string.replace_with("{{ %s }}" % key)

                    else:
                        key = "%s%03d" % (filename, idx)
                        self.json_value[ key ] = unit_string.encode('utf-8')
                        unit_string.replace_with("{{ %s }}" % key)
                        idx += 1

        print soup.prettify()
        return soup.prettify()

    def jsonWriter(self, target_lang):
        return_dict = {}
        return_dict[ target_lang ] = self.json_value
        return json.dumps(return_dict, indent=4)

    def compressFileOrganizer(self, filename, binary):
        self.zip_obj.writestr(filename, buffer(binary))

    def run(self, target_lang):
        for filename in self.file_list:
            print filename
            file_binary = self.old_file_bin.read(filename)
            if filename.split('.')[-1] in self.html_extensions:
                file_binary = self.textExtractor(filename, file_binary)
            self.compressFileOrganizer(filename, file_binary)

        jsonText = self.jsonWriter(target_lang)
        self.compressFileOrganizer('i18n.json', jsonText)
        self.zip_obj.close()

        return self.binary_obj


if __name__ == "__main__":
    localizer = None
    result_binary = None

    with open('../test/testdata/ciceron_webclient.zip', 'r') as f:
        localizer = Localizer('ciceron_webclient.zip', f)
        result_binary = localizer.run('en')

    result_file = open('ciceron_webclient_replaced.zip', 'w')
    result_file.write(result_binary.read())
    result_file.close()
