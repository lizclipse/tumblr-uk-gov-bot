import httpx
from typing import TypedDict, Unpack, NotRequired, cast, Any
from datetime import date


class Member(TypedDict):
    MemberId: int
    Name: str
    Party: str
    SubParty: str
    PartyColour: str
    PartyAbbreviation: str
    MemberFrom: str
    ListAs: str
    ProxyName: str


class Division(TypedDict):
    DivisionId: int
    Date: str  # Date
    PublicationUpdated: str  # Date
    Number: int
    IsDeferred: bool
    EVELType: str
    EVELCountry: str
    Title: str
    AyeCount: int
    NoCount: int
    DoubleMajorityAyeCount: int
    DoubleMajorityNoCount: int
    AyeTellers: list[Member]
    NoTellers: list[Member]
    Ayes: list[Member]
    Noes: list[Member]
    FriendlyDescription: str
    FriendlyTitle: str
    NoVoteRecorded: list[Member]
    RemoteVotingStart: str  # Date
    RemoteVotingEnd: str  # Date


class DivisionSearchParams(TypedDict):
    skip: NotRequired[int]
    take: NotRequired[int]
    searchTerm: NotRequired[str]
    memberId: NotRequired[int]
    includeWhenMemberWasTeller: NotRequired[bool]
    startDate: NotRequired[date]
    endDate: NotRequired[date]
    divisionNumber: NotRequired[int]


BASE_URL = 'https://commonsvotes-api.parliament.uk'


def search(**params: Unpack[DivisionSearchParams]) -> list[Division]:
    return httpx.get(
        BASE_URL + '/data/divisions.json/search',
        params=cast(Any, params),
        timeout=30.0,
    ).raise_for_status().json()


def get(id: int) -> Division:
    return httpx.get(
        BASE_URL + '/data/division/{}.json'.format(id),
        timeout=30.0,
    ).raise_for_status().json()
