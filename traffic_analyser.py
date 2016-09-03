#!/usr/bin/python

import datetime
import json
import urllib2
import socket
import sys
import re
import time
import os
from optparse import OptionParser
from collections import defaultdict
from operator import itemgetter


# Python 2.6 doesn't include Counter module, below is a converted version
# for it.
class Counter(dict):
    '''Dict subclass for counting hashable objects.  Sometimes called a bag
    or multiset.  Elements are stored as dictionary keys and their counts
    are stored as dictionary values.

    >>> Counter('zyzygy')
    Counter({'y': 3, 'z': 2, 'g': 1})

    '''

    def __init__(self, iterable=None, **kwds):
        '''Create a new, empty Counter object.  And if given, count elements
        from an input iterable.  Or, initialize the count from another mapping
        of elements to their counts.

        >>> c = Counter()                           # a new, empty counter
        >>> c = Counter('gallahad')                 # a new counter from an iterable
        >>> c = Counter({'a': 4, 'b': 2})           # a new counter from a mapping
        >>> c = Counter(a=4, b=2)                   # a new counter from keyword args

        '''
        self.update(iterable, **kwds)

    def __missing__(self, key):
        return 0

    def most_common(self, n=None):
        '''List the n most common elements and their counts from the most
        common to the least.  If n is None, then list all element counts.

        >>> Counter('abracadabra').most_common(3)
        [('a', 5), ('r', 2), ('b', 2)]

        '''
        if n is None:
            return sorted(self.iteritems(), key=itemgetter(1), reverse=True)
        return nlargest(n, self.iteritems(), key=itemgetter(1))

    def elements(self):
        '''Iterator over elements repeating each as many times as its count.

        >>> c = Counter('ABCABC')
        >>> sorted(c.elements())
        ['A', 'A', 'B', 'B', 'C', 'C']

        If an element's count has been set to zero or is a negative number,
        elements() will ignore it.

        '''
        for elem, count in self.iteritems():
            for _ in repeat(None, count):
                yield elem

    # Override dict methods where the meaning changes for Counter objects.

    @classmethod
    def fromkeys(cls, iterable, v=None):
        raise NotImplementedError(
            'Counter.fromkeys() is undefined.  Use Counter(iterable) instead.')

    def update(self, iterable=None, **kwds):
        '''Like dict.update() but add counts instead of replacing them.

        Source can be an iterable, a dictionary, or another Counter instance.

        >>> c = Counter('which')
        >>> c.update('witch')           # add elements from another iterable
        >>> d = Counter('watch')
        >>> c.update(d)                 # add elements from another counter
        >>> c['h']                      # four 'h' in which, witch, and watch
        4

        '''
        if iterable is not None:
            if hasattr(iterable, 'iteritems'):
                if self:
                    self_get = self.get
                    for elem, count in iterable.iteritems():
                        self[elem] = self_get(elem, 0) + count
                else:
                    # fast path when counter is empty
                    dict.update(self, iterable)
            else:
                self_get = self.get
                for elem in iterable:
                    self[elem] = self_get(elem, 0) + 1
        if kwds:
            self.update(kwds)

    def copy(self):
        'Like dict.copy() but returns a Counter instance instead of a dict.'
        return Counter(self)

    def __delitem__(self, elem):
        'Like dict.__delitem__() but does not raise KeyError for missing values.'
        if elem in self:
            dict.__delitem__(self, elem)

    def __repr__(self):
        if not self:
            return '%s()' % self.__class__.__name__
        items = ', '.join(map('%r: %r'.__mod__, self.most_common()))
        return '%s({%s})' % (self.__class__.__name__, items)

    # Multiset-style mathematical operations discussed in:
    #       Knuth TAOCP Volume II section 4.6.3 exercise 19
    #       and at http://en.wikipedia.org/wiki/Multiset
    #
    # Outputs guaranteed to only include positive counts.
    #
    # To strip negative and zero counts, add-in an empty counter:
    #       c += Counter()

    def __add__(self, other):
        '''Add counts from two counters.

        >>> Counter('abbb') + Counter('bcc')
        Counter({'b': 4, 'c': 2, 'a': 1})


        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem in set(self) | set(other):
            newcount = self[elem] + other[elem]
            if newcount > 0:
                result[elem] = newcount
        return result

    def __sub__(self, other):
        ''' Subtract count, but keep only results with positive counts.

        >>> Counter('abbbc') - Counter('bccd')
        Counter({'b': 2, 'a': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem in set(self) | set(other):
            newcount = self[elem] - other[elem]
            if newcount > 0:
                result[elem] = newcount
        return result

    def __or__(self, other):
        '''Union is the maximum of value in either of the input counters.

        >>> Counter('abbb') | Counter('bcc')
        Counter({'b': 3, 'c': 2, 'a': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        _max = max
        result = Counter()
        for elem in set(self) | set(other):
            newcount = _max(self[elem], other[elem])
            if newcount > 0:
                result[elem] = newcount
        return result

    def __and__(self, other):
        ''' Intersection is the minimum of corresponding counts.

        >>> Counter('abbb') & Counter('bcc')
        Counter({'b': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        _min = min
        result = Counter()
        if len(self) < len(other):
            self, other = other, self
        for elem in ifilter(self.__contains__, other):
            newcount = _min(self[elem], other[elem])
            if newcount > 0:
                result[elem] = newcount
        return result


# This class includes colors/patterns for text output.
class txt_colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    PURPLE = '\033[35m'
    ORANGE = '\033[33m'
    LIGHTRED = '\033[91m'
    LIGHTGREY = '\033[37m'
    CYAN = '\033[36m'
    HEADER = '\033[95m'
    BOLD = '\033[01m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'


# Function to validate command line arguments
def args_validation(options, args, parser):
    if options.log:
        # remove duplicate values in options.log and args (this occurs when
        # options.log and (options.rmatch or options.ipmatch) is input
        for item in options.log:
            if item in args:
                args.remove(item)
        for log_file in options.log:
            if not os.path.exists(log_file):
                parser.error(
                    'Could not file this log file; {0}. Make sure you\'ve got the correct file name'.format(log_file))
    if options.dir:
        if not os.path.exists(options.dir):
            parser.error(
                'Could not file the directory; {0}. Make sure you\'ve got the correct directory name'.format(options.dir))
    if options.date:
        try:
            datetime.datetime.strptime(options.date[0], "%d/%b/%Y:%H:%M:%S")
            datetime.datetime.strptime(options.date[1], "%d/%b/%Y:%H:%M:%S")
        except ValueError:
            parser.error(
                'Either from_time or to_time is incorrectly formatted. '
                'The correct formatting should be: date/month/year:hour:minute:second | 10/Aug/2016:15:00:00')
    if options.ipmatch:
        try:
            options.ipmatch[0] = int(options.ipmatch[0])
        except ValueError:
            parser.error(
                'The first argument for option -ipmatch is request_number which needs to be an integer')
        if len(args) < 1:
            parser.error(
                'The second argument (and so forth) for option -ipmatch needs to be a ip')
    if options.rmatch:
        try:
            options.rmatch[0] = int(options.rmatch[0])
        except ValueError:
            parser.error(
                'The first argument for option --rmatch is ip_number which needs to be an integer')
        if len(args) < 1:
            parser.error(
                'The second argument (and so forth) for option --rmatch needs to be a request string')
    if options.filter:
        options.filter = options.filter.upper()
        if options.filter not in ['POST', 'GET']:
            parser.error(
                'The --filter option takes only one of these two arguments; POST or GET')

    # Ensure only one option per option group is selected
    time_list = []
    data_list = []
    log_list = []
    search_list = []

    for option, arg in vars(options).iteritems():
        if arg not in [None, False]:
            if option in ['day', 'hour', 'min', 'date']:
                time_list.append(option)
            if option in ['ip', 'request', 'ipmatch', 'rmatch']:
                data_list.append(option)
            if option in ['select', 'log', 'dir']:
                log_list.append(option)
            if option in ['complete', 'top']:
                search_list.append(option)
    for item in [time_list, data_list, log_list, search_list]:
        if len(item) > 1:
            parser.error(
                'You can only use one of the following options: ' + ' '.join(['--{0}'.format(option) for option in item]))
    # Ensure both time and data options are input as a minimum for the script
    # to work.
    if not time_list or not data_list:
        parser.error(
            'You must choose at least one time group option (--min, --hour, --day, --date) '
            'and one data group option (--ip, --request, --ipmatch, --rmatch)')

    return options, args


# Normally you can append variable arguments into the args list
# but this can lead to data clashes if --rmatch or --ipmatch is also used.
# For avoidance this function is currently used to append arguments for
# the --log option.
def multi_args(option, opt_str, value, parser):
    args = []
    for arg in parser.rargs:
        if arg[0] != "-":
            args.append(arg)
        else:
            del parser.rargs[:len(args)]
            break
    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, args)


# optparse is used over argparse due to python 2.6 not including it as a
# standard module
def optionparse_args():
    parser = OptionParser(conflict_handler="resolve")
    # time options group
    parser.add_option('-m', '--min', help='Get data from last X minutes', metavar=('minute'),
                      type='int', nargs=1)
    parser.add_option('-k', '--hour', help='Get data from last X hour(s)', metavar=('hour'),
                      type='int', nargs=1)
    parser.add_option('-d', '--day', help='Get data from last X day(s)', metavar=('day'),
                      type='int', nargs=1)
    parser.add_option('-d', '--date',
                      help='Get data from between two dates. '
                           'Example; date/month/year:hour:minute:second | 10/Aug/2016:15:00:00',
                      metavar=('from_time', 'to_time'), nargs=2)
    # data options group
    parser.add_option('-i', '--ip',
                      help='Get the top X ip\'s along with their top X requests',
                      metavar=('ip_number', 'request_number'), type='int', nargs=2)
    parser.add_option('-r', '--request',
                      help='Get the top X requests\'s along with their top X ip\'s',
                      metavar=('request_number', 'ip_number'), type='int', nargs=2)
    parser.add_option('-i', '--ipmatch',
                      help='Get top X requests for user input list of ip\'(s)s. '
                           'Example: -ipmatch 20 10.10.23.42 134.134.3.13',
                      metavar=('request_number', 'list_of_ip\'s'), action='append')
    parser.add_option('-r', '--rmatch',
                      help='Get top X ip\'s for user input list of request(s). '
                           'Example: -rmatch 10 xmlrpc.php wp-login.php',
                      metavar=('ip_number', 'list_of_requests'), action='append')
    # log options group
    parser.add_option('-s', '--select',
                      help='Choose which logs to check from a list of logs '
                           'currently opened by nginx/apache.',
                      action='store_true')
    parser.add_option("-l", "--log", help='Choose which log files to read from '
                                          '(you can input multiple log files). '
                                          'Example; --log google_access_log yahoo_access_log.1',
                      metavar='log_file',  action="callback", callback=multi_args, dest="log")
    parser.add_option('-d', '--dir',
                      help='Check the logs that are in the current directory '
                           '(the directory must only have text based log files.',
                      nargs=1)
    # search options group (method of searching through a log file)
    parser.add_option('-t', '--top',
                      help='Read log files from the top down (by default logs '
                           'are read from the bottom line up)',
                      action='store_true')
    parser.add_option('-c', '--complete', help='Read every line in log files from the '
                                               'top to bottom line',
                      action='store_true')
    # miscellaneous options group
    parser.add_option(
        '-g', '--nogeo', help='Disable geo information per ip', action='store_true')
    parser.add_option(
        '-f', '--filter', help='filter requests by POST or GET', type='str', nargs=1)

    # args is used for variable user inputs for rmatch and ipmatch only.
    # Options for other user input
    (options, args) = parser.parse_args()
    options, args = args_validation(options, args, parser)

    return options, args


# This function assigns option args to ip number and request number.
def ip_req_number_args(options):
    if options.ip:
        ip_no = options.ip[0]
        request_no = options.ip[1]
    elif options.request:
        ip_no = options.request[1]
        request_no = options.request[0]
    elif options.rmatch:
        request_no = None
        ip_no = int(options.rmatch[0])
    else:  # options.ipmatch:
        ip_no = None
        request_no = options.ipmatch[0]

    # If requesting geo information, limit api to 30 ip's to avoid potential
    # abuse.
    if not options.nogeo:
        if ip_no > 30:
            print txt_colors.LIGHTRED + ('\nWarning: You chose {0} ip\'s when the limit is 30 '
                                         '(this has been adjusted automatically). '
                                         'If you want to display more than 30 ip\'s then use the -nogeo option.'.format(
                                             ip_no)) + txt_colors.ENDC
            ip_no = 30

    return ip_no, request_no


# This function checks if you're running apache/nginx.
def os_httpd_version(options):
    # this will have either apache or nginx
    httpd_list = set()
    # this will have the PID's that are used by either apache or nginx.
    httpd_pid = []
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

    for pid in pids:
        try:
            if os.path.exists('/proc/{0}/exe'.format(pid)):
                processes = os.readlink('/proc/{0}/exe'.format(pid))
                regex_process = re.search("(httpd|nginx|apache2)+", processes)
                if regex_process is not None:
                    httpd_list.add(regex_process.group(1))
                    httpd_pid.append(pid)
        except IOError:
            continue

    # This if/else statement will ensure the script takes only either apache or nginx.
    # Currently it won't work with both services running.
    if len(httpd_list) > 1:
        print ('This server is running both nginx and apache. '
               'This scenario hasn\'t yet been configured to work with '
               'this script. Please email this error (including the command you ran) + server to '
               'tahzeem.taj@rackspace.co.uk.')
        sys.exit()
    elif not httpd_list and not options.dir:
        print ('\nERROR: Could not detect Nginx or Apache running.'
               'Alternatively if you have a directory with access logs, you can use the \'--dir\' option')
        sys.exit()
    # '--dir' option only checks logs in user input directory (and not those opened by apache/nginx).
    if options.dir:
        httpd_server = 'Ignored (--dir option used)'
    else:
        httpd_server = list(httpd_list)[0]

    return httpd_server, httpd_pid


# This func gets all the log files it needs to process based on options
def get_log_files(options):
    logs = set()
    httpd_server, httpd_pid = os_httpd_version(options)
    print '\nWeb Server Detected: {0}'.format(txt_colors.GREEN + httpd_server + txt_colors.ENDC)

    # add logs input by user
    if options.log:
        for files in options.log:
            logs.add(os.path.abspath(files))
    # check if the user wants logs checked from a specific directory only
    elif options.dir:
        for files in os.listdir(options.dir):
            if not files == sys.argv[0]:
                logs.add(os.path.abspath(files))
    # Otherwise, get the log files that are currently open by either
    # Apache/Ngninx.
    else:
        try:
            for pid in httpd_pid:
                for filename in os.listdir('/proc/{0}/fd'.format(pid)):
                    filename = os.readlink(
                        "/proc/{0}/fd/{1}".format(pid, filename))
                    if 'access_log' in filename or 'access.log' in filename:
                        logs.add(filename)
        except:
            print ('ERROR: There was a problem finding the log files. Please email this error '
                   '(including the command you ran) + server to tahzeem.taj@rackspace.co.uk.')
            raise

        # fix the issue where a log file has been moved/archived/deleted
        logs_copy = logs.copy()

        for log in logs:
            if '(deleted)' in log:
                logs_copy.remove(log)

        logs = logs_copy

        # List logs opened by apache/nginx and let the user choose
        if options.select:
            print '\n',
            for n, log in enumerate(logs, 1):
                print '{0}. {1} [{2}]'.format(n, txt_colors.YELLOW + log + txt_colors.ENDC,
                                              filesize(os.path.getsize(log)))
            print '\n',
            while True:
                try:
                    sys.stdin = open('/dev/tty')
                    string_input = raw_input(
                        'Which logs do you want to check? (eg. 1 3 4): ')
                    print '\n',
                    input_list = string_input.split()
                    input_list = [int(a) for a in input_list]
                    # Check user input is correct
                    if max(input_list) > len(logs) or min(input_list) < 1:
                        print 'Error: The logs range from 1 to %d, so where did you get %d from...?' % (
                            len(logs), max(input_list))
                    else:
                        break
                except ValueError:
                    print 'You need to make sure your input are all digits with spacing between them (ie. 4 3 2 1)'

            selected_logs = []

            for n, log in enumerate(logs, 1):
                if n in input_list:
                    selected_logs.append(log)

            return selected_logs

    return logs


# func to calculate the start time variable for min, hour and day.
def calculate_start_time(metric, args_time):
    start_time = (datetime.datetime.now() - datetime.timedelta(**
                                                               {metric: args_time})).strftime("%d/%b/%Y:%H:%M:%S")

    return start_time


# Get the start/end dates based on user input
def start_end_dates(options):
    end_time = datetime.datetime.now().strftime("%d/%b/%Y:%H:%M:%S")

    if options.date:
        start_time = options.date[0]
        end_time = options.date[1]
    elif options.min:
        args_time = options.min
        start_time = calculate_start_time('minutes', args_time)
    elif options.hour:
        args_time = options.hour
        start_time = calculate_start_time('hours', args_time)
    else:  # --day option:
        args_time = options.day
        start_time = calculate_start_time('days', args_time)

    start_time = datetime.datetime.strptime(start_time, "%d/%b/%Y:%H:%M:%S")
    end_time = datetime.datetime.strptime(end_time, "%d/%b/%Y:%H:%M:%S")

    return start_time, end_time


# These are default dicts to store data for each IP, request and time.
def ip_record():
    return {
        'count': 0,
        'get_post': Counter(),
        'date': defaultdict(date_record)
    }


def request_record():
    return {
        'count': 0,
        'ip': Counter(),
        'date': defaultdict(date_record)
    }


def date_record():
    return {
        'count': 0,
        'hour': defaultdict(ten_minutes_record),
    }


def ten_minutes_record():
    return {
        'count': 0,
        'ten_min': Counter()
    }


# This default dict gets combined hits of all data
def overall_date_count():
    return {
        'count': 0,
        'hour': defaultdict(ten_minutes_record),
    }


# Convert bytes to readable format.
def filesize(bytes, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T']:
        if abs(bytes) < 1024.0:
            return "{0:.2f} {1}{2}".format(round(bytes, 2), unit, suffix)
        bytes /= 1024.0


# Read a file in reverse. Useful for logs where user input is based on last X minutes.
# SO reference http://stackoverflow.com/a/23646049/1165419
def reverse_readline(filename, buf_size=8192):
    """a generator that returns the lines of a file in reverse order"""
    with open(filename) as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split('\n')
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # if the previous chunk starts right from the beginning of line
                # do not concact the segment to the last line of new chunk
                # instead, yield the segment first
                if buffer[-1] is not '\n':
                    lines[-1] += segment
                else:
                    yield segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if len(lines[index]):
                    yield lines[index]
        # Don't yield None if the file was empty
        if segment is not None:
            yield segment


# This func adds ip/requests/time data to count dictionaries
def dict_add(ip_req_count, date_count, regex_req_ip, found_time, hour, minute):
    found_time_hour = str(hour)
    found_time_minute = str(minute)
    found_time_date = found_time.date()
    # add data to ip or request dictionary
    # regex_req_ip can be ip or request
    ip_req_count[regex_req_ip]['count'] += 1
    ip_req_count[regex_req_ip]['date'][found_time_date]['count'] += 1
    ip_req_count[regex_req_ip]['date'][found_time_date][
        'hour'][found_time_hour]['count'] += 1
    ip_req_count[regex_req_ip]['date'][found_time_date]['hour'][found_time_hour]['ten_min'][
        found_time_minute[0]] += 1
    # add data to overall date dictionary
    date_count[found_time_date]['count'] += 1
    date_count[found_time_date]['hour'][found_time_hour]['count'] += 1
    date_count[found_time_date]['hour'][found_time_hour][
        'ten_min'][found_time_minute[0]] += 1

    return ip_req_count, date_count


# This functions takes a line of a log file and retrieves only the
# information required
def evaluate_line(line, ip_req_count, date_count, start_time, end_time, regex_date, regex_requests, datetime_func, month_dict, options, args):
    regex_date = regex_date(line).group()

    # check if get or post filter in requests
    if options.filter:
        regex_requests = regex_requests(line)
        if regex_requests:
            regex_requests = regex_requests.group()
        else:
            found_time = None
            return found_time, ip_req_count, date_count
    else:
        regex_requests = regex_requests(line).group()

    ip = line.replace(',', '').split()[0]  # for cloudflare logging format.

    if options.request or options.rmatch:
        regex_req_ip = regex_requests
    else:
        regex_req_ip = ip

    # convert line time into datetime object
    yr = int(regex_date[7:11])
    mon = month_dict[(regex_date[3:6])]
    day = int(regex_date[0:2])
    hr = regex_date[12:14]
    mins = regex_date[15:17]
    sec = int(regex_date[18:20])
    found_time = datetime_func(yr, mon, day, int(hr), int(mins), sec)

    # compare time from log line to user input time range and retrieve data in
    # between
    if start_time <= found_time <= end_time:
        # list of ip's to check
        if options.ipmatch:
            ipmatch = args
            if regex_req_ip in ipmatch:
                ip_req_count, date_count = dict_add(
                    ip_req_count, date_count, regex_req_ip, found_time, hr, mins)
                ip_req_count[regex_req_ip]['get_post'][regex_requests] += 1
        # list of requests to check
        elif options.rmatch:
            rmatch = args
            if any(string in regex_requests for string in rmatch):
                ip_req_count, date_count = dict_add(
                    ip_req_count, date_count, regex_req_ip, found_time, hr, mins)
                ip_req_count[regex_req_ip]['ip'][ip] += 1
        # top ip's or top requests to check
        else:
            ip_req_count, date_count = dict_add(
                ip_req_count, date_count, regex_req_ip, found_time, hr, mins)
            if options.request:
                # Add ip data from line to dict
                ip_req_count[regex_req_ip]['ip'][ip] += 1
            else:
                # add request data from line to dict
                ip_req_count[regex_req_ip]['get_post'][regex_requests] += 1

    return found_time, ip_req_count, date_count


# This func gets data required from log files
def get_data_from_logs(options, args):
    start_time, end_time = start_end_dates(options)

    # Use the relevant count dictionary for requests or ip
    if options.request or options.rmatch:
        ip_req_count = defaultdict(request_record)
    else:  # --ip or --ipmatch options
        ip_req_count = defaultdict(ip_record)

    date_count = defaultdict(overall_date_count)
    logs = get_log_files(options)

    # compile regex for speed
    regex_date_compile = r"(\d{2}/\w+/\d{4}:\d{2}:\d{2}:\d{2})"
    regex_date = re.compile(regex_date_compile).search

    if options.filter:
        regex_requests_compile = r'"%s[^"]*" \d{3}' % options.filter
    else:
        regex_requests_compile = r'"[^"]*" \d{3}'

    regex_requests = re.compile(regex_requests_compile).search
    datetime_func = datetime.datetime
    # month dict for converting time into datetime object
    month_dict = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

    while True:
        print 'Total Log File(s) to Check:', txt_colors.GREEN + str(len(logs)) + txt_colors.ENDC
        print 'Report Time Range: {0} - {1}'.format(txt_colors.LIGHTRED + str(start_time.strftime('%d/%b/%Y %H:%M:%S')),
                                                    str(end_time.strftime('%d/%b/%Y %H:%M:%S')) + txt_colors.ENDC), '\n'

        # Go through each log file and grab required data
        for logfile in logs:
            print 'Checking log file {0} [{1}]...'.format(txt_colors.YELLOW + logfile + txt_colors.ENDC,
                                                          filesize(os.path.getsize(logfile)))
            if options.top:
                # read log file from top to bottom.
                with open(logfile) as infile:
                    for line in infile:
                        found_time, ip_req_count, date_count = evaluate_line(line, ip_req_count, date_count, start_time,
                                                                             end_time, regex_date, regex_requests, datetime_func, month_dict, options, args)
                        # Once we find the end date time we no longer need to
                        # carry on checking lines.
                        if found_time:
                            if found_time >= end_time:
                                break
            # read log file from top line to the bottom line with no cut off
            elif options.complete:
                with open(logfile) as infile:
                    for line in infile:
                        found_time, ip_req_count, date_count = evaluate_line(line, ip_req_count, date_count, start_time,
                                                                             end_time, regex_date, regex_requests, datetime_func, month_dict, options, args)
            # read the log file from bottom up
            else:
                for line in reverse_readline(logfile):
                    found_time, ip_req_count, date_count = evaluate_line(line, ip_req_count, date_count, start_time,
                                                                         end_time, regex_date, regex_requests, datetime_func, month_dict, options, args)
                    if found_time:
                        if found_time <= start_time:
                            break
            # Iterate through the log file(s) selected by user and print data
            # for each
            if options.select:
                print_data(ip_req_count, date_count,
                           start_time, end_time, options)
                # reset ip/requests and overall date count for each log file
                # iteration
                if options.request:
                    ip_req_count = defaultdict(request_record)
                else:
                    ip_req_count = defaultdict(ip_record)

                date_count = defaultdict(overall_date_count)
                print '\n'
                raw_input("Press Enter to continue...")
                print '\n',
        else:
            # break out of the while loop
            break

    return ip_req_count, date_count, start_time, end_time, options


# Get IP information from API
def ip_api(ip):
    url = 'http://ip-api.com/json/{0}'.format(ip)
    result = urllib2.urlopen(url, timeout=15)
    ip_data = json.loads(result.read())

    # u'message' occurs if ip information cannot be found (ie. private ip)
    if u'message' in ip_data:
        ip_country = ip_data[u'message']
        ip_isp = ip_data[u'message']
        ip_city = ip_data[u'message']
    else:
        try:
            ip_country = ip_data['country']
        except ValueError:
            ip_country = 'Unknown'
        try:
            ip_isp = ip_data['isp']
        except ValueError:
            ip_isp = 'Unknown'
        try:
            ip_city = ip_data['city']
        except ValueError:
            ip_city = 'Unknown'
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except socket.error:
        hostname = 'Unknown'
    # respect api endpoint limit - ip-api.com/docs
    time.sleep(0.5)

    return ip_country.encode('utf-8'), ip_city.encode('utf-8'), ip_isp.encode('utf-8'), hostname


def print_10min(logs):
    for ten_min_key, ten_min_count_value in logs.most_common():
        print '{0} [{1}] |'.format(txt_colors.CYAN + ten_min_key + '0' + txt_colors.ENDC,
                                   ten_min_count_value),


# this func prints all data related to date/time.
def print_date(date_logs, start_time, end_time):
    # sorts dates by total count, highest to lowest
    date_logs = sorted(date_logs.items(), key=itemgetter(1), reverse=True)
    # avoid repetition of strtftime
    start_time_minute = start_time.strftime('%M')
    start_time_hour = start_time.strftime('%H')
    end_time_minute = end_time.strftime('%M')
    end_time_hour = end_time.strftime('%H')

    for date_key, date_values in date_logs:  # date_values contain count, hour
        # sort hours by total count
        hour_sort = sorted(
            date_values['hour'].items(), key=itemgetter(1), reverse=True)
        # The if/else statements below are to ensure accurate data is printed to console.
        # if users date range is multiple days
        if not start_time.date() == end_time.date():
            # print date information
            # first date
            if date_key == start_time.date():
                print '\n\n', '{0} ({1}-23:59) [{2}]'.format(
                    txt_colors.CYAN +
                    start_time.strftime('%d/%b/%Y') + txt_colors.ENDC,
                    start_time.strftime('%H:%M'),
                    date_values['count']), '\n\n',
                print 'Hourly: \n\n',
                # print hour information per date
                for hour_key, hour_count_value in hour_sort:  # hour_count_value contain ten_min and count
                    # in case start time hour is incomplete
                    # we want exact minutes within that hour to show
                    if hour_key == start_time_hour:
                        print '{0} ({1}-59) [{2}]'.format(txt_colors.GREEN + hour_key + txt_colors.ENDC,
                                                          start_time_minute,
                                                          hour_count_value['count']),
                        # print 10 min interval information per hour
                        print '{',
                        print_10min(hour_count_value['ten_min']),
                        print '}\n',
                    else:
                        print '{0} [{1}]'.format(txt_colors.GREEN + hour_key + txt_colors.ENDC,
                                                 hour_count_value['count']),
                        print '{',
                        print_10min(hour_count_value['ten_min']),
                        print '}\n',

            # last date
            elif date_key == end_time.date():
                print '\n\n', '{0} (00:00-{1}) [{2}]'.format(
                    txt_colors.CYAN +
                    end_time.strftime('%d/%b/%Y') +
                    txt_colors.ENDC, end_time.strftime('%H:%M'),
                    date_values['count']), '\n\n',
                print 'Hourly: \n\n',
                for hour_key, hour_count_value in hour_sort:
                    # Last hour of the last date
                    if hour_key == end_time_hour:
                        print '{0} (00-{1}) [{2}]'.format(txt_colors.GREEN + hour_key + txt_colors.ENDC,
                                                          end_time_minute,
                                                          hour_count_value['count']),
                        print '{',
                        # print 10 min interval hit count for the hour
                        print_10min(hour_count_value['ten_min']),
                        print '}\n',
                    else:
                        # Any hour of the last date
                        print '{0} [{1}]'.format(txt_colors.GREEN + hour_key + txt_colors.ENDC,
                                                 hour_count_value['count']),
                        print '{',
                        print_10min(hour_count_value['ten_min']),
                        print '}\n',
            # Any date that is not the first or the last
            else:
                print '\n\n', '{0} (00:00:23:59) [{1}]'.format(
                    txt_colors.CYAN +
                    datetime.datetime.strftime(
                        date_key, '%d/%b/%Y') + txt_colors.ENDC,
                    date_values['count']), '\n\n',
                print 'Hourly: \n\n',
                for hour_key, hour_count_value in hour_sort:
                    print '{0} [{1}]'.format(txt_colors.GREEN + hour_key + txt_colors.ENDC, hour_count_value['count']),
                    print '{',
                    print_10min(hour_count_value['ten_min']),
                    print '}\n',
        # If the start time date and the end time date are both the same day
        else:
            print '\n\n', '{0} ({1}-{2}) [{3}]'.format(
                txt_colors.CYAN +
                start_time.strftime('%d/%b/%Y') + txt_colors.ENDC,
                start_time.strftime('%H:%M'), end_time.strftime('%H:%M'),
                date_values['count']), '\n\n',
            print 'Hourly: \n\n',
            for hour_key, hour_count_value in hour_sort:
                # if user input dates are not within the same hour
                if not start_time.hour == end_time.hour:
                    if hour_key == start_time_hour:
                        print '{0} ({1}-59) [{2}]'.format(txt_colors.GREEN + hour_key + txt_colors.ENDC,
                                                          start_time_minute,
                                                          hour_count_value['count']),
                        print '{',
                        print_10min(hour_count_value['ten_min']),
                        print '}\n',
                    # Last hour of the last date
                    elif hour_key == end_time_hour:
                        print '{0} (00-{1}) [{2}]'.format(txt_colors.GREEN + hour_key + txt_colors.ENDC,
                                                          end_time_minute,
                                                          hour_count_value['count']),
                        print '{',
                        print_10min(hour_count_value['ten_min']),
                        print '}\n',
                    # any hour of the day
                    else:
                        print '{0} [{1}]'.format(txt_colors.GREEN + hour_key + txt_colors.ENDC,
                                                 hour_count_value['count']),
                        print '{',
                        print_10min(hour_count_value['ten_min']),
                        print '}\n',
                # if it is within the same hour
                else:
                    print '{0} ({1}-{2}) [{3}]'.format(txt_colors.GREEN + hour_key + txt_colors.ENDC,
                                                       start_time_minute,
                                                       end_time_minute, hour_count_value['count']),
                    print '{',
                    print_10min(hour_count_value['ten_min']),
                    print '}\n',


# print all ip related data
def print_ip(ip_logs, start_time, end_time, ip_no, request_no, options):
    print '=== Total hits per ip between {0} - {1} ==='.format(txt_colors.LIGHTRED + str(start_time.strftime('%d/%b/%Y %H:%M:%S')),
                                                               str(end_time.strftime('%d/%b/%Y %H:%M:%S')) + txt_colors.ENDC)
    # sort per IP with highest hits
    ip_logs = sorted(ip_logs.items(), key=itemgetter(
        1), reverse=True)
    # ipmatch should only display the ip's user inputs
    if not options.ipmatch:
        ip_logs = ip_logs[:ip_no]
    for number, (ip_key, ip_values) in enumerate(ip_logs, 1):
        # count how many unique requests are left that aren't being shown
        request_count = len(ip_values['get_post']) - request_no
        request_total = request_count if request_count > 0 else 0
        # check if --nogeo is enabled
        geo_information = (
            '' if options.nogeo else "| [Country: {0} ({1})] [ISP: {2}] [Hostname: {3}]".format(*ip_api(ip_key)))
        print '\n---------------------------------'
        # print ip/count
        print '\n', '{0}. [{1}] {2} {3}'.format(number, ip_values['count'],
                                                txt_colors.PURPLE + ip_key + txt_colors.ENDC,
                                                geo_information)
        # print requests per ip
        print ''.join(
            ['[{1:d}] {0}\n'.format(*kv) for kv in ip_values['get_post'].most_common()[:request_no]]),
        print '... and {0} more unique requests'.format(txt_colors.LIGHTRED + str(request_total) + txt_colors.ENDC),
        # print date related hits per ip
        print_date(ip_values['date'], start_time, end_time)


# print all requests related data
def print_request(request_logs, start_time, end_time, ip_no, request_no, options):
    print '=== Total hits per request between {0} - {1} ==='.format(txt_colors.LIGHTRED + str(start_time.strftime('%d/%b/%Y %H:%M:%S')),
                                                                    str(end_time.strftime('%d/%b/%Y %H:%M:%S')) + txt_colors.ENDC)
    # sort requests per count
    request_logs = sorted(request_logs.items(),
                          key=itemgetter(1), reverse=True)

    # rmatch should only display the requests the user inputs
    if not options.rmatch:
        request_logs = request_logs[:request_no]
    for number, (request_key, request_values) in enumerate(request_logs, 1):
        # count how many unique ip's are left that aren't being shown
        ip_count = len(request_values['ip']) - ip_no
        ip_total = ip_count if ip_count > 0 else 0
        print '\n---------------------------------'
        # print requests and count
        print '\n', '{0}. [{1}] {2}'.format(number, request_values['count'],
                                            txt_colors.PURPLE + request_key + txt_colors.ENDC)
        # print total ip per requests
        for ip_key, ip_values in request_values['ip'].most_common()[:ip_no]:
            # check if --nogeo is enabled
            geo_information = (
                '' if options.nogeo else "| [Country: {0} ({1})] [ISP: {2}] [Hostname: {3}]".format(*ip_api(ip_key)))
            # print ip and count
            print '[{0}] {1} {2}'.format(ip_values, ip_key, geo_information)
        print '... and {0} more unique ip\'s'.format(txt_colors.LIGHTRED + str(ip_total) + txt_colors.ENDC),
        # print date related hits per request
        print_date(request_values['date'], start_time, end_time)


# Print the results of data gathered from logs into console
def print_data(*arguments):
    ip_req_logs, overall_date_logs, start_time, end_time, options = arguments
    ip_no, request_no = ip_req_number_args(options)
    # print total count for date and per hourly basis
    if options.filter and options.ipmatch:
        data = 'for {0} with listed IP\'s'.format(options.filter)
    elif options.filter and options.rmatch:
        data = 'for {0} with listed requests'.format(options.filter)
    elif options.filter:
        data = 'for {0}'.format(options.filter)
    elif options.ipmatch:
        data = 'for listed IP\'s'
    elif options.rmatch:
        data = 'for listed requests'
    else:
        data = ''

    print '\n\n==== OVERALL HITS between {0} - {1} {2} ===='.format(txt_colors.LIGHTRED + str(start_time.strftime('%d/%b/%Y %H:%M:%S')),
                                                                    str(end_time.strftime('%d/%b/%Y %H:%M:%S')) + txt_colors.ENDC, data)

    print '\n\n{0}: {1} (*minutes) [count] ( {2} [count] | )'.format(txt_colors.YELLOW + 'Key' + txt_colors.ENDC,
                                                                     txt_colors.GREEN + 'Hour' + txt_colors.ENDC,
                                                                     txt_colors.CYAN + '10 min intervals' + txt_colors.ENDC),
    # print overall date hits for all ip's or requests
    print_date(overall_date_logs, start_time, end_time)
    print '\n'
    # print request or ip data depending on user input
    if options.request or options.rmatch:
        print_request(ip_req_logs, start_time, end_time,
                      ip_no, request_no, options)
    else:
        print_ip(ip_req_logs, start_time, end_time, ip_no, request_no, options)


def main():
    options, args = optionparse_args()
    # --select options cycles through logs and prints them one at a time
    if options.select:
        get_data_from_logs(options, args)
    else:
        print_data(*get_data_from_logs(options, args))

    print '\n'

    try:
        sys.stdout.close()
    except:
        pass
    try:
        sys.stderr.close()
    except:
        pass


if __name__ == "__main__":
    main()
