#------------------------------------
# Name: hdens.py
# Description: Calculate ratio of number of households and areas used for living in every urban area
# Author: Tomas KRIVKA, Department of Geoinformatics, Faculty of Science, Palacky University Olomouc, 2011
# Update to ArcMap v10: Jan KREJSA, Department of Geoinformatics, Faculty of Science, Palacky University Olomouc, 2018
#------------------------------------

#Import modules, make geoprocesor, set workspace...
#--------------------------------------------------
import arcpy, os, math, tempfile, locale
from arcpy import env
directory_name=tempfile.mkdtemp()
print directory_name
env.workspace=directory_name
env.overwriteoutput=1

#Input
#-----
arcpy.AddMessage(" ")
arcpy.AddMessage("Input")

# Urban Areas in polygon SHP
inobv=arcpy.GetParameterAsText(0)
# Number of Household field from Urban Areas
housefld=arcpy.GetParameterAsText(1)
# Landuse data in lines SHP
inlu=arcpy.GetParameterAsText(2)
# landuse class field
lufld=arcpy.GetParameterAsText(3)
# Living value from landuse
thevalue_l=arcpy.GetParameterAsText(4)

thevalue=thevalue_l.upper()
itsplg="itsplg.shp"

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
#2
msg= "This tool was designed to work with Polygon Feature Classes... Please set Polygon feature class in third parametr."
description = arcpy.Describe(inlu)
print description.ShapeType
if description.ShapeType<>"Polygon":
    raise arcpy.AddError(msg)
#3
#4
arcpy.AddMessage(" ")
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

#Summing areas used for living (from polygon landuse layer) in every Urban Area
#------------------------------------------------------------------------------
arcpy.AddMessage("Summing areas used for living (from polygon landuse layer) in every Urban Area")
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

#Calculating density of households in every urban area
#-----------------------------------------------------
arcpy.AddMessage("Calculating density of households in every urban area")
arcpy.AddField_management(inobv, "hdens", "double")
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    theid=row.getValue("idplgfld")
    if theid in listid:
        thenum=row.getValue(housefld)
        order=listid.index(theid)
        thearea=listar[order]
        if thearea==0:
            row.setValue("hdens","0")
            rows.updateRow(row)
        else:
            dens=thenum/thearea
            row.setValue("hdens", dens)
            rows.updateRow(row)
    else:
        row.setValue("hdens","0")
        rows.updateRow(row)
    row = rows.next()
del row, rows

#Z-score
#-------
arcpy.AddMessage("Z-score")
arcpy.Statistics_analysis(inobv, "stat.dbf","hdens mean; hdens std")

rows = arcpy.SearchCursor("stat.dbf")
row = rows.next()

themean=row.getValue("mean_hdens")
thestd=row.getValue("std_hdens")
print themean, thestd

arcpy.AddField_management(inobv, "hdens_z_sc", "double")
rows = arcpy.UpdateCursor(inobv)
row = rows.next()

while row:
    thehdens=row.getValue("hdens")
    thehdens_st=(thehdens-themean)/(thestd*1.0)
    row.setValue("hdens_z_sc", thehdens_st)
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
    thevalue=row.getValue("hdens_z_sc")
    list_dec.append(thevalue)
    row = rows.next()
del row, rows

arcpy.AddField_management(inobv, "hdens_dec", "double")
list_dec.sort()
print list_dec
thelen=len(list_dec)
p_dec=thelen/float(10)
print p_dec
print thelen, p_dec
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    thevalue=row.getValue("hdens_z_sc")
    order=list_dec.index(thevalue)
    k=1
    while 1:
        k_dec=k*p_dec
        if order<k_dec:
            row.setValue("hdens_dec", k)
            rows.updateRow(row)
            break
        k=k+1
    row = rows.next()
del row, rows

arcpy.DeleteField_management(inobv, "idplgfld")
arcpy.Delete_management("stat.dbf")
arcpy.Delete_management(itsplg)
os.removedirs(directory_name)

arcpy.AddMessage(" ")