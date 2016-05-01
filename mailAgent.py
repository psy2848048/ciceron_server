# -*- coding: utf-8 -*-
import psycopg2
import ciceron_lib as lib
import mail_template


DATABASE = None
if os.environ.get('PURPOSE') == 'PROD':
    DATABASE = "host=ciceronprod.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=%s"
else:
    DATABASE = "host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=%s"


class MailAgent:

    def __init__(self, dbInfo):
        self.conn = psycopg2.connect(dbInfo)

    def parallel_send_email(user_name, user_email, noti_type, request_id, language_id, optional_info=None):
        import mail_template
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

