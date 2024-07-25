#!/usr/bin/env python
from dotenv import dotenv_values
from pytumblr2 import TumblrRestClient
from typing import Any

from config import Config
from format import strip_html
from vote import VotePoster
import vote
import gov.bills
import gov.divisions.commons
import gov.divisions.lords
import gov.members


def missing_error() -> Any:
    raise KeyError()


env = dotenv_values()
client = TumblrRestClient(
    consumer_key=env['CONSUMER_KEY'] or missing_error(),
    consumer_secret=env['CONSUMER_SECRET'] or missing_error(),
    oauth_token=env['TOKEN'] or missing_error(),
    oauth_secret=env['TOKEN_SECRET'] or missing_error()
)

blog = env['BLOG'] or missing_error()
config_post_id = int(env['CONFIG_POST_ID'] or missing_error())

config = Config(client, blog, config_post_id)


class CommonsVotePoster(VotePoster):
    house = 'Commons'

    def __init__(self, blog: str, client: TumblrRestClient, config: Config):
        self.blog = blog
        self.client = client
        self.config = config
        self.members_total = gov.members.total_members_commons()

    @property
    def last_id(self) -> int:
        return self.config.last_commons_vote

    @last_id.setter
    def last_id(self, value: int) -> None:
        self.config.last_commons_vote = value

    def division_page(self, size: int, offset: int) -> list[vote.Div]:
        page = gov.divisions.commons.search(take=size, skip=offset)
        page = [gov.divisions.commons.get(div['DivisionId']) for div in page]

        return [vote.Div(
            id=div['DivisionId'],
            title_prefix='On: ',
            title=div['Title'],
            desc=None,
            yes=self._parse_members(div['Ayes']),
            yes_count=div['AyeCount'],
            no=self._parse_members(div['Noes']),
            no_count=div['NoCount'],
        ) for div in page]

    def _parse_members(
        self,
        members: list[gov.divisions.commons.Member]
    ) -> list[vote.Member]:
        return [vote.Member(
            name=member['Name'],
            sortName=member['Name'],
            party=member['Party'],
            abbr=member['PartyAbbreviation'],
        ) for member in members]

    def vote_url(self, id: int) -> str:
        return 'https://votes.parliament.uk/votes/commons/division/' + str(id)


class LordsVotePoster(VotePoster):
    house = 'Lords'

    def __init__(self, blog: str, client: TumblrRestClient, config: Config):
        self.blog = blog
        self.client = client
        self.config = config
        self.members_total = gov.members.total_members_lords()

    @property
    def last_id(self) -> int:
        return self.config.last_lords_vote

    @last_id.setter
    def last_id(self, value: int) -> None:
        self.config.last_lords_vote = value

    def division_page(self, size: int, offset: int) -> list[vote.Div]:
        page = gov.divisions.lords.search(take=size, skip=offset)

        return [vote.Div(
            id=div['divisionId'],
            title_prefix='On: ',
            title=div['title'],
            desc=strip_html(div['amendmentMotionNotes']),
            yes=self._parse_members(div['contents']),
            yes_count=div['authoritativeContentCount'],
            no=self._parse_members(div['notContents']),
            no_count=div['authoritativeNotContentCount'],
        ) for div in page]

    def _parse_members(
        self,
        members: list[gov.divisions.lords.Member]
    ) -> list[vote.Member]:
        return [vote.Member(
            name=member['listAs'],
            sortName=member['listAs'],
            party=member['party'],
            abbr=member['partyAbbreviation'],
        ) for member in members]

    def vote_url(self, id: int) -> str:
        return 'https://votes.parliament.uk/votes/lords/division/' + str(id)


if __name__ == '__main__':
    # TODO: look into why some bills seem to be missing for the commons
    # eg. 1825, 1826
    print('====> Commons')
    CommonsVotePoster(blog, client, config).post()
    # TODO: look into why some bills seem to be missing for the lords
    # eg. 3124, 3127
    print('====> Lords')
    LordsVotePoster(blog, client, config).post()
