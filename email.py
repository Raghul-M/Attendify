import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from azure.storage.blob import BlockBlobService

def send_email_with_attachment(to, subject, body, attachment_path):
    # Set up the email message
    message = MIMEMultipart()
    message['From'] = os.environ['EMAIL_FROM']
    message['To'] = to
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    # Attach the file to the email
    with open(attachment_path, 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='pdf')
        attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
        message.attach(attachment)

    # Send the email
    smtp_server = os.environ['SMTP_SERVER']
    smtp_port = os.environ['SMTP_PORT']
    smtp_username = os.environ['SMTP_USERNAME']
    smtp_password = os.environ['SMTP_PASSWORD']
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.login(smtp_username, smtp_password)
        server.sendmail(os.environ['EMAIL_FROM'], to, message.as_string())

def main(blob: str):
    # Retrieve the file from the Blob Storage Container
    block_blob_service = BlockBlobService(account_name=os.environ['STORAGE_ACCOUNT_NAME'], account_key=os.environ['STORAGE_ACCOUNT_KEY'])
    blob_stream = block_blob_service.get_blob_to_text(os.environ['STORAGE_CONTAINER_NAME'], blob)
    attachment_path = os.path.join(os.environ['TEMP'], blob)

    # Save the file to a temporary directory
    with open(attachment_path, 'w') as f:
        f.write(blob_stream.content)

    # Send the email with the attachment
    send_email_with_attachment(os.environ['TO_EMAIL'], os.environ['EMAIL_SUBJECT'], os.environ['EMAIL_BODY'], attachment_path)
