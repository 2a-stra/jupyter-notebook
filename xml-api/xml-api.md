# Mitel SIP-phone XML API configuration server on Python/Flask and registration on Asterisk PBX



Agenda:

0. Configuration server
1. SIP-phones XML configuration
2. Flask XML server
3. Asterisk SIP extensions configuration

## 0. Configuration server

Setting up configuration server for SIP-phones was described on previous post:
[Configuration server](https://2a-stra.blogspot.com/2023/01/how-to-run-small-http-server.html)

We will use the following configuration file `startup.cfg`:
```
# Configuration server
download protocol:HTTP
http server:192.168.5.22  #can be IP or FQDN
http path:aastra68xxi
http port:8888

firmware server: "http://192.168.5.22:8888/firmware"

# SIP server
sip transport protocol:1 #UDP(1),TCP(2),TLS(4)
sip srtp mode:0          #0(SRTP disabled),1(SRTP preferred),2(SRTP only)
sip line1 user name: EmergencyCallsOnly
sip proxy ip: 192.168.5.22
sip proxy port: 5060
sip registrar ip: 192.168.5.22
sip registrar port: 5060

# XML server
xml application uri: "http://192.168.5.22:8888"

# Time settings
time server disabled:0    #server enabled(0), server disabled(1)
time server1: de.pool.ntp.org
time zone name: Custom  #Required setting if time-server is enabled
time zone minutes: -240  # -240 minutes => UTC+4
time format:1 #12hours(0), 24hours(1)
date format:2 #YYYY-MM-DD(2)

#Classic XML Logon
softkey5 label:"Login"
softkey5 type:xml
softkey5 value:"http://$$PROXYURL$$:8888/input"
softkey5 states:idle
softkey5 line:1

# XML Application button
softkey6 type:"xml"
softkey6 label:"App"
softkey6 value:"http://$$PROXYURL$$:8888/app"
```

## 1. SIP phones XML configuration

Create `templates` folder to put XML files: 

```bash
$ ls
aastra68xxi/  app.py  firmware/  templates/

$ ls templates/
input.xml  sip.xml  uptime.xml
```

Text screen template `uptime.xml` for testing:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AastraIPPhoneTextScreen>
    <Title>Good day!</Title>
    <Text>Uptime: {{ uptime }}</Text>
</AastraIPPhoneTextScreen>
```

Input Fields `input.xml` to send extension number and password to the XML server as a GET parameters:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AastraIPPhoneInputScreen type="string" destroyOnExit="yes">
    <Title>Enter auth data</Title>
    <URL>http://192.168.5.22:8888/login</URL>
    <InputField type="number">
        <Prompt>Extension number:</Prompt>
        <Parameter>extension</Parameter>
    </InputField>
    <InputField type="number" password="yes">
        <Prompt>Password:</Prompt>
        <Parameter>password</Parameter>
    </InputField>
</AastraIPPhoneInputScreen>
```

Template `sip.xml` to push SIP configuration to the phone over XML API:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AastraIPPhoneConfiguration setType="local">
    <ConfigurationItem>
        <Parameter>sip line1 user name</Parameter>
        <Value>{{ user }}</Value>
    </ConfigurationItem>
    <ConfigurationItem>
        <Parameter>sip line1 auth name</Parameter>
        <Value>{{ user }}</Value>
    </ConfigurationItem>
    <ConfigurationItem>
        <Parameter>sip line1 password</Parameter>
        <Value>{{ passw }}</Value>
    </ConfigurationItem>
</AastraIPPhoneConfiguration>
```

## 2. Flask XML server

Python/Flash application `app.py`:

```python
import os
from flask import Flask
from flask import request, render_template
from flask import send_from_directory

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, Flask!";


@app.route('/aastra68xxi/<path:filename>', methods=['GET'])
def download(filename):
    return send_from_directory("aastra68xxi", filename, as_attachment=False)


@app.route('/firmware/<path:filename>', methods=['GET'])
def download_fw(filename):
    return send_from_directory("firmware", filename, as_attachment=False)


@app.route('/login', methods=['GET'])
def xml():
    extension = request.args.get("extension")
    password = request.args.get("password")
    return render_template("sip.xml", user=extension, passw=password)


@app.route('/input', methods=['GET'])
def login():
    return render_template("input.xml")


@app.route('/app', methods=['GET'])
def appl():
    up = os.popen("uptime").read().strip()
    return render_template("uptime.xml", uptime=up)


if __name__ == "__main__":
    app.run(debug = False, host = "192.168.5.22", port = 8888)
```

Test XML server using http request by `curl` command:

```bash
$ curl -i http://192.168.5.22:8888/app
HTTP/1.1 200 OK
Server: Werkzeug/2.2.2 Python/3.7.3
Content-Type: text/html; charset=utf-8
Content-Length: 214
Connection: close

<?xml version="1.0" encoding="UTF-8"?>
<AastraIPPhoneTextScreen>
    <Title>Good day!</Title>
    <Text>Uptime: 09:53:45 up 14 days, 22:19,  1 user,  load average: 0.00, 0.02, 0.06</Text>
</AastraIPPhoneTextScreen>
```

Running Flask application:

```bash
$ python3 app.py
 * Serving Flask app 'app'

 * Running on http://192.168.5.22:8888
Press CTRL+C to quit
192.168.5.11 - - [30/Jan/2023 10:37:21] "GET /aastra68xxi/security.tuz HTTP/1.1" 404 -
192.168.5.11 - - [30/Jan/2023 10:37:21] "GET /aastra68xxi/startup.cfg HTTP/1.1" 200 -
192.168.5.11 - - [30/Jan/2023 10:37:21] "GET /aastra68xxi/6869i.cfg HTTP/1.1" 404 -
192.168.5.11 - - [30/Jan/2023 10:37:21] "GET /aastra68xxi/00085Dxxxxxx.cfg HTTP/1.1" 404 -
192.168.5.11 - - [30/Jan/2023 10:37:22] "GET /aastra68xxi/startup.lic HTTP/1.1" 404 -
192.168.5.11 - - [30/Jan/2023 10:37:22] "GET /aastra68xxi/00085Dxxxxxx.lic HTTP/1.1" 404 -
192.168.5.11 - - [30/Jan/2023 10:37:23] "GET /firmware/6869i.st HTTP/1.1" 200 -
192.168.5.11 - - [30/Jan/2023 10:37:37] "GET /input HTTP/1.1" 200 -
192.168.5.11 - - [30/Jan/2023 10:37:52] "GET /login?extension=100&password=1234 HTTP/1.1" 200 -
```

Restart the SIP phone after setting up Configuration server Address, Path and Port in the SIP phone menu. During restart the phone requests configuration files and firmware from the server. After restart we could press "Login" softkey button and get input screen retrieved from XML server for for authentication:

![](input.jpeg)

We could check successful SIP registration from SIP-phone 'Status' -> 'System information' menu:
```
SIP Status
Line	SIP Account	Status	Backup Registrar Used?
1	100@192.168.5.22:5060	Registered	No
2	100@192.168.5.22:5060	Registered	No
```

Test XML application by pressing "App" softkey button:

![](uptime.jpeg)


## 3. Asterisk SIP extensions configuration

Context 'test' in `/etc/asterisk/extensions.conf` file:

```
[test]
exten => _10X,1,Dial(SIP/${EXTEN},20,rt)        ; permit transfer
same => n,Hangup()

exten => 110,1,Answer()
exten => 110,2,Background(demo-instruct)
same => n,Hangup()
```

Create 2 extensions `100` and `101` with context `test` in `/etc/asterisk/sip.conf` file:

```
[100]
type=friend
secret=1234
context=test
host=dynamic
directmedia=yes
disallow=all
allow=alaw

[101]
type=friend
secret=1234
context=test
host=dynamic
directmedia=yes
disallow=all
allow=alaw
```

Restart asterisk `dialplan` and `sip`:
```bash
$ sudo asterisk -rvvv
Connected to Asterisk 16.28.0~dfsg-0+deb10u1 currently running on pi (pid = 22712)
pi*CLI> dialplan reload
Dialplan reloaded.

pi*CLI> sip reload
 Reloading SIP
```

Check the phones registration:

```bash
pi*CLI>  sip show peers
Name/username             Host                                    Dyn Forcerport Comedia    ACL Port     Status      Description
100/100                   192.168.5.11                             D  Auto (No)  No             5060     Unmonitored
101/101                   192.168.5.5                              D  Auto (No)  No             5060     Unmonitored
2 sip peers [Monitored: 0 online, 0 offline Unmonitored: 2 online, 0 offline]
```

Check sip channels:

```bash
pi*CLI> sip show channelstats
Peer             Call ID      Duration Recv: Pack  Lost       (     %) Jitter Send: Pack  Lost       (     %) Jitter
192.168.5.5      58df4de0382  00:01:32 0000004338  0000000000 ( 0.00%) 0.0000 0000004343  0000000000 ( 0.00%) 0.0001
192.168.5.11     385eb2fa2ee  00:01:32 0000004343  0000000000 ( 0.00%) 0.0000 0000004338  0000000000 ( 0.00%) 0.0001
2 active SIP channels

pi*CLI> core show channels
Channel              Location             State   Application(Data)
SIP/100-0000000c     (None)               Up      AppDial((Outgoing Line))
SIP/101-0000000b     100@test:1           Up      Dial(SIP/100,20,rt)
2 active channels
1 active call
10 calls processed
```
