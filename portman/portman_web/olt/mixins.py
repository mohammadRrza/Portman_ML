

import re
from .models import *
from .serializers import *
from olt import utility
from rest_framework.response import Response
from rest_framework import status
from .services.mini_services import add_audit_log
from django.db import transaction

class SetupOntMixin:
    def config_ont_by_reservation(self, reservedPortId, request=None):
        reservation = ReservedPorts.objects.all().filter(pk=reservedPortId).first()
        if reservation == None:
            return Response(dict(results=f"Reservation Not Found"), status=status.HTTP_404_NOT_FOUND)

        reservationData = ReservedPortFullSerializer(reservation).data
        if reservationData['splitter_info']:
            fatInfo = reservationData['splitter_info']['fat_info']
        else:
            fatInfo = reservationData['patch_panel_port_info']['fat_info']
        oltInfo = OLT.objects.all().filter(pk=fatInfo['olt_info']['id']).first()
        if oltInfo == None:
            return Response(dict(results=f"OLT Not Found"), status=status.HTTP_404_NOT_FOUND)

        #check for status 
        if reservation.status != ReservedPorts.STATUS_READY_TO_CONFIG:
            return Response(dict(results=f"Reservation status must be ready to config", code=100), status=status.HTTP_400_BAD_REQUEST)

        #upsert pon sn if exists
        ponSerialNumber = request.data.get('pon_serial_number', reservationData['pon_serial_number'])
        if re.match(r'^[0-9a-zA-Z]+$', ponSerialNumber) == False:
            return Response(dict(results=f"ONT serial number is missed or wrong", code=100), status=status.HTTP_400_BAD_REQUEST)
        
        if reservationData['pon_serial_number'] != ponSerialNumber:
            reservation.pon_serial_number = ponSerialNumber
            reservation.save()

        commandParams = dict( ##### !!!!! PLACE ACTUAL VALUES  !!!!!
                port_conditions=dict(slot_number=-1, port_number=-1),
                serial_number=ponSerialNumber.upper(),
                description=reservationData['customer_name_en'].replace(" ", "_"),
                request_from_ui=False
            )

        result = utility.olt_run_command(oltInfo.pk, "setup ont", commandParams)

        if request != None:
            description = dict(olt_id=oltInfo.id, reserved_port_id=reservedPortId, command_result=str(result), params=str(commandParams))
            add_audit_log(request, 'OntSetup', reservedPortId, 'BY_RESERVATION', str(description))

        errorMessage = "Error while configuring ONT. Please Review Inputs"
        if result != None and result != '' and result['status'] == 200:
            try:
                with transaction.atomic():
                    #configParams = result['result']
                    
                    # find ont type
                    #ontTypeInstance, created = ONTType.objects.get_or_create(name=configParams['equipment_type'])

                    # create ont model
                    #ont = ONT.objects.create(olt_slot_number=configParams['slot'], olt_port_number=configParams['port'], 
                    #ont_type= ontTypeInstance, serial_number=configParams['serial'], is_active=True)

                    # create user model
                    #ftthUser = User.objects.create(lat=reservation.lat, long=reservation.lng, crm_id=reservation.crm_id, ont=ont)

                    # log setup info
                    #ontSetup = OntSetup.objects.create(lat=reservation.lat, lng=reservation.lng, description="", pon_serial_number=configParams['serial'],
                    #slot=configParams['slot'], port=configParams['port'], reserved_port=reservation, customer_name=reservation.customer_name_en, customer_username=reservation.crm_username,
                    #confirm_ont_id=configParams['ont_id'], confirmor=request.user, commands="", ftth_ont_id=ont.id, fat=reservation.fat, ftth_user_id=ftthUser.id)

                    # update reservation
                    #reservation.ftth_user = ftthUser
                    reservation.status = ReservedPorts.STATUS_READY_TO_INSTALL
                    reservation.save()

                    return Response(dict(results="ONT Configured Successfully", code=10), status=200)
            except Exception as e:
                print(e)
                errorMessage = "Ont Configured but not completely, try again in a few seconds"
                pass
        elif result != None and result != '' and result['result'] != None:
            errorMessage = result['result']

        return Response(dict(results=errorMessage, code=100), status=status.HTTP_400_BAD_REQUEST)
