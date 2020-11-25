#------------------------------------
# Name: far.py
# Description: Calculate FAR (floor area ratio) index. It means rate of commercial objects (point layer) per area of commercial class in landuse layer (polygon layer).
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
arcpy.toolbox = "management", "analysis", "stat"

#Input
#-----
arcpy.AddMessage(" ")
arcpy.AddMessage("Input")

# Urban Areas data in polygon SHP
inobv=arcpy.GetParameterAsText(0)
# Landuse data in polygon SHP
inlu=arcpy.GetParameterAsText(1)
# Landuse class field
lufld=arcpy.GetParameterAsText(2)
# Commercial value from Landuse
thevalue_s=arcpy.GetParameterAsText(3)
# Commercial buildings data in point SHP
inpnt=arcpy.GetParameterAsText(4)
# Area field from Commercial buildings
areapntfld=arcpy.GetParameterAsText(5)

thevalue=thevalue_s.upper()
itsplg="itsplg.shp"
itspnt="itspnt.shp"

#Check if inputs are correct
#---------------------------
arcpy.AddMessage("Check if inputs are correct")
#0
msg= "This tool was designed to work with Polygon Feature Classes... Please set Polygon feature class in first parametr."
description = arcpy.Describe(inobv)
print description.ShapeType
if description.ShapeType<>"Polygon":
    raise arcpy.AddError(msg)
#1
msg= "This tool was designed to work with Polygon Feature Classes... Please set Polygon feature class in second parametr."
description = arcpy.Describe(inlu)
print description.ShapeType
if description.ShapeType<>"Polygon":
    raise arcpy.AddError(msg)
#2
#3
#4
msg= "This tool was designed to work with Point Feature Classes... Please set Point feature class in fifth parametr."
description = arcpy.Describe(inpnt)
if description.ShapeType<>"Point":
    raise arcpy.AddError(msg)
#5

#Calculating id-key in input layer of urban areas
#------------------------------------------------
arcpy.AddMessage("Calculating id-key in input layer of urban areas")
arcpy.AddField_management(inobv, "idplgfld", "short")
i=0
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    row.setValue("idplgfld",i)
    rows.updateRow(row)
    i=i+1
    rows.updateRow(row)
    row = rows.next()
del row, rows

#Intersect input landuse layer and layer of urban areas
#------------------------------------------------------
arcpy.AddMessage("Intersect input landuse and layer of urban areas")
arcpy.Intersect_analysis(inobv+"; "+inlu, itsplg)
fields = arcpy.ListFields(itsplg)
for field in fields:
    namefld=field.name
    if namefld=="area":
        arcpy.DeleteField_management(itsplg, "area")
arcpy.AddField_management(itsplg, "area", "double")
desc = arcpy.Describe(itsplg)
shapefieldname = desc.ShapeFieldName

rows = arcpy.UpdateCursor(itsplg)
row = rows.next()
while row:
    geometry = row.getValue(shapefieldname)
    thearea=geometry.area
    row.setValue("area",thearea)
    rows.updateRow(row)
    row = rows.next()
del row, rows

#Summing areas used for commerce in every urban area (known from polygon layer)
#------------------------------------------------------------------------------
arcpy.AddMessage("Summing areas used for commerce in every urban area (known from polygon layer)")
rows = arcpy.SearchCursor(itsplg)
row = rows.next()
listid=[]
listar=[]
while row:
    theidplg=row.getValue("idplgfld")
    plocha = row.getValue("area")
    thelu=row.getValue(lufld)
    theln=len(thelu)
    area_div=plocha/theln
    for char in thelu:
        if char==thevalue:
            if theidplg not in listid:
                listid.append(theidplg)
                listar.append(area_div)
            else:
                poradi=listid.index(theidplg)
                listar[poradi]=listar[poradi]+area_div
    row = rows.next()
del row, rows
print listid
print listar

#Filling field by areas used for commerce (known from polygon layer) to input layer of urban areas
#-------------------------------------------------------------------------------------------------
arcpy.AddMessage("Filling field by areas used for commerce (known from polygon layer) to input layer of urban areas")
arcpy.AddField_management(inobv, "area_lu", "double")
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    theid=row.getValue("idplgfld")
    if theid in listid:
        order=listid.index(theid)
        thearea=listar[order]
        row.setValue("area_lu", thearea)
        rows.updateRow(row)
    else:
        row.setValue("area_lu","0")
        rows.updateRow(row)
    row = rows.next()
del row, rows

#Summming areas used for commerce in every urban area (known from point layer)
#-----------------------------------------------------------------------------
arcpy.AddMessage("Summming areas used for commerce in every urban area (known from point layer)")
listid=[]
list_area=[]
arcpy.Intersect_analysis(inpnt+";"+inobv, itspnt, "ALL")
rows = arcpy.UpdateCursor(itspnt)
row = rows.next()
while row:
    thearea=row.getValue(areapntfld)
    theid=row.getValue("idplgfld")
    if theid not in listid:
        listid.append(theid)
        list_area.append(thearea)
    else:
        order=listid.index(theid)
        list_area[order]=list_area[order]+thearea
    row = rows.next()
del row, rows

#Filling field by areas used for commerce (known from point layer) to input layer of urban areas
#-----------------------------------------------------------------------------------------------
arcpy.AddMessage("Filling field of areas used for commerce (known from point layer) to input layer of urban areas")
arcpy.AddField_management(inobv, "area_obch", "double")
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    theid=row.getValue("idplgfld")
    if theid in listid:
        order=listid.index(theid)
        print order
        thearea=list_area[order]
        row.setValue("area_obch", thearea)
        rows.updateRow(row)
    else:
        row.setValue("area_obch","0")
        rows.updateRow(row)
    row = rows.next()
del row, rows

#Calculating FAR index
#---------------------
arcpy.AddMessage("Calculating FAR index")
arcpy.AddField_management(inobv, "far", "double")
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    theareaobch=row.getValue("area_obch")
    thearealu=row.getValue("area_lu")
    if thearealu==0:
        row.setValue("far", "0")
    else:
        thefar=theareaobch/thearealu
        row.setValue("far", thefar)
    rows.updateRow(row)
    row=rows.next()
del row, rows

#Z-score
#-------
arcpy.AddMessage("Z-score")
arcpy.Statistics_analysis(inobv, "stat.dbf","far mean; far std")
rows = arcpy.SearchCursor("stat.dbf")
row = rows.next()
themean=row.getValue("mean_far")
thestd=row.getValue("std_far")
print themean, thestd
arcpy.AddField_management(inobv, "far_z_sc", "double")
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    thefar=row.getValue("far")
    thefar_st=(thefar-themean)/thestd
    row.setValue("far_z_sc", thefar_st)
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
    thevalue=row.getValue("far_z_sc")
    list_dec.append(thevalue)
    row = rows.next()
del row, rows

arcpy.AddField_management(inobv, "far_dec", "double")
list_dec.sort()
thelen=len(list_dec)
p_dec=thelen/float(10)
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    thevalue=row.getValue("far_z_sc")
    order=list_dec.index(thevalue)
    k=1
    while 1:
        k_dec=k*p_dec
        if order<k_dec:
            row.setValue("far_dec", k)
            rows.updateRow(row)
            break
        k=k+1
    row = rows.next()
del row, rows

arcpy.Delete_management(itsplg)
arcpy.Delete_management(itspnt)
arcpy.DeleteField_management(inobv, "idplgfld")
arcpy.DeleteField_management(inobv, "area_lu")
arcpy.DeleteField_management(inobv, "area_obch")
arcpy.Delete_management("stat.dbf")
os.removedirs(directory_name)

arcpy.AddMessage(" ")