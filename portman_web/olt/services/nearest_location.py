from olt.models import Splitter, FAT
from olt.serializers import SplitterParentSerializer
from django.db import connection
from olt.models import ReservedPorts

import os, sys


class NearestEquipments:

    def __init__(self, params):
        self.province_id = params.get('province_id')
        self.query = ''

    def get_queryset(self, lat_col_name='lat', lng_col_name='long'):
        exclude = ''
        # if self.table != 'olt_routes':
        #     exclude = 'AND deleted_at IS NULL'
        # query = f"SELECT * FROM (" \
        #         f"SELECT *, acos(sin(radians({self.lat})) * sin(radians(CAST(lat AS FLOAT))) + cos(radians({self.lat}))" \
        #         f" * cos(radians(CAST({lat_col_name} AS FLOAT))) * cos( radians({self.long})- radians(CAST({lng_col_name} AS FLOAT))) )" \
        #         f" * 6371  AS distance FROM {self.table}) as a" \
        #         f" WHERE distance <= {self.radius} {exclude} ORDER BY distance ASC"
        cursor = connection.cursor()
        cursor.execute(self.query)
        queryset = cursor.fetchall()
        columns_name = [desc[0] for desc in cursor.description]
        return queryset, columns_name


class NearestCabinet(NearestEquipments):

    def get_nearest(self):

        self.query = f"""
                SELECT "cab"."id", "cab"."name", "cab"."lat", "cab"."long", "cab"."is_odc",
                "city"."id" As city_id, "city"."name" As city_name, "city"."lat" As city_lat, "city"."long" As city_long, 
                (
                SELECT "approved_at"
                FROM "olt_property" AS p
                WHERE p.content_type_id = (SELECT id FROM django_content_type WHERE app_label = 'olt' AND model = 'oltcabinet') 
                AND p.object_id = cab.id
                LIMIT 1
                ) AS approved_at
                FROM "olt_oltcabinet" AS "cab"
                INNER JOIN "dslam_city" AS "city" ON ("cab"."city_id" = "city"."id")
                WHERE "cab"."deleted_at" IS NULL
                    """
        if self.province_id:
            self.query += f' AND "city"."parent_id" = {self.province_id}'
        queryset, columns_name = super().get_queryset()
        cabinet_list = []
        odc_list = []
        for row in queryset:
            data = dict(id=row[columns_name.index('id')],
                        display_name=row[columns_name.index('name')],
                        lat=row[columns_name.index('lat')], long=row[columns_name.index('long')],
                        approved_at=row[columns_name.index('approved_at')],
                        city_info=dict(id=row[columns_name.index('city_id')], name=row[columns_name.index('city_name')],
                                       lat=row[columns_name.index('city_lat')], long=row[columns_name.index('city_long')]),)

            if row[columns_name.index('is_odc')]:
                odc_list.append(data)
            else:
                cabinet_list.append(data)
        return cabinet_list, odc_list


class NearestFat(NearestEquipments):
    def __init__(self, params):
        super().__init__(params)
        self.table = 'olt_fat'

    def get_nearest(self):
        self.query = self.query = f"""
            SELECT "fat"."id", "fat"."name", "fat"."lat", "fat"."long", "fat"."address", "fat"."parent_id", "fat"."is_otb",
            "fat"."is_tb", "city"."id" As city_id, "city"."name" As city_name, "city"."lat" As city_lat, "city"."long" As city_long,
            (SELECT json_agg(
            json_build_object( 'id', "splitter"."id", 'name', "splitter"."name"))
            FROM "olt_splitter" AS "splitter"
            WHERE "splitter"."FAT_id" = "fat"."id") AS "splitters",
            (
                SELECT "approved_at"
                FROM "olt_property" AS p
                WHERE p.content_type_id = (SELECT id FROM django_content_type WHERE app_label = 'olt' AND model = 'fat') 
                AND p.object_id = fat.id
                LIMIT 1
            ) AS approved_at
            FROM "olt_fat" AS "fat"
            INNER JOIN "olt_olt" AS "olt" ON ("fat"."olt_id" = "olt"."id")
            INNER JOIN "olt_oltcabinet" AS "cabinet" ON ("olt"."cabinet_id" = "cabinet"."id")
            INNER JOIN "dslam_city" AS "city" ON ("cabinet"."city_id" = "city"."id")
            WHERE "fat"."deleted_at" IS NULL
        """

        if self.province_id:
            self.query += f' AND "city"."parent_id" = {self.province_id}'

        queryset, columns_name = super().get_queryset()
        fat_list = []
        f_fat_list = []
        otb_list = []
        tb_list = []
        for row in queryset:
            data = dict(id=row[columns_name.index('id')],
                        display_name=row[columns_name.index('name')],
                        lat=row[columns_name.index('lat')], long=row[columns_name.index('long')],
                        address=row[columns_name.index('address')],
                        approved_at=row[columns_name.index('approved_at')],
                        city_info=dict(id=row[columns_name.index('city_id')], name=row[columns_name.index('city_name')],
                                       lat=row[columns_name.index('city_lat')], long=row[columns_name.index('city_long')]),
                        splitters=row[columns_name.index('splitters')] if row[columns_name.index('splitters')] else [])

            if not row[columns_name.index('parent_id')]:
                fat_list.append(data)
            elif row[columns_name.index('is_tb')]:
                tb_list.append(data)
            elif row[columns_name.index('is_otb')]:
                otb_list.append(data)
            else:
                f_fat_list.append(data)

        return dict(fat_list=fat_list, f_fat_list=f_fat_list, otb_list=otb_list, tb_list=tb_list)


class NearestUsers(NearestEquipments):
    def __init__(self, params):
        super().__init__(params)
        self.table = 'olt_reservedports'

    def get_nearest(self):
        self.query = f"""
                   SELECT 
                       rp.id, rp.customer_name as display_name, rp.lat, rp.lng as long
                   FROM 
                       olt_reservedports rp
                   JOIN 
                       olt_fat f ON rp.fat_id = f.id
                   JOIN 
                       olt_olt o ON f.olt_id = o.id
                   JOIN 
                       olt_oltcabinet oc ON o.cabinet_id = oc.id
                   JOIN 
                       dslam_city c ON oc.city_id = c.id
                   WHERE 
                       rp.status IN {tuple(ReservedPorts.NOT_FREE_STATUZ)}
                   """
        if self.province_id:
            self.query += f' AND "c"."parent_id" = {self.province_id}'
        with connection.cursor() as cursor:
            cursor.execute(self.query)
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            return [dict(zip(column_names, row)) for row in result]


class NearestHandhole(NearestEquipments):
    def __init__(self, params):
        super().__init__(params)
        self.table = 'olt_handhole'

    def get_nearest(self):

        self.query = f"""
                        SELECT "handhole"."id", "handhole"."number", "handhole"."lat", "handhole"."long", "handhole"."description", "handhole"."is_t",
                        "city"."id" As city_id, "city"."name" As city_name, "city"."lat" As city_lat, "city"."long" As city_long,
                        (
                            SELECT "approved_at"
                            FROM "olt_property" AS p
                            WHERE p.content_type_id = (SELECT id FROM django_content_type WHERE app_label = 'olt' AND model = 'handhole') 
                            AND p.object_id = handhole.id
                            LIMIT 1
                        ) AS approved_at
                        FROM "olt_handhole" AS "handhole"
                        INNER JOIN "dslam_city" AS "city" ON ("handhole"."city_id" = "city"."id")
                        WHERE "handhole"."deleted_at" IS NULL 
                    """
        if self.province_id:
            self.query += f' AND "city"."parent_id" = {self.province_id}'
        queryset, columns_name = super().get_queryset()
        handhole_list = []
        t_list = []
        for row in queryset:
            data = dict(id=row[columns_name.index('id')],
                        display_name=row[columns_name.index('number')],
                        description=row[columns_name.index('description')],
                        approved_at=row[columns_name.index('approved_at')],
                        lat=row[columns_name.index('lat')], long=row[columns_name.index('long')],
                        city_info=dict(id=row[columns_name.index('city_id')], name=row[columns_name.index('city_name')],
                                       lat=row[columns_name.index('city_lat')],
                                       long=row[columns_name.index('city_long')]),
                        )
            if row[columns_name.index('is_t')]:
                t_list.append(data)
            else:
                handhole_list.append(data)
        return handhole_list, t_list


class NearestRoutes(NearestEquipments):
    def __init__(self, params):
        super().__init__(params)
        self.table = 'olt_routes'

    def get_nearest(self):
        queryset, columns_name = super().get_queryset()
        result = []
        for row in queryset:
            data = dict(id=row[columns_name.index('id')],
                        display_name=row[columns_name.index('device_type')],
                        description=row[columns_name.index('description')],
                        lat=row[columns_name.index('lat')], long=row[columns_name.index('long')],
                        distance=round(row[columns_name.index('distance')] * 1000, 3))
            result.append(data)
        return result


class NearestMicroductMap(NearestEquipments):
    def __init__(self, params):
        super().__init__(params)
        self.table = 'olt_microduct'
    def get_nearest(self):
        try:

            self.query = f"""
            SELECT 
                m.id,
                m.channel_count,
                m.size,
                m.code,
                (
                    SELECT "approved_at"
                    FROM "olt_property" AS p
                    WHERE p.content_type_id = (SELECT id FROM django_content_type WHERE app_label = 'olt' AND model = 'microduct') 
                    AND p.object_id = m.id
                    LIMIT 1
                ) AS approved_at,
                (
                    SELECT COUNT(*)
                    FROM olt_microductscables mc
                    WHERE mc.microduct_id = m.id AND mc.deleted_at IS NULL
                ) AS cables_count,
                (
                    SELECT JSON_AGG(r)
                    FROM (
                        SELECT *
                        FROM olt_routes r
                        WHERE r.device_type = 'microduct' AND r.device_id = m.id
                        ORDER BY r.index
                    ) AS r
                ) AS route,
                (
                    CASE 
                        WHEN m.src_device_type IS NULL THEN NULL
                        ELSE (
                            SELECT json_build_object('id', d.id, 'lat', d.lat, 'long', d.long, 'type', d.type)
                            FROM (
                                SELECT id, lat, long, 'cabinet' AS type
                                FROM olt_oltcabinet
                                WHERE id = m.src_device_id AND m.src_device_type = 'cabinet'
                                UNION ALL
                                SELECT id, lat, long, 'odc' AS type
                                FROM olt_oltcabinet
                                WHERE id = m.src_device_id AND m.src_device_type = 'odc'
                                UNION ALL
                                SELECT id, lat, long, 'fat' AS type
                                FROM olt_fat
                                WHERE id = m.src_device_id AND m.src_device_type = 'fat'
                                UNION ALL
                                SELECT id, lat, long, 'handhole' AS type
                                FROM olt_handhole
                                WHERE id = m.src_device_id AND m.src_device_type = 'handhole'
                                UNION ALL
                                SELECT id, lat, long, 't' AS type
                                FROM olt_handhole
                                WHERE id = m.src_device_id AND m.src_device_type = 't'
                            ) AS d
                        )
                    END
                ) AS src_device_info,
                (
                    CASE 
                        WHEN m.dst_device_type IS NULL THEN NULL
                        ELSE (
                            SELECT json_build_object('id', d.id, 'lat', d.lat, 'long', d.long, 'type', d.type)
                            FROM (
                                SELECT id, lat, long, 'cabinet' AS type
                                FROM olt_oltcabinet
                                WHERE id = m.dst_device_id AND m.dst_device_type = 'cabinet'
                                UNION ALL
                                SELECT id, lat, long, 'odc' AS type
                                FROM olt_oltcabinet
                                WHERE id = m.src_device_id AND m.src_device_type = 'odc'
                                UNION ALL
                                SELECT id, lat, long, 'fat' AS type
                                FROM olt_fat
                                WHERE id = m.dst_device_id AND m.dst_device_type = 'fat'
                                UNION ALL
                                SELECT id, lat, long, 'handhole' AS type
                                FROM olt_handhole
                                WHERE id = m.dst_device_id AND m.dst_device_type = 'handhole'
                                UNION ALL
                                SELECT id, lat, long, 't' AS type
                                FROM olt_handhole
                                WHERE id = m.dst_device_id AND m.dst_device_type = 't'
                                
                                
                            ) AS d
                        )
                    END
                ) AS dst_device_info
            FROM 
                olt_microduct m
                    INNER JOIN "dslam_city" AS "city" ON ("m"."city_id" = "city"."id")
                    WHERE m.deleted_at IS NULL"""
            if self.province_id:
                self.query += f' AND "city"."parent_id" = {self.province_id}'
            with connection.cursor() as cursor:
                cursor.execute(self.query)
                result = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                return [dict(zip(column_names, row)) for row in result]

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return {'row': str(ex) + '////' + str(exc_tb.tb_lineno)}


class UnknownEquipment(NearestEquipments):

    def get_nearest(self):
        return 'Please Enter correct equipment name!'


class NearestEquipmentsFactory:
    equipment_types = {
        "cabinet": NearestCabinet,
        "fat": NearestFat,
        "handhole": NearestHandhole,
        "microduct": NearestRoutes,
        "microduct_map": NearestMicroductMap,
        "users": NearestUsers
    }

    @staticmethod
    def create_equipment(equipment_type):
        equipment_class = NearestEquipmentsFactory.equipment_types.get(equipment_type)
        if equipment_class:
            return equipment_class
        else:
            return UnknownEquipment


class NearestLocation:
    @staticmethod
    def get_nearest_device(object_type, lat, long, radius):
        try:
            lat = (float(lat))
            long = (float(long))
            radius = float(radius)

            if object_type == 'cabinet':
                db_table = 'olt_oltcabinet'

            elif object_type == 'fat':
                db_table = 'olt_fat'
            elif object_type == 'user':
                db_table = 'olt_user'
            else:
                return "Object type is invalid please enter 'cabinet', 'fat' or 'user'!!!"

            query = f"""
                     SELECT * FROM (
                        SELECT 
                            id, 
                            name, 
                            CASE 
                                WHEN is_otb THEN 'otb' 
                                WHEN parent_id IS NOT NULL THEN 'ffat' 
                                ELSE 'fat' 
                            END AS type, 
                            lat, 
                            long, 
                            address,
                            is_active, 
                            ROUND(
                                CASE 
                                    WHEN (sin(radians({lat})) * sin(radians(CAST(lat AS FLOAT))) + 
                                          cos(radians({lat})) * cos(radians(CAST(lat AS FLOAT))) * 
                                          cos(radians({long}) - radians(CAST(long AS FLOAT)))) BETWEEN -1 AND 1 
                                    THEN acos(sin(radians({lat})) * sin(radians(CAST(lat AS FLOAT))) + 
                                              cos(radians({lat})) * cos(radians(CAST(lat AS FLOAT))) * 
                                              cos(radians({long}) - radians(CAST(long AS FLOAT)))) 
                                    ELSE NULL 
                                END * 6371 * 1000
                            ) AS distance 
                        FROM olt_fat 
                        WHERE deleted_at IS NULL AND is_otb IS FALSE AND is_tb IS FALSE
                    ) AS a 
                    WHERE distance IS NOT NULL AND distance <= {radius} 
                    ORDER BY distance ASC;
            """

            with connection.cursor() as cursor:
                cursor.execute(query, (lat, lat, long, radius))
                result = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                return [dict(zip(column_names, row)) for row in result]
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return {'row': str(ex) + '////' + str(exc_tb.tb_lineno)}

    @staticmethod
    def get_nearest_building(lat, long, radius):
        lat = (float(lat))
        long = (float(long))
        radius = float(radius)
        query = f"""
                        SELECT subquery.id, 
                   subquery.name, 
                   subquery.unit_count, 
                   subquery.phone, 
                   subquery.postal_address, 
                   MIN(subquery.distance) AS distance,
                   CONCAT_WS('.', 
                       subquery.province_abbr, 
                       subquery.city_abbr, 
                       'Z' || subquery.urban_district, 
                       'B' || (subquery.id + 99)
                   ) AS code
            FROM (
                SELECT b.id, 
                       b.name, 
                       b.unit_count, 
                       b.phone, 
                       b.postal_address,
                       ROUND((acos(sin(radians({lat})) * sin(radians(CAST(r.lat AS FLOAT))) + 
                       cos(radians({lat})) * cos(radians(CAST(r.lat AS FLOAT))) * 
                       cos(radians({long}) - radians(CAST(r.lng AS FLOAT)))) 
                       * 6371 * 1000)) AS distance, 
                       b.urban_district,
                       c.abbr AS city_abbr,
                       cp.abbr AS province_abbr
                FROM olt_routes r
                JOIN olt_building b ON b.id = r.device_id
                JOIN dslam_city c ON b.city_id = c.id
                JOIN dslam_city cp ON c.parent_id = cp.id  -- Assuming 'parent_id' links to the province
                WHERE r.device_type = 'building' AND b.deleted_at IS NULL
            ) AS subquery
            WHERE subquery.distance <= {radius} 
            GROUP BY subquery.id, subquery.name, subquery.unit_count, subquery.phone, subquery.postal_address, 
                     subquery.urban_district, subquery.province_abbr, subquery.city_abbr
            ORDER BY distance ASC
        """
        with connection.cursor() as cursor:
            cursor.execute(query, (lat, lat, long, radius))
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            return [dict(zip(column_names, row)) for row in result]
