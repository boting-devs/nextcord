# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from . import abc
from .asset import Asset
from .colour import Colour
from .enums import DefaultAvatar
from .flags import PublicUserFlags
from .utils import MISSING, obj_to_base64_data, snowflake_time

if TYPE_CHECKING:
    from datetime import datetime

    from typing_extensions import Self

    from .channel import DMChannel
    from .file import File
    from .guild import Guild
    from .message import Attachment, Message
    from .state import ConnectionState
    from .types.channel import DMChannel as DMChannelPayload
    from .types.user import PartialUser as PartialUserPayload, User as UserPayload


__all__ = (
    "User",
    "ClientUser",
)


class _UserTag:
    __slots__ = ()
    id: int


class BaseUser(_UserTag):
    __slots__ = (
        "name",
        "id",
        "discriminator",
        "_state",
    )

    if TYPE_CHECKING:
        name: str
        id: int
        discriminator: str
        _state: ConnectionState

    def __init__(
        self, *, state: ConnectionState, data: Union[PartialUserPayload, UserPayload]
    ) -> None:
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return f"<BaseUser id={self.id} name={self.name!r} discriminator={self.discriminator!r}>"

    def __str__(self) -> str:
        return f"{self.name}#{self.discriminator}"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, _UserTag) and other.id == self.id

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return self.id >> 22

    def _update(self, data: Union[PartialUserPayload, UserPayload]) -> None:
        self.name = data["username"]
        self.id = int(data["id"])
        self.discriminator = data["discriminator"]

    @classmethod
    def _copy(cls, user: Self) -> Self:
        self = cls.__new__(cls)  # bypass __init__

        self.name = user.name
        self.id = user.id
        self.discriminator = user.discriminator
        self._state = user._state

        return self

    def _to_minimal_user_json(self) -> Dict[str, Any]:
        return {
            "username": self.name,
            "id": self.id,
            "discriminator": self.discriminator,
        }

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user."""
        return f"<@{self.id}>"

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the user's creation time in UTC.

        This is when the user's Discord account was created.
        """
        return snowflake_time(self.id)

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name.

        For regular users this is just their username, but
        if they have a guild specific nickname then that
        is returned instead.
        """
        return self.name

    def mentioned_in(self, message: Message) -> bool:
        """Checks if the user is mentioned in the specified message.

        Parameters
        ----------
        message: :class:`Message`
            The message to check if you're mentioned in.

        Returns
        -------
        :class:`bool`
            Indicates if the user is mentioned in the message.
        """

        if message.mention_everyone:
            return True

        return any(user.id == self.id for user in message.mentions)


class ClientUser(BaseUser):
    """Represents your Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's name with discriminator.

    Attributes
    ----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    discriminator: :class:`str`
        The user's discriminator. This is given when the username has conflicts.
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).

        .. versionadded:: 1.3

    verified: :class:`bool`
        Specifies if the user's email is verified.
    locale: Optional[:class:`str`]
        The IETF language tag used to identify the language the user is using.
    mfa_enabled: :class:`bool`
        Specifies if the user has MFA turned on and working.
    """

    __slots__ = ("__weakref__",)

    def __repr__(self) -> str:
        return f"<ClientUser id={self.id} name={self.name!r} discriminator={self.discriminator!r}>"

    def _update(self, data: UserPayload) -> None:
        super()._update(data)

    async def edit(
        self,
        *,
        username: str = MISSING,
        avatar: Optional[Union[bytes, Asset, Attachment, File]] = MISSING,
    ) -> ClientUser:
        """|coro|

        Edits the current profile of the client.

        .. note::

            To upload an avatar, a :term:`py:bytes-like object` must be passed in that
            represents the image being uploaded. If this is done through a file
            then the file must be opened via ``open('some_filename', 'rb')`` and
            the :term:`py:bytes-like object` is given through the use of ``fp.read()``.

            The only image formats supported for uploading is JPEG and PNG.

        .. versionchanged:: 2.0
            The edit is no longer in-place, instead the newly edited client user is returned.

        .. versionchanged:: 2.1
            The ``avatar`` parameter now accepts :class:`File`, :class:`Attachment`, and :class:`Asset`.

        Parameters
        ----------
        username: :class:`str`
            The new username you wish to change to.
        avatar: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`, or :class:`Asset`
            representing the image to upload. Could be ``None`` to denote no avatar.

        Raises
        ------
        HTTPException
            Editing your profile failed.
        InvalidArgument
            Wrong image format passed for ``avatar``.

        Returns
        -------
        :class:`ClientUser`
            The newly edited client user.
        """
        payload: Dict[str, Any] = {}
        if username is not MISSING:
            payload["username"] = username
        if avatar is not MISSING:
            payload["avatar"] = await obj_to_base64_data(avatar)

        data: UserPayload = await self._state.http.edit_profile(payload)
        return ClientUser(state=self._state, data=data)


class User(BaseUser, abc.Messageable):
    """Represents a Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's name with discriminator.

    Attributes
    ----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    discriminator: :class:`str`
        The user's discriminator. This is given when the username has conflicts.
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).
    """

    __slots__ = ("_stored",)

    def __init__(
        self, *, state: ConnectionState, data: Union[PartialUserPayload, UserPayload]
    ) -> None:
        super().__init__(state=state, data=data)
        self._stored: bool = False

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name!r} discriminator={self.discriminator!r}>"

    def __del__(self) -> None:
        try:
            if self._stored:
                self._state.deref_user(self.id)
        except Exception:
            pass

    @classmethod
    def _copy(cls, user: User):
        self = super()._copy(user)
        self._stored = False
        return self

    async def _get_channel(self) -> DMChannel:
        ch = await self.create_dm()
        return ch

    @property
    def dm_channel(self) -> Optional[DMChannel]:
        """Optional[:class:`DMChannel`]: Returns the channel associated with this user if it exists.

        If this returns ``None``, you can create a DM channel by calling the
        :meth:`create_dm` coroutine function.
        """
        return self._state._get_private_channel_by_user(self.id)

    @property
    def mutual_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: The guilds that the user shares with the client.

        .. note::

            This will only return mutual guilds within the client's internal cache.

        .. versionadded:: 1.7
        """
        return [guild for guild in self._state._guilds.values() if guild.get_member(self.id)]

    async def create_dm(self) -> DMChannel:
        """|coro|

        Creates a :class:`DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.

        Returns
        -------
        :class:`.DMChannel`
            The channel that was created.
        """
        found = self.dm_channel
        if found is not None:
            return found

        state = self._state
        data: DMChannelPayload = await state.http.start_private_message(self.id)
        return state.add_dm_channel(data)
