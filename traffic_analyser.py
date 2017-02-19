#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Author:       Tahzeem Taj
#               tahzeem.taj@gmail.com
# Source:       https://github.com/tahz7/traffic_analyser

from datetime import datetime, timedelta
import json
import urllib2
import socket
import sys
import re
import time
import os
import gzip
from sys import stdout
from time import sleep
from optparse import OptionParser
from collections import defaultdict
from operator import itemgetter


class Col(object):
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    PURPLE = '\033[35m'
    LIGHTRED = '\033[91m'
    CYAN = '\033[36m'
    U = '\033[4m'
    ENDC = '\033[0m'


class Title(object):
    line = u'●▬▬▬▬▬▬▬▬▬▬▬▬▬▬๑۩۩๑▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬●'
    traffic_analyser = u'▂▃▅▇█▓▒░۩۞۩ TRAFFIC ANALYSER ۩۞۩░▒▓█▇▅▃▂'
    log_info = u'▂▃▅▇█▓▒░۩۞۩ LOGS INFO ۩۞۩░▒▓█▇▅▃▂'
    log_result = u'▂▃▅▇█▓▒░۩۞۩ LOG RESULTS ۩۞۩░▒▓█▇▅▃▂'
    general_info = u'▂▃▅▇█▓▒░۩۞۩ GENERAL INFO ۩۞۩░▒▓█▇▅▃▂'


class CmdArgs(object):

    def __init__(self):
        self.cmd_args = defaultdict(dict)

    def args_validation(self, options, args, parser, help_text):
        """
        Validate command line options/arguments
        """
        if options.help:
            print help_text
            sys.exit()
        # set default options
        if len(sys.argv) < 2:
            options.compact = (10, 10)
            options.hour = 1
            self.cmd_args['default_arg'] = "--compact 10 10 --hour 1"
        elif (options.select or options.log) and not (options.compact or
                                                      options.ip or
                                                      options.rmatch or
                                                      options.ipmatch or
                                                      options.request or
                                                      options.hour or
                                                      options.min or
                                                      options.day or
                                                      options.date):
            options.compact = (10, 10)
            options.hour = 1
            self.cmd_args['default_arg'] = "--compact 10 10 --hour 1"
        elif (options.select or options.log) and (options.hour or
                                                  options.min or
                                                  options.date or
                                                  options.day) and not (
                options.compact or options.ip or
                options.rmatch or options.ipmatch or
                options.request):

            options.compact = (10, 10)
            self.cmd_args['default_arg'] = "--compact 10 10"
        elif (options.select or options.log) and (options.compact or
                                                  options.ip or
                                                  options.rmatch or
                                                  options.ipmatch or
                                                  options.request) and not (
                options.hour or
                options.min or
                options.date or
                options.day):
            options.hour = 1
            self.cmd_args['default_arg'] = "--hour 1"
        elif (options.compact or options.ip or options.rmatch or
              options.ipmatch or options.request) and not (options.hour or
                                                           options.min or
                                                           options.date or
                                                           options.day):
            options.hour = 1
            self.cmd_args['default_arg'] = "--hour 1"
        elif (options.hour or options.min or options.date or
              options.day) and not (options.compact or options.ip or
                                    options.rmatch or options.ipmatch or
                                    options.request):
            options.compact = (10, 10)
            self.cmd_args['default_arg'] = "--compact 10 10"

        if options.log:
            # cycle will display results for each individual log file
            if 'cycle' in options.log:
                self.cmd_args['cycle_all'] = True
                options.log.remove('cycle')
            # remove duplicate values in options.log and args (this occurs when
            # options.log and (options.rmatch or options.ipmatch)) is input
            for log_file in options.log:
                # cycle will display results for each individual log file
                if log_file in args:
                    args.remove(log_file)
                elif not os.path.exists(log_file):
                    parser.error("Could not find this log file; {0}. Make sure"
                                 " you've got the correct file name".format(
                                     log_file))
        elif options.dir:
            sys.exit("--dir options has been removed. Use {0} instead.".format(
                Col.CYAN + "--log /path/to/directory/*" + Col.ENDC))
        if options.date:
            args_number = len(options.date)
            if args_number > 2:
                parser.error(
                    'You input more than two arguments. '
                    'The correct formatting should be: date/month/year:hour:'
                    'minute:second | 10/Jan/2017:15:00:00')
            if args_number == 2:
                try:
                    datetime.strptime(options.date[0], "%d/%b/%Y:%H:%M:%S")
                    datetime.strptime(options.date[1], "%d/%b/%Y:%H:%M:%S")
                except ValueError:
                    parser.error('Either from_time or to_time is incorrectly '
                                 'formatted. The correct formatting should '
                                 'be: date/month/year:hour:minute:second | '
                                 '10/Jan/2017')
            else:
                regex_date = re.search(r"(\d{2}/\w+/\d{4})", options.date[0])
                if regex_date:
                    try:
                        datetime.strptime(options.date[0], "%d/%b/%Y")
                        self.cmd_args['single_date'] = True
                    except ValueError:
                        parser.error(
                            'There was a problem with your --date argument. '
                            'The correct formatting should be: date/month/year'
                            ' | 10/Aug/2016:15:00:00')
                else:
                    parser.error(
                        'There was a problem with your --date argument. '
                        'The correct formatting should be: date/month/year'
                        ' | 10/Aug/2016:15:00:00')
        if options.ipmatch:
            try:
                options.ipmatch[0] = int(options.ipmatch[0])
            except ValueError:
                parser.error(
                    'The first argument for option -ipmatch is request_number '
                    'which needs to be an integer')
            if len(args) < 1:
                parser.error(
                    'The second argument (and so forth) for option -ipmatch '
                    'needs to be a ip')
        if options.rmatch:
            try:
                options.rmatch[0] = int(options.rmatch[0])
            except ValueError:
                parser.error(
                    'The first argument for option --rmatch is ip_number '
                    'which needs to be an integer')
            if len(args) < 1:
                parser.error(
                    'The second argument (and so forth) for option --rmatch '
                    'needs to be a request string')
        if options.filter:
            options.filter = options.filter.upper()
            if options.filter not in ['POST', 'GET']:
                parser.error(
                    'The --filter option takes only one of these two '
                    'arguments; POST or GET')
        if options.select:
            for item in args:
                if item.lower() == 'all':
                    args.remove(item)
                    self.cmd_args['cycle_all'] = True
        if options.ten:
            if options.ten.lower() not in ['on', 'off']:
                parser.error("You can only use the --ten option with either "
                             "on or off argument. ie. --ten on (to enable ten "
                             "minute intervals)")
            elif options.ten.lower() == 'on':
                self.cmd_args['ten_min'] = True
            else:
                self.cmd_args['ten_min'] = False

        # Ensure only one option per option group is selected
        time_list = []
        data_list = []
        log_list = []
        search_list = []

        for option, arg in vars(options).iteritems():
            if arg not in [None, False]:
                if option in ['day', 'hour', 'min', 'date']:
                    time_list.append(option)
                if option in ['ip', 'request', 'ipmatch', 'rmatch', 'compact']:
                    data_list.append(option)
                if option in ['select', 'log', 'dir']:
                    log_list.append(option)
                if option in ['complete', 'top']:
                    search_list.append(option)
        for item in [time_list, data_list, log_list, search_list]:
            if len(item) > 1:
                parser.error('You can only use one of the following '
                             'options: ' + ' '.join(['--{0}'.format(option)
                                                     for option in item]))

        # Ensure both time and data options are input as a minimum
        # for the script to work.
        if not time_list or not data_list:
            parser.error('You must choose at least one time group option '
                         '(--min, --hour, --day, --date) and one data group '
                         'option (--ip, --request, --ipmatch, --rmatch, '
                         '--compact)')

        return options, args

    def multi_args(self, option, opt_str, value, parser):
        """ Normally you can append variable arguments into the args list
        but this can lead to data clashes if --rmatch or --ipmatch is also
        used. For avoidance this function is currently used to append
        arguments for the --log option.
        """
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

    def main_args(self):
        # format options when displayed
        lst_args = ['Time Options', 'minute', 'hour', 'day', 'from time',
                    'to time', 'day', 'Data Options', 'ip number',
                    'request number', 'ip number', 'request number',
                    'request number', 'ip number', 'request number',
                    'list of ip\'s', 'ip number',  'list of requests',
                    'Log Options', 'all', 'log file(s)', 'log file(s)',
                    'Search Options', 'Miscellaneous Options', 'on/off',
                    'get/post']
        lst_args_format = map(lambda x: Col.U + x + Col.ENDC
                              if x not in ['Time Options', 'Data Options',
                                           'Log Options', 'Search Options',
                                           'Miscellaneous Options'] else
                              Col.LIGHTRED + x + Col.ENDC, lst_args)

        help_text = '''\n  Options:

                      -h, --help            show this help message and exit

                      {0}

                      --min {1}    Get data from last X minutes
                      --hour {2}   Get data from last X hour(s)
                      --day {3}    Get data from last X day(s)
                      --date {4} {5} or --date {6}
                                Get data from between two dates (Example;
                                date/month/year:hour:minute:second |
                                10/Aug/2016:15:00:00). Or get the whole day
                                (Example: 11/Jan/2017)

                      {7}

                      --compact {8} {9}
                                 Get a simple version of a list of the top X
                                 ip's and a list of the top X requests.
                                 (Example: --compact 10 10)
                      --ip {10} {11}
                                 Get the top X ip's along with their top X
                                 requests
                      --request {12} {13}
                                 Get the top X requests's along with their top
                                 X ip's
                      --ipmatch {14} {15}
                                 Get top X requests for user input list of
                                 ip'(s)s. (Example: --ipmatch 20 10.10.23.42
                                 134.134.3.13)
                      --rmatch {16} {17}
                                 Get top X ip's for user input list of
                                 request(s).
                                 (Example: --rmatch 10 xmlrpc.php wp-login.php)

                      {18}

                      --select or --select {19}
                                 Choose which logs to check from a list of logs
                                 currently opened by nginx/apache. Or you can
                                 cycle all the open log files using
                                 --select all
                      --log {20} or --log cycle {21}
                                 Choose which log files to read from (you can
                                 input multiple log files, (Example; --log
                                 google_access_log /var/log/httpd/*access*) Or
                                 you can cycle the log files to get data
                                 per-log file
                                 (Example: --log cycle logfile1 logfile2)

                      {22}

                      By default logs are read from bottom to top. You can
                      override this setting using the following;

                      --top
                                 Read log files from the top down (by
                                 default logs are read from the bottom line
                                 up)
                      --complete
                                 Read every line in log files from the top
                                 to bottom line

                      {23}

                      --nogeo      Disable geo information per ip
                      --ten {24}
                                   Manually enable or disable10 min hit count
                                   intervals. By default the 10 minute interval
                                   hit count is disabled for data over 6 hours.
                      --filter {25}
                                   filter requests by POST or GET

                      Further documentation can be viewed in the Wiki -
                      https://github.com/tahz7/traffic_analyser/wiki

                        '''.format(*lst_args_format)

        parser = OptionParser(
            usage=help_text, conflict_handler="resolve", add_help_option=False)

        # time options group
        parser.add_option('-m', '--min', type='int', nargs=1)
        parser.add_option('-k', '--hour', type='int', nargs=1)
        parser.add_option('-d', '--day', type='int', nargs=1)
        parser.add_option('-d', '--date', action="callback",
                          callback=self.multi_args, dest="date")
        # data options group
        parser.add_option('-c', '--compact', type='int', nargs=2)
        parser.add_option('-i', '--ip', type='int', nargs=2)
        parser.add_option('-r', '--request', type='int', nargs=2)
        parser.add_option('-i', '--ipmatch', action='append')
        parser.add_option('-r', '--rmatch', action='append')
        # log options group
        parser.add_option('-s', '--select', action='store_true')
        parser.add_option("-l", "--log", action="callback",
                          callback=self.multi_args, dest="log")
        parser.add_option('-d', '--dir', nargs=1)
        # search options group (method of searching through a log file)
        parser.add_option('-t', '--top', action='store_true')
        parser.add_option('-c', '--complete', action='store_true')
        # miscellaneous options group
        parser.add_option('-t', '--ten', type='str',  nargs=1)
        parser.add_option(
            '-g', '--nogeo', help='Disable geo information per ip',
            action='store_true')
        parser.add_option(
            '-f', '--filter', help='filter requests by POST or GET',
            type='str',
            nargs=1)
        parser.add_option('-h', '--help', dest='help', action='store_true',
                          help='show this help message and exit')
        # args is used for variable user inputs for rmatch and ipmatch only.
        # Options for other user input
        (options, args) = parser.parse_args()

        options, args = self.args_validation(options, args, parser, help_text)

        self.cmd_args['opts'] = options
        self.cmd_args['args'] = args
        self.cmd_args['help_text'] = help_text

        return self.cmd_args


class GetData(object):

    def __init__(self, cmd_args):
        self.cmd_args = cmd_args
        # contains httpd type, log files, time period
        self.data = defaultdict(dict)

    def control_flow(self):
        opts = self.cmd_args['opts']
        # get start and end times
        start_time, end_time = self.start_end_dates(opts)
        # check whether to enable/disable ten min interval
        self.ten_min_interval(start_time, end_time)
        # get httpd type and httpd pids
        httpd_pid_dict = self.get_httpd_type(opts)
        # get log files
        self.get_log_files(opts,
                           httpd_pid_dict)
        # get ip and request number
        self.ip_req_number_args(opts)

        return self.data

    def total_seconds(self, time_input):
        return ((time_input.microseconds + 0.0 +
                 (time_input.seconds + time_input.days * 24 * 3600) *
                 10 ** 6) / 10 ** 6)

    def ten_min_interval(self, start_time, end_time):
        """ Disable ten min interval hit count if date range is over 6 hours.
        Otherwise disable/enable based on --ten option
        """
        if (self.total_seconds(end_time - start_time) / 3600 < 6 and (
            'ten_min' not in self.cmd_args) or
                self.cmd_args['ten_min']):
            self.data['ten_min_enable'] = True

    def get_log_files(self, opts, httpd_pid_dict):
        """ Grab log files based on options/args """

        logs = set()

        # add logs input by user
        if opts.log:
            for log_file in opts.log:
                if os.path.isfile(log_file):
                    logs.add(log_file)
        # Otherwise, get the log files that are currently open by either
        # Apache/Ngninx.
        else:
            httpd_pid = httpd_pid_dict[self.data['httpd_type']]['ports']
            for pid in httpd_pid:
                try:
                    for log_file in os.listdir('/proc/{0}/fd'.format(pid)):
                        log_file = os.readlink(
                            "/proc/{0}/fd/{1}".format(pid, log_file))
                        # Don't include deleted files
                        if 'access' in log_file and ('(deleted)' not in
                                                     log_file):
                            logs.add(log_file)
                except IOError:
                    continue

        start_time, end_time = (self.data['time_period'][0],
                                self.data['time_period'][1])

        # total_logs = len(logs)
        # get log file size + date and then add to data dict
        for log_file in logs:
            log_size = self.filesize(os.path.getsize(log_file))
            log_last_modified = datetime.strptime(
                time.ctime(os.path.getmtime(log_file)), '%a %b %d %H:%M:%S %Y')
            if start_time <= log_last_modified and (log_size != '0.00 B'):
                self.data['logs'][log_file] = log_size
                self.data['last_modified'][log_file] = log_last_modified

        # add total log files count
        self.data['log_count'] = len(self.data['logs'])
        self.data['logs_skipped'] = len(logs) - len(self.data['logs'])

        if self.data['log_count'] == 0:
            print ("There are no log files to check. Exiting script..."
                   "\n\n Note: if a log file is empty or its 'last modified "
                   "time' is not within the time-range specified, then the "
                   "script will skip it.")
            sys.exit()

        # List logs opened by apache/nginx and let the user choose
        if opts.select and 'cycle_all' not in self.cmd_args:
            print
            # prompt user to choose log files to check
            for n, (log_file, size) in enumerate(
                    self.data['logs'].iteritems(), 1):
                print '{0}. {1} [{2}]'.format(n,
                                              Col.YELLOW + log_file +
                                              Col.ENDC, size)
            print
            log_count = len(self.data['logs'])
            while True:
                try:
                    sys.stdin = open('/dev/tty')
                    user_input = raw_input(
                        "Which logs would you like to analyse? "
                        "(eg. 1 3 4 or all) ")
                    input_list = user_input.split()
                    if not input_list:
                        print (
                            "You need to make sure your input is either"
                            " all(selects all logs) or are digits with "
                            "spacing between them (ie. 4 3 2 1)")
                    else:
                        if 'all'.lower() in input_list:
                            break
                        else:
                            input_list = [int(a) for a in input_list]
                            # Check user input is correct
                            if (max(input_list) >
                                    log_count or min(input_list) <
                                    1):
                                print ("Error: The logs range from 1 to "
                                       "{0}, so where did you get {1} "
                                       "from...?".format(log_count,
                                                         max(input_list)))
                            else:
                                # remove logs the user doesn't want
                                for n, log_file in enumerate(
                                        self.data['logs'].copy().keys(), 1):
                                    if n not in input_list:
                                        self.data['logs'].pop(log_file)
                                        self.data['last_modified'].pop(
                                            log_file)

                                self.data['log_count'] = len(self.data['logs'])
                                break
                except ValueError:
                    print ("You need to make sure your input is either"
                           " all(selects all logs) or are digits with "
                           "spacing between them (ie. 4 3 2 1)")

        return self.data

    def filesize(self, bytes, suffix='B'):
        """ Convert bytes to readable format. """

        for unit in ['', 'K', 'M', 'G', 'T']:
            if abs(bytes) < 1024.0:
                return "{0:.2f} {1}{2}".format(round(bytes, 2), unit, suffix)
            bytes /= 1024.0

    def get_httpd_type(self, opts):
        """ Get httpd version (nginx or apache) """

        httpd_pid_dict = defaultdict(dict)
        pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

        for pid in pids:
            try:
                if os.path.exists('/proc/{0}/exe'.format(pid)):
                    processes = os.readlink('/proc/{0}/exe'.format(pid))
                    regex_process = re.search("(httpd|nginx|apache2)+",
                                              processes)
                    if regex_process is not None:
                        httpd_regex = regex_process.group(1)
                        if httpd_regex in ['apache2', 'httpd']:
                            httpd_regex = 'apache'
                        (httpd_pid_dict[httpd_regex].
                         setdefault('ports', []).append(pid))
            except IOError:
                continue

        if not httpd_pid_dict and not opts.log:
            sys.exit("{0}\nERROR: The script cannot continue as it could not"
                     " detect nginx or apache running. Also the '--log' option"
                     " is not used.".format(self.cmd_args['help_text']))
        elif not httpd_pid_dict and opts.log:
            httpd_type = "Webserver not detected."
            self.data['httpd_extra_info'] = "--log option is used"
        elif len(httpd_pid_dict) > 1:
            # if both nginx/apache running, grab what's listening on port 80
            httpd_type = self.httpd_port_number(httpd_pid_dict)
            self.data['httpd_extra_info'] = ("Both nginx/apache detected, "
                                             "defaulting to what's "
                                             "listening on port 80")
        else:
            httpd_type = list(httpd_pid_dict)[0]

        self.data['httpd_type'] = httpd_type

        return httpd_pid_dict

    def socket_number(self, socket_no=None):
        """ Get one of the socket number(s) listening on tcp/tcp6 port 80
        """
        for protocol in ['tcp', 'tcp6']:
            with open(os.path.join('/proc/net', protocol), 'r') as socket_file:
                socket_table = socket_file.readlines()
                for line in socket_table:
                    line = line.split()
                    if line[3] == '0A':
                        hex_port = line[1].split(':')[1]
                        port = int(hex_port, 16)
                        if port == 80:
                            socket_no = line[-8]
                            break
        return socket_no

    def httpd_port_number(self, httpd_list):
        """ Find whether apache or nginx is listening on port 80
        """
        socket_no = self.socket_number()
        httpd_type = None
        if socket_no:
            for httpd, port in httpd_list.iteritems():
                pid = port['ports'][0]
                try:
                    for filename in os.listdir('/proc/{0}/fd'.format(pid)):
                        filename = os.readlink(
                            "/proc/{0}/fd/{1}".format(pid, filename))
                        # check if socket number matches open sockets for
                        # httpd pid
                        if socket_no in filename:
                            # print filename
                            httpd_type = httpd
                            break
                except IOError:
                    continue

        # Quit if cannot detect what is running on port 80
        if not httpd_type:
            print ("{0}\nERROR: Could not detect whether apache or nginx is "
                   "listening on port 80".format(self.cmd_args['help_text']))
            sys.exit()

        return httpd_type

    def calculate_start_time(self, metric, args_time):
        """
        calculate the start time variable for min, hour and day.
        """
        start_time = ((datetime.now() -
                       timedelta(**{metric: args_time})).
                      strftime("%d/%b/%Y:%H:%M:%S"))

        return start_time

    def start_end_dates(self, opts):
        """
        Get the start/end dates based on user input
        """
        # end time is current time unless --date option is used.
        end_time = datetime.now().strftime("%d/%b/%Y:%H:%M:%S")

        if opts.day:
            args_time = opts.day
            start_time = self.calculate_start_time('days', args_time)
        elif opts.min:
            args_time = opts.min
            start_time = self.calculate_start_time('minutes', args_time)
        elif opts.hour:
            args_time = opts.hour
            start_time = self.calculate_start_time('hours', args_time)
        elif 'single_date' in self.cmd_args:  # --date option:
            args_date = datetime.strptime(opts.date[0], "%d/%b/%Y")
            start_time = datetime.strftime(args_date, "%d/%b/%Y:%H:%M:%S")
            if datetime.now().date() != args_date.date():
                end_time = opts.date[0] + ":23:59:59"
        else:
            start_time = opts.date[0]
            end_time = opts.date[1]

        start_time = datetime.strptime(start_time,
                                       "%d/%b/%Y:%H:%M:%S")
        end_time = datetime.strptime(end_time, "%d/%b/%Y:%H:%M:%S")

        self.data.setdefault('time_period', []).extend(
            [start_time, end_time])

        return start_time, end_time

    def ip_req_number_args(self, opts):
        """ assigns user options to ip number and request number. """

        if opts.ip:
            ip_no = opts.ip[0]
            request_no = opts.ip[1]
        elif opts.request:
            ip_no = opts.request[1]
            request_no = opts.request[0]
        elif opts.rmatch:
            request_no = None
            ip_no = int(opts.rmatch[0])
        elif opts.ipmatch:
            ip_no = None
            request_no = opts.ipmatch[0]
        else:  # options.compact
            ip_no = opts.compact[0]
            request_no = opts.compact[1]

        # Limit geo api to 30 ip's to avoid potential abuse.
        if not opts.nogeo:
            if ip_no > 30:
                self.data['geo_limit'] = ip_no
                ip_no = 30

        self.data['ip_no'] = ip_no
        self.data['request_no'] = request_no


class LogDataStructure(object):

    def ip_record(self):
        """ Count hits per ip and hits for requests per ip.
         Used with the --ip/--ipmatch option.
        """
        return {
            'count': 0,
            'get_post': Counter(),
            'date': defaultdict(self.date_record)
        }

    def request_record(self):
        """ Count hits per requests and hits for ip per requests.
         Used with the --request/--rmatch option.
        """
        return {
            'count': 0,
            'ip': Counter(),
            'date': defaultdict(self.date_record)
        }

    def compact_record(self):
        """ Count top ip and top requests only. Used with --compact option """

        return {
            'ip': Counter(),
            'request': Counter()
        }

    def date_record(self):
        """ Count hits per date and per hour for either ip or request only.
        Used with --ip/--request option.
        """
        return {
            'count': 0,
            'hour': defaultdict(self.ten_minutes_record),
        }

    def ten_minutes_record(self):
        """ Count hits per every 10 minutes """

        return {
            'count': 0,
            'ten_min': Counter()
        }

    # This default dict gets combined hits of all data
    def overall_date_count(self):
        """ Count all hits per date and per hour """

        return {
            'count': 0,
            'hour': defaultdict(self.ten_minutes_record),
        }


class AnalyseLogs(LogDataStructure):

    def __init__(self, cmd_args, data):
        super(LogDataStructure, self).__init__()
        self.cmd_args = cmd_args
        self.data = data
        self.hit_count = 0
        # If the start/end time is longer than 6 hours, then we want
        # disable the 10 min intervals for readability
        self.ten_min_enable = (True if 'ten_min_enable' in self.data else
                               False)

        if self.cmd_args['opts'].ipmatch or (
                self.cmd_args['opts'].rmatch):
            self.date_count = None
        else:
            # overall date count dict
            self.date_count = defaultdict(self.overall_date_count)

        # Use the relevant count dict for requests or ip
        if self.cmd_args['opts'].request or self.cmd_args['opts'].rmatch:
            self.ip_req_count = defaultdict(self.request_record)
        elif self.cmd_args['opts'].ip or self.cmd_args['opts'].ipmatch:
            self.ip_req_count = defaultdict(self.ip_record)
        else:  # create a new dict for compact option
            self.ip_req_count = self.compact_record()

        # month dict for converting time into datetime object
        self.month_dict = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5,
                           'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10,
                           'Nov': 11, 'Dec': 12}

    def grab_log_data(self):
        """ Get data from logs """

        ip_req_count, date_count = self.get_data_from_logs()
        logs_data = ip_req_count, date_count

        return logs_data

    def regex_compile(self, opts):
        """ Compile regex's for matching log file lines """

        # compile date and request regex
        regex_date_compile = r"(\d{2}/\w+/\d{4}:\d{2}:\d{2}:\d{2})"
        regex_date = re.compile(regex_date_compile).search

        if opts.filter:
            # Only look for requests that start with get or post
            regex_requests_compile = r'"%s[^"]*" \d{3}' % opts.filter
        else:  # get all request matches
            regex_requests_compile = r'"[^"]*" \d{3}'

        regex_requests = re.compile(regex_requests_compile).search

        return regex_date, regex_requests

        # This func adds ip/requests/time data to count dictionaries

    def dict_add(self, req_ip, found_time_date, found_time_hour,
                 found_time_minute):
        """  add date data to ip or request dict """

        # regex_req_ip can be ip or request
        self.ip_req_count[req_ip]['count'] += 1
        # add date
        self.ip_req_count[req_ip]['date'][found_time_date]['count'] += 1
        # add hour
        self.ip_req_count[req_ip]['date'][found_time_date][
            'hour'][found_time_hour]['count'] += 1
        if self.ten_min_enable:
            # add 10 minute interval
            self.ip_req_count[req_ip]['date'][found_time_date]['hour'][
                found_time_hour]['ten_min'][
                found_time_minute[0]] += 1

    def dict_date_add(self, found_time_date, found_time_hour,
                      found_time_minute):
        """ Add date data to overall date count dict """

        # add date
        self.date_count[found_time_date]['count'] += 1
        # add hour
        self.date_count[found_time_date]['hour'][found_time_hour]['count'] += 1
        # add 10 minute interval
        self.date_count[found_time_date]['hour'][found_time_hour][
            'ten_min'][found_time_minute[0]] += 1

    def evaluate_line(self, line, start_time, end_time,
                      regex_date, regex_requests, opts, args, found_time=None):
        """ Grab required data from log line """

        regex_date = regex_date(line)
        regex_requests = regex_requests(line)

        if regex_date and regex_requests:
            date = regex_date.group()
            # convert line date into datetime object
            yr = int(date[7:11])
            mon = self.month_dict[(date[3:6])]
            day = int(date[0:2])
            hr = date[12:14]
            minute = date[15:17]
            sec = int(date[18:20])
            found_time = datetime(yr, mon, day, int(hr), int(minute), sec)

            found_time_date = found_time.date()
            found_time_hour = date[12:14]
            found_time_minute = date[15:17]

            # compare time from log line to user input time range
            if start_time <= found_time <= end_time:
                requests = regex_requests.group()
                ip = line.split()[0]

                if opts.request or opts.rmatch:
                    # collect data based upon requests
                    req_ip = requests
                else:  # instead do it for ip
                    req_ip = ip

                # add to overall dict count
                if not opts.rmatch and not opts.ipmatch:
                    self.dict_date_add(found_time_date, found_time_hour,
                                       found_time_minute)

                if opts.ipmatch:
                    # compare ip with the ip's from user input
                    ipmatch_list = args
                    if req_ip in ipmatch_list:
                        self.dict_add(req_ip, found_time_date,
                                      found_time_hour, found_time_minute)
                        self.ip_req_count[req_ip]['get_post'][
                            requests] += 1
                elif opts.rmatch:
                    # compare request with the requests from user input
                    rmatch_list = args
                    if any(x in requests for x in rmatch_list):
                        self.dict_add(req_ip, found_time_date,
                                      found_time_hour, found_time_minute)
                        self.ip_req_count[req_ip]['ip'][ip] += 1
                # compact option collects only ip's and requests without
                # their time hit count data
                elif opts.compact:
                    self.ip_req_count['ip'][ip] += 1
                    self.ip_req_count['request'][requests] += 1
                # top ip's or top requests to check
                else:
                    self.dict_add(req_ip, found_time_date,
                                  found_time_hour, found_time_minute)
                    if opts.request:
                        # Add ip data from line to dict
                        self.ip_req_count[req_ip]['ip'][ip] += 1
                    else:
                        # add request data from line to dict
                        self.ip_req_count[req_ip]['get_post'][
                            requests] += 1

            else:
                found_time = None

        return found_time

    def get_data_from_logs(self, logs=None):
        """ Process each log file and grab requested data """

        opts = self.cmd_args['opts']
        args = self.cmd_args['args']
        start_time, end_time = (self.data['time_period'][0],
                                self.data['time_period'][1])
        regex_date, regex_requests = self.regex_compile(opts)

        first_recorded_date = None
        last_recorded_date = None

        # sort logs by 'last modified date' to grab earliest and last record
        if not opts.select and 'cycle_all' not in self.cmd_args:
            logs = [log[0] for log in sorted(
                self.data['last_modified'].items(), key=itemgetter(1),
                reverse=True)]

        log_count = self.data['log_count']

        while True:
            # Go through each log file and grab required data
            for number, logfile in enumerate(logs, 1):
                if not opts.select and 'cycle_all' not in self.cmd_args:
                    # dynamic print update status
                    stdout.write(
                        "\r\x1b[K" + "Checking log file {0}/{1}... "
                                     "{2} ({3})".format(
                                         number, log_count, logfile,
                                         self.data['logs'][logfile]))
                    stdout.flush()
                    sleep(1)

                gzip_file_check = (True if logfile.endswith('.gz') else False)

                if gzip_file_check:
                    # read gzip files
                    infile = self.openfile(logfile)
                    for line in infile:
                        found_time = self.evaluate_line(line, start_time,
                                                        end_time,
                                                        regex_date,
                                                        regex_requests,
                                                        opts, args)
                        # Once we find the end date time we no longer
                        # need to carry on checking lines.
                        if found_time:
                            self.hit_count += 1
                            last_recorded_date = found_time
                            if not first_recorded_date:
                                first_recorded_date = found_time
                            if found_time >= end_time:
                                break

                elif opts.top:
                    # read log file from top to bottom.
                    with self.openfile(logfile) as infile:
                        for line in infile:
                            found_time = self.evaluate_line(line, start_time,
                                                            end_time,
                                                            regex_date,
                                                            regex_requests,
                                                            opts, args)
                            if found_time:
                                self.hit_count += 1
                                last_recorded_date = found_time
                                if not first_recorded_date:
                                    first_recorded_date = found_time
                                if found_time >= end_time:
                                    break
                # read log file from top line to the bottom  completely
                elif opts.complete:
                    with self.openfile(logfile) as infile:
                        for line in infile:
                            found_time = self.evaluate_line(line, start_time,
                                                            end_time,
                                                            regex_date,
                                                            regex_requests,
                                                            opts, args)
                            if found_time:
                                self.hit_count += 1
                                last_recorded_date = found_time
                                if not first_recorded_date:
                                    first_recorded_date = found_time

                # read the log file from bottom up
                else:
                    for line in self.reverse_readline(logfile):
                        found_time = self.evaluate_line(line, start_time,
                                                        end_time,
                                                        regex_date,
                                                        regex_requests,
                                                        opts, args)
                        if found_time:
                            self.hit_count += 1
                            first_recorded_date = found_time
                            if not last_recorded_date:
                                last_recorded_date = found_time
                            if found_time <= start_time:
                                break

                # record hit count of each log file
                self.data['hit_count'][logfile] = self.hit_count
                self.hit_count = 0

            else:  # break out of the while loop
                break

        # add the first and last recorded line to data dict
        self.data.setdefault('time_period', []).extend(
            [first_recorded_date, last_recorded_date])

        return self.ip_req_count, self.date_count

    def openfile(self, filename, mode='r'):
        if filename.endswith('.gz'):
            return gzip.open(filename, mode)
        else:
            return open(filename, mode)

    def reverse_readline(self, filename, buf_size=8192):
        """ a generator that returns the lines of a file in reverse order """

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
                # the first line of the buffer is probably not a complete line
                # so we'll save it and append it to the last line of the next
                # buffer we read
                if segment is not None:
                    # if the previous chunk starts right from the beginning
                    # of line do not connect the segment to the last line of
                    # new chunk instead, yield the segment first
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


class PrintData(object):

    def __init__(self, cmd_args, data):
        self.cmd_args = cmd_args
        self.data = data

    def time_range(self, start_time, end_time):
        earliest_record = self.data['time_period'][2].strftime(
            '%d/%b/%Y %H:%M:%S')
        last_record = self.data['time_period'][3].strftime(
            '%d/%b/%Y %H:%M:%S')

        time_range = (self.display_time_range(start_time, end_time,
                                              self.cmd_args['opts'],
                                              short_version=True))
        print "Time Range: {0}".format(time_range)
        print "Earliest Record Found: {0}".format(earliest_record)
        print "Last Record Found: {0}".format(last_record)

    def print_log_count(self, log_num=''):
        print "✄ Log files ordered by hit count: \n"

        logs = sorted(self.data['hit_count'].items(), key=itemgetter(1),
                      reverse=True)
        for n, (log, hit_count) in enumerate(logs, 1):
            size = self.data['logs'][log]
            # print log file and hit count
            print '{0}.{1} [{2}] {3} ({4})'.format(n, ('' if log_num == ''
                                                       else Col.BLUE + ' (' +
                                                       str(log_num[log]) +
                                                       ')' + Col.ENDC),
                                                   hit_count,
                                                   Col.YELLOW + log +
                                                   Col.ENDC, str(size))

    def print_logs_info(self):
        print
        logs_skipped = ('' if self.data['logs_skipped'] ==
                        0 else '\n✄ {0} logs were skipped due to either'
                        ' being empty or the logs last modified time is'
                        ' older than requested start time'.format(
                        self.data['logs_skipped']))

        print ('✄ A total of {0} logs were analysed{1}. '.format(
            Col.YELLOW + str(self.data['log_count']) + Col.ENDC, logs_skipped))

        if not self.cmd_args[
                'opts'].select and 'cycle_all' not in self.cmd_args:
            if None in self.data['time_period']:
                sys.exit("\nThere was no matching records found between "
                         "{0} - {1} for the log(s) "
                         "analysed\n".format(self.data['time_period'][0].
                                             strftime('%d/%b/%Y %H:%M:%S'),
                                             self.data['time_period'][1].
                                             strftime('%d/%b/%Y %H:%M:%S')))

        if self.cmd_args['opts'].select or 'cycle_all' in self.cmd_args:
            print ('✄ Log file results below are listed unordered. In order '
                   'to save memory consumption, the hit count per '
                   'log file will be shown at the very end.')
        else:
            self.print_log_count()

    def print_data(self, logs_data):
        """ Print the results of data gathered from logs into console
        """
        opts = self.cmd_args['opts']
        ip_req_logs, overall_date_logs = logs_data
        start_time, end_time = (self.data['time_period'][0],
                                self.data['time_period'][1])
        ip_no, request_no = self.data['ip_no'], self.data['request_no']

        if not self.cmd_args[
                'opts'].select and 'cycle_all' not in self.cmd_args:
            print
            print u'●▬▬▬▬▬▬▬▬▬▬▬▬▬▬๑۩۩๑▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬●'
            print
            print ("✄ Results below are a combined collection of the log files"
                   " listed above. For per-log analysis consider using"
                   " '--select' or '--log cycle /path/to/log(s)' options.")

        print
        print
        # print time range details
        self.time_range(start_time, end_time)

        # print request or ip data depending on user input
        if opts.ip or opts.request or opts.compact:
            # total_hit
            total_hits = sum(y['count'] for y in overall_date_logs.values())

            print '\nTOTAL HIT COUNT: [{0}]'.format(Col.LIGHTRED +
                                                    str(total_hits) +
                                                    Col.ENDC),
            self.print_date_logs(overall_date_logs, start_time, end_time)

        if opts.request or opts.rmatch:
            self.print_request(ip_req_logs, start_time, end_time,
                               ip_no, request_no, opts)
        elif opts.ip or opts.ipmatch:
            self.print_ip(ip_req_logs, start_time, end_time,
                          ip_no, request_no, opts)
        else:  # opts.compact
            self.print_compact(ip_req_logs, start_time, end_time,
                               ip_no, request_no, opts)

        print

    def print_format(self, date_logs):
        """ Get the max string length for both hour and 10 minute interval.
        This is later used to format and neatly print the output
        """
        ten_min_len = set()
        hour_len = set()

        for date, date_value in date_logs:
            for hour, hour_value in date_value['hour'].items():
                h_len = len(hour + str(hour_value['count']))
                hour_len.add(h_len)
                for ten_min, ten_min_value in hour_value['ten_min'].items():
                    ten_len = len(ten_min + str(ten_min_value))
                    ten_min_len.add(ten_len)

        try:
            # get the maximum string length size, which will be used in
            # table format
            ten_min_len = max(ten_min_len)
            hour_len = max(hour_len)
        except ValueError:
            ten_min_len = 0
            hour_len = 0

        return ten_min_len, hour_len

    def print_10min(self, hour_logs, ten_min_len):
        """ print 10 minute count """

        # sort by 10 min interval
        hour_logs = sorted(hour_logs.items())
        # get 10 min interval that have hit counts
        active_mins = [i[0] for i in hour_logs]

        # get 10 min interval that have no hit count
        for i in range(6):
            i = str(i)
            if i not in active_mins:
                hour_logs.insert(int(i), ('None', 'None'))

        # get count/ten min width for formatting
        count_width = ten_min_len + 1
        ten_min_width = ' ' * ten_min_len
        log_len = len(hour_logs)

        for n, (ten_min_key, ten_min_count_value) in enumerate(hour_logs, 1):
            pipe_format = ('' if n == log_len else '|')
            # if there are no hits, then print an empty space
            if ten_min_key == 'None':
                space_format = (' ' * 7 + ten_min_width + pipe_format if n == 1
                                else ' ' * 8 + ten_min_width + pipe_format)
                print space_format,
                continue

            from_min_time = (ten_min_key if ten_min_key is '0'
                             else ten_min_key + '0')
            to_min_time = str(int(ten_min_key) + 1) + '0'
            print '{0}-{1} {2:{3}s} {4}'.format(
                Col.CYAN + from_min_time, to_min_time + Col.ENDC,
                '[' + str(ten_min_count_value) + ']',
                count_width, pipe_format),

    def print_hour(self, print_hour_variables):
        """ print hour count  """

        (hour_sort, date, start_time_hour, end_time_hour,
         start_time_minute, end_time_minute, start_time_date, end_time_date,
         hour_len, ten_min_len, ten_min_enable) = print_hour_variables

        for hour_key, hour_count_value in hour_sort:
            hour_count = str(hour_count_value['count'])
            # get the hour/count width for formatting
            hour_width = (15 if '00' in start_time_minute and '00' in
                          end_time_minute else 21)
            count_width = hour_len
            # in case start time hour is incomplete
            # we want exact minutes within that hour to show
            # first hour of first date
            if (hour_key == start_time_hour and date == start_time_date and
                    not (start_time_date == end_time_date and
                         start_time_hour == end_time_hour)):
                hour_key_format = (hour_key + ':00' if start_time_minute ==
                                   '00' else '{0}:{1}-{2}:00'
                                   .format(hour_key, start_time_minute,
                                           int(hour_key) + 1))
                print '{0:{1}s}{2:^{3}s}'.format(
                    Col.GREEN + hour_key_format + Col.ENDC,
                    hour_width,
                    '[' + hour_count + ']', count_width),
            # Last hour of the last date
            elif hour_key == end_time_hour and date == end_time_date and not (
                    start_time_date == end_time_date and
                    start_time_hour == end_time_hour):
                hour_key_format = (hour_key + ':00' if end_time_minute == '00'
                                   else '{0}:00-{1}:{2}'.format(
                                       hour_key, hour_key, end_time_minute))
                print '{0:{1}s}{2:^{3}s}'.format(
                    Col.GREEN + hour_key_format + Col.ENDC,
                    hour_width,
                    '[' + hour_count + ']', count_width),
            # first/last hour of the same date
            elif (start_time_date == end_time_date and
                  start_time_hour == end_time_hour):
                hour_key_format = (hour_key + ':00' if start_time_minute ==
                                   '00' and end_time_minute == '00'
                                   else '{0}:{1}-{2}:{3}'.format(
                                       hour_key, start_time_minute,
                                       hour_key, end_time_minute))
                print '{0:{1}s}{2:^{3}s}'.format(
                    Col.GREEN + hour_key_format + Col.ENDC,
                    hour_width,
                    '[' + hour_count + ']', count_width),
            # all other hours
            else:
                hour_key_format = hour_key + ':00'
                print '{0:{1}s}{2:^{3}s}'.format(
                    Col.GREEN + hour_key_format + Col.ENDC,
                    hour_width,
                    '[' + hour_count + ']', count_width),

            if ten_min_enable:
                print '|',
                self.print_10min(hour_count_value['ten_min'], ten_min_len),

            print '\n',

    def print_date_logs(self, date_logs, start_time, end_time):
        # sorts by date
        date_logs = sorted(date_logs.items())
        # for formatting/display purposes, grab hour/ten_min string lengths
        ten_min_len, hour_len = self.print_format(date_logs)
        # If the start/end time is longer than 6 hours, then we want
        # disable the 10 min intervals for readability
        ten_min_enable = (True if 'ten_min_enable' in self.data else False)

        # avoid repetition of strtftime function
        start_time_minute = start_time.strftime('%M')
        start_time_hour = start_time.strftime('%H')
        end_time_minute = end_time.strftime('%M')
        end_time_hour = end_time.strftime('%H')
        start_time_date = start_time.date()
        end_time_date = end_time.date()

        for date_key, date_values in date_logs:
            # sort by hour
            hour_sort = sorted(
                date_values['hour'].items())
            date_count = str(date_values['count'])
            # pack hour variables in tuple
            print_hour_variables = (
                hour_sort, date_key, start_time_hour, end_time_hour,
                start_time_minute, end_time_minute,
                start_time_date, end_time_date, hour_len, ten_min_len,
                ten_min_enable)
            # The if/else statements below are to ensure accurate data is
            # printed to console if users date range is multiple days
            if start_time_date != end_time_date:
                # print date information
                # first date
                if date_key == start_time_date:
                    print '\n\n', '{0} ({1}-00:00) [{2}]'.format(
                        Col.CYAN +
                        start_time.strftime('%d/%b/%Y') + Col.ENDC,
                        start_time.strftime('%H:%M'),
                        date_count), '\n\n',
                    # print hour information per date
                    self.print_hour(print_hour_variables)
                # last date
                elif date_key == end_time_date:
                    print '\n\n', '{0} (00:00-{1}) [{2}]'.format(
                        Col.CYAN +
                        end_time.strftime('%d/%b/%Y') +
                        Col.ENDC, end_time.strftime('%H:%M'),
                        date_count), '\n\n',
                    self.print_hour(print_hour_variables)
                # Any date that is not the first or the last
                else:
                    print '\n\n', '{0} [{1}]'.format(
                        Col.CYAN +
                        datetime.strftime(
                            date_key, '%d/%b/%Y') + Col.ENDC,
                        date_count), '\n\n',
                    self.print_hour(print_hour_variables)
            # If the start time date and the end time date are both
            # the same day
            else:
                print '\n\n', '{0} ({1}-{2}) [{3}]'.format(
                    Col.CYAN +
                    start_time.strftime('%d/%b/%Y') + Col.ENDC,
                    start_time.strftime('%H:%M'),
                    end_time.strftime('%H:%M'),
                    date_count), '\n\n',
                self.print_hour(print_hour_variables)

    def print_compact(self, compact_logs, start_time, end_time, ip_no,
                      request_no, opts):
        """ print compact version of script output """

        ip_logs = compact_logs['ip']
        request_logs = compact_logs['request']
        # get total unique ip's and unique requests
        ip_count = len(ip_logs) - ip_no
        ip_total = (ip_count if ip_count > 0 else 0)
        request_count = len(request_logs) - request_no
        request_total = request_count if request_count > 0 else 0

        # print top ip's
        print
        self.display_time_range(start_time, end_time, opts, ip_no,
                                "ip's")

        for number, (ip, ip_count) in enumerate(ip_logs.most_common()[:ip_no],
                                                1):
            # check for cloudflare formatting
            ip = ip.replace(',', '')
            # check if --nogeo is enabled
            geo_information = ('' if opts.nogeo else "| [Country: {0} ({1})] "
                               "[ISP: {2}] [Hostname: {3}]".format(
                                   *self.ip_api(ip)))
            # print ip/count
            print '\n', '{0}. [{1}] {2} {3}'.format(number, ip_count,
                                                    Col.PURPLE + ip + Col.ENDC,
                                                    geo_information),
        print '\n... and {0} more unique ip\'s'.format(
            Col.LIGHTRED + str(ip_total) + Col.ENDC),
        # print top requests
        print
        print
        self.display_time_range(start_time, end_time, opts, request_no,
                                "request(s)")
        for number, (request, request_count) in enumerate(
                request_logs.most_common()[:request_no], 1):
            print '\n', '{0}. [{1}] {2}'.format(
                number, request_count, Col.PURPLE + request + Col.ENDC),
        print '\n... and {0} more unique requests'.format(
            Col.LIGHTRED + str(request_total) + Col.ENDC),
        print

    def print_ip(self, ip_logs, start_time, end_time, ip_no, request_no, opts):
        """ print all ip related data """

        print
        self.display_time_range(start_time, end_time, opts, ip_no,
                                "ip's")
        # sort per IP with highest hits
        ip_logs = sorted(ip_logs.items(), key=itemgetter(
            1), reverse=True)
        # ipmatch should only display the ip's user inputs
        if not opts.ipmatch:
            ip_logs = ip_logs[:ip_no]
        for number, (ip, ip_values) in enumerate(ip_logs, 1):
            ip = ip.replace(',', '')
            # count how many unique requests are left that aren't being shown
            request_count = len(ip_values['get_post']) - request_no
            request_total = request_count if request_count > 0 else 0
            # check if --nogeo is enabled
            geo_information = (
                '' if opts.nogeo else "| [Country: {0} ({1})] [ISP: {2}] "
                                      "[Hostname: {3}]".format(*self.ip_api(
                                                               ip)))
            # print ip/count
            print '\n', '{0}. [{1}] {2} {3}'.format(number, ip_values['count'],
                                                    Col.PURPLE + ip + Col.ENDC,
                                                    geo_information)
            # print requests per ip
            print ''.join(
                ['[{1:d}] {0}\n'.format(*kv) for kv in
                 ip_values['get_post'].most_common()[:request_no]]),
            print '... and {0} more unique requests'.format(
                Col.LIGHTRED + str(request_total) + Col.ENDC),
            # print date related hits per ip
            self.print_date_logs(ip_values['date'], start_time, end_time)

    def print_request(self, request_logs, start_time, end_time, ip_no,
                      request_no, opts):
        """ print all requests related data """

        print
        self.display_time_range(start_time, end_time, opts, request_no,
                                'request(s)')

        # sort requests per count
        request_logs = sorted(request_logs.items(),
                              key=itemgetter(1), reverse=True)

        # rmatch should only display the requests the user inputs
        if not opts.rmatch:
            request_logs = request_logs[:request_no]
        for number, (request, request_values) in enumerate(request_logs, 1):
            # count how many unique ip's are left that aren't being shown
            ip_count = len(request_values['ip']) - ip_no
            ip_total = ip_count if ip_count > 0 else 0
            print '\n---------------------------------'
            # print requests and count
            print '\n', '{0}. [{1}] {2}'.format(number,
                                                request_values['count'],
                                                Col.PURPLE + request +
                                                Col.ENDC)
            # print total ip per requests
            for ip, ip_values in request_values['ip'].most_common()[
                    :ip_no]:
                # check if --nogeo is enabled
                geo_information = (
                    '' if opts.nogeo else "| [Country: {0} ({1})] "
                                          "[ISP: {2}] [Hostname: {3}]".format(
                                              *self.ip_api(ip)))
                # print ip and count
                print '[{0}] {1} {2}'.format(ip_values, ip,
                                             geo_information)
            print '... and {0} more unique ip\'s'.format(
                Col.LIGHTRED + str(ip_total) + Col.ENDC),
            # print date related hits per request
            self.print_date_logs(request_values['date'], start_time, end_time)

    def display_time_range(self, start_time, end_time, opts, arg_no=None,
                           arg_type=None, short_version=False):
        """ Format date """

        if opts.min:
            arg_time = " (Last {0} minutes)".format(str(opts.min))
        elif opts.hour:
            arg_time = " (Last {0} hour)".format(str(opts.hour))
        elif opts.day:
            arg_time = " (Last {0} day)".format(str(opts.day))
        else:
            arg_time = ''

        if start_time.date() == end_time.date():
            time_range = ("{0} ({1} - {2})".format(
                start_time.strftime('%d/%b/%Y'),
                start_time.strftime('%H:%M'),
                end_time.strftime('%H:%M')))
        else:
            time_range = ("{0} - {1}".format(
                start_time.strftime('%d/%b/%Y %H:%M:%S'),
                end_time.strftime('%d/%b/%Y %H:%M:%S')))

        if short_version:
            return Col.LIGHTRED + time_range + Col.ENDC + arg_time

        if opts.ip or opts.request or opts.compact:
            print ("=== Top {0} {1} between {2}{3} ===".format(
                arg_no, arg_type, Col.LIGHTRED + str(time_range) + Col.ENDC,
                arg_time))
        else:  # ipmatch or rmatch
            ip_or_req = ', '.join(x for x in self.cmd_args['args'])
            print ("=== Matching {0} ({1}) between {2}{3} ===".format(
                arg_type, ip_or_req, Col.LIGHTRED + str(time_range) + Col.ENDC,
                arg_time))

    def ip_api(self, ip):
        """ Get IP information from API """

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

        return ip_country.encode('utf-8'), ip_city.encode(
            'utf-8'), ip_isp.encode('utf-8'), hostname

    def general_info(self, opts):
        print
        print Title.general_info
        print

        httpd_log_dir = (" ({0})".format(self.data['httpd_extra_info']) if
                         'httpd_extra_info' in self.data else "")
        print "✄ Webserver: {0}{1}".format(
            Col.GREEN + self.data["httpd_type"] + Col.ENDC, httpd_log_dir)

        if 'ten_min_enable' not in self.data:
            print ("✄ Ten minute interval hit count has been disabled (this "
                   "occurs when time range is 6 hours or longer). You can "
                   "manually enable/disable it with '--ten on/off' option")
        if opts.filter:
            print ("✄ You have used the --filter {0} command, note that any "
                   "hit count numbers below are strictly based on the filter "
                   "matches".format(opts.filter))
        if 'geo_limit' in self.data:
            print("✄ Your chosen number of ip's ({0}) has been reduced "
                  "to 30. This is to respect api limits. You can use "
                  "'--nogeo' option without "
                  "limitations".format(str(self.data['geo_limit'])))
        if 'default_arg' in self.cmd_args:
            print("✄ Default options detected. The follow "
                  "options have been "
                  "assumed '{0}'".format(self.cmd_args['default_arg']))

        print

    def print_select(self, print_stuff):
        log_len = len(self.data['logs'])
        num_list = list(range(1, log_len + 1))
        get_logs = self.data['logs'].keys()
        log_num = dict(zip(get_logs, num_list))

        print
        print Title.log_info
        print_stuff.print_logs_info()
        print
        print

        print Title.log_result

        for n, (log_file, size) in enumerate(self.data['logs'].iteritems(), 1):
            log = [log_file]
            ip_req_count, date_count = (
                AnalyseLogs(self.cmd_args, self.data).get_data_from_logs(log))
            logs_data = (ip_req_count, date_count)

            print Title.line
            print

            print ("{0}. Checking log file {1}/{2}... {3} ({4})".format(
                Col.BLUE + '(' + str(log_num[log_file]) + ')' + Col.ENDC,
                n, self.data['log_count'], Col.YELLOW + log_file +
                Col.ENDC, size)),
            print

            if None in self.data['time_period'] or not ip_req_count:
                print
                print "TOTAL HIT COUNT: [{0}]".format(
                    Col.LIGHTRED + '0' + Col.ENDC)
                print ("\nThere was no matching records found between "
                       "{0} - {1}.\n".format(self.data['time_period'][0]
                                             .strftime('%d/%b/%Y %H:%M:%S'),
                                             self.data['time_period'][1]
                                             .strftime('%d/%b/%Y %H:%M:%S')))
            else:
                print_stuff.print_data(logs_data)
                ip_req_count.clear()
                if not (self.cmd_args['opts'].ipmatch or
                        self.cmd_args['opts'].rmatch):
                    date_count.clear()
            # reset first/last recorde date
            del self.data['time_period'][-2:]

        # print log count
        print
        print Title.line
        print
        print_stuff.print_log_count(log_num)
        print


def print_main_header():
    print
    print Title.traffic_analyser
    print
    print 'Version: {0}'.format(Col.GREEN + 'v2.1' + Col.ENDC)
    print 'Last Updated: {0}'.format(Col.GREEN + '19/Feb/2017' +
                                     Col.ENDC)
    print 'See changelog here: {0}'.format(
        Col.GREEN + 'https://github.com/tahz7/traffic_analyser/'
                    'blob/master/CHANGELOG.md' + Col.ENDC)
    print 'Report bugs/issues to: {0}'.format(
        Col.GREEN + 'https://github.com/tahz7/traffic_analyser' + Col.ENDC)
    print


class Counter(dict):
    """Python 2.6 doesn't include Counter module, below is a converted version.

    Dict subclass for counting hashable objects.  Sometimes called a bag
    or multiset.  Elements are stored as dictionary keys and their counts
    are stored as dictionary values.

    >>> Counter('zyzygy')
    Counter({'y': 3, 'z': 2, 'g': 1})
    """

    def __init__(self, iterable=None, **kwds):
        """Create a new, empty Counter object.  And if given, count elements
        from an input iterable.  Or, initialize the count from another mapping
        of elements to their counts.

        >>> c = Counter()                     # a new, empty counter
        >>> c = Counter('gallahad')           # a new counter from an iterable
        >>> c = Counter({'a': 4, 'b': 2})     # a new counter from a mapping
        >>> c = Counter(a=4, b=2)             # a new counter from keyword args
        """

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
        """Like dict.copy() but returns a Counter instance instead of a dict.
        """
        return Counter(self)

    def __delitem__(self, elem):
        """Like dict.__delitem__() but does not raise KeyError for missing
        values.
        """
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


def main():
    # print headers
    print_main_header()
    # get arguments
    cmd_args = CmdArgs().main_args()
    # grab data
    data = GetData(cmd_args).control_flow()
    # create PrintData instance
    print_stuff = PrintData(cmd_args, data)
    # print general info
    print_stuff.general_info(cmd_args['opts'])

    if cmd_args['opts'].select or 'cycle_all' in cmd_args:
        print_stuff.print_select(print_stuff)
    else:
        print
        print Title.log_info
        print
        # grab log data
        logs_data = AnalyseLogs(cmd_args, data).grab_log_data()
        print
        print_stuff.print_logs_info()
        print
        print
        print Title.log_result
        print_stuff.print_data(logs_data)

    sys.stdout.flush()
    sys.stdout.close()
    sys.stderr.close()


if __name__ == "__main__":
    main()
