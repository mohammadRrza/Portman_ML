from olt.models import OLT, OLTCabinet, FAT, Handhole, Splitter, ReservedPorts, Terminal, HandholeRelations, Joint
from olt.models import Cable, TerminalPort, OltPort, OltCard, JointsCables
from django.contrib.contenttypes.models import ContentType
import concurrent.futures
from django.db.models import Q, Case, When


class FatRelations:
    def __init__(self, fat: FAT):
        self.fat = fat
        self.ffat = None
        self.otb = None
        self.initialize_fat_ffat_otb()
        self.cabinet = self.get_cabinet()
        self.equipment_sequence = self.get_equipment_sequence(self.fat)

    def check_is_ffat(self, fat: FAT):
        return bool(fat.parent and not fat.is_otb)

    def check_is_otb(self, fat: FAT):
        return bool(fat.parent and fat.is_otb)


    def check_is_tb(self, fat: FAT):
        return self.check_is_otb(fat) and bool(fat.is_tb)

    def initialize_fat_ffat_otb(self):
        if self.check_is_ffat(self.fat):
            self.ffat = self.fat
            self.fat = self.ffat.parent
        elif self.check_is_otb(self.fat):
            self.otb = self.fat
            if self.check_is_ffat(self.otb.parent):
                self.ffat = self.otb.parent
                self.fat = self.otb.parent.parent
            else:
                self.fat = self.otb.parent

    def get_cabinet(self) -> OLTCabinet:
        return OLTCabinet.objects.filter(olt__in=OLT.objects.exclude(
            deleted_at__isnull=False), olt__fat=self.fat).exclude(deleted_at__isnull=False).first()

    def get_splitters(self, fat):
        return Splitter.objects.filter(FAT=fat).exclude(deleted_at__isnull=False).order_by('id')

    def get_olts(self, cabinet: OLTCabinet):
        return OLT.objects.filter(cabinet=cabinet).exclude(deleted_at__isnull=False).order_by('id')

    def get_reserved_ports(self, splitter: Splitter):
        return ReservedPorts.objects.filter(splitter=splitter, status__in=ReservedPorts.NOT_FREE_STATUZ)

    def get_patch_panels(self, instance):  # instance is cabinet or fat
        return Terminal.objects.filter(content_type=ContentType.objects.get_for_model(instance),
                                       object_id=instance.id).exclude(deleted_at__isnull=False).order_by('code')

    def get_cabinet_cables(self, cabinet: OLTCabinet):
        cables = Cable.objects.filter(src_device_type='cabinet', src_device_id=cabinet.id).exclude(deleted_at__isnull=False)
        return cables

    def get_ffats(self, fat: FAT):
        return FAT.objects.filter(parent=fat, deleted_at__isnull=True)

    def get_equipment_sequence(self, fat):
        first_handholes = []
        handhole_relations = []
        first_odcs = []
        odc_relations = []
        first_fats = []
        fat_relations = []
        relations = []
        handholes_id = []
        odcs_id = []
        fats_id = []
        fat_types = ['fat', 'ffat', 'otb', 'tb']

        fat_cables = Cable.objects.filter(
            Q(dst_device_type__in=fat_types),
            dst_device_id=fat.id,
            deleted_at__isnull=True
        )
        for cable in fat_cables:

            if cable.src_device_type == 'handhole':
                first_handholes.append(dict(src=dict(id=cable.src_device_id, type='handhole'),
                                            dst=dict(id=fat.id, type='fat'),
                                            cable=cable))
            elif cable.src_device_type == 'odc':
                first_odcs.append(dict(src=dict(id=cable.src_device_id, type='odc'),
                                       dst=dict(id=fat.id, type='fat'),
                                       cable=cable))
            elif cable.src_device_type in fat_types:
                first_fats.append(dict(src=dict(id=cable.src_device_id, type='fat'),
                                       dst=dict(id=fat.id, type='fat'),
                                       cable=cable))
            elif cable.src_device_type == 'cabinet':
                relations.append(dict(src=dict(id=cable.src_device_id, type='cabinet'),
                                            dst=dict(id=fat.id, type='fat'),
                                            cable=cable))

        def traverse_handhole_relation(relation, uplink: Cable):
            handhole_relations.append(relation)
            if relation['src']['id'] in handholes_id:
                return
            input_cables = Cable.objects.filter(Q(uplink=uplink) | Q(pk=uplink.id),
                                                dst_device_id=relation['src']['id'],
                                                dst_device_type='handhole',
                                                deleted_at__isnull=True)
            handholes_id.append(relation['src']['id'])

            for cable in input_cables:
                if cable.src_device_type == 'handhole':
                    next_relation = dict(src=dict(id=cable.src_device_id, type='handhole'),
                                         dst=dict(id=cable.dst_device_id, type='handhole'),
                                         cable=cable)
                    traverse_handhole_relation(next_relation, uplink)
                elif cable.src_device_type == 'cabinet':
                    next_relation = dict(src=dict(id=cable.src_device_id, type='cabinet'),
                                         dst=dict(id=cable.dst_device_id, type='handhole'),
                                         cable=cable)
                    handhole_relations.append(next_relation)

        def traverse_odc_relation(relation, uplink: Cable):
            odc_relations.append(relation)
            if relation['src']['id'] in odcs_id:
                return
            input_cables = Cable.objects.filter(Q(uplink=uplink) | Q(pk=uplink.id),
                                                dst_device_id=relation['src']['id'],
                                                dst_device_type='odc',
                                                deleted_at__isnull=True)
            odcs_id.append(relation['src']['id'])

            for cable in input_cables:
                if cable.src_device_type == 'odc':
                    next_relation = dict(src=dict(id=cable.src_device_id, type='odc'),
                                         dst=dict(id=cable.dst_device_id, type='odc'),
                                         cable=cable)
                    traverse_odc_relation(next_relation, uplink)

                elif cable.src_device_type == 'cabinet':
                    next_relation = dict(src=dict(id=cable.src_device_id, type='cabinet'),
                                         dst=dict(id=cable.dst_device_id, type='odc'),
                                         cable=cable)
                    odc_relations.append(next_relation)

        def traverse_fat_relation(relation, uplink: Cable):
            fat_relations.append(relation)
            if relation['src']['id'] in fats_id:
                return

            input_cables = Cable.objects.filter(
                Q(uplink=uplink) | Q(pk=uplink.id),
                Q(dst_device_type__in=fat_types),
                dst_device_id=relation['src']['id'],
                deleted_at__isnull=True
            )
            fats_id.append(relation['src']['id'])

            for cable in input_cables:
                if cable.src_device_type == 'odc':
                    next_relation = dict(src=dict(id=cable.src_device_id, type='odc'),
                                         dst=dict(id=cable.dst_device_id, type='fat'),
                                         cable=cable)
                    traverse_odc_relation(next_relation, uplink)

                elif cable.src_device_type == 'handhole':
                    next_relation = dict(src=dict(id=cable.src_device_id, type='handhole'),
                                         dst=dict(id=cable.dst_device_id, type='fat'),
                                         cable=cable)
                    traverse_handhole_relation(next_relation, uplink)

                elif cable.src_device_type in fat_types:
                    next_relation = dict(src=dict(id=cable.src_device_id, type='fat'),
                                         dst=dict(id=cable.dst_device_id, type='fat'),
                                         cable=cable)
                    traverse_fat_relation(next_relation, uplink)

                elif cable.src_device_type == 'cabinet':
                    next_relation = dict(src=dict(id=cable.src_device_id, type='cabinet'),
                                         dst=dict(id=cable.dst_device_id, type='fat'),
                                         cable=cable)
                    fat_relations.append(next_relation)

        for relation in first_handholes:
            uplink = relation['cable'].uplink
            if uplink:
                traverse_handhole_relation(relation, uplink)
        for relation in first_odcs:
            uplink = relation['cable'].uplink
            if uplink:
                traverse_odc_relation(relation, uplink)

        for relation in first_fats:
            uplink = relation['cable'].uplink
            if uplink:
                traverse_fat_relation(relation, uplink)

        def make_unique(data):
            seen = set()
            unique_data = []
            for d in data:
                values = (d['src']['id'], d['src']['type'], d['dst']['id'], d['dst']['type'], d['cable'])
                if values not in seen:
                    seen.add(values)
                    unique_data.append(d)

            return unique_data

        def make_unique_list(input_list):
            unique_list = []
            for i in input_list:
                if i not in unique_list:
                    unique_list.append(i)
            return unique_list

        odcs_id = make_unique_list(list(reversed(odcs_id)))
        handholes_id = make_unique_list(list(reversed(handholes_id)))
        fats_id = make_unique_list(list(reversed(fats_id)))
        relations = relations + list(reversed(handhole_relations)) + list(reversed(odc_relations)) + list(reversed(fat_relations))
        relations = make_unique(relations)

        return dict(handholes_id=handholes_id,
                    odcs_id=odcs_id,
                    fats_id=fats_id,
                    relations=relations)

    def get_joints(self, hanhole):

        return Joint.objects.filter(handhole=hanhole)

    def get_legs_info(self, splitter: Splitter):
        reserved_ports = self.get_reserved_ports(splitter)
        ffats = self.get_ffats(self.fat)
        ffats = ffats.filter(fat_splitter=splitter)
        splitters = Splitter.objects.filter(parent=splitter, deleted_at__isnull=True)
        ports = TerminalPort.objects.filter(in_splitter=splitter).exclude(deleted_at__isnull=False)
        legs = []

        for leg_number in range(1, splitter.splitter_type.legs_count + 1):
            reserved_port = next((port for port in reserved_ports if port.leg_number == leg_number), None)
            if reserved_port:
                reserved_title = reserved_port.customer_name or reserved_port.customer_name_en
                reserved_port_id = reserved_port.id
            else:
                reserved_title, user, reserved_port_id = None, None, None
            ffat_title = next((f'** #{ffat.name}' for ffat in ffats if ffat.leg_number == leg_number), None)
            splitter_title = next((f'>> #{splitter.name}' for splitter in splitters if splitter.parent_leg_number == leg_number), None)
            ppport_title = next((f'{ppp.terminal.code}: {ppp.cassette_number}-{ppp.port_number}' for ppp in ports if ppp.splitter_leg_number == leg_number), None)
            ppport_id = next((ppp.id for ppp in ports if ppp.splitter_leg_number == leg_number), None)
            title = reserved_title if reserved_title else ffat_title
            title = splitter_title if splitter_title else title
            title = f'-- {ppport_title}' if ppport_title else title
            leg = {
                "reserved_port_id": reserved_port_id,
                "title": title if title else '',
                "leg": leg_number,
                "splitter": next((f'splitter_{splitter.id}' for splitter in splitters if splitter.parent_leg_number == leg_number), None),
                "cassette_port": ppport_title,
                "ppp_id": ppport_id,
                "ffat_id": next((ffat.id for ffat in ffats if ffat.leg_number == leg_number), None)
            }
            legs.append(leg)

        return legs

    def get_splitter_info(self, splitter):
        legs_info = self.get_legs_info(splitter)
        splitter_info = dict(id=f'splitter_{splitter.id}',
                             code=splitter.code,
                             name=splitter.name,
                             type='splitter',
                             info=dict(ports=splitter.splitter_type.legs_count),
                             legs=legs_info)
        return splitter_info

    def get_fat_pp_links(self, patch_panel: Terminal):
        links = []
        ports = TerminalPort.objects.filter(terminal=patch_panel).exclude(deleted_at__isnull=False)
        splitters = Splitter.objects.filter(patch_panel_port__in=ports).exclude(deleted_at__isnull=False)
        fats = FAT.objects.filter(patch_panel_port__in=ports).exclude(deleted_at__isnull=False)
        users = ReservedPorts.objects.filter(patch_panel_port__in=ports, status__in=ReservedPorts.NOT_FREE_STATUZ)

        for port in ports:
            if port.in_splitter:
                link = {'from': {'id': f'splitter_{port.in_splitter.id}',
                                 'type': 'splitter',
                                 'leg_number': port.splitter_leg_number
                                 },

                        'title': f'{port.in_splitter.name}:{port.splitter_leg_number}',
                        'to': {'cassette': port.cassette_number,
                               'port': port.port_number,
                               'port_id': port.id},
                        }
                links.append(link)
        for splitter in splitters:
            link = {'from': {'cassette': splitter.patch_panel_port.cassette_number,
                             'port': splitter.patch_panel_port.port_number,
                             'port_id': splitter.patch_panel_port.id},
                    'to': {'id': f'splitter_{splitter.id}',
                           'type': 'splitter'},
                    'title': ''
                    }
            links.append(link)

        for fat in fats:
            link = {'from': {'cassette': fat.patch_panel_port.cassette_number,
                             'port': fat.patch_panel_port.port_number,
                             'port_id': fat.patch_panel_port.id},
                    'to': {'id': f'fat_{fat.id}',
                           'type': 'fat'},
                    'title': f'** {fat.name}'
                    }
            links.append(link)

        for user in users:
            link = {'from': {'cassette': user.patch_panel_port.cassette_number,
                             'port': user.patch_panel_port.port_number,
                             'port_id': user.patch_panel_port.id},
                    'to': {'id': f'user_{user.id}',
                           'type': 'user'},
                    'title': user.customer_name if user.customer_name else user.customer_name_en
                    }
            links.append(link)
        return links

    def get_fat_pp_info(self, patch_panel: Terminal):
        links = self.get_fat_pp_links(patch_panel)
        pp_info = dict(id=f'pp_{patch_panel.id}',
                       code=patch_panel.code,
                       type='patch_panel',
                       info=dict(cassette_count=patch_panel.cassette_count, port_count=patch_panel.port_count),
                       links=links)
        return pp_info

    def get_cable_link(self, pp_owner, cable: Cable, direction='in'):
        """
        pp_owner can be a cabinet or fat
        """
        links = []
        content_type = ContentType.objects.get_for_model(pp_owner)
        pp_ports = (TerminalPort.objects.filter(terminal__content_type=content_type, terminal__object_id=pp_owner.id,  deleted_at__isnull=True,))
        if direction == 'in':
            pp_ports = pp_ports.filter(cable=cable).exclude(Q(loose_color__isnull=True) | Q(core_color__isnull=True)).order_by('id')
        else:
            pp_ports = pp_ports.filter(out_cable=cable).exclude(Q(out_loose_color__isnull=True) | Q(out_core_color__isnull=True)).order_by('id')
        for port in pp_ports:
            link = {'from': {'loose': port.loose_color if direction == 'in' else port.out_loose_color,
                             'core': port.core_color if direction == 'in' else port.out_core_color,
                             'direction': direction},
                    'to': {'id': f'pp_{port.terminal.id}',
                           'type': 'patch_panel',
                           'cassette': port.cassette_number,
                           'port': port.port_number,
                           'port_id': port.id}
                    }
            links.append(link)
        return links

    def get_cable_info(self, owner, cable: Cable, prefixId='', direction='in'):

        links = self.get_cable_link(pp_owner=owner, cable=cable, direction=direction)
        cable_info = dict(id=f'{prefixId}cable_{cable.id}',
                          code=f'{cable.code}[{cable.id}]',
                          type='cable',
                          direction=direction,
                          info=dict(loose_count=int(cable.type.core_count / 12), core_count=cable.type.core_count),
                          links=links)
        return cable_info

    def get_fat_cables(self, fat: FAT):
        fat_types = ['fat', 'ffat', 'otb', 'tb']
        in_cables = Cable.objects.filter(
            dst_device_type__in=fat_types,
            dst_device_id=fat.id
        ).exclude(deleted_at__isnull=False)
        out_cables = Cable.objects.filter(
            src_device_type__in=fat_types,
            src_device_id=fat.id
        ).exclude(deleted_at__isnull=False)
        return in_cables, out_cables

    def get_fat_info(self, fat: FAT):
        patch_panels = self.get_patch_panels(fat)
        patch_panels_info = [self.get_fat_pp_info(patch_panel) for patch_panel in patch_panels]
        splitters = self.get_splitters(fat)
        splitters_info = [self.get_splitter_info(splitter) for splitter in splitters]
        in_cables, out_cables = self.get_fat_cables(fat)
        cables_info = \
            [self.get_cable_info(owner=fat, cable=cable, prefixId=f'fat_{fat.id}') for cable in in_cables] #+\
            #[self.get_cable_info(owner=fat, cable=cable, prefixId=f'fat_{fat.id}', direction='out') for cable in out_cables]
        device_type = 'ffat' if self.check_is_ffat(fat) else ('otb' if self.check_is_otb(fat) else 'fat')
        device_type = 'tb' if self.check_is_tb(fat) else device_type

        return dict(id=f'fat_{fat.id}', code=fat.code, name=fat.name, type='fat', device_type=device_type,
                    info=dict(ports=fat.fat_type.port_count),
                    has=dict(patch_panel=patch_panels_info, splitter=splitters_info, cable=cables_info))

    def get_fat_sequence_info(self):
        fats_id = self.equipment_sequence.get('fats_id')
        fats = FAT.objects.filter(id__in=fats_id).order_by(
            Case(*[When(id=fid, then=pos) for pos, fid in enumerate(fats_id)]))
        fats_info = [self.get_fat_info(fat) for fat in fats]
        return fats_info

    def get_olt_cards(self, olt):
        slots = OltCard.objects.filter(olt=olt).exclude(deleted_at__isnull=False).order_by('number')
        cards = []
        total_ports = 0
        for slot in slots:
            cards.append({'number': slot.number, 'port_count': slot.ports_count})
            total_ports += slot.ports_count
        return [cards, total_ports]

    def get_olt_info(self, olt):
        cards, total_ports = self.get_olt_cards(olt)
        return dict(
            id=f'olt_{olt.id}', name=olt.name, type='olt',
            info=dict(vlan=olt.vlan_number, ip=olt.ip, slots=len(cards), ports=total_ports, 
            brand=olt.olt_type.model.replace('olt_', '')) if olt.olt_type else "", 
            cards=cards
        )

    def get_cabinet_pp_links(self, patch: Terminal):
        pp_ports = TerminalPort.objects.filter(terminal=patch, deleted_at__isnull=True, olt_port__isnull=False)
        links = []
        for port in pp_ports:
            link = {'from': dict(cassette=port.cassette_number,
                                 port=port.port_number,
                                 color=port.loose_color if port.loose_color else 'black',
                                 port_id=port.id),
                    'to': dict(id=f'olt_{port.olt_port.card.olt.id}',
                               type='olt',
                               slot=port.olt_port.card.number,
                               port=port.olt_port.port_number,
                               port_id=port.olt_port.id)}
            links.append(link)
        return links

    def get_cabinet_pp_info(self, patch: Terminal):
        links = self.get_cabinet_pp_links(patch)
        return dict(id=f'pp_{patch.id}', code=patch.code, type='patch_panel',
                    info=dict(cassette_count=patch.cassette_count, port_count=patch.port_count),
                    links=links)

    def get_cabinet_info(self, cabinet: OLTCabinet):
        olts = [self.get_olt_info(olt) for olt in self.get_olts(cabinet)]
        patch_panels = [self.get_cabinet_pp_info(patch) for patch in self.get_patch_panels(cabinet)]
        cables = self.get_cabinet_cables(cabinet)
        cables_info = [self.get_cable_info(owner=cabinet, cable=cable, prefixId=f'cab_{cabinet.id}') for cable in cables]
        device_type = 'infrastructure' if cabinet.parent else 'cabinet'

        cabinet_info = dict(id=f'cabinet_{cabinet.id}', code=cabinet.code, name=cabinet.name, type='cabinet', device_type=device_type,
                            info=dict(),
                            has=dict(olt=olts, patch_panel=patch_panels, cable=cables_info))
        return cabinet_info

    def get_handhole_cables(self, handhole: Handhole):
        input_cables = Cable.objects.filter(dst_device_type='handhole', dst_device_id=handhole.id).exclude(
            deleted_at__isnull=False)
        output_cables = Cable.objects.filter(src_device_type='handhole', src_device_id=handhole.id).exclude(
            deleted_at__isnull=False)

        return dict(input_cables=input_cables, output_cables=output_cables)

    def get_joint_cables(self, joint: Joint):
        cables = self.get_handhole_cables(joint.handhole)
        input_cables = cables.get('input_cables')
        output_cables = cables.get('output_cables')
        content_type = ContentType.objects.get(model='joint')
        cables_info = []
        for cable in input_cables:
            pp_ports = (TerminalPort.objects.filter(cable=cable, terminal__content_type=content_type,
                                                    terminal__object_id=joint.id).
                        exclude(Q(loose_color__isnull=True) | Q(core_color__isnull=True)).order_by('id'))
            links = []
            for port in pp_ports:
                link = {'from': {'loose': port.loose_color,
                                 'core': port.core_color,
                                 'direction': 'in'},
                        'to': {'id': f'pp_{port.terminal.id}',
                               'type': 'patch_panel',
                               'cassette': port.cassette_number,
                               'port': port.port_number,
                               'port_id': port.id}
                        }
                links.append(link)
            cable_info = dict(id=f'injoint_{joint.id}cable_{cable.id}', code=cable.code,
                              type='cable', direction='in',
                              info=dict(loose_count=int(cable.type.core_count / 12),
                                        core_count=cable.type.core_count),
                              links=links)
            cables_info.append(cable_info)

        for cable in output_cables:
            pp_ports = (TerminalPort.objects.filter(out_cable=cable,
                                                    deleted_at__isnull=True,
                                                    terminal__content_type=content_type,
                                                    terminal__object_id=joint.id).
                        exclude(Q(out_loose_color__isnull=True) | Q(out_core_color__isnull=True)).order_by('id'))
            links = []
            for port in pp_ports:
                link = {'from': {'loose': port.out_loose_color,
                                 'core': port.out_core_color,
                                 'direction': 'out'},
                        'to': {'id': f'pp_{port.terminal.id}',
                               'type': 'patch_panel',
                               'cassette': port.cassette_number,
                               'port': port.port_number,
                               'port_id': port.id}
                        }
                links.append(link)

            cable_info = dict(id=f'outjoint_{joint.id}cable_{cable.id}', code=cable.code,
                              type='cable', direction='out',
                              info=dict(loose_count=int(cable.type.core_count / 12),
                                        core_count=cable.type.core_count),
                              links=links)
            cables_info.append(cable_info)

        return cables_info

    def get_joint_pp_info(self, patch_panel: Terminal):
        pp_info = dict(id=f'pp_{patch_panel.id}',
                       code=patch_panel.code,
                       type='patch_panel',
                       info=dict(cassette_count=patch_panel.cassette_count, port_count=patch_panel.port_count))
        return pp_info

    def get_joint_info(self, joint: Joint):
        patch_panels = self.get_patch_panels(joint)
        patch_panels_info = [self.get_joint_pp_info(patch_panel) for patch_panel in patch_panels]
        cables = self.get_joint_cables(joint)

        return dict(id=f'joint_{joint.id}', code=joint.code, type='joint', info=dict(),
                    has=dict(patch_panel=patch_panels_info, cable=cables))

    def get_handhole_info(self, handhole):
        joints = self.get_joints(handhole)
        joints_info = []
        for joint in joints:
            joint_info = self.get_joint_info(joint)
            joints_info.append(joint_info)

        return dict(dict(id=f'handhole_{handhole.id}', code=handhole.number, type='handhole', device_type='handhole',
                         has=dict(joint=joints_info)))

    def get_handholes_info(self):
        handholes_id = self.equipment_sequence.get('handholes_id')
        handholes = Handhole.objects.filter(id__in=handholes_id).order_by(
            Case(*[When(id=fid, then=pos) for pos, fid in enumerate(handholes_id)]))
        handholes_info = [self.get_handhole_info(handhole) for handhole in handholes]
        return handholes_info

    def get_instance_pp_ports(self, instance):
        pp_ports = TerminalPort.objects.filter(terminal__content_type=ContentType.objects.get_for_model(instance),
                                               terminal__object_id=instance.id,
                                               cable__isnull=False,
                                               loose_color__isnull=False,
                                               deleted_at__isnull=True,
                                               core_color__isnull=False).select_related('terminal').prefetch_related(
            'cable', 'terminal__terminalport_set')
        return pp_ports


    def get_odc_pp_info(self, patch_panel: Terminal):

        pp_info = dict(id=f'pp_{patch_panel.id}',
                       code=patch_panel.code,
                       type='patch_panel',
                       info=dict(cassette_count=patch_panel.cassette_count, port_count=patch_panel.port_count))
        return pp_info

    def get_odc_cables(self, odc):
        input_cables = Cable.objects.filter(dst_device_type='odc', dst_device_id=odc.id, deleted_at__isnull=True)
        output_cables = Cable.objects.filter(src_device_type='odc', src_device_id=odc.id, deleted_at__isnull=True)

        return dict(input_cables=input_cables, output_cables=output_cables)

    def get_odc_cables_info(self, odc):
        cables = self.get_odc_cables(odc)
        input_cables = cables.get('input_cables')
        output_cables = cables.get('output_cables')
        content_type = ContentType.objects.get_for_model(odc)
        cables_info = []
        for cable in input_cables:
            pp_ports = (TerminalPort.objects.filter(cable=cable,
                                                    deleted_at__isnull=True,
                                                    terminal__content_type=content_type,
                                                    terminal__object_id=odc.id).
                        exclude(Q(loose_color__isnull=True) | Q(core_color__isnull=True)).order_by('id'))
            links = []
            for port in pp_ports:
                link = {'from': {'loose': port.loose_color,
                                 'core': port.core_color,
                                 'direction': 'in'},
                        'to': {'id': f'pp_{port.terminal.id}',
                               'type': 'patch_panel',
                               'cassette': port.cassette_number,
                               'port': port.port_number,
                               'port_id': port.id}
                        }
                links.append(link)
            cable_info = dict(id=f'inodc_{odc.id}cable_{cable.id}', code=cable.code,
                              type='cable', direction='in',
                              info=dict(loose_count=int(cable.type.core_count / 12),
                                        core_count=cable.type.core_count),
                              links=links)
            cables_info.append(cable_info)

        for cable in output_cables:
            pp_ports = (TerminalPort.objects.filter(out_cable=cable,
                                                    deleted_at__isnull=True,
                                                    terminal__content_type=content_type,
                                                    terminal__object_id=odc.id).
                        exclude(Q(out_loose_color__isnull=True) | Q(out_core_color__isnull=True)).order_by('id'))
            links = []
            for port in pp_ports:
                link = {'from': {'loose': port.out_loose_color,
                                 'core': port.out_core_color,
                                 'direction': 'out'},
                        'to': {'id': f'pp_{port.terminal.id}',
                               'type': 'patch_panel',
                               'cassette': port.cassette_number,
                               'port': port.port_number,
                               'port_id': port.id}
                        }
                links.append(link)

            cable_info = dict(id=f'outodc_{odc.id}cable_{cable.id}', code=cable.code,
                              type='cable', direction='out',
                              info=dict(loose_count=int(cable.type.core_count / 12),
                                        core_count=cable.type.core_count),
                              links=links)
            cables_info.append(cable_info)

        return cables_info

    def get_odcs_info(self):
        odcs_id = self.equipment_sequence.get('odcs_id')
        odcs = OLTCabinet.objects.filter(id__in=self.equipment_sequence.get('odcs_id'), is_odc=True).order_by(
            Case(*[When(id=fid, then=pos) for pos, fid in enumerate(odcs_id)]))
        odcs_info = []
        for odc in odcs:
            patch_panels = [self.get_odc_pp_info(patch) for patch in self.get_patch_panels(odc)]
            cables = self.get_odc_cables_info(odc)
            odc_info = dict(id=f'odc_{odc.id}', code=odc.code, type='odc',
                            info=dict(), name=odc.name,
                            has=dict(patch_panel=patch_panels, cable=cables))
            odcs_info.append(odc_info)
        return odcs_info

    def get_external_links(self):
        relations = self.equipment_sequence.get('relations')
        links = []
        for relation in relations:
            link = {'from': dict(id=f"{relation['src']['type']}_{relation['src']['id']}", type=relation['src']['type']),
                    'to': dict(id=f"{relation['dst']['type']}_{relation['dst']['id']}", type=relation['dst']['type']),
                    'cable': dict(id=f'cable_{relation["cable"].id}',
                                  code=relation["cable"].code)}
            links.append(link)

        def add_link_if_exists(links, from_device, to_device):
            fat_types = ['fat', 'ffat', 'otb', 'tb']

            cables = Cable.objects.filter(
                Q(
                    Q(dst_device_type__in=fat_types) &
                    Q(src_device_type__in=fat_types) &
                    (
                            Q(dst_device_id=to_device.id, src_device_id=from_device.id) |
                            Q(dst_device_id=from_device.id, src_device_id=to_device.id)
                    )
                )
            ).exclude(deleted_at__isnull=False)
            for cable in cables:
                link = {'from': dict(id=f'fat_{from_device.id}', type='fat'),
                        'to': dict(id=f'fat_{to_device.id}', type='fat'),
                        'cable': dict(id=f'cable_{cable.id}', code=cable.code)
                        }
                links.append(link)

        if self.ffat:
            add_link_if_exists(links, self.fat, self.ffat)

        if self.otb and not self.ffat:
            add_link_if_exists(links, self.fat, self.otb)

        if self.otb and self.ffat:
            add_link_if_exists(links, self.ffat, self.otb)
        return links

    def get_relations(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            fat_info = executor.submit(self.get_fat_info, self.fat).result()
            cabinet_info = executor.submit(self.get_cabinet_info, self.cabinet).result()
            infrastructure_info = executor.submit(self.get_cabinet_info, self.cabinet.parent).result() if self.cabinet.parent else None
            handholes_info = executor.submit(self.get_handholes_info).result()
            links = executor.submit(self.get_external_links).result()
            odc_info = executor.submit(self.get_odcs_info).result()
            ffat_info = executor.submit(self.get_fat_info, self.ffat).result() if self.ffat else None
            otb_info = executor.submit(self.get_fat_info, self.otb).result() if self.otb else None
            fat_sequence_info = executor.submit(self.get_fat_sequence_info).result()

        fat_info = fat_sequence_info + [info for info in [fat_info, ffat_info, otb_info] if info is not None]
        cabinet_info = [info for info in [cabinet_info, infrastructure_info] if info is not None]
        ftth_data = dict(
            title = f"FAT \"{self.fat.name}\" Connections",
            code = self.fat.code,
            eqs = dict(
                fat=fat_info,
                cabinet=cabinet_info,
                handhole=handholes_info,
                odc=odc_info
            ),
            links=links
        )
        return ftth_data
