# -*- coding: utf-8 -*-
import os
import io
import traceback
from collections import OrderedDict
from flask import request, send_file, make_response, g, json
import psycopg2
import requests

#Connection info: ADDRESS=ciceron.xyz PORT=5432 DATABASE=photo USER=ciceron_web PASS=noSecret01! SCHEMA=raw

try:
    import ciceron_lib
except:
    from . import ciceron_lib

try:
    from ciceron_lib import login_required, admin_required
except:
    from .ciceron_lib import login_required, admin_required


class KangarooAdmin(object):
    def __init__(self, conn):
        self.conn = conn

    def tagListing(self):
        cursor = self.conn.cursor()
        cursor.execute("select id, tag_name as name from RAW.f_crawltag")
        columns = [ desc[0] for desc in cursor.description ]
        taginfo = cursor.fetchall()
        tag_list = ciceron_lib.dbToDict(columns, taginfo)

        return 200, tag_list

    def tagInfoUpdate(self, tag_id, category_1, category_2):
        pass

    def tagCategoryHierarchy(self, category_1):
        if category_1 == 1:
            return [1]

        elif category_1 == 2:
            return [2]

        elif category_1 == 3:
            return [3,4,5,6]

        elif category_1 == 4:
            return [7,8,9,10,11,12]

        elif category_1 == 5:
            return [13, 14, 15, 16]

    def deleteTag(self, tag_id):
        pass

    def imageList(self, tag_id):
        pass

    def provideImageOfTag(self, tag_id, img_id):
        pass

    def updateImageOfTag(self, tag_id, img_id, new_img_binary):
        pass
    def deleteImageOfTag(self, tag_id, img_id):
        pass


class KangarooAdminAPI(object):
    def __init__(self, app, endpoints):
        self.app = app
        self.endpoints = endpoints

        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in self.endpoints:
            self.app.add_url_rule('{}/admin/kangaroo/tag'.format(endpoint), view_func=self.adminKangarooTagListing, methods=["GET"])
            self.app.add_url_rule('{}/admin/kangaroo/tag/category1/<int:category1>'.format(endpoint), view_func=self.adminKangarooTagCategoryHierarchy, methods=["GET"])
            self.app.add_url_rule('{}/admin/kangaroo/tag'.format(endpoint), view_func=self.adminKangarooTagUpdate, methods=["POST"])
            self.app.add_url_rule('{}/admin/kangaroo/tag/<int:tag_id>'.format(endpoint), view_func=self.adminKangarooTagDelete, methods=["DELETE"])

            self.app.add_url_rule('{}/admin/kangaroo/tag/<int:tag_id>'.format(endpoint), view_func=self.adminKangarooTagImageLists, methods=["GET"])
            self.app.add_url_rule('{}/admin/kangaroo/tag/<int:tag_id>/img/<int:img_id>/<filename>'.format(endpoint), view_func=self.adminKangarooTagProvideImageBinary, methods=["GET"])
            self.app.add_url_rule('{}/admin/kangaroo/tag/<int:tag_id>/img/<int:img_id>/<filename>'.format(endpoint), view_func=self.adminKangarooTagUpdateImageBinary, methods=["PUT"])
            self.app.add_url_rule('{}/admin/kangaroo/tag/<int:tag_id>/img/<int:img_id>/<filename>'.format(endpoint), view_func=self.adminKangarooTagDeleteImageBinary, methods=["DELETE"])

    def adminKangarooTagListing(self):
        """
        새로 들어온 태그 리스팅

        **Parameters**: Nothing

        **Response**
          #. **200**

            .. code-block:: json
               :linenos:

               {
                 "data": [
                   {
                     "id": 1,
                     "name": "blah"
                   },
                   {
                     "id": 2,
                     "name": "haha"
                   }
                 ]
               }

        """
        kangarooAdminObj = KangarooAdmin(g.db)
        resp_code, tag_list = kangarooAdminObj.tagListing()

        return make_response(json.jsonify(data=tag_list), resp_code)

    def adminKangarooTagUpdate(self):
        """
        태그에 정보 넣기

        **Parameters**
          #. **"tag_id"**: Int, Tag ID
          #. **"category_level_1"**: Int
            #. 1 - 장소
            #. 2 - 활동
            #. 3 - 요리
            #. 4 - 재료
            #. 5 - Others
          #. **"category_level_2"**: Int
            #. 1 - 장소
            #. 2 - 활동
            #. 3 - 한식
            #. 4 - 중식
            #. 5 - 일식
            #. 6 - 요리/Others
            #. 7 - 육류
            #. 8 - 어류
            #. 9 - 조류
            #. 10 - 채소
            #. 11 - 과일
            #. 12 - 공산품
            #. 13 - 동물
            #. 14 - 식물
            #. 15 - 물건
            #. 16 - 자연경관
        """
        pass

    def adminKangarooTagCategoryHierarchy(self, category1):
        """
        태그 상위 카테고리로 하위 카테고리 주기

        **Parameters**
          #. **"category1"**: URL에 삽입, Integer

        **Response**
          #. **200**

            .. code-block:: json
               :linenos:

               {
                 "data": [ 1, 2 ]
               }

        """
        pass

    def adminKangarooTagDelete(self, tag_id):
        """
        태그 지우기

        **Parameters**
          **"tag_id"**: URL에 직접 삽입, Tag ID

        **Response**
          #. **200**: OK
          #. **410**: Fail
        """
        pass

    def adminKangarooTagImageLists(self, tag_id):
        """
        태그를 통하여 불러온 이미지 리스팅

        **Parameters**
          #. **"page"**: Paging int, OPTIONAL

        **"Response"**
          #. **200**

            .. code-block:: json
               :linenos:

               {
                 "data": [
                   {
                     "id": 1,
                     "image_url": "/api/v2/admin/kangaroo/tag/1/img/4/img.jpg"
                   }
                 ]
               }

        """
        pass

    def adminKangarooTagProvideImageBinary(self, tag_id, img_id, filename):
        """
        이미지 제공 API

        **Parameters**
          #. **"tag_id"**: URL에 직접 삽입, Tag ID
          #. **"img_id"**: URL에 직접 삽입. Image ID
          #. **"filename"**: URL에 직접 삽입. 파일 이름

        **Response**
          #. **200**: 파일 제공
          #. **404**: 파일 없음
        """
        pass

    def adminKangarooTagUpdateImageBinary(self, tag_id, img_id, filename):
        """
        이미지 업데이트 API

        **Parameters**
          #. **"tag_id"**: URL에 직접 삽입, Tag ID
          #. **"img_id"**: URL에 직접 삽입. Image ID
          #. **"photo_bin"**: 사진 Binary

        **Response**
          #. **200**: 업데이트 성공
          #. **410**: 실패
        """
        pass

    def adminKangarooTagDeleteImageBinary(self, tag_id, img_id, filename):
        """
        이미지 삭제 API

        **Parameters**
          #. **"tag_id"**: URL에 직접 삽입, Tag ID
          #. **"img_id"**: URL에 직접 삽입. Image ID
          #. **"filename"**: URL에 직접 삽입. 파일명

        **Response**
          #. **200**: 삭제 성공
          #. **410**: 실패
        """
        pass

if __name__ == "__main__":
    pass
