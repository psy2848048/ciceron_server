# -*- coding: utf-8 -*-
import os
import csv
from bs4 import BeautifulSoup
import tarfile
import zipfile
import json
import io


class Localizer(object):

    def __init__(self, file_name, file_bin):
        self.old_file_bin = None
        if file_name.endswith('.tar.gz') or file_name.endswith('.tar.bz2'):
            self.old_file_bin = tarfile.open(file_bin)
        elif file_name.endswith('.zip'):
            self.old_file_bin = zipfile.open(file_bin)
        else:
            raise Exception('Compressed tar file of Zip are supported!')
        self.file_list = self.old_file_bin.getnames()
        self.json_value = {}

        self.binary_obj = io.BytesIO()
        self.zip_obj = zipfile.ZipFile(binary_obj, 'w')

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
            if tag.startswith('<script>') or tag.startswith('<style>'):
                # Skip for script of style code
                continue

            strings = tag.strings
            for detail_idx, string in enumerate(strings):
                if string is not None:
                    can_find, key = self._findKeyByBalue(filename, string.encode('utf-8'))
                    if can_find == True:
                        tag.strings[detail_idx] = "{{ %s }}" % key

                    else:
                        key = "%s%03d" % (filename, idx)
                        self.json_value[ key ] = string.encode('utf-8')
                        tag.strings[detail_idx] = "{{ %s }}" % key
                        idx += 1

        return soup.prettify()

    def jsonWriter(self, target_lang):
        return_dict = {}
        return_dict[ target_lang ] = self.json_value
        return json.dumps(return_dict, indent=4)

    def compressFileOrganizer(self, filename, binary):
        self.zip_obj.writestr(filename, binary)

    def run(self, target_lang):
        for filename in self.file_list:
            file_binary = self.zip_obj.extract(filename)
            if filename.split['.'][-1] in self.html_extensions:
                file_binary = self.textExtractor(filename, file_binary)
            self.compressFileOrganizer(filename, file_binary)

        jsonText = self.jsonWriter(target_lang)
        self.compressFileOrganizer('i18n.json', jsonText)
        self.zip_obj.close()

        return self.binary_obj


if __name__ == "__main__":
    localizer = Localizer()
