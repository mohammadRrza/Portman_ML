from datetime import datetime
from dj_bridge import Reminder
from django.contrib.contenttypes.models import ContentType


def get_pending_reminders():
    reminders = Reminder.objects.filter(
        status=Reminder.STATUS_INCOMPLETE,
        reminder_time__lte=datetime.now())
    return reminders


def send_reminder(reminder: Reminder):
    channels = []
    if 'email' in reminder.sending_methods.lower():
        channels.append('email')
    if 'in_app' in reminder.sending_methods.lower():
        channels.append('in_app')
    if 'ticket' in reminder.sending_methods.lower():
        channels.append('ticket')
    if 'sms' in reminder.sending_methods.lower():
        channels.append('sms')

    reminder.user.send_notification(
        channel_names=channels,
        content_type=ContentType.objects.get_for_model(reminder),
        object_id=reminder.id,
        subject=reminder.title,
        message=reminder.description,
        metadata=reminder.meta
    )


def set_to_reminded(reminder: Reminder):
    reminder.mark_as_complete()


if __name__ == '__main__':
    pending_reminders = get_pending_reminders()
    for reminder in pending_reminders:
        send_reminder(reminder)
        set_to_reminded(reminder)

