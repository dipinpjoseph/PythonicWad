# DynuClient
Dynamic DNS Service client in Python for updating IP at regular time intervals.

Dynamic Ip was something which restricts people to test or launch their small web applications. Later some websites started offering their subdomains for free to normal people so they could get a permanent web address for web application/sites. 

All you need to do is, 
Point your dynamic IP to the provided subdomain.
Update the dynamic IP regularly. So IP change won't restrict app's performance and gives near to 100% uptime.

dynu.com is a pioneer in providing this service. In this repo, I'm sharing python code which regularly updates your IP to dynu's dynamic service. In the code, from different service we will retrieve current IP address. Next we will load different parameters needed, in addition the password is programmatically converted to md5 for security reasons. Along with the parameters, new IP is updated to Dynu Dynamic DNS Service.

Please note that the code will update only IPv4 address. Please modify the code and configuration if you have a IPv6 service.

Add this code to a cron job(Linux) or task scheduler(windows)

Python Libraries required,

configparser
requests
re
hashlib
