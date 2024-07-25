import httpx
from typing import NotRequired, TypedDict, Union, Literal, Unpack, cast, Any

BASE_URL = 'https://members-api.parliament.uk'


class Party(TypedDict):
    id: int
    name: str
    abbreviation: str
    backgroundColour: str
    foregroundColour: str
    isLordsMainParty: bool
    isLordsSpiritualParty: bool
    governmentType: int
    isIndependentParty: bool


class Member(TypedDict):
    id: int
    nameListAs: str
    nameDisplayAs: str
    nameFullTitle: str
    nameAddressAs: str
    latestParty: Party


def total_members_commons() -> int:
    return search(
        House=1,
        IsCurrentMember=True,
        skip=0,
        take=1
    )['totalResults']


def total_members_lords() -> int:
    return search(
        House=2,
        IsCurrentMember=True,
        skip=0,
        take=1
    )['totalResults']


class MemberSearchResultMember(TypedDict):
    value: Member


class MemberSearchResult(TypedDict):
    items: list[MemberSearchResultMember]
    totalResults: int
    resultContext: str
    skip: int
    take: int


class MemberSearchParams(TypedDict):
    House: NotRequired[Union[Literal[1], Literal[2]]]
    IsCurrentMember: NotRequired[bool]
    skip: NotRequired[int]
    take: NotRequired[int]


def search(**params: Unpack[MemberSearchParams]) -> MemberSearchResult:
    return httpx.get(
        BASE_URL + '/api/Members/Search',
        params=cast(Any, params),
        timeout=30.0,
    ).raise_for_status().json()
