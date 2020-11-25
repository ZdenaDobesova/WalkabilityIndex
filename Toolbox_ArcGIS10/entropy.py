#------------------------------------
# Name: entropy.py
# Description: Calculate Entropy index of landuse in every urban area
# Author: Tomas KRIVKA, Department of Geoinformatics, Faculty of Science, Palacky University Olomouc, 2011
# Update to ArcMap v10: Jan KREJSA, Department of Geoinformatics, Faculty of Science, Palacky University Olomouc, 2018
#------------------------------------

#Import modules, make geoprocesor, set workspace...
#--------------------------------------------------
import arcpy, sys, math, os, tempfile
from arcpy import env
arcpy.toolbox = "management", "analysis", "stat"
directory_name=tempfile.mkdtemp()
print directory_name
env.workspace=directory_name
env.overwriteOutput = True

#Input
#-----
arcpy.AddMessage(" ")
arcpy.AddMessage("Input")

# Urban Areas data in polygon SHP
inobv=arcpy.GetParameterAsText(0)
# Landuse data in polygon SHP
inlu_w=arcpy.GetParameterAsText(1)
# landuse class field
lufld=arcpy.GetParameterAsText(2)
# Water value from landuse
val_w=arcpy.GetParameterAsText(3)

inlu="inlu.shp"
itsplg="intersect.shp"

#check if inputs are correct
#---------------------------
arcpy.AddMessage("Check if inputs are correct")
#0
msg= "This tool was designed to work with Polygon Feature Classes... Please set Polygon feature class in first parametr."
description = arcpy.Describe(inobv)
if description.ShapeType<>"Polygon":
    raise arcpy.AddError(msg)
#1
msg= "This tool was designed to work with Polygon Feature Classes... Please set Polygon feature class in second parametr."
description = arcpy.Describe(inlu_w)
if description.ShapeType<>"Polygon":
    raise arcpy.AddError(msg)
#2
#3

#Calculating id-key in input layer of urban areas
#------------------------------------------------
arcpy.AddMessage("Calculating id-key in input layer of urban areas")
arcpy.AddField_management(inobv, "the_id_obv", "short")
i=0
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    row.setValue("the_id_obv",i)
    rows.updateRow(row)
    i=i+1
    rows.updateRow(row)
    row = rows.next()
del row, rows

#Erase water bodies from landuse
#-------------------------------
arcpy.AddMessage("Erase water bodies from landuse")
query=str(lufld)+"<>'"+str(val_w)+"'"
arcpy.Select_analysis(inlu_w, inlu, query)

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

#Calculating areas of landuse classes in every urban area
#--------------------------------------------------------
arcpy.AddMessage("Calculating areas of landuse classes in every urban area")
arcpy.Statistics_analysis("intersect.shp", "sumstat.dbf", "area sum", "the_id_obv;" + lufld)

rows = arcpy.SearchCursor("sumstat.dbf")
row = rows.next()
sezid=[]
sezar_b=[]
sezca_b=[]

while row:
    theidplg=row.getValue("the_id_obv")
    plocha = row.getValue("sum_area")
    thelu=row.getValue(lufld)
    theln=len(thelu)
    if theidplg not in sezid:
        for char in thelu:
            area_div=plocha/theln
            sezid.append (theidplg)
            sezar_s=[]
            sezar_s.append(plocha)
            sezar_b.append(sezar_s)
            sezca_s=[]
            sezca_s.append(char)
            sezca_b.append(sezca_s)
    else:
        poradi=sezid.index(theidplg)
        area_div=plocha/theln
        for char in thelu:
            if char not in sezca_b[poradi]:
                sezar_b[poradi].append(area_div)
                sezca_b[poradi].append(char)
            else:
                poradi_s=sezca_b[poradi].index(char)
                (sezar_b[poradi])[poradi_s]=(sezar_b[poradi])[poradi_s]+area_div
    row = rows.next()
del row, rows
print sezid
print sezar_b
print sezca_b

#Ascertain numbers and sums in lists
#-----------------------------------
arcpy.AddMessage("Ascertain numbers and sums in lists")
sezsum=[]
sezcount=[]
for x in sezar_b:
    pocet=len(x)
    sezcount.append(pocet)
    suma=0
    for y in x:
        suma=suma+y
    sezsum.append(suma)

print sezsum
print sezcount

#Calculating entropy
#-------------------
arcpy.AddMessage("Calculating entropy")
sezent=[]
i=0
for x in sezar_b:
    if sezcount[i]==1:
        ent=0
        sezent.append(ent)
    else:
        cit=0
        for y in x:
            cit=cit + (y/sezsum[i]*(math.log(y/sezsum[i])))
        ent=(-1)*(cit/math.log(sezcount[i]))
        sezent.append(ent)
    i=i+1
print sezent

#Filling layer of urban areas by entropy index
#---------------------------------------------
arcpy.AddMessage("Filling layer of urban areas by entropy index")
arcpy.AddField_management(inobv, "ent", "double")
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    theid=row.getValue("the_id_obv")
    theorder=sezid.index(theid)
    print theorder
    thevalue=sezent[theorder]
    row.setValue("ent", thevalue)
    rows.updateRow(row)
    row = rows.next()
del row, rows
arcpy.Delete_management(inlu)

#Z-score
#-------
arcpy.AddMessage("Z-score")
arcpy.Statistics_analysis(inobv, "stat.dbf","ent mean; ent std")

rows = arcpy.SearchCursor("stat.dbf")
row = rows.next()

themean=row.getValue("mean_ent")
thestd=row.getValue("std_ent")
print themean, thestd

arcpy.AddField_management (inobv, "ent_z_sc", "double")
rows = arcpy.UpdateCursor(inobv)
row = rows.next()

while row:
    theent=row.getValue("ent")
    theent_st=(theent-themean)/thestd
    row.setValue("ent_z_sc", theent_st)
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
    thevalue=row.getValue("ent_z_sc")
    list_dec.append(thevalue)
    row = rows.next()
del row, rows

arcpy.AddField_management (inobv, "ent_dec", "double")
list_dec.sort()
print list_dec
thelen=len(list_dec)
p_dec=thelen/float(10)
print p_dec
print thelen, p_dec
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    thevalue=row.getValue("ent_z_sc")
    order=list_dec.index(thevalue)
    k=1
    while 1:
        k_dec=k*p_dec
        print k, k_dec
        if order<k_dec:
            row.setValue("ent_dec", k)
            rows.updateRow(row)
            break
        k=k+1
    row = rows.next()
del row, rows

arcpy.DeleteField_management(inobv, "the_id_obv")
arcpy.Delete_management("intersect.shp")
arcpy.Delete_management("stat.dbf")
arcpy.Delete_management("sumstat.dbf")
os.removedirs(directory_name)

arcpy.AddMessage(" ")
