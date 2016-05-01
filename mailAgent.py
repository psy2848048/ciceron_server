# -*- coding: utf-8 -*-
import psycopg2
import ciceron_lib as lib
import mail_temppplate
from multiprocessing import Process
import argparse


class MailAgent:

    def __init__(self, dbInfo):
        self.conn = psycopg2.connect(dbInfo)

    def publicize(self):
        # No Expected time
        cursor = self.conn.cursor()
        translator_list = []
        client_list = []

        query_no_expected_time = """SELECT ongoing_worker_id, client_user_id, id
            FROM CICERON.F_REQUESTS
            WHERE (isSos = false AND status_id = 1 AND expected_time is null AND (CURRENT_TIMESTAMP - start_translating_time) > (due_time - start_translating_time)/2 AND start_translating_time + interval '30 minutes' < due_time)
            OR    (isSos= false AND status_id = 1 AND expected_time is null AND (CURRENT_TIMESTAMP - start_translating_time) > (due_time - start_translating_time)/3 AND start_translating_time + interval '30 minutes' > due_time) """
        cursor.execute(query_no_expected_time)
        rs = cursor.fetchall()
        for item in rs:
            lib.send_noti_suite(gcm_server, self.conn, item[0], 6, item[1], item[2])
            lib.send_noti_suite(gcm_server, self.conn, item[1], 10, item[0], item[2])
            translator_list.append(item[0])
            client_list.append(item[1])

        # Expired deadline
        query_expired_deadline = """SELECT ongoing_worker_id, client_user_id, id
            FROM CICERON.F_REQUESTS
            WHERE isSos = false AND status_id = 1 AND CURRENT_TIMESTAMP > due_time """
        cursor.execute(query_expired_deadline)
        rs = cursor.fetchall()
        for item in rs:
            lib.send_noti_suite(gcm_server, self.conn, item[1], 12, item[0], item[2])
            lib.send_noti_suite(gcm_server, self.conn, item[0],  4, item[1], item[2])
            translator_list.append(item[0])
            client_list.append(item[1])

        # No translators
        query_no_translators = """SELECT client_user_id, id
            FROM CICERON.F_REQUESTS
            WHERE isSos = false AND status_id = 0 AND CURRENT_TIMESTAMP > due_time """
        cursor.execute(query_no_translators)
        rs = cursor.fetchall()
        for item in rs:
            lib.send_noti_suite(gcm_server, self.conn, item[0], 13, None, item[1])
            client_list.append(item[0])

        cursor.execute("""UPDATE CICERON.F_REQUESTS SET status_id = -1
            WHERE isSos = false AND status_id IN (0,1) AND CURRENT_TIMESTAMP > due_time """)
        cursor.execute("""UPDATE CICERON.F_REQUESTS SET status_id = 0, ongoing_worker_id = null, start_translating_time = null
            WHERE (isSos= false AND status_id = 1 AND expected_time is null AND (CURRENT_TIMESTAMP - start_translating_time) > (due_time - start_translating_time)/2 AND start_translating_time + interval '30 minutes' < due_time)
            OR    (isSos= false AND status_id = 1 AND expected_time is null AND (CURRENT_TIMESTAMP - start_translating_time) > (due_time - start_translating_time)/3 AND start_translating_time + interval '30 minutes' > due_time) """)
        self.conn.commit()

        for user_id in translator_list: lib.update_user_record(self.conn, translator_id=user_id)
        for user_id in client_list:     lib.update_user_record(self.conn, client_id=user_id)
        self.conn.commit()

    def ask_expected_time(self):
        cursor = self.conn.cursor()
        query = """SELECT fact.ongoing_worker_id, fact.id, fact.client_user_id FROM CICERON.F_REQUESTS fact
            LEFT OUTER JOIN CICERON.V_NOTIFICATION noti ON fact.id = noti.request_id AND noti.noti_type_id = 1
            WHERE fact.isSos= false AND fact.status_id = 1 AND fact.expected_time is null AND noti.is_read is null
            AND (
              (CURRENT_TIMESTAMP > fact.start_translating_time + interval '30 minutes' AND fact.due_time > CURRENT_TIMESTAMP + interval '30 minutes')
            OR 
              (CURRENT_TIMESTAMP - fact.start_translating_time > (fact.due_time - fact.start_translating_time)/3 AND fact.due_time < CURRENT_TIMESTAMP + interval '30 minutes') 
            )"""
        cursor.execute(query) 
        rs = cursor.fetchall()
        for item in rs:
            lib.send_noti_suite(gcm_server, self.conn, item[0], 2, item[2], item[1])

        self.conn.commit()

    def delete_sos(self):
        # Expired deadline
        # Using ongoing_worker_id and client_user_id, and update statistics after commit
        cursor = self.conn.cursor()
        translator_list = []
        client_list = []

        query_expired_deadline = """SELECT ongoing_worker_id, client_user_id, id
            FROM CICERON.F_REQUESTS
            WHERE isSos = true AND status_id = 1 and ongoing_worker_id is not null AND CURRENT_TIMESTAMP > due_time """
        cursor.execute(query_expired_deadline)
        rs = cursor.fetchall()
        for item in rs:
            lib.send_noti_suite(gcm_server, self.conn, item[1], 12, item[0], item[2])
            lib.send_noti_suite(gcm_server, self.conn, item[0],  4, item[1], item[2])
            translator_list.append(item[0])
            client_list.append(item[1])

        # No translators
        query_no_translators = """SELECT client_user_id, id
            FROM CICERON.F_REQUESTS
            WHERE isSos = true AND status_id = 0 AND CURRENT_TIMESTAMP > due_time """
        cursor.execute(query_no_translators)
        rs = cursor.fetchall()
        for item in rs:
            send_noti_suite(gcm_server, self.conn, item[0], 13, None, item[1])
            client_list.append(item[0])

        cursor.execute("""UPDATE CICERON.F_REQUESTS SET status_id = -1
                         WHERE status_id in (0,1) AND isSos = true AND CURRENT_TIMESTAMP >= registered_time + interval '30 minutes'""")
        self.conn.commit()

        for user_id in translator_list: lib.update_user_record(self.conn, translator_id=user_id)
        for user_id in client_list:     lib.update_user_record(self.conn, client_id=user_id)


    def _unitMailSender(self, user_name, user_email, noti_type, request_id, language_id, optional_info=None):
        template = mail_template.mail_format()
        message = None

        if noti_type == 1:
            message = template.translator_new_ticket(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/stoa/%d') % request_id}
    
        elif noti_type == 2:
            message = template.translator_check_expected_time(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/translating/%d') % request_id,
                 "expected": optional_info.get('expected')}
                # datetime.now() + timedelta(seconds=(due_time - start_translating_time)/3)

        elif noti_type == 3:
            message = template.translator_complete(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/activity/%d') % request_id}
                
        elif noti_type == 4:
            message = template.translator_exceeded_due(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/stoa/%d') % request_id}

        elif noti_type == 5:
            message = template.translator_extended_due(langauge_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/translating/%d') % request_id,
                 "new_due": optional_info.get('new_due')}

        elif noti_type == 6:
            message = template.translator_no_answer_expected_time(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/stoa/%d') % request_id}

        elif noti_type == 7:
            message = template.client_take_ticket(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/processingrequests/%d') % request_id,
                 'hero': optional_info.get('hero')}

        elif noti_type == 8:
            message = template.client_check_expected_time(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/processingrequests/%d') % request_id}

        elif noti_type == 9:
            message = template.client_giveup_ticket(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/stoa/%d') % request_id,
                 "hero": optional_info.get('hero')}

        elif noti_type == 10:
            message = template.client_no_answer_expected_time_go_to_stoa(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/stoa/%d') % request_id}

        elif noti_type == 11:
            message = template.client_complete(language_id) %{"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/donerequests/%d') % request_id,
                 "hero": optional_info.get('hero')}

        elif noti_type == 12:
            message = template.client_incomplete(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/processingrequests/%d') % request_id}

        elif noti_type == 13:
            message = template.client_no_hero(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/processingrequests/%d') % request_id}

        elif noti_type == 15:
            message = template.client_no_hero(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
                 "user": user_name,
                 "link": (HOST + '/stoa')}

        lib.send_mail(user_email, "Here is your news, %s" % user_name, message)

    def parallel_send_email(self):
        cursor = self.conn.cursor()
        query = """SELECT 
            user_id, user_email, user_name, noti_type_id, noti_type, request_id, context, registered_time, expected_time, submitted_time, start_translating_time, due_time, points, target_user_id, target_user_email, target_user_name, target_profile_pic_path, ts, is_read, user_profile_pic_path, status_id
            FROM CICERON.V_NOTIFICATION 
                WHERE is_read = false AND is_mail_sent = false AND CURRENT_TIMESTAMP > ts + interval '3 minutes'
            ORDER BY ts"""
        cursor.execute(query)
        rs = cursor.fetchall()
        process_pool = []

        for idx, item in enumerate(rs):
            user_id = item[0]
            query_mother_lang = "SELECT mother_language_id FROM CICERON.D_USERS WHERE id = %s"
            cursor.execute(query_mother_lang, (user_id, ) )
            mother_lang_id = cursor.fetchall()[0][0]

            proc = Process(target=self._unitMailSender,
                           args=(item[2], item[1], item[3], item[5], mother_lang_id),
                           kwargs={"optional_info": {
                                       "expected": item[10] + (item[11] - item[10])/3 if item[10] != None and item[11] != None else None,
                                       "new_due": item[11],
                                       "hero": item[15]
                                      }
                                  }
                           )
    
            process_pool.append(proc)

            #parallel_send_email(item[2], item[1], item[3], item[5], mother_lang_id,
            #               optional_info={
            #                           "expected": string2Date(item[10]) + (string2Date(item[11]) - string2Date(item[10]))/3 if item[10] != None and item[11] != None else None,
            #                           "new_due": string2Date(item[11]) if item[11] != None else None,
            #                           "hero": str(item[15]) if item[15] != None else None
            #                          }
            #               )
    
            if idx % 5 == 4 or idx == len(rs)-1:
                for i in process_pool:
                    i.start()
                for i in process_pool:
                    i.join()
                process_pool = []

        query = "UPDATE CICERON.F_NOTIFICATION SET is_mail_sent = true WHERE is_read = false AND CURRENT_TIMESTAMP > ts + interval '3 minutes'"
        cursor.execute(query)
        self.conn.commit()

    def run(self, isCheck=True):

if __name__ == "__main__":
    DATABASE = None
    if os.environ.get('PURPOSE') == 'PROD':
        DATABASE = "host=ciceronprod.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=%s"
    else:
        DATABASE = "host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=%s"

    parser = argparse.ArgumentParser(description='Translation agent')
    parser.add_argument('--dbpass', dest='dbpass', help='DB password')
    parser.add_argument('--check', dest='check', default='false', help='Just for check')
    args = parser.parse_args()

    dbInfo = DATABASE % args.dbpass
    mailAgent = MailAgent(dbInfo)
