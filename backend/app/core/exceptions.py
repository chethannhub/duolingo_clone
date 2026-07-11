from enum import StrEnum
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ErrorCode(StrEnum):
    COURSE_NOT_FOUND = "COURSE_NOT_FOUND"
    COURSE_NOT_ENROLLED = "COURSE_NOT_ENROLLED"
    LEVEL_LOCKED = "LEVEL_LOCKED"
    LESSON_NOT_FOUND = "LESSON_NOT_FOUND"
    LESSON_NOT_AVAILABLE = "LESSON_NOT_AVAILABLE"
    OUT_OF_HEARTS = "OUT_OF_HEARTS"
    ATTEMPT_NOT_FOUND = "ATTEMPT_NOT_FOUND"
    ATTEMPT_NOT_ACTIVE = "ATTEMPT_NOT_ACTIVE"
    ATTEMPT_ALREADY_COMPLETED = "ATTEMPT_ALREADY_COMPLETED"
    EXERCISE_NOT_CURRENT = "EXERCISE_NOT_CURRENT"
    ANSWER_ALREADY_SUBMITTED = "ANSWER_ALREADY_SUBMITTED"
    ANSWER_PAYLOAD_INVALID = "ANSWER_PAYLOAD_INVALID"
    REWARD_LOCKED = "REWARD_LOCKED"
    REWARD_ALREADY_CLAIMED = "REWARD_ALREADY_CLAIMED"
    INSUFFICIENT_GEMS = "INSUFFICIENT_GEMS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ApiError(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: ErrorCode,
        message: str,
        details: dict | None = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or {}


def error_response(code: str, message: str, status_code: int, details: dict | None = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": str(uuid4()),
            }
        },
    )


async def api_error_handler(request: Request, exc: ApiError):
    return error_response(exc.code, exc.message, exc.status_code, exc.details)


async def http_error_handler(request: Request, exc: HTTPException):
    code = ErrorCode.INTERNAL_ERROR if exc.status_code >= 500 else ErrorCode.VALIDATION_ERROR
    return error_response(code, str(exc.detail), exc.status_code)


async def validation_error_handler(request: Request, exc: RequestValidationError):
    return error_response(
        ErrorCode.VALIDATION_ERROR,
        "Request validation failed.",
        422,
        {"errors": exc.errors()},
    )
