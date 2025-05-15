import os
import sys
import re
from datetime import datetime, date
from dj_bridge import OLT, olt_utility, OLT_BACKUP_PATH


def update_backup_date(olts):
    for olt in olts:
        olt.last_backup_date = datetime.now()
        olt.save()


def latest_olt():
    olts = OLT.objects.all().exclude(deleted_at__isnull=False).exclude(active=False).exclude(
                                    olt_type__model='olt_zyxel').order_by('last_backup_date')
    olts = olts.filter(last_backup_date__lt=date.today())[:3]
    update_backup_date(olts)
    return olts


def olt_backup():
    olts = latest_olt()
    params = dict(is_queue=False, request_from_ui=True)
    command = 'get backup'
    for olt in olts:
        try:
            backup_path = OLT_BACKUP_PATH + olt.olt_type.model + '/'
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
            result = olt_utility.olt_run_command(olt.pk, command, params)
            if olt.olt_type.model == 'olt_huawei':
                result['result'] = result['result'].split("\r\n")
                result['result'] = [re.sub(r"-+\s[a-zA-Z\s(\')-]+\S+\s+\S\[37D", "", val) for val in result['result']]
                result['result'] = "\r\n".join(result['result'])
            if result.get('status', None) == 200 and len(result.get('result', None)) > 100:
                with open(backup_path + "{0}@{1}_{2}.txt".format(
                        olt.fqdn, olt.ip, str(datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))),
                          "w") as backup_file:
                    backup_file.write(result.get('result'))
            else:
                with open(
                        backup_path + 'Error#{0}@{1}_{2}.txt'.format(
                            olt.fqdn, olt.ip, str(datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))),
                        'w') as error_file:
                    error_file.write("Error_ %s" % result.get('result'))
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            try:
                with open(
                        backup_path + 'Error#{0}@{1}_{2}.txt'.format(olt.fqdn, olt.ip,
                                                              str(datetime.today().strftime(
                                                                  '%Y-%m-%d-%H:%M:%S'))), 'w') as error_file:
                    error_file.write("Error_ %s" % str(ex))
            except Exception as ex:
                print(ex)
                continue


if __name__ == '__main__':
    olt_backup()
