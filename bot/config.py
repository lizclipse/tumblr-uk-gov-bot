from pytumblr2 import TumblrRestClient
from datetime import datetime
import yaml

from tumblr_neue import NpfContent


class Config:
    _last_commons_vote: int
    _last_lords_vote: int

    def __init__(self,
                 client: TumblrRestClient,
                 blog: str,
                 config_post_id: int):
        self._client = client
        self._blog = blog
        self._config_post_id = config_post_id

        config_post = client.get_single_post(blog, config_post_id)
        content = config_post['content'][0]['text']
        config = yaml.load(content, Loader=yaml.SafeLoader)

        self._last_commons_vote = config['last_commons_vote']
        self._last_lords_vote = config['last_lords_vote']

    @property
    def last_commons_vote(self) -> int:
        return self._last_commons_vote

    @last_commons_vote.setter
    def last_commons_vote(self, value: int) -> None:
        self._last_commons_vote = value
        self._save()

    @property
    def last_lords_vote(self) -> int:
        return self._last_lords_vote

    @last_lords_vote.setter
    def last_lords_vote(self, value: int) -> None:
        self._last_lords_vote = value
        self._save()

    def _save(self) -> None:
        cfg = yaml.dump({
            'last_commons_vote': self._last_commons_vote,
            'last_lords_vote': self._last_lords_vote,
        })

        content: list[NpfContent] = [{
            'type': 'text',
            'text': cfg
        }]

        self._client.edit_post(
            self._blog, self._config_post_id,
            content=content,
            tags=[
                'config',
                "this post exists to store config data because it's easier than some local method",
                f'updated: {datetime.utcnow().isoformat()}',
                'non-wankerwatch',
            ]
        )
        print('config saved')
