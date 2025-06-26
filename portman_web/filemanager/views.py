from rest_framework import viewsets, status
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from rest_framework.decorators import action
import mimetypes
from django.http import FileResponse
import os
import time
from .models import File, FileLog
from .serializers import FileSerializer
from rest_framework.exceptions import NotFound
import base64
from django.conf import settings
from django.http import Http404
# Create your views here.
from rest_framework.permissions import IsAuthenticated
from .permissions import CanViewFileList
from django.shortcuts import get_object_or_404
from datetime import datetime
from olt.models import FAT, OLTCabinet, Joint, OLT, Handhole, Microduct, Cable, Splitter
from users.models import User as MainUser
from cartable.models import Ticket, Task
from django.contrib.contenttypes.models import ContentType


class FileViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, CanViewFileList)
    queryset = File.objects.all()
    serializer_class = FileSerializer
    ALLOWED_FILE_TYPES = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.xlsx', '.kmz', '.kml']
    ALLOWED_CONTENT_TYPES = [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.google-earth.kmz',
        'application/vnd.google-earth.kml+xml'
    ]
    MAX_FILE_SIZE = 2 * 1024 * 1024
    model_mapping = {
        'ftth-fat': FAT,
        'ftth-cabinet': OLTCabinet,
        'ftth-joint': Joint,
        'ftth-odc': OLTCabinet,
        'ticket': Ticket,
        'task': Task,
        'ftth-olt': OLT,
        'ftth-handhole': Handhole,
        'ftth-microduct': Microduct,
        'ftth-cable': Cable,
        'ftth-splitter': Splitter,
        'user': MainUser
    }

    def get_queryset(self):
        content_type = self.request.query_params.get('content_type')
        content_type = ContentType.objects.get_for_model(self.model_mapping.get(content_type))
        content_id_base64 = self.request.query_params.get('content_id')

        queryset = File.objects.all().exclude(deleted_at__isnull=False)

        if content_type and content_id_base64:
            # Decode the base64 values
            object_id = base64.b64decode(content_id_base64).decode('utf-8')

            queryset = queryset.filter(content_type=content_type, object_id=object_id)

        return queryset

    @action(detail=False, methods=["post"])
    def upload(self, request, *args, **kwargs):
        files = request.FILES.getlist('files')
        content_type = request.data.get('content_type')
        object_id = request.data.get('object_id')
        comment = request.data.get('comment', None)
        if not all([files, content_type, object_id]):
            return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)
        model = self.model_mapping.get(content_type.lower())
        if not model:
            raise ValidationError(dict(results='Invalid content_type'))
        content_type = ContentType.objects.get_for_model(model)

        saved_files = []
        errors = []

        for file in files:

            # Validate file type
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension not in self.ALLOWED_FILE_TYPES:
                error_message = f'Invalid file type: {file.name}'
                errors.append(error_message)
                save_log(None, request.user, action='upload', error_message=error_message)
                continue

            # Validate file content type
            file_content_type = file.content_type
            if file_content_type not in self.ALLOWED_CONTENT_TYPES:
                error_message = f'Invalid file content type: {file.name}'
                errors.append(error_message)
                save_log(None, request.user, action='upload', error_message=error_message)
                continue
            
            # Validate file size
            if file.size > self.MAX_FILE_SIZE:
                error_message = f'File size exceeds the limit: {file.name}'
                errors.append(error_message)
                save_log(None, request.user, action='upload', error_message=error_message)
                continue

            file_type = None
            if 'image' in file_content_type:
               file_type = 'image'
            elif 'pdf' in file_content_type:
               file_type = 'pdf'
            elif 'word' in file_content_type:
                file_type = 'word'
            elif 'spreadsheetml.sheet' in file_content_type:
                file_type = 'excel'
            elif 'google-earth.kmz' in file_content_type:
                file_type = 'kmz'
            elif 'google-earth.kml' in file_content_type:
                file_type = 'kml'

            # Fetch the label (file name) from the uploaded file
            label = file.name
            unique_filename = self.generate_unique_filename(content_type.name, object_id, file_extension)
            
            try:
                # Save the file to the storage location
                saved_file = File(
                    label=label,
                    content_type=content_type,
                    object_id=object_id,
                    comment=comment,
                    file=file,
                    name=unique_filename,
                    size=file.size,
                    type=file_type
                )
                saved_file.full_clean()  # Run model validation
                saved_file.save()
                saved_files.append(saved_file)
                save_log(saved_file, request.user, action='upload')
            except ValidationError as e:
                errors.append(f'Error saving file {file.name}: {str(e)}')
                save_log(None, request.user, action='upload', error_message=str(e))

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FileSerializer(saved_files, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        try:
            decoded_pk = base64.b64decode(pk).decode('utf-8')
            file = get_object_or_404(File, pk=decoded_pk)
            if file.deleted_at:
                raise NotFound('File not found')
            file_path = file.file.path
            file_name = file.label

            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            save_log(file, request.user, action='download')

            return response

        except FileNotFoundError as e:
            save_log(None, request.user, action='download', error_message=str(e.args))
            raise NotFound('File not found')

    def destroy(self, request, *args, **kwargs):
        try:
            decoded_pk = base64.b64decode(kwargs['pk']).decode('utf-8')
            instance = get_object_or_404(File, pk=decoded_pk)
            instance.deleted_at = datetime.now()
            instance.save()
            save_log(instance, request.user, action='delete')
        except Http404:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            # Delete file from storage
            file_path = instance.file.path
            os.remove(file_path)
        except OSError as e:
            error_message = str(e.args)
            save_log(instance, request.user, action='delete', error_message=error_message)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def generate_unique_filename(self, content_type, content_id, file_extension):
        timestamp = str(int(time.time())) 
        base_filename = f"{content_type}_{content_id}_{timestamp}"
        unique_filename = f"{base_filename}{file_extension}"
        counter = 1
        while File.objects.filter(name=unique_filename).exists():
            unique_filename = f"{base_filename}_{counter}{file_extension}"
            counter += 1
        return unique_filename


def save_log(file, user, action, error_message=None):
    try:

        file_log = FileLog(file=file, user=user, action=action, error_message=error_message)
        file_log.save()
    except Exception as e:
        print(f"Error file log: {str(e)}")
