# -*- coding: utf-8 -*-
import os
import io
import traceback
from collections import OrderedDict
from flask import request, send_file, make_response

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
        pass

    def tagInfoUpdate(self, tag_id, category_1, category_2):
        pass

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
        pass

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

