from django.core.mail import EmailMultiAlternatives
from django.template import loader

from .celery import app


@app.task
def async_send_email(
    subject_template_name,
    email_template_name,
    context,
    from_email,
    to_email,
    *args,
    **kwargs
):

    subject = loader.render_to_string(subject_template_name, context)
    subject = " ".join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    return email_message.send()
