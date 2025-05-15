from django.db import models
import os
from users.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

# Create your models here.


def get_file_upload_path(instance, filename):
    content_type = instance.content_type.name
    unique_filename = instance.name
    return os.path.join('uploads/filemanager', content_type, unique_filename)


class File(models.Model):
    label = models.CharField(max_length=128)
    name = models.CharField(max_length=255)
    size = models.PositiveIntegerField()
    type = models.CharField(max_length=16)
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    comment = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=get_file_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return self.name


class FileLog(models.Model):
    file = models.ForeignKey(File, on_delete=models.DO_NOTHING, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    timestamp = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(null=True, blank=True)
    action = models.CharField(max_length=12)

    def __str__(self):
        return f"{self.file} - {self.timestamp}"
