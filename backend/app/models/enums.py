from enum import StrEnum


class RoleEnum(StrEnum):
    USER = "user"
    ADMIN = "admin"


class UserStatusEnum(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    BUSY = "busy"


class ConversationTypeEnum(StrEnum):
    DIRECT = "direct"
    GROUP = "group"


class ConversationDisplayCategoryEnum(StrEnum):
    PRIVATE = "private"
    WORK = "work"
    OTHER = "other"


class MessageStatusEnum(StrEnum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    DELETED = "deleted"


class MessageCategoryEnum(StrEnum):
    PRIVATE = "private"
    URGENT = "urgent"
    ANNOUNCEMENT = "announcement"
    SPAM = "spam"
    OFFER = "offer"
    QUESTION = "question"


class NotificationTypeEnum(StrEnum):
    MESSAGE = "message"
    AUTOMATION = "automation"
    SYSTEM = "system"


class AutoResponderTriggerEnum(StrEnum):
    OFF_HOURS = "off_hours"
    KEYWORD = "keyword"
    QUESTION = "question"
