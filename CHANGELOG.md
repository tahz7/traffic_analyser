#### 19/Feb/2017 ####

--Bug Fixes--

- Python 2.6 doesn't support exit for gzip files for the with statement. http://www.python.org/dev/peps/pep-0343/ Updated this to open gzip files without the with statement.

#### 01/Feb/2017 ####

--Changes/Additions--

- Changed the display interface to try and make it more user friendly
- Log files that were last modified before the user input start time are now
ignored. Same for empty log files.
- A quick summary of the Log files are now displayed at the very top (or in
some scenarios bottom) and ordered by hit count. This enables the user to see
which website is taking the brunt of the traffic.
- Added 'Total hit count' display.
- Added default arguments. eg ) You can now run the script without any args or
with minimal args such as '--min 15' or '--select --min 15'
- Added 'Earliest and Last record found' display. This indicates the first
record matching record and the last matching record within the time-range
specified. Useful to see if you're potentially missing data tthrough
log-rotate, networking issue or something else.
- Added option where you can input a single date. eg ) '--date 18/Jan/2017'
- Added ability to manually enable or disable the 10 min interval hit count
using '--ten on/off'.
- Added ability to read gzip (compressed) files
- Added command line option to cycle through all opened log files for nginx or
apache. Now you can do something like '--select all' or choose that option
when prompted in '--select'.
- The script will now detect if both nginx and apache are running. It will
choose to check open log files for whichever service is running on port 80
- Added cycle option for the --log command. Something like this '--log cycle
/path/to/log/*access*' will now display data per log file, rather than
combined.
- Removed '--dir' option, no point when you can just do this --log
/path/to/dir/*
- When 10 min interval data is disabled, then the script will not bother
collecting this data within memory.
- Removed '--ignored' option, the script now functions the same as grep does.
Only collects data that matches regex.
- Removed prompting per log file for the '--select' option. It's not necassary
to have the user prompt to check each log file.
- Should be sligtly faster in processing logs than before.

--Bug Fixes--

- '--select' should now iterate log files properly.
- Fixed I/O error for when apache hits max clients
