from pprint import pprint
from datetime import datetime
import requests
import time
from tqdm import tqdm
import json


class VkUser:
    with open('token_vk.txt', 'r') as file_object:
        token_vk = file_object.read().strip()
    username_or_id = input('Введите username или id пользователя vk: ')
    url = 'https://api.vk.com/method/'

    def __init__(self, token_vk=token_vk, version='5.131'):
        self.params = {
            'access_token': token_vk,
            'v': version
        }

    def get_photos(self, username_or_id=username_or_id):
        url = self.url + 'users.get'
        params = {
            'user_ids': username_or_id,
            'timeout': 2
        }
        req = requests.get(url, params={**self.params, **params}).json()
        for dict in req['response']:
            vk_id = dict['id']
        url_photos = self.url + 'photos.get'
        params_photos = {
            'owner_id': vk_id,
            'album_id': 'profile',
            'extended': '1'
        }
        req = requests.get(url_photos, params={**self.params, **params_photos}).json()
        if 'error' in list(req.keys()):
            return print("Данный профиль закрыт, укажите публичный профиль")
        elif 'items' in list(req['response'].keys()):
            req = requests.get(url_photos, params={**self.params, **params_photos}).json()['response']
            photos_list = []
            for dict in req['items']:
                photos_dict = {}
                for key, value in dict.items():
                    if key == 'likes':
                        photos_dict.update(likes=value['count'])
                    elif key == 'date':
                        photos_dict.update(date=value)
                    elif key == 'sizes':
                        max_sizes = value[-1]
                        photos_dict.update(url=max_sizes['url'])
                        photos_dict.update(size=max_sizes['type'])
                photos_list.append(photos_dict)
            return photos_list


class YaUploader(VkUser):
    token_ya = input('Укажите токен с Полигона Яндекс.Диска: ')
    current_date = datetime.now().date()

    def __init__(self, token_ya=token_ya):
        super().__init__()
        self.token_ya = token_ya

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token_ya)
        }

    def get_files_list(self):
        files_url = 'https://cloud-api.yandex.net/v1/disk/resources/files'
        headers = self.get_headers()
        response = requests.get(files_url, headers=headers).json()['items']
        files_name = []
        for dict in response:
            files_name.append(dict['name'])
        return files_name

    def get_folders_list(self):
        folder_url = 'https://cloud-api.yandex.net/v1/disk/resources/'
        headers = self.get_headers()
        params = {"path": "disk:/"}
        response = requests.get(folder_url, headers=headers, params=params).json()['_embedded']
        items = response['items']
        names_folder = []
        for dict in items:
            names_folder.append(dict['name'])
        return names_folder

    def get_a_folder(self, current_date=current_date):
        folder_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {"path": f"/backup/"}
        response = requests.put(folder_url, headers=headers, params=params).json()
        params = {"path": f"/backup/{current_date}"}
        response = requests.put(folder_url, headers=headers, params=params).json()
        return response

    def _get_upload_link(self, current_date=current_date):
        self.get_a_folder()
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {"path": f"/backup {current_date}"}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def upload_file_to_disk(self, current_date=current_date):
        self.get_a_folder()
        headers = self.get_headers()
        photos_list = self.get_photos()
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        files_info = []
        for dict in tqdm(photos_list):
            time.sleep(1)
            if str(dict['likes']) in self.get_files_list():
                params = {"path": f"/backup/{current_date}/{dict['likes']}_{dict['date']}",
                          "url": dict['url']}
                response = requests.post(upload_url, headers=headers, params=params)
                files_dict = {"file_name": f"{dict['likes']}_{dict['date']}",
                              "size": "z"}
                files_info.append(files_dict)
            else:
                params = {"path": f"/backup/{current_date}/{dict['likes']}",
                          "url": dict['url']}
                response = requests.post(upload_url, headers=headers, params=params)
                files_dict = {"file_name": f"{dict['likes']}",
                              "size": "z"}
                files_info.append(files_dict)
        with open("info.json", "w") as f:
            json.dump(files_info, f, ensure_ascii=False, indent=2)
        url = f"https://disk.yandex.ru/client/disk/backup/{current_date}/"
        recover_path = f"Резервная копия файлов сохранена по адресу {url}"
        print(recover_path)
        return recover_path


if __name__ == '__main__':
    vk_client = VkUser()
    yandex_user = YaUploader()
    yandex_user.upload_file_to_disk()
