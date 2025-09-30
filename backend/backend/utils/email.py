from django.core.mail import EmailMessage
from django.template import Template, Context
from django.utils.html import strip_tags

# A small, reusable HTML email builder. Keep it formal and clean.
BASE_HTML_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; color: #111; }
      .container { max-width: 680px; margin: 24px auto; padding: 24px; border: 1px solid #e6e6e6; border-radius: 8px; }
      .header { font-size: 18px; font-weight: 600; margin-bottom: 12px; }
      .meta { color: #666; font-size: 13px; margin-bottom: 18px; }
      .content { font-size: 15px; line-height: 1.5; margin-bottom: 18px; }
      .details { background: #f9f9f9; padding: 12px; border-radius: 6px; font-family: monospace; white-space: pre-wrap; }
      .footer { color: #777; font-size: 13px; margin-top: 18px; }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">{{ subject }}</div>
      <div class="meta">{{ preheader }}</div>
      <div class="content">{{ content }}</div>
      {% if details %}
      <div class="details">{{ details }}</div>
      {% endif %}
      <div class="footer">Sincerely,<br/>The Booking Team</div>
    </div>
  </body>
</html>
"""


def send_html_email(subject, to_email, content, details=None, preheader=None, from_email=None, fail_silently=True):
    """Send an HTML email with a plain-text fallback.

    - subject: email subject
    - to_email: single address or list
    - content: main HTML/content body (can be plain text)
    - details: optional detail section (will be shown in monospace box)
    - preheader: short subtitle under subject
    - from_email: override default
    """
    if isinstance(to_email, str):
        recipient_list = [to_email]
    else:
        recipient_list = to_email

    context = Context({
        'subject': subject,
        'preheader': preheader or '',
        'content': content,
        'details': details or ''
    })

    template = Template(BASE_HTML_TEMPLATE)
    html_body = template.render(context)
    text_body = strip_tags(html_body)

    email = EmailMessage(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=recipient_list,
    )
    email.content_subtype = 'plain'
    # Attach the html alternative
    email.attach_alternative(html_body, "text/html")
    try:
        email.send(fail_silently=fail_silently)
    except Exception:
        if not fail_silently:
            raise
 