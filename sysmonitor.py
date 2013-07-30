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
from sys import platform as _platform

if _platform == u"win32":
    import wmi
elif _platform == u"linux" or _platform == u"linux2":
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
        
        
        #get CPU temperature (depending on platform)
        templist=[]
        if _platform == u"win32":
            #this is old code using standard wmi provided by windows
            
#             try:
#                 w = wmi.WMI(namespace="root\wmi",privileges=["Security"])
#             
#                 temperature_infos = w.MSAcpi_ThermalZoneTemperature()
#                 for idx,temp_cpu in enumerate(temperature_infos):
#                     temp = {"Sensor":idx,"Temperature":temp_cpu.CurrentTemperature/10-273}
#                     templist.append(temp)
#             except wmi.x_access_denied:
#                 print 'Cannot get CPU temperature, please run as admin!'
#             except wmi.x_wmi:
#                 print 'Error grabbing CPU temperature. Your machine might not be supported.'
            
            try:
                w = wmi.WMI(namespace="root\OpenHardwareMonitor")
                temperature_infos = w.Sensor()
                for sensor in temperature_infos:
                    if sensor.SensorType==u'Temperature':
                        temp = {u"Sensor":sensor.Name,u"Temperature":sensor.Value}
                        templist.append(temp)
            except wmi.x_wmi, x:
                print u'WMI Exception. Is Open Hardware Monitor running?'
                print u'Exception number', x.com_error.hresult
        
        
        if _platform == u"linux" or _platform == u"linux2":
            try:
                for chip in sensors.iter_detected_chips():
                    #print '%s at %s' % (chip, chip.adapter_name)
                    for feature in chip:
                        #print '  %s: %.2f' % (feature.label, feature.get_value())
                        if feature.label.find(u'Temp'):
                            temp = {u"Sensor":str(chip)+" "+feature.label,u"Temperature":feature.get_value()}
                            templist.append(temp)
            finally:
                sensors.cleanup()
        #print json.dumps(templist)
        
        
        #get CPU time
        cpu = psutil.cpu_times_percent()
        cpudict = {u"User":int(cpu.user),u"System":int(cpu.system),u"Idle":int(cpu.idle)}
        #print json.dumps(cpudict)
        
        
        #get disk information
        hdlist=[]
        for part in psutil.disk_partitions(all=False):
            if not(os.name==u'nt' and (u'cdrom' in part.opts or u'removable' in part.opts)):
                usage=psutil.disk_usage(part.mountpoint)
                hd = {u"Mount":part.mountpoint,u"Free":bytes2human(usage.free),u"Used":bytes2human(usage.used),u"Total":bytes2human(usage.total)}
                hdlist.append(hd)
        #print json.dumps(hdlist)
            
            
        #get memory usage
        physmem = psutil.virtual_memory()
        physmemdict = {u"Available":bytes2human(physmem.available),u"Used":bytes2human(physmem.used),u"Free":bytes2human(physmem.free),u"Total":bytes2human(physmem.total)}
        #print json.dumps(physmemdict)
        
        
        #get network usage
        nw = psutil.net_io_counters()
        nwdict = {u"Sent":bytes2human(nw.bytes_sent),u"Recv":bytes2human(nw.bytes_recv),u"PacketsSent":bytes2human(nw.packets_sent),u"PacketsRecv":bytes2human(nw.packets_recv)}
        #print json.dumps(nwdict)
        
        
        #get disk throughput
        disktp = psutil.disk_io_counters()
        disktpdict = {u"TimesRead":disktp.read_count,u"TimesWrite":disktp.write_count,u"BytesRead":bytes2human(disktp.read_bytes),u"BytesWrite":bytes2human(disktp.write_bytes)}
        #print json.dumps(disktpdict)
        
        
        #combine all info in a dict
        allinfo = {u"Temp":templist,u"CPU":cpudict,u"HDD":hdlist,u"Memory":physmemdict,u"Network":nwdict,u"DiskThroughput":disktpdict}
        
        
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