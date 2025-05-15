from django.db import connection


def delete_log():

    delete_userauditlog_query = "DELETE FROM users_userauditlog WHERE created_at < current_date - interval '2 month'"
    cursor = connection.cursor()
    cursor.execute(delete_userauditlog_query)

    delete_portman_log_query = "DELETE FROM users_portmanlog WHERE log_date < current_date - interval '2 month'"
    cursor.execute(delete_portman_log_query)

    delete_port_command_query = "DELETE FROM dslam_portcommand WHERE created_at < current_date - interval '2 month'"
    cursor.execute(delete_port_command_query)

    cursor.close()

