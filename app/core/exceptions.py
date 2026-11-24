from fastapi import HTTPException, status

class BiometricException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class LivenessFailedException(HTTPException):
    def __init__(self, detail: str = "Anti-spoofing verification failed: Potential presentation attack detected."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class CooldownActiveException(HTTPException):
    def __init__(self, detail: str = "Attendance already recorded recently. Cooldown active."):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
