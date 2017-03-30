# -*- coding: utf-8 -*-

import psycopg2
from unittest import TestCase
import sys
sys.path.append('../app')

import application
from adminKangaroo import KangarooAdmin

class KangarooAdminTestCase(TestCase):
	def _sessionMarkedAsLoggedIn(self):
		pass

	def setUp(self):
		application.app.config['TESTING'] = True
		self.app = application.app.test_client()

	def tearDown(self):
		pass


	def test_adminKangarooTagListing(self):
	    res = self.app.get('/api/v2/admin/kangaroo/tag')
	    self.assertEqual(res.status_code, 200)

	def test_adminKangarooTagCategorryHierarchy(self):
		res = self.app.get('/api/v2/admin/kangaroo/tag/category1/1')
		self.assertEqual(res.status_code, 200)



	def test_adminKangarooTagUpdate(self):
		res = self.app.post('/api/v2/admin/kangaroo/tag',
		                    data = dict(
			                    tag_id = 1,
			                    category_level_1 = 1,
			                    category_level_2 = 2,
		                    ))
		self.assertEqual(res.status_code, 200)

	def test_adminKangarooTagDelete(self):
		res = self.app.delete('/api/v2/admin/kangaroo/tag/1')
		self.assertEqual(res.status_code, 200)

    # 성공
	def test_adminKangarooTagImageLists(self):
		res = self.app.get('/api/v2/admin/kangaroo/tag/12')
		self.assertEqual(res.status_code, 200)

	# 실패 => 없는 tag 파라미터를 넣었을때
	def test_adminKangarooTagImageLists_fail1(self):
		res = self.app.get('/api/v2/admin/kangaroo/tag/10')
		self.assertEqual(res.status_code, 404)


	# 404 실패 => db에 데이터가 없을때
	def test_adminKangarooTagProvideImageBinary_fail1(self):
		res = self.app.get('/api/v2/admin/kangaroo/tag/12/img/2/img.jpg')
		self.assertEqual(res.status_code, 404)













