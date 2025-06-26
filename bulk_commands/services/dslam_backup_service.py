
from .params import Param, PortCondition
import json
from dj_bridge import DSLAM
from dj_bridge import utility, DSLAM_BACKUP_PATH
import os
import sys
from datetime import datetime, date


def update_backup_date(dslam_objs):
    for dslam in dslam_objs:
        dslam.last_backup_date = datetime.now()
        dslam.save()


def check_last_backup_date(dslam_type):

    if dslam_type == 'fiberhome':
        dslam_type_ids = [3, 4, 5]
        dslam_objs = DSLAM.objects.filter(dslam_type__id__in=dslam_type_ids).order_by('last_backup_date').exclude(
            name__icontains='collected').exclude(active=False)
    else:
        dslam_type_ids = [1, 2, 7]
        dslam_objs = DSLAM.objects.filter(dslam_type__id__in=dslam_type_ids).order_by('last_backup_date').exclude(
            name__icontains='collected').exclude(active=False)

    dslam_objs = dslam_objs.filter(last_backup_date__lt=date.today())[:3]
    update_backup_date(dslam_objs)
    return dslam_objs


def get_dslam_backup(dslam_type):
    dslam_objs = check_last_backup_date(dslam_type)
    zyxel_path = DSLAM_BACKUP_PATH + 'zyxel/'
    zyxel_1248_path = DSLAM_BACKUP_PATH + 'zyxel_1248/'
    fiberhome_3300_path = DSLAM_BACKUP_PATH + 'fiberhome_3300/'
    fiberhome_2200_path = DSLAM_BACKUP_PATH + 'fiberhome_2200/'
    fiberhome_5006_path = DSLAM_BACKUP_PATH + 'fiberhome_5006/'
    huawei_path = DSLAM_BACKUP_PATH + 'huawei/'
    if not os.path.exists(zyxel_path):
        os.makedirs(zyxel_path)
    if not os.path.exists(zyxel_1248_path):
        os.makedirs(zyxel_1248_path)
    if not os.path.exists(fiberhome_2200_path):
        os.makedirs(fiberhome_2200_path)
    if not os.path.exists(fiberhome_3300_path):
        os.makedirs(fiberhome_3300_path)
    if not os.path.exists(fiberhome_5006_path):
        os.makedirs(fiberhome_5006_path)
    if not os.path.exists(huawei_path):
        os.makedirs(huawei_path)
    try:
        for dslam_obj in dslam_objs:
            print(dslam_obj.name, datetime.now())
            params = Param()
            params.type = 'dslamport'
            params.is_queue = False
            params.fqdn = dslam_obj.fqdn
            params.command = 'get config'
            dslam_type = dslam_obj.dslam_type_id
            params.port_conditions = PortCondition()
            params.port_conditions.slot_number = 1
            params.port_conditions.port_number = 1
            params = json.dumps(params, default=lambda x: x.__dict__)
            if dslam_type == 4:
                path = fiberhome_2200_path
            elif dslam_type == 1:
                path = zyxel_path
            elif dslam_type == 2:
                path = huawei_path
            elif dslam_type == 3:
                path = fiberhome_3300_path
            elif dslam_type == 5:
                path = fiberhome_5006_path
            else:
                path = zyxel_1248_path
            try:
                result = utility.dslam_port_run_command(dslam_obj.pk, 'get config', json.loads(params))

                if result.get('status', None) == 200:
                    with open(path + "{0}@{1}_{2}.txt".format(
                            dslam_obj.fqdn, dslam_obj.ip, str(datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))),
                              "w") as backup_file:
                        backup_file.write(result.get('result'))
                else:
                    with open(
                            path + 'Error#{0}@{1}_{2}.txt'.format(
                                dslam_obj.fqdn, dslam_obj.ip, str(datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))),
                            'w') as text_file:
                        text_file.write("Error_ %s" % result.get('result'))
            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print(ex)
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                try:
                    with open(
                            path + 'Error#{0}@{1}_{2}.txt'.format(dslam_obj.fqdn, dslam_obj.ip,
                                                                              str(datetime.today().strftime(
                                                                                  '%Y-%m-%d-%H:%M:%S'))), 'w') as text_file:
                        text_file.write("Error_ %s" % str(ex))
                except Exception as ex:
                    print(ex)
                    continue

    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f"Error is {0}'.format({ex}), 'Line': {str(exc_tb.tb_lineno)}, 'ip': {dslam_obj.ip}")

