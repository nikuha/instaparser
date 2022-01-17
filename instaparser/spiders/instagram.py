import json
import re
from copy import deepcopy
from urllib.parse import urlencode

import scrapy
from scrapy.http import HtmlResponse

from instaparser.items import InstaparserItem


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'

    inst_login_name = 'Onliskill_udm'
    inst_login_pwd = '#PWD_INSTAGRAM_BROWSER:10:1642094301:ASZQAK3xQiN26pezmbNTERAktepuAKlWlqcVqr7z3rsE5QVlY3+nAifmia79/DHxjFYAEDdYBKj4jWG+n69gVxvObSIcbyeYMnhZQctoc6QcJo7R7ulkoaD18rDvHEaQm+dFbB28veuLCZFUtGll'

    parse_users = ['lanternia_design', 'ceramicsochi']
    friendship_url = 'https://i.instagram.com/api/v1/friendships'
    following_count = 12
    api_headers = {'User-Agent': 'Instagram 155.0.0.37.107'}

    def parse(self, response: HtmlResponse):
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_link,
            method='POST',
            callback=self.login,
            formdata={'username': self.inst_login_name, 'enc_password': self.inst_login_pwd},
            headers={'X-CSRFToken': csrf}
        )

    def login(self, response: HtmlResponse):
        j_body = response.json()
        if j_body.get('authenticated'):
            for parse_user in self.parse_users:
                yield response.follow(f'/{parse_user}',
                                      callback=self.user_data_parse,
                                      cb_kwargs={'username': parse_user}
                                      )

    def user_data_parse(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)

        following_url = f'{self.friendship_url}/{user_id}/following/?count={self.following_count}'
        yield response.follow(following_url,
                              callback=self.user_following_parse,
                              cb_kwargs={'username': username, 'user_id': user_id},
                              headers=self.api_headers)

        follower_url = f'{self.friendship_url}/{user_id}/followers/?count={self.following_count}'
        yield response.follow(follower_url,
                              callback=self.user_follower_parse,
                              cb_kwargs={'username': username, 'user_id': user_id},
                              headers=self.api_headers)

    def user_following_parse(self, response: HtmlResponse, username, user_id):
        j_data = response.json()
        max_id = j_data.get('next_max_id')
        if max_id:
            following_url = f'{self.friendship_url}/{user_id}/following/?count={self.following_count}&max_id={max_id}'
            yield response.follow(following_url,
                                  callback=self.user_following_parse,
                                  cb_kwargs={'username': username, 'user_id': user_id},
                                  headers=self.api_headers)
        users = j_data.get('users')
        if users:
            for user in users:
                item = InstaparserItem(
                            from_user_id=user_id,
                            from_username=username,
                            follow_type='following',
                            user_id=user.get('pk'),
                            username=user.get('username'),
                            photo=user.get('profile_pic_url'),
                            _id=''
                        )
                yield item

    def user_follower_parse(self, response: HtmlResponse, username, user_id):
        j_data = response.json()
        max_id = j_data.get('next_max_id')
        if max_id:
            follower_url = f'{self.friendship_url}/{user_id}/followers/?count={self.following_count}&max_id={max_id}'
            yield response.follow(follower_url,
                                  callback=self.user_follower_parse,
                                  cb_kwargs={'username': username, 'user_id': user_id},
                                  headers=self.api_headers)
        users = j_data.get('users')
        if users:
            for user in users:
                item = InstaparserItem(
                            from_user_id=user_id,
                            from_username=username,
                            follow_type='follower',
                            user_id=user.get('pk'),
                            username=user.get('username'),
                            photo=user.get('profile_pic_url'),
                            _id=''
                        )
                yield item

    def fetch_csrf_token(self, text):
        ''' Get csrf-token for auth '''
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, username):
        try:
            matched = re.search(
                '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
            ).group()
            return json.loads(matched).get('id')
        except:
            return re.findall('\"id\":\"\\d+\"', text)[-1].split('"')[-2]
