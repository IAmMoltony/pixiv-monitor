import requests
from pixivmodel import PixivIllustration
import json

class PixivAjaxError(Exception):
    pass

class PixivAjaxAPI:
    def user_illusts(self, user_id):
        """
        Returns a list of recent illust IDs for a given user.
        """
        response = requests.get(f"https://www.pixiv.net/ajax/user/{user_id}/profile/all").json()
        if response["error"]:
            raise PixivAjaxError(response["message"])
        illust_ids = []
        balls = json.dumps(response, indent=2)
        for illust_key in list(response["body"]["illusts"].keys())[:5]: # TODO user-chosen value?
            illust_ids.append(int(illust_key))
        return illust_ids

    def illust_detail(self, illust_id):
        """
        Returns illustration details for a given illustration.
        """
        response = requests.get(f"https://www.pixiv.net/ajax/illust/{illust_id}").json()
        if response["error"]:
            raise PixivAjaxError(response["message"])
        return response["body"]
