#------------------------------------
# Name: connect.py
# Description: Calculate number of crossings per area in every urban area
# Author: Tomas KRIVKA, Department of Geoinformatics, Faculty of Science, Palacky University Olomouc, Czech Republic, 2011
# Update to ArcMap v10: Jan KREJSA, Department of Geoinformatics, Faculty of Science, Palacky University Olomouc, Czech Republic, 2018
# Update by Zdena DOBESOVA: Improvement and remove of error in calculation of urban area without industry areas and water bodies (Department of Geoinformatics, Faculty of Science, Palacky University Olomouc, Czech Republic, 2020)
#------------------------------------

#Import modules, make geoprocesor, set workspace...
#--------------------------------------------------
import arcpy, sys, math, os, tempfile, locale
from arcpy import env
directory_name=tempfile.mkdtemp()

env.workspace=directory_name
arcpy.AddMessage(directory_name)
env.overwriteOutput=1


#Input
#-----
arcpy.AddMessage(" ")
arcpy.AddMessage("Input")

# Urban Areas data in polygon SHP
inobv_w=arcpy.GetParameterAsText(0)
# Street network data in line SHP
inline_h=arcpy.GetParameterAsText(1)
# Street class field
linefld=arcpy.GetParameterAsText(2)
# Highway value from street network
val_h=arcpy.GetParameterAsText(3)
# Landuse data in polygon SHP
inlu=arcpy.GetParameterAsText(4)
# landuse class field
lufld=arcpy.GetParameterAsText(5)
# Water value from Landuse
val_ws=arcpy.GetParameterAsText(6)
# Industrial value from Landuse
val_ind=arcpy.GetParameterAsText(7)
# Merge crossing radius
ri=arcpy.GetParameter(8)
# Parking eliminate
parking=arcpy.GetParameterAsText(9)

r=ri/2
val_w=val_ws.upper()
val_i=val_ind.upper()
lu_water="lu_water.shp"
lu_industry="lu_industry.shp"
inobvw="inobvw.shp"
inobv="inobv.shp"
inline="streets.shp"
vert="vert.shp"
outpnt="outpnt.shp"
cross="cross.shp"

#Check if inputs are correct
#---------------------------
arcpy.AddMessage("Check if inputs are correct")
#0
msg= "This tool was designed to work with Polygon Feature Classes... Please set Polygon feature class in first parametr."
description = arcpy.Describe(inobv_w)
if description.ShapeType != "Polygon":
    raise arcpy.AddError(msg)

msg= "This tool was designed to work with Polyline Feature Classes... Please set Polyline feature class in second parametr."
description = arcpy.Describe(inline_h)
if description.ShapeType != "Polyline":
    raise arcpy.AddError(msg)

msg= "This tool was designed to work with Polygon Feature Classes... Please set Polygon feature class in fifth parametr."
description = arcpy.Describe(inlu)
if description.ShapeType != "Polygon":
    raise arcpy.AddError(msg)


#Calculating id-key in input layer of urban areas
#------------------------------------------------
arcpy.AddMessage("Calculating id-key in input layer of urban areas")
arcpy.AddField_management(inobv_w, "idplgfld", "short")
rows = arcpy.UpdateCursor(inobv_w)
row = rows.next()
i=1
while row:
    row.setValue("idplgfld",i)
    rows.updateRow(row)
    i=i+1
    row = rows.next()
del row, rows

#Erase highways and city passes from street network
#--------------------------------------------------
arcpy.AddMessage("Erase highways from street network layer")
query=str(linefld)+"<>'"+str(val_h)+"'"
arcpy.Select_analysis(inline_h, inline, query)

#Erase water bodies from layer of urban areas
#--------------------------------------------
arcpy.AddMessage("Erase water bodies from layer of urban areas")
inobv_aw="inobv_aw.shp" # temporary shp
query=str(lufld)+"='"+str(val_w)+"'"
# inlu - origin landuse, inobv_w - input urban areas
arcpy.Select_analysis(inlu, lu_water, query)
arcpy.Union_analysis(inobv_w + ";" + lu_water,inobv_aw,"ALL")

arcpy.MakeFeatureLayer_management(lu_water,"lyr_w")
arcpy.MakeFeatureLayer_management(inobv_aw,"lyr_obv")
arcpy.SelectLayerByLocation_management("lyr_obv", "CONTAINED_BY", "lyr_w")
arcpy.DeleteRows_management("lyr_obv")
arcpy.Delete_management(lu_water)
# use of inobvw variable  - remake ZD
arcpy.Dissolve_management(inobv_aw, inobvw, "idplgfld")
# inobvw - urban areas without water bodies
arcpy.Delete_management(inobv_aw)


#Erase industry areas from layer of urban areas (error by Krejsa removed by ZD)
#--------------------------------------------
arcpy.AddMessage("Erase industry areas from layer of urban areas")
inobv_ai="inobv_ai.shp" # temporary shp
query=str(lufld)+"='"+str(val_i)+"'"

arcpy.Select_analysis(inlu, lu_industry, query)
# Union with previous inobvw instead origin inobv_w
arcpy.Union_analysis(inobvw + ";" + lu_industry,inobv_ai,"ALL")
arcpy.MakeFeatureLayer_management(lu_industry,"lyr_i")

# new name for lyr_obv ->lyr_obvv / error remove by ZD
arcpy.MakeFeatureLayer_management(inobv_ai,"lyr_obvv")
arcpy.SelectLayerByLocation_management("lyr_obvv", "CONTAINED_BY", "lyr_i")
arcpy.DeleteRows_management("lyr_obvv")
arcpy.Delete_management(lu_industry)
arcpy.Dissolve_management(inobv_ai, inobv, "idplgfld")
# inobv - urban areas without water bodies and industry
arcpy.Delete_management(inobv_ai)



#Calculating area in polygon layer of urban areas without water bodies
#---------------------------------------------------------------------
arcpy.AddMessage("Calculating area in polygon layer of urban areas without water bodies")
arcpy.AddField_management(inobv, "area", "double")
desc = arcpy.Describe(inobv)
shapefieldname = desc.ShapeFieldName
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    geometry = row.getValue(shapefieldname)
    thearea=geometry.area
    row.setValue("area",thearea)
    rows.updateRow(row)
    row = rows.next()
del row, rows

#----------------------------------
#Begin of calculating valence field
arcpy.AddMessage("Begin of calculating valence field")
#----------------------------------

#Make layer of vertexes
#----------------------
arcpy.AddMessage("Make layer of vertexes")
desc=arcpy.Describe(inline)
shapefieldname = desc.ShapeFieldName
thesr=desc.SpatialReference
arcpy.CreateFeatureclass_management(env.workspace, vert, "Point","", "ENABLED", "DISABLED", thesr)
arcpy.AddField_management(vert, "valence", "short")
listk=[]
rows=arcpy.SearchCursor(inline)
row = rows.next()
while row:
    feat = row.getValue(shapefieldname)
    partnum=0
    partcount=feat.partCount
    print partcount
    while partnum < partcount:
        part = feat.getPart(partnum)
        pnt = part.next()
        pntcount = 0
        thex=pnt.X
        they=pnt.Y
        thekey=(thex*1000000)+they
        while pnt:
            if thekey not in listk:
                cur = arcpy.InsertCursor(vert)
                rowvert = cur.newRow()
                rowvert.shape = pnt
                cur.insertRow(rowvert)
                listk.append(thekey)
            pnt = part.next()
            pntcount += 1
        partnum += 1
    row=rows.next()
del row, rows, cur

#Wrap-lines around vertexes
#--------------------------
arcpy.AddMessage("Wrap-lines around vertexes")
d=0.01
desc = arcpy.Describe(vert)
shapefieldname = desc.ShapeFieldName
wrline="wrline.shp"
arcpy.CreateFeatureclass_management(env.workspace, wrline, "Polyline", "", "ENABLED", "DISABLED", thesr)
curwr = arcpy.InsertCursor(wrline)
lineArray = arcpy.CreateObject("Array")
rows = arcpy.SearchCursor(vert)
row = rows.next()
while row:
    thefid=row.getValue("FID")
    feat = row.getValue(shapefieldname)
    pnt = feat.getPart()
    thex=pnt.X
    they=pnt.Y
    print thex, they

    pnta = arcpy.CreateObject("Point")
    pntb = arcpy.CreateObject("Point")
    pntc = arcpy.CreateObject("Point")

    pnta.X=thex-(2*d)
    pnta.Y=they-d
    pntb.X=thex+(2*d)
    pntb.Y=they-d
    pntc.X=thex
    pntc.Y=they+(2*d)

    lineArray.add(pnta)
    lineArray.add(pntb)
    lineArray.add(pntc)
    lineArray.add(pnta)
    featwr = curwr.newRow()
    featwr.shape = lineArray
    curwr.insertRow(featwr)
    featwr.setValue("ID",thefid)

    lineArray.removeAll()
    row=rows.next()
del rows, row, curwr

itspnt="itspnt.shp"
singlpnt="singlpnt.shp"
arcpy.Intersect_analysis(wrline + ";" + inline,itspnt,"ALL","","POINT")
arcpy.MultipartToSinglepart_management(itspnt,singlpnt)

#Use select by atribute to calculate Valence
#-------------------------------------------
arcpy.AddMessage("Use select by atribute to calculate valence field")
rows = arcpy.UpdateCursor(vert)
row = rows.next()
while row:
    thefid=row.getValue("FID")
    arcpy.MakeFeatureLayer_management(singlpnt,"lyr")
    query='FID_wrline='+str(thefid)
    arcpy.SelectLayerByAttribute_management("lyr", "NEW_SELECTION", query)
    result=arcpy.GetCount_management("lyr")
    num=int(result.getOutput(0))
    print thefid, num
    row.setValue("valence",num)
    rows.updateRow(row)
    row=rows.next()
del rows, row

#Delete vertexes with low Valence
#--------------------------------
arcpy.AddMessage("Delete vertexes with low Valence")
arcpy.MakeFeatureLayer_management(vert,"lyr")
query='valence=0 or valence=1 or valence=2'
arcpy.SelectLayerByAttribute_management("lyr", "NEW_SELECTION", query)
arcpy.DeleteRows_management("lyr")

#---------------------------------
#End of calculatting valence field
arcpy.AddMessage("End of calculatting valence field")
#---------------------------------

#---------------------------------------
#Begin of generalization of near crosses
arcpy.AddMessage("Begin of generalization of near crosses")
#---------------------------------------

#Make buffer zones round crossings and compare their areas
#---------------------------------------------------------
arcpy.AddMessage("Make buffer zones round crossings and compare their areas")
arcpy.Buffer_analysis(vert, "buf.shp", r, "FULL", "#", "ALL")
arcpy.MultipartToSinglepart_management("buf.shp","buf_singl.shp")
arcpy.AddField_management("buf_singl.shp", "area", "double")

desc = arcpy.Describe("buf_singl.shp")
shapefieldname = desc.ShapeFieldName
rows = arcpy.UpdateCursor("buf_singl.shp")
row = rows.next()
while row:
    geometry=row.getValue(shapefieldname)
    thearea=geometry.area
    row.setValue("area",thearea)
    rows.updateRow(row)
    row = rows.next()
del row, rows

#Eliminating parking - new part by Jan Krejsa (2018)
#-------------------------------------------
arcpy.AddMessage("Eliminating parking")
arcpy.AddMessage(parking)
if parking=='true':
    # SET VALUE FOR MINIMUM PARKING BUFFER AREA
    #buf_area= "\"AREA\" >1000" # 2020 ZD
    buf_area= "\"AREA_GEO\" >1000"
    # Creating shapefiles
    arcpy.CreateFeatureclass_management(env.workspace, "buf_20.shp", "Polygon")
    arcpy.CreateFeatureclass_management(env.workspace, "buf_20_singl.shp", "Polygon")
    arcpy.CreateFeatureclass_management(env.workspace, "buf_20_select.shp", "Polygon")
    arcpy.CreateFeatureclass_management(env.workspace, "buf_park.shp", "Polygon")
    arcpy.CreateFeatureclass_management(env.workspace, "buf_select.shp", "Polygon")
    arcpy.CreateFeatureclass_management(env.workspace, "buf_final.shp", "Polygon")
    # Eliminating parking
    arcpy.Buffer_analysis(singlpnt, "buf_20.shp", "10 Meters", "FULL", "ROUND", "ALL", "", "PLANAR")
    arcpy.MultipartToSinglepart_management("buf_20.shp", "buf_20_singl.shp")
     # origin command by Krejsa "AREA"
    #arcpy.AddGeometryAttributes_management("buf_20_singl.shp", "AREA", "", "", "")
    # CHANGE TO "AREA_GEODESIC" 2020, ZD
    arcpy.AddGeometryAttributes_management("buf_20_singl.shp", "AREA_GEODESIC", "", "", "")
    arcpy.Select_analysis("buf_20_singl.shp", "buf_20_select.shp", buf_area)
    arcpy.AddField_management("buf_20_select.shp", "parking", "TEXT", "", "", "10", "", "NULLABLE", "NON_REQUIRED", "")
    cursor = arcpy.UpdateCursor("buf_20_select.shp", '"parking" = \'\'')
    for row in cursor:
        row.setValue("parking", "P")
        cursor.updateRow(row)
    del cursor
    #del row, 2020 ZD
    arcpy.Identity_analysis("buf_singl.shp", "buf_20_select.shp", "buf_park.shp", "ALL", "", "NO_RELATIONSHIPS")
    arcpy.Select_analysis("buf_park.shp", "buf_select.shp", "\"parking\" = 'P'")
    arcpy.Erase_analysis("buf_park.shp", "buf_select.shp", "buf_final.shp", "")
    buf_final="buf_final.shp"
else:
    parking='false'
    buf_final="buf_singl.shp"

#-------------------------------------------
#End of new part by Jan Krejsa (2018)
#-------------------------------------------

arcpy.MakeFeatureLayer_management(buf_final,"lyr")
thearea=(math.pi)*(math.pow(r,2))
query='AREA<'+str(thearea)
print query
arcpy.SelectLayerByAttribute_management("lyr", "NEW_SELECTION", query)
arcpy.DeleteRows_management("lyr")
arcpy.MakeFeatureLayer_management(buf_final,"lyr_ba")
arcpy.MakeFeatureLayer_management("vert.shp","lyr_vert")
arcpy.SelectLayerByLocation_management("lyr_vert", "within", "lyr_ba")
arcpy.DeleteRows_management("lyr_vert")


#Make center-points from polygons
#--------------------------------
arcpy.AddMessage("Make center-points from polygons")
print "create center point from polygon"
arcpy.CreateFeatureclass_management(env.workspace, "centroid.shp", "Point", "", "ENABLED", "DISABLED", thesr)
arcpy.AddField_management("centroid.shp", "valence", "short")
cur_cent=arcpy.InsertCursor("centroid.shp")
desc = arcpy.Describe(buf_final)
shapefieldname = desc.ShapeFieldName
rows = arcpy.SearchCursor(buf_final)
row = rows.next()
while row:
    k=0
    sumx=0
    sumy=0
    # Create the geometry object
    feat = row.getValue(shapefieldname)
    partnum = 0
    partcount = feat.partCount
    while partnum < partcount:
        # Print the part number
        #print "Part " + str(partnum) + ":"
        part = feat.getPart(partnum)
        pnt = part.next()
        pntcount = 0
        while pnt:
            sumx=sumx+pnt.X
            sumy=sumy+pnt.Y
            k=k+1
            pnt = part.next()
            pntcount += 1
            # If pnt is null, either the part is finished or there is an
            #   interior ring
            if not pnt:
                pnt = part.next()
        partnum += 1
    pnt=arcpy.CreateObject("Point")
    pnt.X=sumx/k
    pnt.Y=sumy/k
    feat=cur_cent.newRow()
    feat.shape=pnt
    feat.setValue("valence","4")
    cur_cent.insertRow(feat)
    lineArray.removeAll()
    row = rows.next()
del row, rows, cur_cent
#-------------------------------------
#End of generalization of near crosses
arcpy.AddMessage("End of generalization of near crosses")
#-------------------------------------


arcpy.Delete_management("itspnt.shp")
arcpy.Delete_management("singlpnt.shp")
arcpy.Delete_management("wrline.shp")
arcpy.Delete_management("buf_singl.shp")
arcpy.Delete_management("buf.shp")
arcpy.Delete_management("buf_20.shp")
arcpy.Delete_management("buf_20_singl.shp")
arcpy.Delete_management("buf_20_select.shp")
arcpy.Delete_management("buf_park.shp")
arcpy.Delete_management("buf_select.shp")



#Make final layer of crossings
#-----------------------------
arcpy.AddMessage("Make finall layer of crosses")
arcpy.Merge_management("centroid.shp"+";"+"vert.shp", cross)
arcpy.Delete_management("centroid.shp")
arcpy.Delete_management("vert.shp")
arcpy.Delete_management(inline)

#Calculating Connectivity index
#------------------------------
arcpy.AddMessage("Calculating Connectivity index")
arcpy.AddField_management (inobv, "area", "double")
arcpy.SpatialJoin_analysis (cross, inobv, "spjoin.shp")
sezid=[]
sezval=[]
rows = arcpy.SearchCursor("spjoin.shp")
row = rows.next()
while row:
    idplg=row.getValue("idplgfld")
    valval=row.getValue("valence")
    if not idplg in sezid:
        sezid.append(idplg)
        sezval.append(valval)
    else:
        order=sezid.index(idplg)
        sezval[order]=sezval[order]+valval
#        print sezval[order]
    row = rows.next()
del rows, row
print sezid
print sezval

arcpy.AddField_management(inobv, "cross_num", "short")
hustkrizfld="hustkriz"
rows = arcpy.UpdateCursor(inobv)
row = rows.next()
while row:
    idplg=row.getValue("idplgfld")
    print idplg
    if idplg in sezid:
        order=sezid.index(idplg)
        y=sezval[order]
        row.setValue("cross_num",y)
    else:
        row.setValue("cross_num","0")
    rows.updateRow(row)
    row = rows.next()
del rows, row
arcpy.AddField_management(inobv, "conn", "double")
arcpy.CalculateField_management(inobv,"conn","[cross_num] / [area]")

#Copy final values of Connectivity index to input layer of urban areas
#---------------------------------------------------------------------
arcpy.AddMessage("Copy final values of Connectivity index to input layer of urban areas")
sezid=[]
sezcr=[]
rows = arcpy.SearchCursor(inobv)
row = rows.next()
while row:
    idplg=row.getValue("idplgfld")
    cross=row.getValue("conn")
    sezid.append(idplg)
    sezcr.append(cross)
    row = rows.next()
del rows, row

arcpy.AddField_management(inobv_w, "conn", "double")
rows = arcpy.UpdateCursor(inobv_w)
row = rows.next()
while row:
    idplg=row.getValue("idplgfld")
    order=sezid.index(idplg)
    y=sezcr[order]
    row.setValue("conn",y)
    rows.updateRow(row)
    row = rows.next()
del rows, row

arcpy.Delete_management("spjoin.shp")

#Z-score
#-------
arcpy.AddMessage("Z-score")
arcpy.Statistics_analysis(inobv_w, "stat.dbf","conn mean; conn std")

rows = arcpy.SearchCursor("stat.dbf")
row = rows.next()

themean=row.getValue("mean_conn")
thestd=row.getValue("std_conn")
print themean, thestd
arcpy.AddField_management(inobv_w, "conn_z_sc", "double")
rows = arcpy.UpdateCursor(inobv_w)
row = rows.next()
while row:
    thecdens=row.getValue("conn")
    if not thestd==0:
        thecdens_st=(thecdens-themean)/thestd
        row.setValue("conn_z_sc", thecdens_st)
        rows.updateRow(row)
    row = rows.next()
del row, rows

#Deciles
#-------
arcpy.AddMessage("Deciles")
list_dec=[]
rows = arcpy.SearchCursor(inobv_w)
row = rows.next()
while row:
    thevalue=row.getValue("conn_z_sc")
    list_dec.append(thevalue)
    row = rows.next()
del row, rows

arcpy.AddField_management(inobv_w, "conn_dec", "double")
list_dec.sort()
thelen=len(list_dec)
p_dec=thelen/float(10)
print thelen, p_dec
rows = arcpy.UpdateCursor(inobv_w)
row = rows.next()
while row:
    thevalue=row.getValue("conn_z_sc")
    order=list_dec.index(thevalue)
    k=1
    while 1:
        k_dec=k*p_dec
#        print k, k_dec
        if order<k_dec:
            row.setValue("conn_dec", k)
            rows.updateRow(row)
            break
        k=k+1
    row = rows.next()
del row, rows

arcpy.Delete_management("stat.dbf")
arcpy.DeleteField_management(inobv_w, "idplgfld")
arcpy.Delete_management("cross.shp")
arcpy.Delete_management("inobv.shp")
arcpy.Delete_management("buf_final.shp")
env.workspace=None

arcpy.AddMessage(" ")
