#------------------------------------
# Name: wai.py
# Description: Calculate final Walkabity index
# Author: Tomas KRIVKA, Department of Geoinformatics, Faculty of Science, Palacky University Olomouc, 2011
# Update to ArcMap v10: Jan KREJSA, Department of Geoinformatics, Faculty of Science, Palacky University Olomouc, 2018
#------------------------------------

#Import modules, make geoprocesor, set workspace...
#--------------------------------------------------
import arcpy, sys, math, os, tempfile, locale
from arcpy import env
directory_name=tempfile.mkdtemp()
print directory_name
env.workspace=directory_name
env.overwriteoutput=1

#Input
#-----
arcpy.AddMessage(" ")
arcpy.AddMessage("Input")

# Urban Areas in SHP
inobv=arcpy.GetParameterAsText(0)
# Connectivity index deciles field
confld=arcpy.GetParameterAsText(1)
# Entropy index deciles field
entfld=arcpy.GetParameterAsText(2)
# FAR index deciles field
farfld=arcpy.GetParameterAsText(3)
# Household density index deciles field
hsdfld=arcpy.GetParameterAsText(4)

#Check if inputs are correct
#---------------------------
arcpy.AddMessage("Check if inputs are correct")
#0
msg= "This tool was designed to work with Polygon Feature Classes... Please set Polygon feature class in first parametr."
description = arcpy.Describe(inobv)
if description.ShapeType<>"Polygon":
    raise arcpy.AddError(msg)
#1
#2
#3
#4

#Calculating Walkability index
#-----------------------------
arcpy.AddMessage("Calculating Walkability index")
arcpy.AddField_management(inobv, "WAI", "double")
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    thecon=row.getValue(confld)
    theent=row.getValue(entfld)
    thefar=row.getValue(farfld)
    thehsd=row.getValue(hsdfld)
    thewai=(2*thecon)+theent+thefar+thehsd
    row.setValue("WAI",thewai)
    rows.updateRow(row)
    row = rows.next()
del row, rows

#Deciles
#-------
arcpy.AddMessage("Deciles")
list_dec=[]
rows = arcpy.SearchCursor(inobv)
row = rows.next()
while row:
    thevalue=row.getValue("WAI")
    list_dec.append(thevalue)
    row = rows.next()
del row, rows

arcpy.AddField_management(inobv, "wai_dec", "double")
list_dec.sort()
print list_dec
thelen=len(list_dec)
p_dec=thelen/float(10)
print p_dec
print thelen, p_dec
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    thevalue=row.getValue("WAI")
    order=list_dec.index(thevalue)
    k=1
    while 1:
        k_dec=k*p_dec
        print k, k_dec
        if order<k_dec:
            print "ano"
            row.setValue("wai_dec", k)
            rows.updateRow(row)
            break
        k=k+1
    row = rows.next()
del row, rows
os.removedirs(directory_name)
env.workspace=None

arcpy.AddMessage(" ")