import html

class PixivUser:
    def __init__(self, iden, name, account):
        self.iden = iden
        self.name = name
        self.account = account
 
    def __str__(self):
        return f"\033[0;36m\033]8;;{self.pixiv_link()}\033\\{self.name}\033]8;;\033\\\033[0m \033]8;;{self.pixiv_stacc_link()}\033\\(@{self.account})\033]8;;\033\\"
    
    @staticmethod
    def from_json(json_user):
        return PixivUser(json_user["id"], json_user["name"], json_user["account"])

    def pixiv_link(self):
        return f"https://pixiv.net/en/users/{self.iden}"

    def pixiv_stacc_link(self):
        return f"https://pixiv.net/stacc/{self.account}"

class PixivTag:
    def __init__(self, name, translated_name):
        self.name = name
        self.translated_name = translated_name
    
    def __str__(self, use_color=True):
        if use_color:
            if self.translated_name is None:
                if self.name == "R-18" or self.name == "R-18G":
                    return f"\033[0;31m{self.name}\033[0m"
                else:
                    return f"\033[0;36m{self.name}\033[0m"
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
    def __init__(self, iden, title, caption, user, tags, page_count, create_date):
        self.iden = iden
        self.title = title
        self.caption = caption
        self.user = user
        self.tags = tags
        self.page_count = page_count

        # for log:
        self.create_date = create_date
    
    def __str__(self):
        unescape_caption = html.unescape(self.caption)
        multiline_caption = unescape_caption.replace("<br />", "\n")
        newline = "\n" if multiline_caption != unescape_caption else ""
        caption_string = f"Caption: \033[0;36m{newline}{multiline_caption}\033[0m\n" if len(self.caption.strip()) != 0 else ""

        page_count_string = "" if self.page_count == 0 else f" \033[0;33m({self.page_count} pages)\033[0m"

        return (
            f"\033]8;;{self.pixiv_link()}\033\\pixiv #{self.iden}\033]8;;\033\\{page_count_string}\n"
            f"Title: \033[0;36m{self.title}\033[0m\n"
            f"{caption_string}"
            f"Artist: {str(self.user)}\n"
            f"Tags: {self.get_tag_string()}"
        )

    def get_tag_string(self, use_color=True):
        return ", ".join(tag.__str__(use_color) for tag in self.tags)

    def pixiv_link(self):
        return f"https://www.pixiv.net/en/artworks/{self.iden}"
    
    def get_r18_tag(self):
        return next((tag.name for tag in self.tags if tag.name == "R-18" or tag.name == "R-18G"), "")
    
    @staticmethod
    def from_json(json_illust):
        return PixivIllustration(
            json_illust["id"],
            json_illust["title"],
            json_illust["caption"],
            PixivUser.from_json(json_illust["user"]),
            PixivTag.from_json_list(json_illust["tags"]),
            len(json_illust["meta_pages"]),
            json_illust["create_date"]
        )

