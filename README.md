# traffic analyser

### description:

This script provides you with useful information to help troubleshoot traffic related issues such as DDOS attacks, traffic spikes, brute forces, xmlrpc attacks, fake spider/bot attacks etc. 

It's designed to retrieve information as quickly as possible even in light of scenarios where there could be large log files and resource usage limits (server under heavy load).

### requirements:

This script has been tested to run with the following;

1. Python 2.6/2.7
1. Ubuntu, Centos/Red Hat.
1. Apache and Nginx

### usage:

For quick basic usage with default options you can run;

`curl -s https://raw.githubusercontent.com/tahz7/traffic_analyser/master/traffic_analyser.py | python`

For more options please check the [wiki section here](https://github.com/tahz7/traffic_analyser/wiki/0.-Usage)

### features:

The script detects if you're using apache or nginx and also automatically finds the access logs opened by them. 
Below are other features separated into five option groups which you can run in conjunction with each other;
 
**Time Range**
 
* Check last X minutes, hour(s) or Day(s). You can also specify two dates to search in between.
* To help you identify patterns/spikes, the data lists overall hits (between the date range you specify), the hourly hits and 10 minute interval hits. It shows the same per ip/request.
 
**Data**
 
All IP’s that are listed show their Country, city, ISP and their hostname. There is also the option to disable geo information.
 
* Get the top X ip’s with their top X requests 
* Get the top X requests with their top X ip’s.
* Specify X number of IP’s in command line and get their top X requests
* Specify X number of requests in command line and get their top X ip’s making requests.  (for example you can check ip’s that are hitting the request string ‘xmlrpc.php’ to see if there's an attack).

For any of the options above you can filter by 'POST' or 'GET' requests. The script will also tell you how many unique requests/ip hits an IP or a request is making.
 
**Logs**
 
* Check all the logs that are opened to by Apache/nginx.
* Check only the logs in a specific directory (useful if you want to check old archived logs that you can unzip into a directory and check).
* List all the logs that are opened by apache/nginx and then you can choose from that list which logs you want the script to check (useful for checking logs per domain).
* From the command line, list the file name of the log file(s) you want the script to check only.
 
**Search Method**
 
It's important to be able to retrieve the data as quickly as possible, particularly in scenarios where log files are large and the server's under heavy load.

One of the key features of the script is that it has the ability to read a log file from the bottom up. This is particularly useful since in most use cases you want recent data which happens to be at the bottom half of the log file. This means regardless of how big the log file is, if you only want data from the past 30 minutes or the past day then you should get quick results rather than having to go through the whole log file from top to bottom to find the relevant data. As soon as the script detects the ‘end date range’ it closes the log file without reading the rest of the lines since it doesn’t need to. However, there are exceptions to this such as instances where the data you want is closer to the top half of the log file (potentially such as data from a week ago in a very large log file) in which case you have the following options;
 
* Check a log file from the top going down (once it hits the ‘end date range’ then it will close the log file).
* There are extremely rare instances in which apache/nginx writes lines that are not in dated chronological order. This is usually minimal data but if you suspect this and the missing data discrepancy is important to your use case, then you also have the option to tell the script to read the whole log file, top to bottom without breaking off.

**Miscellaneous**

* There may be cases where you don't necassarily need the geo information per ip in which case you can disable this information for faster results. 
