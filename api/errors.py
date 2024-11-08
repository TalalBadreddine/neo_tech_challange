class APIErrorMessages:
    INVALID_CLIENT_ID = {'error': 'Invalid client_id'}
    USER_NOT_FOUND = {'error': 'User does not exist'}
    INVALID_CREDENTIALS = {'error': 'Invalid username or password.'}
    INTERNAL_SERVER_ERROR = {'error': 'Internal Server Error'}
    INVALID_INPUT = {'error': 'Invalid input'}
    USERNAME_EXISTS = {'error': 'A user with this username already exists.'}
    PASSWORD_TOO_SHORT = {'error': 'Password must be at least 8 characters long.'}
    INVALID_DATE_FORMAT = {'error': 'Invalid date format. Please use YYYY-MM-DD.'}
    START_DATE_BEFORE_END_DATE = {'error': 'start_date must be before end_date.'}