from dj_bridge import FAT
import requests
import random


def get_fat_list():
    return FAT.objects.all().exclude(deleted_at__isnull=False)


def save_fat(fat):
    url = "https://my.pishgaman.net/api/pte/setFat"
    payload = {'MdfID': '19607',
               'FatName': fat.name,
               'FatNumber': f'{random.randint(1, 1000)}',
               'NGeoPos': fat.lat,
               'EGeoPos': fat.long,
               'Active': '1'}
    files = [
    ]
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    print(response.text)


if __name__ == '__main__':
    for fat in get_fat_list()[:1]:
        save_fat(fat)
