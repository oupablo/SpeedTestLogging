import os
import io
import speedtest
import datetime
import ConfigParser
import csv
import smtplib
import requests

myPath = os.path.dirname(os.path.abspath(__file__))

class SpeedTestLogging():

	def __init__(self):
	    self.config = ConfigParser.ConfigParser()
	    self.config.read(myPath + "/config.ini")
	
	
	def executeTest (self) :
	
	    s = speedtest.Speedtest()
	    # results = speedtest.SpeedtestResults()
	
	    print("Beginning speed test.  Finding best server")
	
	    s.get_best_server()
	
	    print("starting download test")
	    # start speed test for download and store the results
	    start = datetime.datetime.now()
	    download = s.download()
	    end = datetime.datetime.now()
	
	
	    
	    # find time it took and conver it to MB/s
	    dldTime = end - start
	    timeDelta = datetime.datetime.strptime(str(dldTime),'%H:%M:%S.%f')
	    seconds = float(str((timeDelta.minute * 60) + timeDelta.second) + "." + str(timeDelta.microsecond))
	    mbsDown = s.results.bytes_received / seconds * 0.000008
	
	    print(" ")
	    print (str(round(mbsDown,2)) + " MB/s download")
	    print(" ")
	
	    print ("starting upload test")
	
	    # start speed test for upload and store the results
	    start = datetime.datetime.now()
	    download = s.upload()
	    end = datetime.datetime.now()
	
	
	    # find time it took and conver it to MB/s
	    dldTime = end - start
	    timeDelta = datetime.datetime.strptime(str(dldTime),'%H:%M:%S.%f')
	    seconds = float(str((timeDelta.minute * 60) + timeDelta.second) + "." + str(timeDelta.microsecond))
	    mbsUp = s.results.bytes_sent / seconds * 0.000008
	 
	
	    print (str(round(mbsUp,2)) + " MB/s upload")
	    print(" ")
	    s.results.download = mbsDown
	    s.results.upload = mbsUp
	    self.logToInflux(s.results)
	
	def logResults (self, results) :
	    
	    try :
	        maxSize = int(self.config.get('file','size')) * 1000  #size in bytes
	    except : 
	        print ("error accessing the log file.  Ensure file titled 'config.ini' exists.")
	        raise
	    
	    logFile = myPath +"/logging/current_log.csv"
	
	    # determine if a file exists.  If not, create it.
	    if os.path.isfile(logFile) :
	        print ("accessing log file")
	    else : 
	        print ("creating log file")
	        heading = "serverID,server name,location,datetime,?,ping,download,upload"
	        open(logFile, 'ab').write(heading)
	        open(logFile, 'ab').write('\n')
	
	
	    # determine if it is too large.  If so, archive it and create a new one
	    if os.path.getsize(logFile) > maxSize :
	        print("file too large. Archiving")
	         
	        name = str(datetime.datetime.now()).replace('-','').replace(':','').replace('.','').replace(' ','')+".csv"
	        archiveFile = myPath + "/logging/archive/"+ name
	        os.rename(logFile,archiveFile)
	        heading = "serverID,server name,location,datetime,?,ping,download,upload"
	        open(logFile, 'ab').write(heading)
	        open(logFile, 'ab').write('\n')
	        
	    
	    # log data into file
	    text = results.csv()
	    try :
	        open(logFile, 'ab').write(text)
	        open(logFile,'ab').write('\n')
	        print("logging results")
	    except : 
	        print("unable to access log file")
	        
	
	
	def emailResults(self, results) :
	    
	    # make sure the config file exists and can be used without error
	    try :
	        
	        minDownload = int(self.config.get('email','mindownload'))
	        minUpload = int(self.config.get('email','minupload'))
	        enabled = self.config.get('email','enabled')
	        fromaddr = self.config.get('email','fromaddr')
	        toaddr = self.config.get('email','toaddr')
	        svr = self.config.get('email','svr')
	        euser = self.config.get('email','euser')
	        epasswd = self.config.get('email','epasswd')
	        subject = self.config.get('email','subject')
	        message = self.config.get('email','message')
	
	    except :
	        print ("error accessing the config file.  Ensure a file named 'config.ini' exists \n")
	        raise
	
	    if (enabled == "true") :  #must be enabled in the config file
	
	        if (results.download < minDownload or results.upload < minUpload) :
	            print("results below the threshold, sending notification")
	        
	            # compose the message
	            msg = "\r\n".join([
	                "From: " + fromaddr,
	                "To: " + toaddr,
	                "Subject: " + subject,
	                  "",
	                  message + " \n download = " + str(round(results.download,2)) + " \n upload = " + str(round(results.upload,2))
	                  ])
	        
	            # send the email
	            server = smtplib.SMTP(svr)
	            server.ehlo()
	            server.starttls()
	            server.login(euser,epasswd)
	            server.sendmail(fromaddr, toaddr, msg)
	            server.quit()
	    
	    else :
	        print("email function is disbaled in the config file")



	def logToInflux (self, results) :
	    
	    try :
	        enabled = self.config.get('influx','enabled')
	        influxUrl = self.config.get('influx','url')
	        influxDb = self.config.get('influx', 'db')
			
	        if(enabled) :
				   url = influxUrl + '/write?db=' + influxDb
				   data = 'download,host=home value=' + str(results.download) + '\nupload,host=home value=' + str(results.upload)
				   r = requests.post(url, data=data)
	    except : 
	        print ("error accessing the log file.  Ensure file titled 'config.ini' exists.")
	        raise
	    
	