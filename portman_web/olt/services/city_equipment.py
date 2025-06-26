from olt.models import OLT, OLTCabinet, FAT, City, Handhole
from django.db.models import Q
import zipfile
import io


class CityEquipmentService:
    def __init__(self, city_id):
        self.city_id = city_id
        self.cities = self.get_cities()

    def get_cities(self):
        city = City.objects.get(pk=self.city_id)
        if city.parent is None:
            return City.objects.filter(parent=city)
        else:
            return [city]

    def get_cabinets(self):
        cabinets = OLTCabinet.objects.exclude(deleted_at__isnull=False).filter(city__in=self.cities)
        return cabinets

    def get_fats(self):
        fats = FAT.objects.exclude(deleted_at__isnull=False).filter(
            parent__isnull=True, fat_splitter__isnull=True).filter(olt__cabinet__city__in=self.cities)
        return fats

    def get_ffats(self):
        ffats = FAT.objects.exclude(deleted_at__isnull=False).filter(
            Q(parent__isnull=False) | Q(fat_splitter__isnull=False)).filter(olt__cabinet__city__in=self.cities)
        return ffats

    def get_handholes(self):
        handholes = Handhole.objects.exclude(deleted_at__isnull=False).filter(city__in=self.cities)
        return handholes

    def export_kmz_file(self):
        cabinets = self.get_cabinets()
        fats = self.get_fats()
        ffats = self.get_ffats()
        handholes = self.get_handholes()

        kml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
                <kml xmlns="http://www.opengis.net/kml/2.2">
                    <Document>
                '''

        for cabinet in cabinets:
            kml_content += f'''
                        <Placemark>
                            <name>Cabinet</name>
                            <description>{cabinet.name}</description>
                            <Point>
                                <coordinates>{cabinet.long},{cabinet.lat}</coordinates>
                            </Point>
                        </Placemark>
                    '''

        for fat in fats:
            kml_content += f'''
                      <Placemark>
                          <name>Fat</name>
                          <description>{fat.name}</description>
                          <Point>
                              <coordinates>{fat.long},{fat.lat}</coordinates>
                          </Point>
                      </Placemark>
                  '''

        for ffat in ffats:
            kml_content += f'''
                        <Placemark>
                            <name>FFat</name>
                            <description>{ffat.name}</description>
                            <Point>
                                <coordinates>{ffat.long},{ffat.lat}</coordinates>
                            </Point>
                        </Placemark>
                    '''

        for handhole in handholes:
            kml_content += f'''
                <Placemark>
                    <name>Handhole</name>
                    <description>{handhole.number}</description>
                    <Point>
                        <coordinates>{handhole.long},{handhole.lat}</coordinates>
                    </Point>
                </Placemark>
            '''

        kml_content += '''
            </Document>
        </kml>
        '''
        kmz_file = io.BytesIO()

        with zipfile.ZipFile(kmz_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('doc.kml', kml_content)

        kmz_file.seek(0)
        return kmz_file


