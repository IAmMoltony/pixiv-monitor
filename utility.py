import logging
import datetime

def handle_oauth_error(api, token_switcher):
    logging.getLogger().debug(f"Refreshing access token for account {token_switcher.current_token}")
    token_switcher.refresh_token()
    access_token = token_switcher.get_access_token()
    api.set_auth(access_token)

def hrdatetime():
    return datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S")
