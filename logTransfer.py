# -*- coding: utf-8 -*-
import psycopg2


class LogTransfer:

    def __init__(self, dbInfo):
        self.conn = psycopg2.connect(dbInfo)

    def logTransfer(self, conn):
        cursor = self.conn.cursor()
        
        query_getmax = "SELECT MAX(id) FROM CICERON.TEMP_ACTIONS_LOG"
        cursor.execute(query_getmax)
        max_id = cursor.fetchone()[0]
    
        query_insertLog = """
            INSERT INTO CICERON.USER_ACTIONS (id, user_id, method, api, log_time, ip_address)
            SELECT id, user_id, method, api, log_time, ip_address
            FROM CICERON.TEMP_ACTIONS_LOG
            WHERE id <= %s """
        cursor.execute(query_insertLog, (max_id, ))
    
        query_deleteLog = """DELETE FROM CICERON.TEMP_ACTIONS_LOG WHERE id <= %s """
        cursor.execute(query_deleteLog, (max_id, ))
    
        self.conn.commit()

if __name__ == "__main__":
    DATABASE = None
    if os.environ.get('PURPOSE') == 'PROD':
        DATABASE = "host=ciceronprod.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=%s"
    else:
        DATABASE = "host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=%s"
