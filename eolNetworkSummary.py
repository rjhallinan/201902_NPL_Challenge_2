#!/usr/bin/python3
# -*- coding: utf-8 -*-
""" This python script will evaluate a output from an inventory file generated by NMSaaS. It can read either
	a CSV file or an Excel sheet - it will make the determination based on the file extension. 

	Arguments:
		1) Filename (ends in either .csv or in .xlsx or .xls)
		
"""

# import modules HERE
import sys											# this allows us to analyze the arguments	
import os											# this allows us to check on the file
import xlrd											# this allows us to import an Excel file
import xlwt											# this allows us to output data to an Excel file
from xlutils.copy import copy as excel_copy_rdwt	# this allows a workbook read in to be converted to a workbook that can be written
from datetime import datetime						# useful for getting timing information and for some data translation from Excel files
from contextlib import contextmanager
import statistics									# for calculating some basic statistics

# additional information about the script
__filename__ = "eolNetworkSummary.py"
__author__ = "Robert Hallinan"
__email__ = "rhallinan@netcraftsmen.com"

#
# version history
#


"""
	20190207 - Initially creating the script
"""

@contextmanager
def open_file(path, mode):
	the_file = open(path, mode)
	yield the_file
	the_file.close()

def importFile(passedArgs):
	""" this script will determine which function to run when parsing the input file, import the data, and return a list of dictionaries
	"""

 	# assign variables
	fileInput=str(passedArgs)

	# Does the file exist?
	if not os.path.exists(fileInput):
		print("File name provided to convert does not exist. Closing now...")
		sys.exit()

	if fileInput[-4:].lower() == ".csv":
		print("File Input is: "+fileInput)
		return parseCSV(fileInput)
		
	if fileInput[-4:].lower() == ".xls" or fileInput[-5:].lower() == ".xlsx":
		print("File Input is: "+fileInput)
		return parseExcel(fileInput)
	

def parseCSV (fileInput):
	""" This function parses the CSV file and returns a list of dictionaries with the keys of each dictionary as the column header and the value specific to the row
	"""

	print("Network information will be parsed from the CSV input file....")

	#
	# define outputs
	#

	# make a list for the items in the file
	outputNetDev=[]

	# open the input file for reading
	with open_file(fileInput,'r') as netDevFile:
		netDevFileLines=netDevFile.readlines()

	# set a trigger for first line and second lines - true at start, set to False when encountered
	firstLine = True
	secondLine = True

	# declare some general info so it is accessible for multiple iterations of the for loop once initially modified
	colHeaderList=[]

	for netDev in netDevFileLines:

		# declare empty dictionary that we can add to for this item's information
		newItem={}
		
		# skip the first line
		if firstLine:
			firstLine = False
			continue

		# Read in the second line as the column headers
		if secondLine:
			colHeaderRead=netDev.split(",")
			for f in range(len(colHeaderRead)):
				colHeaderList.append((f,colHeaderRead[f].rstrip()))
			secondLine = False
			continue
		
		# still going means that this is one of the entries
		
		# get a list of the line since is CSV
		itemList=netDev.split(",")
		
		# check the line - if the length of fields is longer than the length of columns then there is a comma somewhere in the entry
		# user has to make sure that there is no comma
		if len(itemList) != len(colHeaderList):
			print("One or more items have a comma in their value string which makes this impossible to properly parse as a CSV.")
			sys.exit()

		# get the info on this item
		for pair in colHeaderList:
			newItem[pair[1]]=str(itemList[pair[0]]).rstrip()
	
		# assign the dictionary of the new item to the list
		outputNetDev.append(newItem)

	return outputNetDev

def parseExcel(fileInput):
	""" This function parses the Excel file and returns a list of dictionaries with the keys of each dictionary as the column header and the value specific to the row
	"""	
	print("Network information will be parsed from the Excel input file....")

	#
	# define outputs
	#

	# make a list for the items in the file
	outputNetDev=[]
	
	# open the Excel file
	newBook = xlrd.open_workbook(fileInput)
	
	# get a list of the sheet names, take the first one
	sheetNames=[]
	for sheet in newBook.sheets():
		sheetNames.append(sheet.name)
	sheetParse = newBook.sheet_by_name(sheetNames[0])
	# print(sheetParse)
	# print(sheetParse.nrows)
	# print(sheetParse.ncols)
	# print(sheet.row_values(1))

	# declare some general info so it is accessible for multiple iterations of the for loop once initially modified
	colHeaderList=[]
	colHeaderRead=sheet.row_values(1)
	for f in range(len(colHeaderRead)):
		colHeaderList.append((f,colHeaderRead[f].rstrip()))	

	for newDevRow in range(2,sheetParse.nrows):
	
		# declare empty dictionary that we can add to for this item's information
		newItem={}
		
		# get a list of the line since is CSV
		itemList=sheet.row_values(newDevRow)
		# print(itemList)
		
		# check the line - if the length of fields is longer than the length of columns then there is a comma somewhere in the entry
		# user has to make sure that there is no comma
		if len(itemList) != len(colHeaderList):
			print("One or more items have a comma in their value string which makes this impossible to properly parse as a CSV.")
			sys.exit()

		# get the info on this item
		for pair in colHeaderList:
			# does this need to be a datestamp translated?
			if 'Created' in pair[1] or 'End-of' in pair[1]:
				# print("testing on row: "+str(newDevRow))
				# print("value testing: "+str(itemList[pair[0]]))
				try:
					newItem[pair[1]]=str(datetime(*xlrd.xldate_as_tuple(itemList[pair[0]], newBook.datemode))).rstrip()
				except:
					# print("this didn't work")
					# must be an empty field
					newItem[pair[1]]=''
			else:
				newItem[pair[1]]=str(itemList[pair[0]]).rstrip()
	
		# assign the dictionary of the new item to the list
		outputNetDev.append(newItem)

	return outputNetDev
	
def outputExcel(listOutput,fileName,tabName):
	""" listOutput: this should be a list of lists; first item should be header file which should be written.
		fileName: Name of the Excel file to which this data should be written
		tabName: Name of the tab to which this data should be written
	"""
	
	# since before this would get called - it is assumed that the file was initialized - if the file now exists it is because another
	# tab is already in it from this script - thus check to see if the file is there - if so then just open workbook using xlrd
	if os.path.exists(fileName):
		outBook = xlrd.open_workbook(fileName)
		outBookNew = excel_copy_rdwt(outBook)
		outBook = outBookNew
	else:	
		# make the new Workbook object
		outBook = xlwt.Workbook()

	# add the sheet with the tab name specified
	thisSheet = outBook.add_sheet(tabName)
	
	# get number of columns
	numCols=len(listOutput[0])
	
	for rowNum in range(len(listOutput)):
		writeRow = thisSheet.row(rowNum)
		# print(listOutput[rowNum])
		for x in range(numCols):
			writeRow.write(x,str(listOutput[rowNum][x]))
			
	# save it to the Excel sheet at the end
	outBook.save(fileName)
	
def main(system_arguments):

	# get a python list of dictionaries by parsing the CSV file - validate that there is even an argument there using try
	try:
		networkInventory = importFile(system_arguments[1])
	except:
		print("No valid argument of a filename provided. Exiting...")
		sys.exit()

	# get a total list of all of the vendor, model, operating systems in the inventory
	totalVenDevSw = [ (x['Vendor'],x['Model'],x['Operating System'],x['Device End-of-Life']) for x in networkInventory ]

	# get a set of unique vendor/device model/sw version/eol date
	uniqueVenDevSw = set()
	for eachEntry in totalVenDevSw:
		uniqueVenDevSw.add(eachEntry)

	# get a count
	uniqueVenDevSwCt = set()
	for uniqueEntry in uniqueVenDevSw:
		ctEntry = totalVenDevSw.count(uniqueEntry)
		uniqueVenDevSwCt.add(tuple([ctEntry]+list(uniqueEntry)))
	# print("Unique vendor/device/software count: " + str(len(uniqueVenDevSwCt)))
	
	# get a total list of all of the vendor/device models in the inventory
	totalVenDev = [ (x['Vendor'],x['Model']) for x in networkInventory ]
	
	# get a set of unique vendor/device model
	uniqueVenDev = set()
	for eachEntry in totalVenDev:
		uniqueVenDev.add(eachEntry)
		
	# get a count
	uniqueVenDevCt = set()
	for uniqueEntry in uniqueVenDev:
		ctEntry = totalVenDev.count(uniqueEntry)
		uniqueVenDevCt.add(tuple([ctEntry]+list(uniqueEntry)))
	print("Unique vendor/device count: " + str(len(uniqueVenDevCt)))		
	
	# TESTING 
	# testComp=[ x for x in uniqueVenDevCt if x[0]==1 ]
	# testComp.sort()
	# # print(testComp)
	
	# Define a list of the output
	ls_uniqueVenDevSwCt=list(uniqueVenDevSwCt)
	
	# define the output filename and remove the file if it currently exists
	outputFileName = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "_networksummary.xls"
	print("Output filename is: " + outputFileName)
	print("The file will have three tabs: \n\t1) Data sorted by count\n\t2) Data sorted by End-of-Service date\n\t3) Device count statistics.")
	# Does the file exist?
	if os.path.exists(outputFileName):
		# delete the file
		try:
			os.remove(outputFileName)
		except:
			print("Output file exists but can't delete it right now. Exiting....")
			sys.exit()
	
	# define the list for the tab sorted by device count, vendor, and model
	output_CountVendorModelSort=list()
	output_CountVendorModelSort.append(['Count','Vendor','Model','Software','End of Service'])
	for uniqueDev in sorted(ls_uniqueVenDevSwCt, key=lambda x: (x[0],x[1],x[2])):
		output_CountVendorModelSort.append(list(uniqueDev))
	# print(output_CountVendorModelSort)
	outputExcel(output_CountVendorModelSort,outputFileName,"sort-by-count")
	
	# define the list for the tab sorted by end of service date; this loop is done twice so that devices with no declared
	# end of service date are not sorted as being before devices that have one specified
	output_EosdateVendorModelSort=list()
	output_EosdateVendorModelSort.append(['Count','Vendor','Model','Software','End of Service'])
	for uniqueDev in sorted([x for x in ls_uniqueVenDevSwCt if x[4] is not '' ], key=lambda x: (x[4],x[1],x[2])):
		output_EosdateVendorModelSort.append(list(uniqueDev))
	for uniqueDev in sorted([x for x in ls_uniqueVenDevSwCt if x[4] is '' ], key=lambda x: (x[4],x[1],x[2])):
		output_EosdateVendorModelSort.append(list(uniqueDev))
	# print(output_EosdateVendorModelSort
	outputExcel(output_EosdateVendorModelSort,outputFileName,"sort-by-eos")
	
	# get a list of the counts of devices
	listCounts = [ x[0] for x in ls_uniqueVenDevSwCt ]
	# calculate some basic statistics on the counts
	countMean = round(statistics.mean(listCounts),2)
	countMedian = round(statistics.median(listCounts),2)
	countStdDev = round(statistics.stdev(listCounts),2)

	# figure out what device types have multiple operating systems and provide info to the user
	devMultipleOS=0
	for eachDevType in list(uniqueVenDev):
		# print(list(eachDevType))
		if len([x for x in ls_uniqueVenDevSwCt if x[1] == eachDevType[0] and x[2] == eachDevType[1]]) > 1:
			devMultipleOS += 1	

	# output the calculated statistics in another excel tab
	statInfo = []
	statInfo.append(['Unique Vendor/Device/Software combinations',len(uniqueVenDevSwCt)])
	statInfo.append(['Unique Vendor/Device combinations',len(uniqueVenDevCt)])
	statInfo.append(['Device Count Mean',countMean])
	statInfo.append(['Device Count Median',countMedian])
	statInfo.append(['Device Count Standard Deviation',countStdDev])
	statInfo.append(['Number of device types with > 1 OS',devMultipleOS])
	outputExcel(statInfo,outputFileName,"device-statistics")
	
if __name__ == "__main__":

	# this gets run if the script is called by itself from the command line
	main(sys.argv)