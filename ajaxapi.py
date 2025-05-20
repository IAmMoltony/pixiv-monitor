import requests
from pixivmodel import PixivIllustration
import json
import traceback

class PixivAjaxError(Exception):
    pass

class PixivAjaxAPI:
    def __init__(self, phpsessid=None):
        self.phpsessid = phpsessid

    def set_phpsessid(self, phpsessid):
        self.phpsessid = phpsessid

    def user_illusts(self, user_id):
        """
        Returns a list of recent illust IDs for a given user.
        """
        print("begin get user illusts")
        response = requests.get(f"https://www.pixiv.net/ajax/user/{user_id}/profile/all", cookies=self.get_cookies()).text
        print(f"got resp: {response}")
        raise PixivAjaxError("sdf")
        if response["error"]:
            raise PixivAjaxError(response["message"])
        illust_ids = []
        for illust_key in list(response["body"]["illusts"].keys())[:5]: # TODO user-chosen value?
            illust_ids.append(int(illust_key))
        return illust_ids

    def illust_detail(self, illust_id):
        """
        Returns illustration details for a given illustration.
        """
        response = requests.get(f"https://www.pixiv.net/ajax/illust/{illust_id}", cookies=self.get_cookies()).json()
        if response["error"]:
            raise PixivAjaxError(response["message"])
        return response["body"]
    
    def get_cookies(self):
        if self.phpsessid is None:
            return {}
        return {"PHPSESSID": self.phpsessid}
