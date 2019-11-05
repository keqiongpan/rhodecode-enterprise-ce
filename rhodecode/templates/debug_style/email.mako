<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">

<html>
<head></head>

<body>

SUBJECT:
<pre>${c.subject}</pre>

HEADERS:
<pre>
${c.headers}
</pre>

PLAINTEXT:
<pre>
${c.email_body_plaintext|n}
</pre>

</body>
</html>
<br/><br/>

HTML:

${c.email_body|n}


