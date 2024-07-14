import httpx
from typing import TypedDict, Unpack, NotRequired, cast, Any, Optional


class Member(TypedDict):
    memberId: int
    name: str
    listAs: str
    memberFrom: str
    party: str
    partyColour: str
    partyAbbreviation: str
    partyIsMainParty: bool


class Division(TypedDict):
    divisionId: int
    date: str  # Date
    number: int
    notes: Optional[str]
    title: str
    isWhipped: bool
    isGovernmentContent: bool
    authoritativeContentCount: int
    authoritativeNotContentCount: int
    divisionHadTellers: bool
    tellerContentCount: int
    tellerNotContentCount: int
    memberContentCount: int
    memberNotContentCount: int
    sponsoringMemberId: int
    isHouse: bool
    amendmentMotionNotes: str
    isGovernmentWin: bool
    remoteVotingStart: str  # Date
    remoteVotingEnd: str  # Date
    divisionWasExclusivelyRemote: bool
    contentTellers: list[Member]
    notContentTellers: list[Member]
    contents: list[Member]
    notContents: list[Member]


DivisionSearchParams = TypedDict('DivisionSearchParams', {
    'MemberId': NotRequired[int],
    'SearchTerm': NotRequired[str],
    'IncludeWhenMemberWasTeller': NotRequired[bool],
    'StartDate': NotRequired[str],
    'EndDate': NotRequired[str],
    'DivisionNumber': NotRequired[int],
    'TotalVotesCast.Comparator': NotRequired[str],
    'TotalVotesCast.ValueToCompare': NotRequired[int],
    'Majority.Comparator': NotRequired[str],
    'Majority.ValueToCompare': NotRequired[int],
    'skip': NotRequired[int],
    'take': NotRequired[int],
})


BASE_URL = 'https://lordsvotes-api.parliament.uk/'


def search(**params: Unpack[DivisionSearchParams]) -> list[Division]:
    return httpx.get(
        BASE_URL + '/data/Divisions/search',
        params=cast(Any, params)
    ).raise_for_status().json()
