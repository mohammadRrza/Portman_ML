from django.db.models.signals import post_save
import os
from django.dispatch import receiver
from .models import TicketComment, Reminder, TicketReplication, TicketType
from datetime import datetime

PORTMAN_ENV = os.environ.get('PORTMAN_ENV', 'dev')

@receiver(post_save, sender=TicketComment)
def on_ticket_comment_model_saved(sender, instance, created, **kwargs):
    user_title =  instance.user.fa_first_name + " " + instance.user.fa_last_name

    if instance.ticket.creator.id != instance.user.id:
        title = f"کامنت جدید توسط " + user_title
        Reminder.objects.create(user=instance.ticket.creator, title=title, description=instance.body,
                                reminder_time=datetime.now(), sending_methods='In_App')
    if instance.in_reply_to:
        title = user_title + f" به کامنت شما پاسخ داد."
        Reminder.objects.create(user=instance.in_reply_to.user, title=title, description=instance.body,
                                reminder_time=datetime.now(), sending_methods='In_App')

@receiver(post_save, sender=TicketReplication)
def on_ticket_replication_model_saved(sender, instance, created, **kwargs):
    if created and instance.ticket.creator != instance.receiver:
        metadata = {}
        title = 'اطلاع‌ رسانی درباره نامه جدید شما'
        sending_methods = 'Email'
        cc = ["a.behravan@pishgaman.net", ] if instance.ticket.type and instance.ticket.type.name in [TicketType.TYPE_FTTH_PLAN_CHANGES,
                                                                                                      TicketType.TYPE_FTTH_PLAN_IMPLEMENTATION,
                                                                                                      TicketType.TYPE_FTTH_USER_INSTALL] else None
        metadata['cc'] = cc if cc else []
        metadata['structure'] = "ticket_notification"

        description = f"""
                        <div dir="rtl" style="font-family:'Calibri', sans-serif;">
                           <h3>با سلام و احترام</h3>
                           <br />
                           <p>نامه جدید به کارتابل شما ارسال شده است. </p>
                           <p>برای مشاهده جزئیات نامه و پیگیری وضعیت آن، لطفا به حساب کاربری خود وارد شوید.</p>

                           <div style="border-right:4px solid #007bff; padding-right:1rem; font-family:'Calibri'">
                             <h4 style="color:#007bff;">جزئیات نامه:</h4>
                             <p><strong>موضوع:</strong> {instance.ticket.subject}</p>
                             <p><a target="_blank" href="https://portman.pishgaman.net/#/cartable/list?id={instance.ticket.id}">جزییات بیشتر</a></p>
                           </div>
                           <br />

                           <div dir="rtl" style="font-family:'Calibri', sans-serif;">
                             <p>سامانه پورتمن</p>
                           </div>
                         </div>
        
        """
        Reminder.objects.create(title=title, description=description, meta=metadata, user=instance.receiver,
                                sending_methods=sending_methods, reminder_time=datetime.now())
