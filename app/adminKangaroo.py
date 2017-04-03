# -*- coding: utf-8 -*-
import os
import io
import traceback
from collections import OrderedDict
from flask import request, send_file, make_response, g, json
import psycopg2
import requests
from datetime import datetime, timedelta
from PIL import Image

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
        query_select_tags = """
        SELECT id, tag_name as name FROM RAW.f_crawltag
        WHERE status_id IS NULL
              OR status_id = 0
        """
        cursor.execute(query_select_tags)
        columns = [ desc[0] for desc in cursor.description ]
        taginfo = cursor.fetchall()
        tag_list = ciceron_lib.dbToDict(columns, taginfo)

        return 200, tag_list

    def updateTagInfo(self, tag_id, category1, category2):
        cursor = self.conn.cursor()
        query_update_taginfo = """
        UPDATE RAW.f_crawltag
        SET tag_category_level1 = %s, tag_category_level2 = %s, status_id = 1 
        WHERE id = %s 
        """

        if category1 is None or category2 is None:
            return False

        try:
            cursor.execute(query_update_taginfo, (category1, category2, tag_id, ))
            if cursor.rowcount == 0:
                return False
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False
        
        return True

    def deleteTag(self, tag_id):
        cursor = self.conn.cursor()
        query_update_tagstatus = """
        UPDATE RAW.f_crawltag
        SET status_id = 2 
        WHERE id = %s
        """

        try:
            cursor.execute(query_update_tagstatus, (tag_id, ))
            if cursor.rowcount == 0:
                return False
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False
        
        return True

    def tagCategoryHierarchy(self, category1):
        if category1 == 1:
            return [1]

        elif category1 == 2:
            return [2]

        elif category1 == 3:
            return [3,4,5,6]

        elif category1 == 4:
            return [7,8,9,10,11,12]

        elif category1 == 5:
            return [13, 14, 15, 16]
        
        else: 
            msg = "This category don't exist."
            return msg

    def imageListing(self, tag_id, page=1):
        cursor = self.conn.cursor()
        query_count_tag_photos = """
        SELECT count(*) FROM RAW.f_mapping_photo_crawltag 
        WHERE crawltag_id = %s
        """
        query_select_tag_photos = """
        SELECT id, 
               concat('/api/v2/admin/kangaroo/tag/', crawltag_id, '/img/', id, '/', filename) as image_url
        FROM RAW.f_mapping_photo_crawltag mpc
        JOIN RAW.f_photo p on (mpc.photo_id = p.id)
        WHERE crawltag_id = %s
        LIMIT 20 
        OFFSET 20 * (%s - 1)
        """
       
        # 태그에 해당하는 사진 개수 구하기
        cursor.execute(query_count_tag_photos, (tag_id, ))
        cnt = cursor.fetchone()[0]
        if cnt == 0:
            msg = "This page don't exist."
            return 404, msg

        # 해당하는 사진 출력
        cursor.execute(query_select_tag_photos, (tag_id, int(page), ))
        columns = [ desc[0] for desc in cursor.description ]
        imageinfo = cursor.fetchall()
        image_list = ciceron_lib.dbToDict(columns, imageinfo)

        return 200, image_list

    def provideImageOfTag(self, img_id):
        cursor = self.conn.cursor()
        query_select_photo = """
        SELECT file_binary FROM RAW.f_photo
        WHERE id = %s
        """
        cursor.execute(query_select_photo, (img_id,))
        
        if cursor.rowcount == 0:
            return None
        else: 
            image = cursor.fetchone()[0]
            return io.BytesIO(image)

    def deleteImageOfTag(self, img_id):
        cursor = self.conn.cursor()
        query_update_photo_isok = """
        UPDATE RAW.f_photo
        SET is_ok = FALSE
        WHERE id = %s
        """
        try:
            cursor.execute(query_update_photo_isok, (img_id, ))
            if cursor.rowcount == 0:
                return False
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False
        return True

    def updateImageOfTag(self, img_id, location=None):
        cursor = self.conn.cursor()
        query_select_photo = """
        SELECT file_binary FROM RAW.f_photo
        WHERE id = %s
        """
        query_update_photo = """
        UPDATE RAW.f_photo
        SET file_binary = %s
        WHERE id = %s
        """

        try:
            # DB에서 id에 해당하는 이미지를 꺼낸다.
            cursor.execute(query_select_photo, (img_id, ))
            # bytes로 저장된 사진을 bytesio로 이미지 파일로 바꾼다.
            img_bytes = io.BytesIO(cursor.fetchone()[0])
            img = Image.open(img_bytes)
            
            # 받은 좌표를 crop()에 맞춰서 바꿔주기 (start_x, start_y, start_x + width, start_y + height)
            location[2] += location[0]
            location[3] += location[1]
            
            # 입력받은 좌표를 이용하여 crop()한다.
            crop_img = img.crop(location)
            b = io.BytesIO()
            crop_img.save(b, format="PNG")
            img_bytes = b.getvalue()

            # 크롭한 이미지를 DB에 저장한다.
            cursor.execute(query_update_photo, (bytearray(img_bytes), img_id, ))
            if cursor.rowcount == 0:
                return False
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False
        return True

    def updateImageOfTag_before(self, img_id, new_image=None):
        cursor = self.conn.cursor()
        query_update_photo = """
        UPDATE RAW.f_photo
        SET file_binary = %s
        WHERE id = %s
        """
        
        if new_image is not None:
            try:
                img_bin = new_image.read()
                cursor.execute(query_update_photo, (bytearray(img_bin), img_id, ))
                if cursor.rowcount == 0:
                    return False
            except:
                traceback.print_exc()
                self.conn.rollback()
                return False
        return True


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
            self.app.add_url_rule('{}/admin/kangaroo/tag/<int:tag_id>/img/<int:img_id>/before'.format(endpoint), view_func=self.adminKangarooTagUpdateImageBinary_before, methods=["PUT"])
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
        kangarooAdminObj = KangarooAdmin(g.db_kang)
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
        kangarooAdminObj = KangarooAdmin(g.db_kang)
        parameters = ciceron_lib.parse_request(request)
        tag_id = parameters.get("tag_id", None)
        category1 = parameters.get("category_level_1", None)
        category2 = parameters.get("category_level_2", None)

        is_updated = kangarooAdminObj.updateTagInfo(tag_id, category1, category2)
        if is_updated == True:
            g.db_kang.commit()
            return make_response(json.jsonify(message = "Updated Successfully"), 200)
        else:
            g.db_kang.rollback()
            return make_response(json.jsonify(message = "Something Wrong"), 405)

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
        kangarooAdminObj = KangarooAdmin(g.db_kang)
        category2 = kangarooAdminObj.tagCategoryHierarchy(category1)

        if type(category2) is str:
            return make_response(json.jsonify(data=category2), 400)
        else:
            return make_response(json.jsonify(data=category2), 200)

    def adminKangarooTagDelete(self, tag_id):
        """
        태그 지우기

        **Parameters**
          **"tag_id"**: URL에 직접 삽입, Tag ID

        **Response**
          #. **200**: OK
          #. **410**: Fail
        """
        kangarooAdminObj = KangarooAdmin(g.db_kang)

        is_updated = kangarooAdminObj.deleteTag(tag_id)
        if is_updated == True:
            g.db_kang.commit()
            return make_response(json.jsonify(message = "Updated Successfully"), 200)
        else:
            g.db_kang.rollback()
            return make_response(json.jsonify(message = "Something Wrong"), 410)

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
        kangarooAdminObj = KangarooAdmin(g.db_kang)
        page = request.args.get('page', 1)

        if not page:
            return make_response(json.jsonify(data="Page is entered but there is no value."), 410)
        else:
           resp_code, image_list = kangarooAdminObj.imageListing(tag_id, page)
           return make_response(json.jsonify(data=image_list), resp_code)

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
        kangarooAdminObj = KangarooAdmin(g.db_kang)
        image = kangarooAdminObj.provideImageOfTag(img_id)
        if image is None:
            return make_response(json.jsonify(message="No Photo"), 404)
        else:
            return send_file(image, attachment_filename=filename)

    def adminKangarooTagUpdateImageBinary(self, tag_id, img_id, filename):
        """
        이미지 업데이트 API

        **Parameters**
          #. **"tag_id"**: URL에 직접 삽입, Tag ID
          #. **"img_id"**: URL에 직접 삽입. Image ID
          #. **"x"**: x 좌표
          #. **"y"**: y 좌표
          #. **"w"**: width
          #. **"h"**: height

        **Response**
          #. **200**: 업데이트 성공
          #. **410**: 실패
        """
        kangarooAdminObj = KangarooAdmin(g.db_kang)
        parameters = ciceron_lib.parse_request(request)
        x = parameters.get("x", None)
        y = parameters.get("y", None)
        w = parameters.get("w", None)
        h = parameters.get("h", None)
       
        location = [ float(value) for value in (x,y,w,h) ]
        if not location:
            return make_response(json.jsonify(message = "location not entered."), 400)

        is_updated = kangarooAdminObj.updateImageOfTag(img_id, location)
        if is_updated == True:
            g.db_kang.commit()
            return make_response(json.jsonify(message = "Change Image Successfully"), 200)
        else:
            g.db_kang.rollback()
            return make_response(json.jsonify(message = "Something Wrong"), 410)

    def adminKangarooTagUpdateImageBinary_before(self, tag_id, img_id):
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
        kangarooAdminObj = KangarooAdmin(g.db_kang)
        image = request.files.get("photo_bin", None)
        
        if image is None:
            return make_response(json.jsonify(message = "'photo_bin' not entered."), 410)

        is_updated = kangarooAdminObj.updateImageOfTag_before(img_id, new_image=image)
        if is_updated == True:
            g.db_kang.commit()
            return make_response(json.jsonify(message = "Change Image Successfully"), 200)
        else:
            g.db_kang.rollback()
            return make_response(json.jsonify(message = "Something Wrong"), 410)

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
        kangarooAdminObj = KangarooAdmin(g.db_kang)
        is_updated = kangarooAdminObj.deleteImageOfTag(img_id)
        if is_updated == True:
            g.db_kang.commit()
            return make_response(json.jsonify(message = "Change Image Status Successfully"), 200)
        else:
            g.db_kang.rollback()
            return make_response(json.jsonify(message = "Something Wrong"), 410)


if __name__ == "__main__":
    pass
