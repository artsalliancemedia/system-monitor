'''
Created on 24 Jul 2013

@author: Tobias Fischer
'''

import psutil
import os
#import datetime
import json
import time
import urllib2
import contextlib
from sys import platform

if platform == u"win32":
    import wmi
elif platform == u"linux" or platform == u"linux2":
    import sensors
    sensors.init()
    

def bytes2human(n):
    # http://code.activestate.com/recipes/578019
    # >>> bytes2human(10000)
    # '9.8K'
    # >>> bytes2human(100001221)
    # '95.4M'
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i+1)*10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return u'%.1f%s' % (value, s)
    return u"%sB" % n

def main():
    while True:
        #read config file
        config = json.load(open(os.path.join(os.path.dirname(__file__), u'settings.json'), 'r'))
        
        
        #get cpu_psutil temperature (depending on platform)
        sensor_temperatures=[]
        if platform == u"win32":
            #this is old code using standard wmi provided by windows
            
#             try:
#                 w = wmi.WMI(namespace="root\wmi",privileges=["Security"])
#             
#                 temperature_infos = w.MSAcpi_ThermalZoneTemperature()
#                 for idx,temp_cpu_psutil in enumerate(temperature_infos):
#                     temp = {"Sensor":idx,"Temperature":temp_cpu_psutil.CurrentTemperature/10-273}
#                     sensor_temperatures.append(temp)
#             except wmi.x_access_denied:
#                 print 'Cannot get cpu_psutil temperature, please run as admin!'
#             except wmi.x_wmi:
#                 print 'Error grabbing cpu_psutil temperature. Your machine might not be supported.'
            
            try:
                w = wmi.WMI(namespace="root\OpenHardwareMonitor")
                temperature_infos = w.Sensor()
                for sensor in temperature_infos:
                    if sensor.SensorType==u'Temperature':
                        temp = {u"Sensor":sensor.Name,u"Temperature":sensor.Value}
                        sensor_temperatures.append(temp)
            except wmi.x_wmi, x:
                print u'WMI Exception. Is Open Hardware Monitor running?'
                print u'Exception number', x.com_error.hresult
        
        
        if platform == u"linux" or platform == u"linux2":
            try:
                for chip in sensors.iter_detected_chips():
                    #print '%s at %s' % (chip, chip.adapter_name)
                    for feature in chip:
                        #print '  %s: %.2f' % (feature.label, feature.get_value())
                        if feature.label.find(u'Temp'):
                            temp = {u"Sensor":str(chip)+" "+feature.label,u"Temperature":feature.get_value()}
                            sensor_temperatures.append(temp)
            finally:
                sensors.cleanup()
        #print json.dumps(sensor_temperatures)
        
        
        #get cpu_psutil time
        cpu_psutil = psutil.cpu_times_percent()
        cpu = {u"User":int(cpu_psutil.user),u"System":int(cpu_psutil.system),u"Idle":int(cpu_psutil.idle)}
        #print json.dumps(cpu)
        
        
        #get disk information
        hard_drives=[]
        for part in psutil.disk_partitions(all=False):
            if not(os.name==u'nt' and (u'cdrom' in part.opts or u'removable' in part.opts)):
                usage=psutil.disk_usage(part.mountpoint)
                hd = {u"Mount":part.mountpoint,u"Free":bytes2human(usage.free),u"Used":bytes2human(usage.used),u"Total":bytes2human(usage.total)}
                hard_drives.append(hd)
        #print json.dumps(hard_drives)
            
            
        #get memory usage
        physmem_psutil = psutil.virtual_memory()
        physmem = {u"Available":bytes2human(physmem_psutil.available),u"Used":bytes2human(physmem_psutil.used),u"Free":bytes2human(physmem_psutil.free),u"Total":bytes2human(physmem_psutil.total)}
        #print json.dumps(physmem)
        
        
        #get network usage
        nw_psutil = psutil.net_io_counters()
        nw = {u"Sent":bytes2human(nw_psutil.bytes_sent),u"Recv":bytes2human(nw_psutil.bytes_recv),u"PacketsSent":bytes2human(nw_psutil.packets_sent),u"PacketsRecv":bytes2human(nw_psutil.packets_recv)}
        #print json.dumps(nw)
        
        
        #get disk throughput
        disk_tp_psutil = psutil.disk_io_counters()
        disk_tp = {u"TimesRead":disk_tp_psutil.read_count,u"TimesWrite":disk_tp_psutil.write_count,u"BytesRead":bytes2human(disk_tp_psutil.read_bytes),u"BytesWrite":bytes2human(disk_tp_psutil.write_bytes)}
        #print json.dumps(disk_tpdict)
        
        
        #combine all info in a dict
        allinfo = {u"Temp":sensor_temperatures,u"CPU":cpu,u"HDD":hard_drives,u"Memory":physmem,u"Network":nw,u"DiskThroughput":disk_tp}
        
        
        #dump it into JSON
        data = json.dumps(allinfo, sort_keys=True, indent=4, separators=(',', ': '))
        #send data to URL configured in configuration file
        #important: set correct content type!
        req = urllib2.Request(config[u"url"], data, {u'Content-Type': u'application/json'})
        #get and print response
        with contextlib.closing(urllib2.urlopen(req)) as f:
            response = f.read()
            print response
        
        #wait delay time before entering next loop
        time.sleep(config[u"delay"])
        
if __name__ == '__main__':
    main()