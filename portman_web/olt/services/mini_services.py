from olt.models import UsersAuditLog, Splitter, FAT, ReservedPorts, Routes, Microduct, OLTCabinet, FAT, Handhole, Cable, OLTCabinet
from django.contrib.contenttypes.models import ContentType
from olt.models import TerminalPort, OltPort, ReservedPorts
from django.db.models import Q, Count
from math import radians, sin, cos, sqrt, atan2
from django.db import connection
from collections import defaultdict


def add_audit_log(request, model_name, instance_id, action, description=None):
    return UsersAuditLog.objects.create(
        user_id=request.user.id,
        model_name=model_name,
        instance_id=instance_id,
        action=action,
        description=description,
    )


def splitter_available_ports(splitter):
    used_in_ppp = TerminalPort.objects.filter(in_splitter=splitter, deleted_at__isnull=True)
    reserved_ports = splitter.reservedports_set.all().exclude(Q(status=ReservedPorts.STATUS_CANCELED) | Q(status=ReservedPorts.STATUS_RELEASED))
    fat_reserved_port = splitter.fat_set.all().exclude(deleted_at__isnull=False).exclude(is_active=False)
    self_ports = Splitter.objects.all().filter(parent=splitter).exclude(deleted_at__isnull=False).exclude(is_active=False)
    all_ports = list(range(1, splitter.max_capacity + 1))
    used_ports = []
    for port in reserved_ports:
        used_ports.append(port.leg_number)
    for port in fat_reserved_port:
        used_ports.append(port.leg_number)
    for port in self_ports:
        used_ports.append(port.parent_leg_number)
    for port in used_in_ppp:
        used_ports.append(port.splitter_leg_number)
    return list(set(all_ports) - set(used_ports))


def fat_available_ports(fat_id):
    try:
        fat_obj = FAT.objects.get(id=fat_id)
    except FAT.DoesNotExist:
        return "FAT object does not exist."
    ports = list(range(1, fat_obj.fat_type.port_count + 1))
    fat_objs = fat_obj.fat_set.all().exclude(deleted_at__isnull=False).exclude(is_active=False).\
        exclude(fat_splitter__isnull=False)
    splitter_objs = fat_obj.splitter_set.all().exclude(deleted_at__isnull=False).exclude(is_active=False)
    for splitter in splitter_objs:
        while splitter.patch_panel_port in ports:
            ports.remove(splitter.patch_panel_port)

    for fat in fat_objs:
        while fat.leg_number in ports:
            ports.remove(fat.leg_number)

    if not ports:
        return "There are no ports currently accessible or free to use."

    return ports


def find_ports(fat_id):
    try:
        fat_obj = FAT.objects.get(id=fat_id)
    except FAT.DoesNotExist:
        return "FAT object does not exist."
    splitter_objs = fat_obj.splitter_set.all().exclude(deleted_at__isnull=False).exclude(is_active=False)
    result = []
    if not splitter_objs:
        return "There aren't any splitters in this fat."
    for splitter in splitter_objs:
        available_ports = splitter_available_ports(splitter)
        result.append(dict(splitter_id=splitter.id, splitter_code=splitter.code, available_ports=available_ports))
    return result


def get_first_port_from_fat(fat_id):
    fat_ports = find_ports(fat_id)
    if type(fat_ports) == str:
        return fat_ports
    for fat_port in fat_ports:
        available_ports = fat_port.get('available_ports')
        if available_ports:
            first_available_port = available_ports[0]
            return dict(fat_id=fat_id, splitter_id=fat_port.get('splitter_id'),
                        splitter_code=fat_port.get('splitter_code'), leg_number=first_available_port)
    return "There are no ports currently accessible or free to use."


def calculate_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    earth_radius = 6371
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = earth_radius * c
    distance_meters = round(distance * 1000, 2)

    return distance_meters


def find_device(device_type, device_id):
    device_obj = None
    if device_type in ['cabinet', 'odc']:
        device_obj = OLTCabinet.objects.get(id=device_id)

    elif device_type in ['fat', 'ffat', 'otb', 'tb']:
        device_obj = FAT.objects.get(id=device_id)

    elif device_type in ['handhole', 't']:
        device_obj = Handhole.objects.get(id=device_id)
    
    elif device_type in ['user']:
        device_obj = ReservedPorts.objects.get(id=device_id)

    return device_obj


def get_route_length(src_lat, src_long, dst_lat, dst_long, points):
    length = 0
    if points:
        for point in points:
            next_lat = point.get('lat')
            next_long = point.get('lng')
            length += calculate_distance(float(src_lat), float(src_long), float(next_lat), float(next_long))
            src_lat = next_lat
            src_long = next_long

    length += calculate_distance(float(src_lat), float(src_long), float(dst_lat), float(dst_long))

    return round(length, 2)


def get_microduct_length(microduct_id, points):
    microduct_obj = Microduct.objects.get(id=microduct_id)
    src_device = find_device(microduct_obj.src_device_type, microduct_obj.src_device_id)
    dst_device = find_device(microduct_obj.dst_device_type, microduct_obj.dst_device_id)
    return get_route_length(
        src_device.lat, 
        src_device.long if src_device.long else src_device.lng, 
        dst_device.lat, 
        dst_device.long if dst_device.long else dst_device.lng, 
        points
    )


def get_cable_length(cable_id, points):
    cable_obj = Cable.objects.get(id=cable_id)
    src_device = find_device(cable_obj.src_device_type, cable_obj.src_device_id)
    dst_device = find_device(cable_obj.dst_device_type, cable_obj.dst_device_id)
    return get_route_length(
        src_device.lat, 
        src_device.long if src_device.long else src_device.lng, 
        dst_device.lat, 
        dst_device.long if dst_device.long else dst_device.lng,
        points
    )


def get_olt_slot_port(fat_pp_port: TerminalPort):
    if fat_pp_port is None:
        return None
    fat = fat_pp_port.terminal.content_object
    if fat.parent and fat.parent.parent:
        fat = fat.parent

    if fat.patch_panel_port:
        fat_pp_port = fat.patch_panel_port
    elif fat.fat_splitter:
        fat_pp_port = fat.fat_splitter.patch_panel_port

    if fat_pp_port.in_splitter:
        finalSplitter = fat_pp_port.in_splitter
        while finalSplitter and finalSplitter.parent: # n-level parenting
            finalSplitter = finalSplitter.parent

        if finalSplitter.patch_panel_port:
            fat_pp_port = finalSplitter.patch_panel_port

    def cable_navigation(pp_port):
        final_pp_port = pp_port
        if pp_port.cable and pp_port.loose_color and pp_port.core_color:
            middle_pp_port = TerminalPort.objects.filter(out_cable__uplink=pp_port.cable.uplink,
                                                         out_loose_color=pp_port.loose_color,
                                                         out_core_color=pp_port.core_color).first()
            if middle_pp_port:
                cable_navigation(middle_pp_port)
        return final_pp_port

    pp_port = cable_navigation(fat_pp_port)
    if pp_port.cable and pp_port.loose_color and pp_port.core_color:
        cable = pp_port.cable
        loose_color = pp_port.loose_color
        core_color = pp_port.core_color
        cabinet_pp_port = TerminalPort.objects.filter(
            Q(cable__dst_device_type='cabinet') | Q(cable__src_device_type='cabinet'),
            cable=cable.uplink,
            loose_color=loose_color,
            core_color=core_color,
            out_cable=None,
            # terminal__content_type=ContentType.objects.get(model='oltcabinet'),
        ).exclude(pk=pp_port.id).first()
        # if len(cabinet_pp_port) > 1:
        #     cabinet_pp_port = cabinet_pp_port.exclude(terminal__object_id__in=OLTCabinet.objects.filter(is_odc=True).values_list('id', flat=True)).first()
        if cabinet_pp_port:
            #olt_port = OltPort.objects.filter(patch_panel_port=cabinet_pp_port).exclude(deleted_at__isnull=False).first()
            olt_port = cabinet_pp_port.olt_port
            if olt_port:
                return dict(card_id=olt_port.card.id, card_number=olt_port.card.number, olt_name=olt_port.card.olt.name,
                            port_id=olt_port.id, port_number=olt_port.port_number)

    return None


def reservdports_reports(start_date, end_date):

    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND DATE(rp.created_at) BETWEEN '{start_date}' AND '{end_date}'"
    elif start_date:
        date_filter = f"AND DATE(rp.created_at) >= '{start_date}'"
    elif end_date:
        date_filter = f"AND DATE(rp.created_at) <= '{end_date}'"

    query = f"""
           SELECT 
               province.name AS province,
               COUNT(rp.id) AS reserved_ports
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
           JOIN 
               dslam_city province ON c.parent_id = province.id
           WHERE 
               rp.status IN {tuple(ReservedPorts.NOT_FREE_STATUZ)}
                {date_filter}
           GROUP BY 
               province.name;
           """

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        province_reservedports_by_ppport = [dict(zip(column_names, row)) for row in result]

    province_reservedports_sp_count = (
        ReservedPorts.objects
        .filter(status__in=ReservedPorts.NOT_FREE_STATUZ, splitter__isnull=False)
        .select_related('splitter__fat__olt__cabinet__city')
        .values('splitter__FAT__olt__cabinet__city__parent__name')
        .annotate(reserved_ports_count=Count('id'))
    )

    if start_date and end_date:
        province_reservedports_sp_count = province_reservedports_sp_count.filter(created_at__date__range=(start_date, end_date))
    elif start_date:
        province_reservedports_sp_count = province_reservedports_sp_count.filter(created_at__date__gte=start_date)
    elif end_date:
        province_reservedports_sp_count = province_reservedports_sp_count.filter(created_at__date__lte=end_date)

    province_reservedports_by_splitter = [
        {
            'province': entry['splitter__FAT__olt__cabinet__city__parent__name'],
            'reserved_ports': entry['reserved_ports_count']
        }
        for entry in province_reservedports_sp_count
    ]

    province_reservedports = defaultdict(int)

    def update_province_reservdports(province_list):
        for entry in province_list:
            province_reservedports[entry["province"]] += entry["reserved_ports"]

    update_province_reservdports(province_reservedports_by_splitter)
    update_province_reservdports(province_reservedports_by_ppport)
    result = [{"province": province, "reserved_ports": ports} for province, ports in province_reservedports.items()]

    total_reservedports = sum(item["reserved_ports"] for item in result)
    report = dict(total_reservedports=total_reservedports, province_reservedports=result)
    return report
