import os
import sys
from django.http import JsonResponse
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status, views, permissions, pagination
from .models import ConfigRequest, ConfigRequestLog, Device
from .serializers import ConfigRequestSerializer, DeviceSerializer, ConfigRequestLogSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
import paramiko, re, math
import base64, time
from datetime import datetime, timedelta
from classes.mailer import Mail
from classes.utils import PortmanUtils
from .permissions import CanViewDevicesList, ConfigRequestPermissions


class DeviceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Device.objects.all()
    permission_classes = (IsAuthenticated, CanViewDevicesList)
    serializer_class = DeviceSerializer
    #pagination_class = None

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.filter(is_active=True)
        searchText = self.request.query_params.get('search_text', None)
        if searchText:
            queryset = queryset.filter(ip__contains=searchText)

        pagination.PageNumberPagination.page_size = 150
        return queryset


class ConfigRequestViewSet(ModelViewSet):

    MSG_NOT_PERMITTED = 'You are not permitted to approve or run this request. Contact Portman Team!'
    MSG_ALREADY_APPROVED = 'This request is already approved at this level'

    COMMAND_TYPE_CONFIG = 'config'
    COMMAND_TYPE_CHECK_CONFIG = 'check-config'

    STATUS_DONE = 'DONE'
    STATUS_ERROR = 'ERROR'

    LOG_TYPE_APPROVED = 'approved'
    LOG_TYPE_RUN_RUN_CONFIG = 'run_config'

    NOTIFICATION_TYPE_NEW = 'new_request'
    NOTIFICATION_TYPE_NEEDS_APPROVE = 'needs_approve'
    NOTIFICATION_TYPE_CONFIG_RUN = 'config_run'

    NOTIFICATION_RECEIVERS_ADMIN = ['H.Ashrafi@pishgaman.net', 'M.Pourgharib@pishgaman.net']
    NOTIFICATION_APPROVER_L1 = ['h.daryabeigi@pishgaman.net', 'M.Pourgharib@pishgaman.net']
    NOTIFICATION_APPROVER_L2 = ['h.daryabeigi@pishgaman.net', 'M.Pourgharib@pishgaman.net']

    BANDWIDTH_MIN = 1
    BANDWIDTH_MAX = 500

    HOURS = 1

    queryset = ConfigRequest.objects.all()
    serializer_class = ConfigRequestSerializer
    permission_classes = (IsAuthenticated, ConfigRequestPermissions)
    currentUser = None
    configRequest = None
    forceIp = None
    forceBW = None

    def get_queryset(self):
        queryset = self.queryset
        page_size = self.request.query_params.get('page_size', 10)
        device_id = self.request.query_params.get('device_id', None)
        requester_id = self.request.query_params.get('requester_id', None)
        orderBy = self.request.query_params.get('order_by', None)

        if device_id:
            queryset = queryset.filter(device__id=device_id)
        if requester_id:
            queryset = queryset.filter(requester_user__id=requester_id)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10

        queryset = queryset.exclude(deleted_at__isnull=False)
        if orderBy == 'near-expire':
            def next_week():
                today = datetime.today()
                return [
                    today + timedelta(days=0),
                    today + timedelta(days=7)
                ]
            queryset = queryset.filter(due_date__isnull=False).filter(due_date__range=next_week())
            queryset = queryset.order_by('due_date')
        else:
            queryset = queryset.order_by('-id')
        pagination.PageNumberPagination.page_size = page_size
        return queryset

    def create(self, request, *args, **kwargs):
        if request.data['bandwidth'] < self.BANDWIDTH_MIN or request.data['bandwidth'] > self.BANDWIDTH_MAX:
            return self.sayAccessDenied('Value of bandwidth must be between {0} and {1}'.format(self.BANDWIDTH_MIN, self.BANDWIDTH_MAX));

        request.data['requester_user'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        self.notifySupport("", self.NOTIFICATION_TYPE_NEW, self.NOTIFICATION_APPROVER_L1)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, request=self.request, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = datetime.now()
        instance.save()
        # self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def logs(self, request, pk=None):
        config_request = self.get_object()
        log_list = ConfigRequestLog.objects.all().filter(request__id=config_request.id)
        data = ConfigRequestLogSerializer(log_list, many=True)
        return Response({'results': data.data, 'status': status.HTTP_200_OK})

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        self.currentUser = request.user
        self.configRequest = self.get_object()
        self.forceIp = self.configRequest.device.ip

        if request.user.username.lower() not in self.getRunnerUsers():
            return self.sayAccessDenied(self.MSG_NOT_PERMITTED)

        if not self.configRequest.first_approver or not self.configRequest.second_approver:
            return self.sayAccessDenied("This request is not approved.")
        
        if self.configRequest.status == self.STATUS_DONE:
            return self.sayAccessDenied("This request is done.")

        if self.hasDoneRequestRecently():
            return self.sayAccessDenied("This user ({0}) has a Done request in last {1} hour(s).".format(self.configRequest.device.ip, self.HOURS));

        checkSuccessOutput = self.runCommand(self.COMMAND_TYPE_CHECK_CONFIG)
        success, sequenceNumber, bandwidth, line = self.findIpSequenceNumber(checkSuccessOutput, self.configRequest.device.ip)
        if success == False:
            return self.sayError('Unable to get sequence number of {0}'.format(self.configRequest.device.ip))

        result = self.runCommand(self.COMMAND_TYPE_CONFIG, {'sequence_number': sequenceNumber})
        
        if 'invalid' in result or 'Invalid' in result:
            return self.sayError('Device could not run config: {0}'.format(result))

        checkSuccessOutput = self.runCommand(self.COMMAND_TYPE_CHECK_CONFIG)

        logMessage = "Config Result:{0}\r\nCheck Result:{1}".format(result, checkSuccessOutput)
        self.logRequestChange(config_request=self.configRequest, type=self.LOG_TYPE_RUN_RUN_CONFIG, message=logMessage)

        checkSuccess = self.checkWasSuccessfull(checkSuccessOutput)
        if checkSuccess[0]:
            self.configRequest.status = self.STATUS_DONE
        else:
            self.configRequest.status = self.STATUS_ERROR
            

        self.configRequest.updated_at = datetime.now()
        self.configRequest.save()

        self.notifySupport(logMessage, self.NOTIFICATION_TYPE_CONFIG_RUN, self.NOTIFICATION_RECEIVERS_ADMIN)

        if self.configRequest.status == self.STATUS_DONE:
            return self.saySuccess("Config Successfully Runned Over {0}".format(self.configRequest.device.ip))

        return self.sayError("Error while configuration {0},{1}. Check Logs".format(self.configRequest.device.ip, sequenceNumber))

    def hasDoneRequestRecently(self):
        return ConfigRequest.objects.all(). \
        filter(device=self.configRequest.device). \
        filter(status=self.STATUS_DONE). \
        filter(updated_at__gt=(datetime.now() - timedelta(hours=self.HOURS))).first()

    def checkWasSuccessfull(self, command_output, checkClose = True):
        success, sequenceNumber, currentBW, line = self.findIpSequenceNumber(commandOutput=command_output, ip=self.configRequest.device.ip)
        if success != True:
            return [False, 0]

        isClose = True
        if checkClose and self.configRequest:
            isClose = int(self.configRequest.bandwidth) == int(currentBW)

        return [
            isClose,
            currentBW
        ]


    @action(detail=False, methods=["get"])
    def checkbw(self, request):
        deviceId = request.query_params['device_id']
        device = Device.objects.all().filter(pk=deviceId).first()
        self.forceIp = device.ip

        checkSuccessOutput = self.runCommand(self.COMMAND_TYPE_CHECK_CONFIG)
        success, sequenceNumber, bandwidth, line = self.findIpSequenceNumber(checkSuccessOutput, device.ip)
        if (success):
            return self.saySuccess("Current Bandwidth: {0}".format(bandwidth))

        return self.sayError("Unable to get current bandwith : {0}".format(checkSuccessOutput));
        

    @action(detail=True, methods=["put"])
    def approve(self, request, pk=None):
        self.configRequest = self.get_object()
        self.currentUser = request.user

        level = request.data.get("level")
        if level == 1:
            if self.configRequest.first_approver:
                return self.sayAccessDenied(self.MSG_ALREADY_APPROVED)

            if request.user.username.lower() not in self.getLevelOneUsers():
                return self.sayAccessDenied(self.MSG_NOT_PERMITTED)
            
            self.configRequest.first_approver = self.currentUser
            self.configRequest.updated_at = datetime.now()
            self.configRequest.save()
            self.logRequestChange(config_request=self.configRequest)
            self.notifySupport("", self.NOTIFICATION_TYPE_NEEDS_APPROVE, self.NOTIFICATION_APPROVER_L2)
            return self.saySuccess()

        elif level == 2:
            if not self.configRequest.first_approver:
                return self.sayAccessDenied("This request is not approved by first level approver")

            if self.configRequest.second_approver:
                return self.sayAccessDenied(self.MSG_ALREADY_APPROVED)

            if request.user.username.lower() not in self.getLevelTwoUsers():
                return self.sayAccessDenied(self.MSG_NOT_PERMITTED)
                
            self.configRequest.second_approver = self.currentUser
            self.configRequest.updated_at = datetime.now()
            self.configRequest.save()
            self.logRequestChange(config_request=self.configRequest)
            return self.saySuccess()
        else:
            return self.sayAccessDenied()

    def sayAccessDenied(self, message='Access Denied'):
        return Response({'results': message, 'status': status.HTTP_403_FORBIDDEN}, status=status.HTTP_200_OK)

    def saySuccess(self, message='Successfully done'):
        return Response({'results': message, 'status': status.HTTP_200_OK}, status=status.HTTP_200_OK)

    def sayError(self, message='Operation Failed!'):
        return Response({'results': message, 'status': status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_200_OK)

    def getLevelOneUsers(self):
        return ['admin', 'h.daryabeigi', 'h.semnani']

    def getLevelTwoUsers(self):
        return ['admin', 'h.daryabeigi', 'h.semnani']

    def getRunnerUsers(self):
        return ['admin', 'h.daryabeigi', 'h.semnani']

    def logRequestChange(self, config_request, type='approved', message=''):
        return ConfigRequestLog.objects.create(request=config_request, result=message, type=type, user=self.currentUser)


    def runCommand(self, type='', params = {}):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try :
            sshInfo = self.getSshInfo()
            client.connect(sshInfo[0], username=sshInfo[1], password=base64.b64decode(sshInfo[2]), timeout=10,
                               port=1001, allow_agent=False, look_for_keys=False, banner_timeout=200)

            #channel = client.invoke_shell()
            commands = self.getCommand(type=type, params=params)
            output = ''
            if commands:
                for command in commands:
                    std_in, std_out, std_err = client.exec_command(command)
                    time.sleep(1)
                    output += std_out.read().decode('utf-8').strip()

                # while not channel.recv_ready():
                #     pass

                # time.sleep(3.5)
                # while channel.recv_ready():
                #     output += channel.recv(65535).decode()
                #     time.sleep(3.5)
                    

                #channel.close()
                client.close()
            else:
                output = 'Command is not recognized!'
            
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno, ex)
            output = str(ex) + " > Could not connect using ssh"

        return output

    def getSshInfo(self):
        # this function will change when company decides to work with many Data Center
        #return ['185.126.2.1', 'Portman-OSS', 'R1hwKUBSJHM4XilEXnFUIQ==']
        return ['172.22.22.106', 'Portman-OSS', 'R1hwKUBSJHM4XilEXnFUIQ==']

    def getCommand(self, type='config', params = {}):
        if self.configRequest != None:
            userIp = self.configRequest.device.ip

        if self.forceIp != None:
            userIp = self.forceIp

        if type == self.COMMAND_TYPE_CONFIG:
            # bw = self.configRequest.bandwidth * 1024 * 1024
            # return [
            #     "conf t\n",
            #     "policy-map DEDICATED-LIMIT\n",
            #     "no class USER-{0}\n".format(userIp),
            #     "no class DEDICATED-LIMIT\n",
            #     "class USER-{0}\n".format(userIp),
            #     "police cir {0}\n".format(bw),
            #     "conform-action transmit\n",
            #     "exceed-action drop\n",
            #     "class DEDICATED-LIMIT\n",
            #     "police cir 2097000 bc 65531\n",
            #     "conform-action transmit\n",
            #     "exceed-action drop\n",
            #     "\x1a"
            # ]
            return [
                "queue simple remove numbers={0}".format(params['sequence_number']),
                "queue simple add max-limit={0}M/{1}M name={2} target={3}/32".format(self.configRequest.bandwidth, self.configRequest.bandwidth, userIp, userIp)
            ]
        elif type == self.COMMAND_TYPE_CHECK_CONFIG:
            #return ["sho run | s class USER-{0}\n".format(userIp)]
            return [
                "queue simple print without-paging terse"
            ]
        else:
            return False

    def notifySupport(self, log='', type= '', receivers=[]):
        
        if type in [self.NOTIFICATION_TYPE_CONFIG_RUN, self.NOTIFICATION_TYPE_NEEDS_APPROVE]:
            if self.configRequest is None:
                return False

        try:
            mail_info = Mail()
            mail_info.from_addr = 'oss-notification@pishgaman.net'
            mail_info.to_addr = ', '.join(receivers)
            if type == self.NOTIFICATION_TYPE_CONFIG_RUN:
                mail_info.msg_body = "----\r\nIP: USER-{0}\r\nNew Bandwith: {1}\r\nStatus: {2}\r\n\r\nCommand Logs:\r\n\r\n{3}".format(
                    self.configRequest.device.ip,
                    self.configRequest.bandwidth,
                    self.configRequest.status,
                    log
                )
                mail_info.msg_subject = "Portman(Cloud Service) - Command ran on {0}".format(self.configRequest.device.ip)
            elif type == self.NOTIFICATION_TYPE_NEEDS_APPROVE:
                mail_info.msg_body = "A new configuration request is waiting for your approval. {0}".format(self.configRequest.id)
                mail_info.msg_subject = "Portman(Cloud Service) - Approval"
            elif type == self.NOTIFICATION_TYPE_NEW:
                mail_info.msg_body = "A new configuration request is waiting for your approval."
                mail_info.msg_subject = "Portman(Cloud Service) - New Request"
            else:
                return False

            Mail.Send_Mail(mail_info)
            return True
        except:
            return False

    def findIpSequenceNumber(self, commandOutput, ip):
        lines = commandOutput.split('\n')
        for line in lines:
            if f'name={ip} ' in line:
                parts = line.split()
                sq_number = parts[0]
                max_limit = None
                for part in parts:
                    if part.startswith("max-limit="):
                        max_limit = part.split('=')[1]
                        max_limit = max_limit.split('/')[0].replace('M', '')
                return True, int(sq_number), int(max_limit), line
        return False, None, None, ""



