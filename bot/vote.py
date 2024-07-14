from pytumblr2 import TumblrRestClient
from typing import Optional, NamedTuple
from collections.abc import Iterable

from tumblr_neue import NpfContent
import gov.bills
import gov.members


class Member(NamedTuple):
    name: str
    sortName: str
    party: str
    abbr: str


class Div(NamedTuple):
    id: int
    title_prefix: str
    title: str
    desc: Optional[str]
    yes: list[Member]
    yes_count: int
    no: list[Member]
    no_count: int


class VoteTally(NamedTuple):
    total: int
    txt: str


class MemberVoteTally(NamedTuple):
    party: str
    members: list[Member]


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


class VotePoster:
    blog: str
    client: TumblrRestClient
    last_id: int
    members_total: int
    house: str

    def division_page(self, size: int, offset: int) -> list[Div]:
        raise NotImplementedError()

    def vote_url(self, id: int) -> str:
        raise NotImplementedError()

    def post(self) -> None:
        print('collecting unpublished divisions')
        divs = self.load_unposted_divs()

        for div in divs:
            print('preparing content for division', div.id)
            post = Post(div)

            post.header(self.house, self.vote_url(div.id))
            post.tallies(self.members_total)

            short_bill = find_bill_for(div.title)
            if short_bill:
                print('\tfound bill', short_bill['shortTitle'])
                bill = gov.bills.get(short_bill['billId'])
                post.bill(bill)

            read_more_index = post.indv_votes()

            print('\tcreating post for division')
            self.client.create_post(
                self.blog,
                content=post.content,
                tags=['test'],
                layout=[{
                    'type': 'rows',
                    'display': [{'blocks': [i]}
                        for i in range(len(post.content))],
                    'truncate_after': read_more_index,
                }]
            )

            print('\tdone!')
            return

    def load_unposted_divs(self) -> list[Div]:
        divs: list[Div] = []

        size = 20
        offset = 0
        searching = True
        while searching:
            div_page = self.division_page(size, offset)
            for div in div_page:
                if div.id <= self.last_id:
                    searching = False
                    break

                divs.append(div)

            offset = len(divs)

            if len(divs) > 100:
                searching = False

        # Want to go in time order
        divs.reverse()

        return divs

    def vote_count_str(self, tally: Iterable[VoteTally]) -> str:
        percents = map(lambda item: item.txt, tally)

        return ', '.join(percents)


class Post:
    def __init__(self, div: Div) -> None:
        self.div = div
        self.content: list[NpfContent] = []

    def header(self, house: str, vote_url: str) -> None:
        self.content.append({
            'type': 'text',
            'text': '{} Vote'.format(house),
            'subtype': 'heading1',
        })

        title = self.div.title_prefix + self.div.title

        self.content.append({
            'type': 'text',
            'text': title,
            'formatting': [
                {
                    'start': len(self.div.title_prefix),
                    'end': len(title),
                    'type': 'italic',
                },
                {
                    'start': len(self.div.title_prefix),
                    'end': len(title),
                    'type': 'link',
                    'url': vote_url,
                },
            ]
        })

        if self.div.desc:
            self.content.append({
                'type': 'text',
                'text': self.div.desc
            })

    def tallies(self, members_total: int) -> None:
        vote_count_text = 'Ayes: {} '.format(self.div.yes_count)

        aye_tally = self._count_votes(self.div.yes)
        vote_aye_small_start = len(vote_count_text)
        vote_count_text += '({})'.format(self._vote_count_str(aye_tally))
        vote_aye_small_end = len(vote_count_text)

        vote_count_text += '\nNoes: {} '.format(self.div.no_count)

        noe_tally = self._count_votes(self.div.no)
        vote_noe_small_start = len(vote_count_text)
        vote_count_text += '({})'.format(self._vote_count_str(noe_tally))
        vote_noe_small_end = len(vote_count_text)

        vote_count_text += '\nAbsent: ~{} '.format(
            members_total - (self.div.yes_count + self.div.no_count)
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

        self.content.append({
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

    def bill(self, bill: gov.bills.FullBill) -> None:
        BILL_PREFIX = 'Likely Referenced Bill: '
        bill_name = BILL_PREFIX + bill['shortTitle']

        self.content.append({
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

        self.content.append({
            'type': 'text',
            'text': 'Description: {}'.format(bill['longTitle']),
        })

        bill_info = [
            'Originating house: {}'.format(bill['originatingHouse']),
            'Current house: {}'.format(bill['currentHouse']),
            'Bill Stage: {}'.format(
                bill['currentStage']['description']),
        ]

        self.content.append({
            'type': 'text',
            'text': '\n'.join(bill_info),
        })

    def indv_votes(self) -> int:
        self.content.append({
            'type': 'text',
            'text': 'Individual Votes:',
            'subtype': 'heading2',
        })

        read_more_index = len(self.content) - 1

        aye_long_tally = self._count_vote_groups(self.div.yes)
        self.content.append({
            'type': 'text',
            'text': 'Ayes',
            'subtype': 'heading1',
        })
        self._append_vote_groups(aye_long_tally)

        noe_long_tally = self._count_vote_groups(self.div.no)
        self.content.append({
            'type': 'text',
            'text': 'Noes',
            'subtype': 'heading1',
        })
        self._append_vote_groups(noe_long_tally)

        return read_more_index

    def _count_votes(
        self,
        members: Iterable[Member],
    ) -> list[VoteTally]:
        votes: dict[str, int] = {}
        vote_total = 0

        for member in members:
            total = votes.setdefault(member.abbr, 0)
            votes[member.abbr] = total + 1
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

    def _vote_count_str(self, tally: Iterable[VoteTally]) -> str:
        percents = map(lambda item: item.txt, tally)

        return ', '.join(percents)

    def _count_vote_groups(
        self,
        members: Iterable[Member],
    ) -> list[MemberVoteTally]:
        tally: dict[str, list[Member]] = {}

        for member in members:
            party_tally = tally.setdefault(member.party, [])
            party_tally.append(member)

        tally_list = [MemberVoteTally(party, members)
                      for party, members in tally.items()]

        for item in tally_list:
            item.members.sort(key=lambda member: member.sortName)

        tally_list.sort(key=lambda item: len(item.members), reverse=True)
        return tally_list

    def _append_vote_groups(
        self,
        tally: Iterable[MemberVoteTally]
    ) -> None:
        for item in tally:
            self.content.append({
                'type': 'text',
                'text': '{} ({} vote{})'.format(
                    item.party, len(item.members),
                    's' if len(item.members) != 1 else ''
                ),
                'subtype': 'heading2',
            })

            members_list = "\n".join(map(lambda m: m.name, item.members))
            self.content.append({
                'type': 'text',
                'text': members_list,
                'formatting': [{
                        'start': 0,
                        'end': len(members_list),
                        'type': 'small',
                }]
            })
