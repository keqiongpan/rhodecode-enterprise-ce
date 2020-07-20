.. _set-up-mail:

Set up Email
------------

To setup email with your |RCE| instance, open the default
:file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini`
file and uncomment and configure the email section. If it is not there,
use the below example to insert it.

Once configured you can check the settings for your |RCE| instance on the
:menuselection:`Admin --> Settings --> Email` page.

Please be aware that both section should be changed the `[DEFAULT]` for main applications
email config, and `[server:main]` for exception tracking email

.. code-block:: ini

    [DEFAULT]
    ; ########################################################################
    ; EMAIL CONFIGURATION
    ; These settings will be used by the RhodeCode mailing system
    ; ########################################################################

    ; prefix all emails subjects with given prefix, helps filtering out emails
    #email_prefix = [RhodeCode]

    ; email FROM address all mails will be sent
    #app_email_from = rhodecode-noreply@localhost

    #smtp_server = mail.server.com
    #smtp_username =
    #smtp_password =
    #smtp_port =
    #smtp_use_tls = false
    #smtp_use_ssl = true

    [server:main]
    ; Send email with exception details when it happens
    #exception_tracker.send_email = true

    ; Comma separated list of recipients for exception emails,
    ; e.g admin@rhodecode.com,devops@rhodecode.com
    ; Can be left empty, then emails will be sent to ALL super-admins
    #exception_tracker.send_email_recipients =
