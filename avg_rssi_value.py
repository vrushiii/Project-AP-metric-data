
#-----------------script to give average RSSI values---------------------------#

import requests
import urllib3
import os, sys, json
from collections import OrderedDict 
from datetime import datetime, timedelta


urllib3.disable_warnings()

#Org id: Staging
#ORG_ID = '<add your org id here>'
#Org id: Production
#ORG_ID = '<add your org id here>'

#API url
#API_URL = 'https://api.mistsys.com/api/v1'
#API_URL = 'https://api.mist.com/api/v1'

#Staging API Token
#API_TOKEN = '<enter your staging token here>'
#Prod API Token
#API_TOKEN = '<enter your Prod token here>'

SECONDS_PER_DAY = 86400


#source code starts from here

class Project(object):
	def __init__(self, token=''):
		self.session = requests.Session()
		self.header = {'Content-Type': 'application/json', 'Authorization': 'Token ' + token}

	#-----method to get all sites id in that ORG-----#
	def get_Sites(self):
		site_id_list=[]
		session = self.session
		header = self.header
		url = '{}/orgs/{}/sites'.format(API_URL, ORG_ID)
		response = session.get(url, headers=header)
	   
		if response.status_code != 200:
			print('Failed to GET')
			print('\tResponse: {} ({})'.format(response.text, response.status_code))
		data=json.loads(response.text)
		#print(data)
		for item in data:
			site_id_list.append(item['id']) 
		#print('site_id_list:',site_id_list)
		return(site_id_list)

	#-----method to get all device id of the site requested for-----#
	def site_device(self,site_id):
		device_list=[]
		session = self.session
		header = self.header
		url = '{}/sites/{}/stats/devices'.format(API_URL,site_id)
		response = session.get(url, headers=header)

		if response.status_code != 200:
			print('Failed to GET')
			print('\tResponse: {} ({})'.format(response.text, response.status_code))
		data=json.loads(response.text)

		for x in data:
			for value in x:
				if value == 'id':
					device_list.append(x[value])
		#print("device list in method:",device_list)			
		return (device_list)

	#-----method to get AP metric's rssi value with site id and device id requested for-----#		
	def AP_metric(self,data,days_considered,uptime_considered):
		data_dict={}
		session = self.session
		header = self.header
		for key,values in data.items():
			avg_rssi_per_device_per_site=[]
			for item in values:
				if item is not None:
					#print("start:",datetime.now()+timedelta(days=-7))
					#print("end:",datetime.now())
					#print("days considered for calculation:", days_considered)
					url = '{}/sites/{}/insights/ap/{}/stats?start={}&end={}&interval=3600&metrics=rssi'.format(API_URL,key,item,datetime.now()+timedelta(days=-(days_considered)),datetime.now())
					response = session.get(url, headers=header)
						
					if response.status_code != 200:
						print('Failed to GET')
						print('\tResponse: {} ({})'.format(response.text, response.status_code))
			
					(data)=json.loads(response.text)
					#print("-------device id--------",item,"---site id-----",key,"avg_rssi_per_device:",data['avg_rssi'], "length:",len(data['avg_rssi']))
					avg_list=[x for x in data['avg_rssi'] if x is not None]    #remove "None" from the list
					avg_list_per_device_per_site=sum(avg_list)/len(data['avg_rssi'])
					#print("avg_list_per_device:",avg_list_per_device_per_site)
					bool_value = self.get_uptime(key,days_considered,uptime_considered)       #check to see if uptime is more than 7 days
					#print("should AP be considered for the cal? ", bool_value)
					if bool_value is True:                                   #if 'True', append that value of avg
						avg_rssi_per_device_per_site.append(avg_list_per_device_per_site)
					else:
						avg_rssi_per_device_per_site.append(None)            #if 'False', do not append the avg value

						
				#print("site id:",key,"avg_rssi_per_device_per_site",avg_list_per_device_per_site)
			#print("site id",key,"avggggggggg",avg_rssi_per_device_per_site)
			data_dict[key]=avg_rssi_per_device_per_site
		#print("dictionary",data_dict)
		return(data_dict)

	#-----method to calculate averages-----#
	def average_cal(self,data_list):
		ap_list=[x for x in data_list if x is not None]                 #remove "None" from the list
		if len(ap_list) == 0:
			return (ap_list)
		else:
			total=sum(ap_list)
			length=len(ap_list)
			return (total/length)                                      #return the average calculated

	#-----method to see if AP to be considered by seeing the 'uptime' value-----#
	def get_uptime(self,site_id,days_considered,uptime_considered):
		session = self.session
		header = self.header
		url = '{}/sites/{}/stats/devices'.format(API_URL,site_id)
		response = session.get(url, headers=header)
		if response.status_code != 200:
			print('Failed to GET')
			print('\tResponse: {} ({})'.format(response.text, response.status_code))
		data=json.loads(response.text)
		days = days_considered * SECONDS_PER_DAY       #convert number of days in seconds per day
		if uptime_considered == True:
			for temp in data:
				for key in temp:
					if key == 'uptime':                    #get "uptime" for each AP 
						uptime_value=temp['uptime']
						#print(uptime_value)
						if temp['uptime'] < days:          #604800 sec = 7 days
							return False                   #AP not considered
						else: 
							return True                    #AP considered
		else:
			return True

					

			
#------main------#
def main():
	
	device_id=[]
	
	data={}

	

	global ORG_ID, API_URL, API_TOKEN

	ORG_ID=str(input("Please enter ORG id: "))
	print("\n")
	API_URL=str(input("Please enter API url: "))
	print("\n")
	API_TOKEN=str(input("Please enter API Token: "))
	print("\n")

	
	days_considered = int(input("Enter number of days for data calculation: "))    #input for calculation for timerange 

	print("Would you like to see the data as per AP uptime??")
	user_response = str(input("Please enter 'yes' or 'no' : ")).lower()

	if user_response == 'yes':
		uptime_considered = True                 #AP with uptime less than 7 days not considered
		
		print("\n")
	else: 
		uptime_considered = False                #display all AP 


	#create object for class 'Project'
	site_object=Project(API_TOKEN)


	#site id list is gathered here
	site_id_list=site_object.get_Sites()
	print("entire site id list---------------->:",site_id_list)

	print("\n")

	#sending site id as parameter to get respective device id
	for item in site_id_list:
		(device_id).append(site_object.site_device(item))
	
	print("entire device id list--------------->:",device_id)

	print("\n")

	#binding site id and device id in a dictionary
	data = dict(zip(site_id_list,device_id))
	print("site id with device id ----------------->:",data)

	print("\n")

	#getting AP metric stats by sending site id and device id
	data_list=(site_object.AP_metric(data,days_considered,uptime_considered))
	#print ("dictionary returned: ",data_list)
	
	#mapping the avg with site id 
	for item in site_id_list:
		temp=site_object.average_cal(data_list[item])
		data_list[item]=temp
	
	#print ("final data",data_list)

	avg_list_data = sorted(data_list.items(), key =lambda t:0 if type(t[1]) == list else t[1])
	print("\n")
	print("-------------------------------------------------------------------------------------------")
	print("\n")
	print("Data calculated for last", days_considered, "days starting today")
	print("\n")
	print("sorted list with site id and avg rssi values: ", avg_list_data)
	print("\n")
	print("-------------------------------------------------------------------------------------------")
	

main()
