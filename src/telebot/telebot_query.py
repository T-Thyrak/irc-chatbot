from src.mysqlquery import *
from src.ext.feedback import Feedback

LIMIT = 25

def get_feedbacks(page: int, type: str, status: str, row: int, sender_psid: str, name: str) -> list[Feedback]:
    db_conn = create_connection()
    
    if db_conn is None:
        return []
    
    if row != 0:
        query = "SELECT * FROM `feedbacks` WHERE `id` = %s"
        result = execute_query(query, db_conn, (row,))
    elif page == 1 and type == 'all' and status == 'all' and sender_psid == '' and name == '':
        query = f"SELECT * FROM `feedbacks` LIMIT {LIMIT}"
        result = execute_query(query, db_conn)
    else:
        values = []
        query = f"SELECT * FROM `feedbacks`"
        if type != 'all' or status != 'all' or sender_psid != '' or name != '':
            query += " WHERE"
        
        if type != 'all':
            query += f" `feedback_type` = %s"
            values.append(type)
        
        if status != 'all':
            if type != 'all':
                query += " AND"
            query += f" `feedback_status` = %s"
            values.append(status)
        
        if sender_psid != '':
            if type != 'all' or status != 'all':
                query += " AND"
            query += f" `sender_psid` = %s"
            values.append(sender_psid)
            
        if name != '':
            if type != 'all' or status != 'all' or sender_psid != '':
                query += " AND"
            query += f" `name` = %s"
            values.append(name)
            
        query += f" LIMIT {LIMIT} OFFSET {LIMIT * (page - 1)}"
        
        result = execute_query(query, db_conn, tuple(values)) if len(values) > 0 else execute_query(query, db_conn)
    
    destroy_connection(db_conn)
    if result is None:
        return []
    else:
        return [Feedback.from_tuple(row) for row in result]
            
            
def set_feedback_status(row: int, status: str):
    db_conn = create_connection()
    start_commit(db_conn)
    
    query = "UPDATE `feedbacks` SET `feedback_status` = %s WHERE `id` = %s"
    execute_query(query, db_conn, (status, row))
    
    end_commit(db_conn)
    destroy_connection(db_conn)