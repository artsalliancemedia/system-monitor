## System monitor

This utility reads the systems CPU utilisation, disk space, memory usage, network usage as well as disk throughput (using psutil).
The system temps are also read (Windows: using WMI from Open Hardware Monitor, Linux: using pysensors). 
These metrics are grabbed periodically and reported to another service with HTTP POST, formatted as json. 
Where it sends to and how often it does is configurable in a settings.json file.

This utility works in linux/unix & windows.

### Installation

Python 2.6.x is required, pip is useful or look in the requirements.txt to grab the dependencies.

`pip install -r requirements.txt`

For Linux please comment the WMI line and uncomment the pysensors line.
For Windows download and run Open Hardware Monitor: http://openhardwaremonitor.org/

### Next Steps
Take a copy of `settings-template.json`, name it `settings.json` and change the settings to your needs.

To start the app, run:
Start Open Hardware Monitor (Windows only)
`python sysmonitor.py`