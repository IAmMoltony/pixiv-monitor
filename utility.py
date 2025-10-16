import logging
import datetime

def handle_oauth_error(api, token_switcher):
    logging.getLogger().debug(f"Refreshing access token for account {token_switcher.current_token}")
    token_switcher.refresh_token()
    access_token = token_switcher.get_access_token()
    api.set_auth(access_token)

def api_wrapper(api, token_switcher, api_func, *args, **kwargs):
    while True:
        j = api_func(*args, **kwargs) # "Jay"
        if "error" in j:
            error_message = j["error"]["message"]
            if "invalid_grant" in error_message:
                # TODO create some sort of function thing for this oauth handler thing
                logging.getLogger().debug("OAuth error detected; refreshing access token")
                handle_oauth_error(api, token_switcher)
                continue
            if "Rate Limit" in error_message:
                #logging.getLogger().info("We got rate limited; trying again in 5 seconds...")
                token_switcher.switch_token()
                token_switcher.refresh_token()
                #logging.getLogger().info(f"Switch to account {token_switcher.current_token}")
                api.set_auth(token_switcher.get_access_token())
                continue
            logging.getLogger().error("Unknown error. Please handle it properly. %s", j)
        return j

def hrdatetime():
    return datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S")
