class BaseChatException(Exception):
    pass

class WrongCommandFormatChatException(BaseChatException):
    pass

class UserAlreadyExistsChatException(BaseChatException):
    pass

class WrongUsernameOrPasswordException(BaseChatException):
    pass

class UnknownDataProtocolException(BaseChatException):
    pass

class UserNotLoggedInException(BaseChatException):
    pass

class UserIsBannedException(BaseChatException):
    pass

class UserNotFoundException(BaseChatException):
    pass

class UnknownCommandException(BaseChatException):
    pass
