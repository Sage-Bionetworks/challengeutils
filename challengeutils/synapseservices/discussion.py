from .base_service import Service, deserialize_model


class Forum(Service):
    def __init__(self, id=None, projectId=None, etag=None):

        self.openapi_types = {
            'id': str,
            'projectid': str,
            'etag': str
        }

        self.attribute_map = {
            'id': 'id',
            'projectid': 'projectId',
            'etag': 'etag'
        }

        self._id = id
        self._projectid = projectId
        self._etag = etag

    @classmethod
    def from_dict(cls, dikt) -> 'Forum':
        """Returns the dict as a model"""
        return deserialize_model(dikt, cls)

    @property
    def id(self):
        """The `id` property of this Challenge."""
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def projectid(self):
        """The `projectId` property of this Challenge."""
        return self._projectid

    @projectid.setter
    def projectid(self, value):
        if value is None:
            raise ValueError("Invalid value for `projectid`, must not be `None`")  # noqa: E501

        self._projectid = value

    @property
    def etag(self):
        """The `etag` property of this Challenge."""
        return self._etag

    @etag.setter
    def etag(self, value):
        self._etag = value


class Thread(Service):
    def __init__(
            self, id: str = None, forumId: str = None, projectId: str = None,
            title: str = None, createdOn: str = None, createdBy: str = None,
            modifiedOn: str = None, etag: str = None, messageKey: str = None,
            numberOfViews: int = None, numberOfReplies: int = None,
            lastActivity: str = None, activeAuthors: list = None,
            isEdited: bool = False, isDeleted: bool = False,
            isPinned: bool = False
        ):

        self.openapi_types = {
            'id': str,
            'forumid': str,
            'projectid': str,
            'title': str,
            'createdon': str,
            'createdby': str,
            'modifiedon': str,
            'etag': str,
            'messagekey': str,
            'number_of_views': int,
            'number_of_replies': int,
            'last_activity': str,
            'active_authors': list,
            'is_edited': bool,
            'is_deleted': bool,
            'is_pinned': bool
        }

        self.attribute_map = {
            'id': 'id',
            'forumid': 'forumId',
            'projectid': 'projectId',
            'title': 'title',
            'createdon': 'createdOn',
            'createdby': 'createdBy',
            'modifiedon': 'modifiedOn',
            'etag': 'etag',
            'messagekey': 'messageKey',
            'number_of_views': 'numberOfViews',
            'number_of_replies': 'numberOfReplies',
            'last_activity': 'lastActivity',
            'active_authors': 'activeAuthors',
            'is_edited': 'isEdited',
            'is_deleted': 'isDeleted',
            'is_pinned': 'isPinned'
        }

        self._id = id
        self._forumid = forumId
        self._projectid = projectId
        self._title = title
        self._createdon = createdOn
        self._createdby = createdBy
        self._modifiedon = modifiedOn
        self._etag = etag
        self._messagekey = messageKey
        self._number_of_views = numberOfViews
        self._number_of_replies = numberOfReplies
        self._last_activity = lastActivity
        self._active_authors = activeAuthors
        self._is_edited = isEdited
        self._is_deleted = isDeleted
        self._is_pinned = isPinned

    @classmethod
    def from_dict(cls, dikt) -> 'Thread':
        """Returns the dict as a model"""
        return deserialize_model(dikt, cls)

    @property
    def id(self):
        """The `id` property of this Challenge."""
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def forumid(self):
        """The `forumid` property of this Challenge."""
        return self._forumid

    @forumid.setter
    def forumid(self, value):
        self._forumid = value

    @property
    def projectid(self):
        """The `projectid` property of this Challenge."""
        return self._projectid

    @projectid.setter
    def projectid(self, value):
        if value is None:
            raise ValueError("Invalid value for `projectid`, must not be `None`")  # noqa: E501

        self._projectid = value

    @property
    def title(self):
        """The `title` property of this Challenge."""
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def createdon(self):
        """The `createdon` property of this Challenge."""
        return self._createdon

    @createdon.setter
    def createdon(self, value):
        self._createdon = value

    @property
    def createdby(self):
        """The `createdby` property of this Challenge."""
        return self._createdby

    @createdby.setter
    def createdby(self, value):
        self._createdby = value

    @property
    def modifiedon(self):
        """The `modifiedon` property of this Challenge."""
        return self._modifiedon

    @modifiedon.setter
    def modifiedon(self, value):
        self._modifiedon = value

    @property
    def etag(self):
        """The `etag` property of this Challenge."""
        return self._etag

    @etag.setter
    def etag(self, value):
        self._etag = value

    @property
    def messagekey(self):
        """The `projectId` property of this Challenge."""
        return self._messagekey

    @messagekey.setter
    def messagekey(self, value):
        self._messagekey = value

    @property
    def number_of_views(self):
        """The `number_of_views` property of this Challenge."""
        return self._number_of_views

    @number_of_views.setter
    def number_of_views(self, value):
        self._number_of_views = value

    @property
    def number_of_replies(self):
        """The `number_of_replies` property of this Challenge."""
        return self._number_of_replies

    @number_of_replies.setter
    def number_of_replies(self, value):
        self._number_of_replies = value

    @property
    def last_activity(self):
        """The `last_activity` property of this Challenge."""
        return self._last_activity

    @last_activity.setter
    def last_activity(self, value):
        self._last_activity = value

    @property
    def active_authors(self):
        """The `active_authors` property of this Challenge."""
        return self._active_authors

    @active_authors.setter
    def active_authors(self, value):
        self._active_authors = value

    @property
    def is_edited(self):
        """The `is_edited` property of this Challenge."""
        return self._is_edited

    @is_edited.setter
    def is_edited(self, value):
        self._is_edited = value

    @property
    def is_deleted(self):
        """The `is_deleted` property of this Challenge."""
        return self._is_deleted

    @is_deleted.setter
    def is_deleted(self, value):
        self._is_deleted = value

    @property
    def is_pinned(self):
        """The `is_deleted` property of this Challenge."""
        return self._is_pinned

    @is_pinned.setter
    def is_pinned(self, value):
        self._is_pinned = value


class Reply(Service):
    def __init__(
            self, id: str = None, threadId: str = None, forumId: str = None,
            projectId: str = None, createdOn: str = None,
            createdBy: str = None, modifiedOn: str = None, etag: str = None,
            messageKey: str = None, isEdited: bool = False,
            isDeleted: bool = False
        ):

        self.openapi_types = {
            'id': str,
            'threadid': str,
            'forumid': str,
            'projectid': str,
            'createdon': str,
            'createdby': str,
            'modifiedon': str,
            'etag': str,
            'messagekey': str,
            'is_edited': bool,
            'is_deleted': bool,
        }

        self.attribute_map = {
            'id': 'id',
            'threadid': 'threadId',
            'forumid': 'forumId',
            'projectid': 'projectId',
            'createdon': 'createdOn',
            'createdby': 'createdBy',
            'modifiedon': 'modifiedOn',
            'etag': 'etag',
            'messagekey': 'messageKey',
            'is_edited': 'isEdited',
            'is_deleted': 'isDeleted',
        }

        self._id = id
        self._threadid = threadId
        self._forumid = forumId
        self._projectid = projectId
        self._createdon = createdOn
        self._createdby = createdBy
        self._modifiedon = modifiedOn
        self._etag = etag
        self._messagekey = messageKey
        self._is_edited = isEdited
        self._is_deleted = isDeleted

    @classmethod
    def from_dict(cls, dikt) -> 'Thread':
        """Returns the dict as a model"""
        return deserialize_model(dikt, cls)

    @property
    def id(self):
        """The `id` property of this Challenge."""
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def threadid(self):
        """The `threadid` property of this Challenge."""
        return self._threadid

    @threadid.setter
    def threadid(self, value):
        self._threadid = value

    @property
    def forumid(self):
        """The `forumid` property of this Challenge."""
        return self._forumid

    @forumid.setter
    def forumid(self, value):
        self._forumid = value

    @property
    def projectid(self):
        """The `projectid` property of this Challenge."""
        return self._projectid

    @projectid.setter
    def projectid(self, value):
        if value is None:
            raise ValueError("Invalid value for `projectid`, must not be `None`")  # noqa: E501

        self._projectid = value

    @property
    def createdon(self):
        """The `createdon` property of this Challenge."""
        return self._createdon

    @createdon.setter
    def createdon(self, value):
        self._createdon = value

    @property
    def createdby(self):
        """The `createdby` property of this Challenge."""
        return self._createdby

    @createdby.setter
    def createdby(self, value):
        self._createdby = value

    @property
    def modifiedon(self):
        """The `modifiedon` property of this Challenge."""
        return self._modifiedon

    @modifiedon.setter
    def modifiedon(self, value):
        self._modifiedon = value

    @property
    def etag(self):
        """The `etag` property of this Challenge."""
        return self._etag

    @etag.setter
    def etag(self, value):
        self._etag = value

    @property
    def messagekey(self):
        """The `projectId` property of this Challenge."""
        return self._messagekey

    @messagekey.setter
    def messagekey(self, value):
        self._messagekey = value

    @property
    def is_edited(self):
        """The `is_edited` property of this Challenge."""
        return self._is_edited

    @is_edited.setter
    def is_edited(self, value):
        self._is_edited = value

    @property
    def is_deleted(self):
        """The `is_deleted` property of this Challenge."""
        return self._is_deleted

    @is_deleted.setter
    def is_deleted(self, value):
        self._is_deleted = value
