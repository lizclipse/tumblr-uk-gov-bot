#!/usr/bin/env python
import json
from dotenv import dotenv_values
from pytumblr2 import TumblrRestClient
from typing import Any, TypeVar, Optional, NamedTuple
from collections import namedtuple
from collections.abc import Callable, Iterable

from config import Config
from tumblr_neue import NpfContent
import gov.bills
import gov.divisions.commons
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


Div = TypeVar('Div')


def load_unposted_divs(
    page: Callable[[int, int], list[Div]],
    last_div: Callable[[Div], bool],
) -> list[Div]:
    divs: list[Div] = []

    size = 20
    offset = 0
    searching = True
    while searching:
        div_page = page(size, offset)
        for div in div_page:
            if last_div(div):
                searching = False
                break

            divs.append(div)

        offset += len(divs)

        if len(divs) > 100:
            searching = False

    # Want to go in time order
    divs.reverse()

    return divs


def commons_members() -> list[gov.members.Member]:
    print('loading commons members...')
    members: list[gov.members.Member] = []
    offset = 0

    while True:
        page = gov.members.search(
            House=1, IsCurrentMember=True, skip=offset
        )['items']
        print('\tpage', offset, len(page))
        if len(page) == 0:
            return members

        members.extend(map(lambda member: member['value'], page))
        offset = len(members)


class VoteTally(NamedTuple):
    total: int
    txt: str


def count_votes(
    parties: Iterable[str],
) -> list[VoteTally]:
    votes: dict[str, int] = {}
    vote_total = 0

    for party in parties:
        total = votes.setdefault(party, 0)
        votes[party] = total + 1
        vote_total += 1

    tally: list[VoteTally] = [
        VoteTally(
            total,
            '{}% {}'.format(
                round((total / vote_total) * 100, 1), party)
        )
        for party, total in votes.items()
    ]

    tally.sort(key=lambda item: item[0], reverse=True)
    return tally


def vote_count_str(tally: Iterable[VoteTally]) -> str:
    percents = map(lambda item: item.txt, tally)

    return ', '.join(percents)


def find_bill_for(title: str) -> Optional[gov.bills.Bill]:
    bill_index = title.find(' Bill')
    if bill_index < 0:
        return None

    term = title[:bill_index]
    if len(term) == 0:
        return None

    print('\tdivision potentially about a bill, searching', term)
    bills = gov.bills.search(SearchTerm=term, Take=1)
    items = bills['items']

    if len(items) == 0:
        return None

    return items[0]


class MemberVote(NamedTuple):
    name: str
    party: str


class MemberVoteTally(NamedTuple):
    party: str
    members: list[str]


def count_vote_groups(
    members: Iterable[MemberVote],
) -> list[MemberVoteTally]:
    tally: dict[str, list[str]] = {}

    for name, party in members:
        party_tally = tally.setdefault(party, [])
        party_tally.append(name)

    tally_list = [MemberVoteTally(party, members)
                  for party, members in tally.items()]

    for item in tally_list:
        item.members.sort()

    tally_list.sort(key=lambda item: len(item.members), reverse=True)
    return tally_list


def append_vote_groups(
    content: list[NpfContent],
    tally: Iterable[MemberVoteTally]
) -> None:
    for item in tally:
        content.append({
            'type': 'text',
            'text': '{} ({} vote{})'.format(
                item.party, len(item.members),
                's' if len(item.members) != 1 else ''
            ),
            'subtype': 'heading2',
        })

        members_list = "\n".join(item.members)
        content.append({
            'type': 'text',
            'text': members_list,
            'formatting': [{
                    'start': 0,
                    'end': len(members_list),
                    'type': 'small',
            }]
        })


def post_commons(client: TumblrRestClient, config: Config) -> None:
    print('collecting unpublished divisions')
    divs = load_unposted_divs(
        lambda size, offset: gov.divisions.commons.search(
            take=size, skip=offset),
        lambda div: div['DivisionId'] <= config.last_commons_vote
    )

    # members = commons_members()
    members_total = gov.members.total_members_commons()

    for div in divs:
        print('announcing', div['DivisionId'])
        # This API only returns the full ayes/noes for individual results
        div = gov.divisions.commons.get(div['DivisionId'])

        print('\tpreparing content for division')
        content: list[NpfContent] = [{
            'type': 'text',
            'text': 'Commons Vote',
            'subtype': 'heading1',
        }]

        NAME_SUFFIX = 'On: '
        name = NAME_SUFFIX + div['Title']

        content.append({
            'type': 'text',
            'text': name,
            'formatting': [
                {
                    'start': len(NAME_SUFFIX),
                    'end': len(name),
                    'type': 'italic',
                },
                {
                    'start': len(NAME_SUFFIX),
                    'end': len(name),
                    'type': 'link',
                    'url':
                    'https://votes.parliament.uk/votes/commons/division/' +
                        str(div['DivisionId'])
                },
            ]
        })

        vote_count_text = 'Ayes: {} '.format(div['AyeCount'])

        aye_tally = count_votes(
            map(lambda member: member['PartyAbbreviation'], div['Ayes']),
        )
        vote_aye_small_start = len(vote_count_text)
        vote_count_text += '({})'.format(vote_count_str(aye_tally))
        vote_aye_small_end = len(vote_count_text)

        vote_count_text += '\nNoes: {} '.format(div['NoCount'])

        noe_tally = count_votes(
            map(lambda member: member['PartyAbbreviation'], div['Noes']),
        )
        vote_noe_small_start = len(vote_count_text)
        vote_count_text += '({})'.format(vote_count_str(noe_tally))
        vote_noe_small_end = len(vote_count_text)

        vote_count_text += '\nAbsent: ~{} '.format(
            members_total - (div['AyeCount'] + div['NoCount'])
        )

        # absent_members: dict[int, str] = dict(
        #     [(member['id'], member['latestParty']['abbreviation'])
        #         for member in members]
        # )
        # for member in div['Ayes']:
        #     id = member['MemberId']
        #     if id in absent_members:
        #         del absent_members[id]
        # absent_tally = count_votes(absent_members.values())

        # vote_absent_small_start = len(vote_count_text)
        # vote_count_text += '({})'.format(vote_count_str(absent_tally))
        # vote_absent_small_end = len(vote_count_text)

        content.append({
            'type': 'text',
            'text': vote_count_text,
            'formatting': [
                {
                    'start': vote_aye_small_start,
                    'end': vote_aye_small_end,
                    'type': 'small',
                },
                {
                    'start': vote_noe_small_start,
                    'end': vote_noe_small_end,
                    'type': 'small',
                },
                # {
                #     'start': vote_absent_small_start,
                #     'end': vote_absent_small_end,
                #     'type': 'small',
                # },
            ]
        })

        short_bill = find_bill_for(div['Title'])
        if short_bill:
            print('\tfound bill', short_bill['shortTitle'])
            bill = gov.bills.get(short_bill['billId'])

            BILL_PREFIX = 'Likely Referenced Bill: '
            bill_name = BILL_PREFIX + bill['shortTitle']

            content.append({
                'type': 'text',
                'text': bill_name,
                'formatting': [
                    {
                        'start': len(BILL_PREFIX),
                        'end': len(bill_name),
                        'type': 'italic',
                    },
                    {
                        'start': len(BILL_PREFIX),
                        'end': len(bill_name),
                        'type': 'link',
                        'url':
                        'https://bills.parliament.uk/bills/{}' +
                            str(bill['billId'])
                    },
                ]
            })

            content.append({
                'type': 'text',
                'text': 'Description: {}'.format(bill['longTitle']),
            })

            bill_info = [
                'Originating house: {}'.format(bill['originatingHouse']),
                'Current house: {}'.format(bill['currentHouse']),
                'Bill Stage: {}'.format(bill['currentStage']['description']),
            ]

            content.append({
                'type': 'text',
                'text': '\n'.join(bill_info),
            })

        content.append({
            'type': 'text',
            'text': 'Individual Votes:',
            'subtype': 'heading2',
        })

        read_more_index = len(content) - 1

        aye_long_tally = count_vote_groups(
            map(lambda member: MemberVote(
                name=member['Name'], party=member['Party']), div['Ayes'])
        )
        content.append({
            'type': 'text',
            'text': 'Ayes',
            'subtype': 'heading1',
        })
        append_vote_groups(content, aye_long_tally)

        noe_long_tally = count_vote_groups(
            map(lambda member: MemberVote(
                name=member['Name'], party=member['Party']), div['Noes'])
        )
        content.append({
            'type': 'text',
            'text': 'Noes',
            'subtype': 'heading1',
        })
        append_vote_groups(content, noe_long_tally)

        print('\tcreating post for division')
        client.create_post(
            blog,
            content=content,
            tags=['test'],
            layout=[{
                'type': 'rows',
                'display': [{'blocks': [i]} for i in range(len(content))],
                'truncate_after': read_more_index,
            }]
        )

        print('\tdone!')
        return


if __name__ == '__main__':
    post_commons(client, config)
