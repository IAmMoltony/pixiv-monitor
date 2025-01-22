class PixivUser:
    def __init__(self, iden, name, account):
        self.iden = iden
        self.name = name
        self.account = account
    
    def __str__(self):
        return f"\033[0;36m{self.name}\033[0m (@{self.account})"
    
    @staticmethod
    def from_json(json_user):
        return PixivUser(json_user["id"], json_user["name"], json_user["account"])

class PixivTag:
    def __init__(self, name, translated_name):
        self.name = name
        self.translated_name = translated_name
    
    def __str__(self, use_color=True):
        if use_color:
            if self.translated_name is None:
                return "\033[0;31mR-18\033[0m" if self.name == "R-18" else f"\033[0;36m{self.name}\033[0m"
            return f"\033[0;36m{self.name} / {self.translated_name}\033[0m"
        if self.translated_name is None:
            return self.name
        return f"{self.name} / {self.translated_name}"
    
    @staticmethod
    def from_json(tag_json):
        return PixivTag(tag_json["name"], tag_json["translated_name"])
    
    @staticmethod
    def from_json_list(tags_json):
        tags = []
        for tag in tags_json:
            tags.append(PixivTag.from_json(tag))
        return tags

class PixivIllustration:
    def __init__(self, iden, title, caption, user, tags, create_date):
        self.iden = iden
        self.title = title
        self.caption = caption
        self.user = user
        self.tags = tags

        # for log:
        self.create_date = create_date
    
    def __str__(self):
        return f"pixiv \033[0;36m#{self.iden}\033[0m\nTitle: \033[0;36m{self.title}\033[0m\nCaption: \033[0;36m{self.caption}\033[0m\nArtist: {str(self.user)}\nTags: {self.get_tag_string()}"

    def get_tag_string(self, use_color=True):
        return ", ".join(tag.__str__(use_color) for tag in self.tags)
    
    @staticmethod
    def from_json(json_illust):
        return PixivIllustration(
            json_illust["id"],
            json_illust["title"],
            json_illust["caption"],
            PixivUser.from_json(json_illust["user"]),
            PixivTag.from_json_list(json_illust["tags"]),
            json_illust["create_date"]
        )

