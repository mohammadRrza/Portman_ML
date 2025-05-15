from django.db import models
from django.utils import timezone
from users.models import User


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.deleted_at = None
        self.save()


class MobileNumber(TimeStampedModel):
    mobile_number = models.CharField(max_length=16)
    creator = models.ForeignKey(User, on_delete=models.DO_NOTHING)


class Advertiser(TimeStampedModel):
    contact_number = models.CharField(max_length=16)
    chakavak_id = models.PositiveIntegerField(null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"Advertiser (Contact: {self.contact_number})"


class BlockedList(TimeStampedModel):
    advertiser = models.ForeignKey(Advertiser, on_delete=models.DO_NOTHING)
    mobile_number = models.CharField(max_length=16)
    creator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=16, null=True, blank=True)
    ibs_err = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return f"Blocked: {self.advertiser.contact_number} -> {self.mobile_number}"
