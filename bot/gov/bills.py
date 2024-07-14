import httpx
from typing import NotRequired, TypedDict, Union, Literal, Unpack, cast, Any

BASE_URL = 'https://bills-api.parliament.uk'


ParliamentHouse = Union[
    Literal['All'],
    Literal['Commons'],
    Literal['Lords'],
    Literal['Unassigned'],
]


class Stage(TypedDict):
    id: int
    stageId: int
    sessionId: int
    description: str
    abbreviation: str
    house: ParliamentHouse
    stageSittings: list
    sortOrder: int


class Bill(TypedDict):
    billId: int
    shortTitle: str
    currentHouse: ParliamentHouse
    originatingHouse: ParliamentHouse
    lastUpdate: str  # Date
    billWithdrawn: str  # Date
    isDefeated: bool
    billTypeId: int
    introducedSessionId: int
    includedSessionIds: list[int]
    isAct: bool
    currentStage: Stage


class FullBill(Bill):
    longTitle: str
    summary: str
    sponsors: list
    promoters: list
    petitioningPeriod: str
    petitionInformation: str
    agent: dict


class BillsSearchResult(TypedDict):
    items: list[Bill]
    totalResults: int
    itemsPerPage: str


class BillsSearchParams(TypedDict):
    SearchTerm: NotRequired[str]
    Skip: NotRequired[int]
    Take: NotRequired[int]


def search(**params: Unpack[BillsSearchParams]) -> BillsSearchResult:
    return httpx.get(
        BASE_URL + '/api/v1/Bills',
        params=cast(Any, params)
    ).raise_for_status().json()


def get(id: int) -> FullBill:
    return httpx.get(
        BASE_URL + '/api/v1/Bills/{}'.format(id),
    ).raise_for_status().json()
