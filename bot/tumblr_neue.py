from typing import TypedDict, Literal, Union, NotRequired, List


class _TextFormatting(TypedDict):
    start: int
    end: int


class NpfTextFormattingBasic(_TextFormatting):
    type: Union[
        Literal['bold'],
        Literal['italic'],
        Literal['strikethrough'],
        Literal['small'],
    ]


class NpfTextFormattingLink(_TextFormatting):
    type: Literal['link']
    url: str


class NpfTextFormattingMentionBlog(TypedDict):
    uuid: str


class NpfTextFormattingMention(_TextFormatting):
    type: Literal['mention']
    blog: NpfTextFormattingMentionBlog


class NpfTextFormattingColor(_TextFormatting):
    type: Literal['color']
    hex: str


NpfTextFormatting = Union[
    NpfTextFormattingBasic,
    NpfTextFormattingLink,
    NpfTextFormattingMention,
    NpfTextFormattingColor,
]


class NpfTextContent(TypedDict):
    type: Literal['text']
    text: str
    subtype: NotRequired[Union[
        Literal['heading1'],
        Literal['heading2'],
        Literal['quirky'],
        Literal['quote'],
        Literal['indented'],
        Literal['chat'],
        Literal['ordered-list-item'],
        Literal['unordered-list-item'],
    ]]
    formatting: NotRequired[List[NpfTextFormatting]]


NpfContent = Union[NpfTextContent]
