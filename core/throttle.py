from rest_framework.throttling import UserRateThrottle


class CustomRateThrottle(UserRateThrottle):
    rate = '20/minute'