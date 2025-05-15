from olt.models import OLT, OLTCabinet, FAT, Splitter, ONT, User
import os
import sys


class CheckCapacityService:

    @staticmethod
    def get_device_available_capacity(device_type, device_id, exclude_id=None):
        try:
            if device_type.lower() == 'cabinet':
                cabinet_obj = OLTCabinet.objects.get(id=device_id)
                filled_capacity = len(cabinet_obj.olt_set.all().exclude(deleted_at__isnull=False).exclude(active=False))
                max_capacity = cabinet_obj.max_capacity
                available_capacity = max_capacity - filled_capacity

            elif device_type.lower() == 'olt':
                olt_obj = OLT.objects.get(id=device_id)
                filled_capacity = len(olt_obj.fat_set.all().exclude(deleted_at__isnull=False).exclude(is_active=False))
                max_capacity = olt_obj.max_capacity
                available_capacity = max_capacity - filled_capacity

            elif device_type.lower() == 'splitter':
                splitter_obj = Splitter.objects.get(id=device_id)
                ont_count = len(splitter_obj.ont_set.all().exclude(deleted_at__isnull=False).exclude(is_active=False))
                parented_count = len(splitter_obj.splitter_set.all().exclude(deleted_at__isnull=False).exclude(is_active=False))
                filled_capacity = ont_count + parented_count
                max_capacity = splitter_obj.max_capacity
                available_capacity = max_capacity - filled_capacity

            else:
                max_capacity = None
                filled_capacity = None
                available_capacity = None
            return dict(max_capacity=max_capacity, filled_capacity=filled_capacity,
                        available_capacity=available_capacity)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})
            return {'row': str(ex) + '////' + str(exc_tb.tb_lineno)}
