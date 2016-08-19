
# Core

class InvalidBDUSSException(Exception):
    pass


class InvalidBar(Exception):
    pass


class LoginFailure(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class InvalidPassword(LoginFailure):
    pass


class InvalidCaptcha(LoginFailure):
    pass


class InvalidUsername(LoginFailure):
    pass


class DangerousEnvironment(LoginFailure):
    pass

# Core

# Command line

class UserDuplicated(Exception):
    pass


class UserNotFound(Exception):
    pass

# Command line
