import qgis
from osgeo import ogr
from qgis._core import *
import requests
import json


class RfgfLicenseLoader():
    '''
    this is a class to download, parse and save to Geopackage the License Blocks data from https://rfgf.ru/ReestrLic/
    website
    '''
    def __init__(self):
        pass

    def download(self, json_request, json_result):
        '''
        This is a function to download data about license blocks in json format from https://rfgf.ru/ReestrLic/ site
        :param json_request: This is the json request file. Instructions to get a sample of this file: 1. Use Chrome
        to open https://rfgf.ru/ReestrLic/ site; 2. Activate DevTools by pressing F12. Go to Network tab; 3. Make some
        request on the Rfgf catalog page with no filters; 4. in DevTools, select the last query object in Name pane.
        Then go to the Payload tab on the right. Click 'view source'. Then click 'Show more' at the bottom. You now
        see the complete search request to the webservice in json format. Just copy/paste this json text to any text
        editor; 5. Find the "limit":100 parameter and change it to some big value, e.g. 250000. Save the file.
        This is your json request file that you can use for this function.
        :param json_result: path to the result data json file
        :return: NULL
        '''
        a_file = open(json_request, "r")
        json_object = json.load(a_file)
        a_file.close()
        response = requests.post('https://bi.rfgf.ru/corelogic/api/query',
                                 headers={'accept': 'application/json, text/javascript, */*; q=0.01',
                                          'accept-encoding': 'gzip, deflate, br',
                                          'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6',
                                          'authorization': 'Bearer NoAuth',
                                          'content-type': 'application/json',
                                          # 'cookie': '_ym_uid=1656406763932208622; _ym_d=1656406763; _ym_isad=2',
                                          'dnt': '1'
                                          },
                                 json=json_object,
                                 verify=False
                                 )
        data = response.json()
        a_file = open(json_result, "w")
        json.dump(data, a_file, ensure_ascii=False)
        a_file.close()


    def parse(self, json_result):
        '''
        This function just prints to output the list of license blocks from json_result file
        :param json_result: json file with data about license blocks generated by RfgfLicenseLoader.download() function
        :return: NULL
        '''
        file = open(json_result, 'r')
        json_object = json.load(file)
        file.close()
        for i in range(len(json_object['result']['data']['rows'])):
            print('---------------------------------------------------------------')
            for c in range(len(json_object['result']['data']['cols'])):
                print(json_object['result']['data']['cols'][c][0] + ':', json_object['result']['data']['values'][c][i])
            print('---------------------------------------------------------------')

        # print(json_object)


    def json2gpkg(self, json_file, gpkg_file, layer_name):
        '''
        This function parses data from json_file generated by RfgfLicenseLoader.download() function and writes it to
        Geopackage
        :param json_file: path to the json file with data about license blocks generated by RfgfLicenseLoader.download()
        function
        :param gpkg_file: path to geopackage with result layer. Geopackage must exist. Recommended: geopackage name must
        not exceed 3 letters
        :param layer_name: layer name inside geopackage to write the final result. The layer must have multipolygon
        geometry, WGS-1984 CRS and predefined field structure:
            field_name Type Length
            ---------------------------
            gos_reg_num String 0
            date_register Date 0
            license_purpose String 0
            resource_type String 0
            license_block_name String 0
            region String 0
            status String 0
            user_info String 0
            licensor String 0
            license_doc_requisites String 0
            license_cancel_order_info String 0
            date_stop_subsoil_usage Date 0
            limit_conditions_stop_subsoil_usage String 0
            date_license_stop Date 0
            previous_license_info String 0
            asln_link String 0
            source String 0
            license_update_info String 0
            license_re_registration_info String 0
            rfgf_link String 0
            comments String 0
            source_gcs String 0
            coords_text String 0

        :return: prints message about every 1000 json rows parsed
        '''
        #read json file downloaded from RFGF
        j_file = open(json_file, 'r')
        json_data = json.load(j_file)
        j_file.close()

        #convert json data to geopackage
        # create layer object
        vlayer = QgsVectorLayer(gpkg_file, layer_name, 'ogr')
        # counter for blocks written to layer
        b_counter = 0
        # loop through json data rows
        for i in range(len(json_data['result']['data']['rows'])):
            # create new feature
            feat = QgsFeature(vlayer.fields())
            # list of geopackage layer field names
            gpkg_field_names_list = ['rfgf_link', 'gos_reg_num', 'date_register', 'license_purpose', 'resource_type',
                                     'license_block_name', 'region', 'status', 'user_info', 'licensor',
                                     'license_doc_requisites', 'license_update_info', 'license_re_registration_info',
                                     'license_cancel_order_info', 'date_stop_subsoil_usage',
                                     'limit_conditions_stop_subsoil_usage', 'date_license_stop',
                                     'previous_license_info', 'coords_text']
            # list of json data record indexes
            json_attr_index_list = [0, 1, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 8]

            #check if the record has geometry
            if json_data['result']['data']['values'][8][i]:
                if '°' in json_data['result']['data']['values'][8][i]:
                    k = 0  # index of an item in gpkg_field_names_list
                    # loop through  json data record indexes
                    for j in json_attr_index_list:
                        if j not in (3, 16, 18):    # if not date format
                            # add field value to feature
                            feat[gpkg_field_names_list[k]] = json_data['result']['data']['values'][j][i]
                            pass
                        else:                       # if date format
                            feat[gpkg_field_names_list[k]] = json_data['result']['data']['values'][j][i]
                            pass
                        k += 1

                    ## add geometry to feature
                    geom = self.parseGeometry(json_data['result']['data']['values'][8][i], 0.1)
                    # assign new geometry to feature
                    feat.setGeometry(geom)

                    ## add feature to layer
                    (res, outFeats) = vlayer.dataProvider().addFeatures([feat])
                    # next blocks counter
                    b_counter += 1
            # print report about every 1000 rows processed
            if i % 1000 == 0:
                print(f'{i} rows processed')
                print(f'{b_counter} blocks inserted')

    # parse the license block geometry from json cell and transform it to wgs84
    def parseGeometry(self, source_geom, coords_threshold):
        '''
        This function converts the single license block geometry data from https://rfgf.ru/ReestrLic/ from text to
        QgsGeometry. New multipolygon parts are triggered by 'Объект №' or 'Система координат' keywords.
        New rings are triggered by points with number 1. 'Мультиточка' objects are ignored.
        The supported coordinate systems for points are ГСК-2011 (GSK-2011), Пулково-42 (Pulkovo-1942) and WGS-84.
        Transformations are made with GOST 32453-2017 parameters.
        :param source_geom: this is the coordinates of the block copied from https://rfgf.ru/ReestrLic/
        :param coords_threshold: this is the minimum value for coordinates under which the value is ignored
        :return: QgsGeometry.fromMultiPolygonXY() object
        '''

        if coords_threshold == 0:
            coords_threshold = 0.0001
        splitted_geom = self.split_strip(source_geom)

        first_point = QgsPointXY(0, 0)

        ring_list_of_points = []
        pol_list_of_rings = []
        multipol_list_of_pols = []
        Multipoint = False
        first_points_after_multipoint_counter = 0
        row_has_coords = False
        cur_crs_name = ''
        ring_first_point = QgsPointXY(0, 0)
        ring_first_point_transf = QgsPointXY(0, 0)

        context = QgsCoordinateTransformContext()
        pulkovo42_crs = QgsCoordinateReferenceSystem.fromEpsgId(4284)
        wgs84_crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        gsk2011_crs = QgsCoordinateReferenceSystem.fromProj(
            '+proj=longlat +ellps=GSK2011 +towgs84=0.013,-0.092,-0.03,-0.001738,0.003559,-0.004263,0.00739999994614493 +no_defs +type=crs')
        context.addCoordinateOperation(pulkovo42_crs, wgs84_crs,
                                       '+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=push +v_3 +step +proj=cart +ellps=krass +step +proj=helmert +x=23.57 +y=-140.95 +z=-79.8 +rx=0 +ry=-0.35 +rz=-0.79 +s=-0.22 +convention=coordinate_frame +step +inv +proj=cart +ellps=WGS84 +step +proj=pop +v_3 +step +proj=unitconvert +xy_in=rad +xy_out=deg')
        context.addCoordinateOperation(gsk2011_crs,
                                       wgs84_crs,
                                       '+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=push +v_3 +step +proj=cart +ellps=GSK2011 +step +proj=helmert +x=0.013 +y=-0.092 +z=-0.03 +rx=0.001738 +ry=-0.003559 +rz=0.004263 +s=0.00739999994614493 +convention=coordinate_frame +step +inv +proj=cart +ellps=WGS84 +step +proj=pop +v_3 +step +proj=unitconvert +xy_in=rad +xy_out=deg')

        cur_crs = gsk2011_crs

        for row in splitted_geom:
            if len(row) > 0:
                row_has_coords = False
                # row1 = row
                # row2 = row
                # row3 = row
                # row4 = row
                for word in list(row):
                    if 'ГСК-2011' in word:
                        cur_crs = gsk2011_crs
                        cur_crs_name = 'ГСК-2011'
                    elif 'Пулково' in word and '42' in word:
                        cur_crs = pulkovo42_crs
                        cur_crs_name = 'Пулково-1942'
                    elif 'WGS' in word:
                        cur_crs = wgs84_crs
                        cur_crs_name = 'WGS-1984'

                    if '°' in word:
                        row_has_coords = True

                    if 'Мультиточка' in word:
                        Multipoint = True
                        first_points_after_multipoint_counter = 0

                if (any('Объект' in word1 for word1 in list(row)) and any('№' in word2 for word2 in list(row))) or \
                        (any('Система' in word3 for word3 in list(row)) and any('координат' in word4 for word4 in list(row))):
                    if len(ring_list_of_points) > 0:
                        if len(ring_list_of_points) > 2:
                            if ring_first_point_transf.x() > coords_threshold and ring_first_point_transf.y() > coords_threshold and ring_first_point_transf.x() <= 180 and ring_first_point_transf.y() <= 90:
                                ring_list_of_points.append(ring_first_point_transf)
                            pol_list_of_rings.append(ring_list_of_points)
                            multipol_list_of_pols.append(pol_list_of_rings)
                        ring_list_of_points = []
                        pol_list_of_rings = []
                        ring_first_point = QgsPointXY(0, 0)
                        ring_first_point_transf = QgsPointXY(0, 0)
                    # in_pol = 1

                if row[0] == '1' and row_has_coords:
                    if Multipoint:
                        first_points_after_multipoint_counter += 1
                        if first_points_after_multipoint_counter > 1:
                            Multipoint = False
                            first_points_after_multipoint_counter = 0

                    if len(ring_list_of_points) > 2:
                        if ring_first_point_transf.x() > coords_threshold and ring_first_point_transf.y() > coords_threshold and ring_first_point_transf.x() <= 180 and ring_first_point_transf.y() <= 90:
                            ring_list_of_points.append(ring_first_point_transf)
                        pol_list_of_rings.append(ring_list_of_points)
                    ring_list_of_points = []
                    ring_first_point = QgsPointXY(0, 0)

                if row_has_coords and not Multipoint:
                    if row[0] == '1' and self.dms_to_dec(row[2]) > coords_threshold and \
                            self.dms_to_dec(row[1]) > coords_threshold and \
                            (ring_first_point.x() < coords_threshold or ring_first_point.y() < coords_threshold):
                        ring_first_point = QgsPointXY(self.dms_to_dec(row[2]), self.dms_to_dec(row[1]))
                    elif row[0] == '2' and self.dms_to_dec(row[2]) > coords_threshold and \
                            self.dms_to_dec(row[1]) > coords_threshold and \
                            (ring_first_point.x() < coords_threshold or ring_first_point.y() < coords_threshold):
                        ring_first_point = QgsPointXY(self.dms_to_dec(row[2]), self.dms_to_dec(row[1]))
                    elif row[0] == '3' and self.dms_to_dec(row[2]) > coords_threshold and \
                            self.dms_to_dec(row[1]) > coords_threshold and \
                            (ring_first_point.x() < coords_threshold or ring_first_point.y() < coords_threshold):
                        ring_first_point = QgsPointXY(self.dms_to_dec(row[2]), self.dms_to_dec(row[1]))
                    # first_point_geom = QgsGeometry.fromPointXY(first_point)
                    # first_point_geom.transform(QgsCoordinateTransform(cur_crs, wgs84_crs, context))
                    # first_point = first_point_geom.asPoint()

                    if ring_first_point.x() > coords_threshold and ring_first_point.y() > coords_threshold and ring_first_point.x() <= 180 and ring_first_point.y() <= 90:
                        ring_first_point_geom = QgsGeometry.fromPointXY(ring_first_point)
                        ring_first_point_geom.transform(QgsCoordinateTransform(cur_crs, wgs84_crs, context))
                        ring_first_point_transf = ring_first_point_geom.asPoint()


                    if self.dms_to_dec(row[2]) > coords_threshold and self.dms_to_dec(row[1]) > coords_threshold:
                        point = QgsPointXY(self.dms_to_dec(row[2]), self.dms_to_dec(row[1]))
                        point_geom = QgsGeometry.fromPointXY(point)
                        if abs(point.y()) <= 90 and abs(point.x()) <= 180:
                            point_geom.transform(QgsCoordinateTransform(cur_crs, wgs84_crs, context))
                            ring_list_of_points.append(point_geom.asPoint())

        if len(ring_list_of_points) > 2:
            if ring_first_point_transf.x() > coords_threshold and ring_first_point_transf.y() > coords_threshold and ring_first_point_transf.x() <= 180 and ring_first_point_transf.y() <= 90:
                ring_list_of_points.append(ring_first_point_transf)
            pol_list_of_rings.append(ring_list_of_points)
            multipol_list_of_pols.append(pol_list_of_rings)

        multipolygon_geometry = QgsGeometry.fromMultiPolygonXY(multipol_list_of_pols)

        return multipolygon_geometry

    def split_strip(self, my_str):
        while '  ' in my_str:
            my_str = my_str.replace('  ', ' ')
        my_list = [i.strip().split() for i in my_str.splitlines()]
        return my_list

    # converts DDD°MM'SS.SSSSSS"E to decimal
    def dms_to_dec(self, dms_coords):

        dec_coords = abs(float(dms_coords[:dms_coords.find('°')])) + \
                     abs(float(dms_coords[dms_coords.find('°') + 1:dms_coords.find('\'')])) / 60 + \
                     abs(float(dms_coords[dms_coords.find('\'') + 1:dms_coords.find('"')])) / 3600

        if dms_coords[dms_coords.find('"') + 1:] in ['W', 'S']:
            dec_coords *= -1

        if '-' in dms_coords:
            dec_coords *= -1

        return dec_coords


my_rfgfLoader = RfgfLicenseLoader()

## 1. download the json data file with license blocks data from https://rfgf.ru/ReestrLic/ site. Uncomment.
## Read the function infostring carefully. Run the function.
my_rfgfLoader.download('rfgf_request_example_noFilter_250000.json', 'rfgf_request_result_noFilter_250000.json')




## 2. you may parse the result to view its contents in console, if you want. Uncomment.
# my_rfgfLoader.parse('rfgf_request_result_noFilter_10.json')

## 3. Convert json data from json to geopackage. Uncomment. Read the function infostring carefully. Run.
my_rfgfLoader.json2gpkg('rfgf_request_result_noFilter_250000.json', 'd_r__.gpkg', 'l_b')

