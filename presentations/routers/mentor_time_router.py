from datetime import datetime, time
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger

from services.mentor_time_service import MentorTimeService
from utils.jwt_utils import extract_user_id

mentor_time_service = MentorTimeService()

mentor_time_router = APIRouter(
    prefix="/mentor_time",
    tags=["MentorTime"],
    responses={404: {"description": "Not Found"}},
)


class MentorTimeDto(BaseModel):
    id: UUID
    day: int
    time_start: time
    time_end: time
    mentor_id: UUID


class MentorDto(BaseModel):
    id: UUID
    telegram_id: str
    name: str
    info: str


class RequestDto(BaseModel):
    id: UUID
    call_type: bool
    time_sended: datetime
    mentor_id: UUID
    guest_id: UUID
    description: str
    call_time: Optional[datetime]
    response: int


class MentorTimeGetAllResponse(BaseModel):
    mentor_times: List[MentorTimeDto]


class CreateMentorTimeRequestPostRequest(BaseModel):
    day: int
    time_start: time
    time_end: time
    mentor_id: UUID


class CreateMentorTimeRequestGetResponse(BaseModel):
    id: UUID


class MentorTimeGetAllByMentorIdResponse(BaseModel):
    mentor_times: List[MentorTimeDto]


class GetPossibleMentorTimeResponse(BaseModel):
    mentor_times: List[time]


class CountMentorTimeGetRequest(BaseModel):
    count: int


class CheckMentorTimeGetRequest(BaseModel):
    status: bool


class MentorTimeUpdateRequest(BaseModel):
    day: Optional[int] = None
    time_start: Optional[time] = None
    time_end: Optional[time] = None
    mentor_id: Optional[UUID] = None


@mentor_time_router.get("/", response_model=MentorTimeGetAllResponse)
async def get_all(user_id: UUID = Depends(extract_user_id)):
    """
    Get all mentor times.

    Authorization header required with Bearer token containing user_id.

    Returns all mentor times' information.
    """
    try:
        logger.info(f"User {user_id} retrieving all mentor times")
        mentor_times = await mentor_time_service.get_all_mentor_time()

        return MentorTimeGetAllResponse(
            mentor_times=[MentorTimeDto(id=mentor_time.id,
                                 day=mentor_time.day,
                                 time_start=mentor_time.time_start,
                                 time_end=mentor_time.time_end,
                                 mentor_id=mentor_time.mentor_id,)
                     for mentor_time in mentor_times]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving all mentor times: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@mentor_time_router.post("/", response_model=CreateMentorTimeRequestGetResponse, status_code=201)
async def create_mentor_time(mentor_time_request: CreateMentorTimeRequestPostRequest, user_id: UUID = Depends(extract_user_id)):
    """
    Create a new mentor time.

    - **day**: number of the day of the week. For example 0 -- Monday, 1 -- Tuesday, etc.
    - **time_start**: Start time of the free mentor time.
    - **time_end**: End time of the free mentor time.
    - **mentor_id**: Unique identifier of the mentor.

    Authorization header required with Bearer token containing user_id.

    Returns the created mentor time.
    """
    try:
        logger.info(f"User {user_id} creating new mentor time for mentor {mentor_time_request.mentor_id}")
        mentor_time_id = await mentor_time_service.create_mentor_time(
            mentor_time_request.day, mentor_time_request.time_start,
            mentor_time_request.time_end, mentor_time_request.mentor_id)
        return CreateMentorTimeRequestGetResponse(
            id=mentor_time_id,
        )
    except Exception as e:
        logger.error(f"Error creating mentor time: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@mentor_time_router.get("/mentor/{mentor_id}", response_model=MentorTimeGetAllByMentorIdResponse)
async def get_all_by_mentor_id(mentor_id: UUID, user_id: UUID = Depends(extract_user_id)):
    """
    Get all mentor times by mentor ID.

    - **mentor_id**: Unique identifier of the mentor.

    Authorization header required with Bearer token containing user_id.

    Returns all mentor times' information by mentor ID.
    """
    try:
        logger.info(f"User {user_id} retrieving all mentor times for mentor {mentor_id}")
        mentor_times = await mentor_time_service.get_all_mentor_time_by_mentor_id(mentor_id)

        return MentorTimeGetAllByMentorIdResponse(
            mentor_times=[MentorTimeDto(id=mentor_time.id,
                                 day=mentor_time.day,
                                 time_start=mentor_time.time_start,
                                 time_end=mentor_time.time_end,
                                 mentor_id=mentor_time.mentor_id,)
                     for mentor_time in mentor_times]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mentor times by mentor ID: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@mentor_time_router.get("/call_times/{mentor_id}/{day}", response_model=GetPossibleMentorTimeResponse)
async def get_possible_time(mentor_id: UUID, day: int, user_id: UUID = Depends(extract_user_id)):
    """
    Get all possible time to call mentor during day.

    - **mentor_id**: Unique identifier of the mentor.
    - **day**: number of the day of the week. For example 0 -- Monday, 1 -- Tuesday, etc.

    Authorization header required with Bearer token containing user_id.

    Returns all mentor times' information by mentor ID and day.
    """
    try:
        logger.info(f"User {user_id} retrieving possible call times for mentor {mentor_id} on day {day}")
        mentor_times = await mentor_time_service.get_call_times(day=day, mentor_id=mentor_id)

        return GetPossibleMentorTimeResponse(
            mentor_times=mentor_times
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving possible call times: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@mentor_time_router.get("/count/{mentor_id}/{request_time}", response_model=CountMentorTimeGetRequest)
async def count_requests(mentor_id: UUID, request_time: datetime, user_id: UUID = Depends(extract_user_id)):
    """
    Count all call requests to mentor on datetime.

    - **mentor_id**: Unique identifier of the mentor.
    - **request_time**: Datetime of call time in ISO format (e.g., 2023-10-01T12:00:00).

    Authorization header required with Bearer token containing user_id.

    Returns number of call requests to mentor on datetime.
    """
    try:
        logger.info(f"User {user_id} counting requests for mentor {mentor_id} at time {request_time}")
        mentor_cnt = await mentor_time_service.count_requests_for_time(mentor_id=mentor_id, request_time=request_time)

        return CountMentorTimeGetRequest(
            count=mentor_cnt,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error counting requests for time: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@mentor_time_router.get("/check/{mentor_id}/{request_time}", response_model=CheckMentorTimeGetRequest)
async def check_request(mentor_id: UUID, request_time: datetime, user_id: UUID = Depends(extract_user_id)):
    """
    Check is time booked for mentor.

    - **mentor_id**: Unique identifier of the mentor.
    - **request_time**: Datetime of call time in ISO format (e.g., 2023-10-01T12:00:00).

    Authorization header required with Bearer token containing user_id.

    Returns boolean: is time booked for mentor.
    """
    try:
        logger.info(f"User {user_id} checking time reservation for mentor {mentor_id} at time {request_time}")
        mentor_status = await mentor_time_service.check_time_reservation(mentor_id=mentor_id, request_time=request_time)

        return CheckMentorTimeGetRequest(
            status=mentor_status,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking time reservation: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@mentor_time_router.patch("/{slot_id}")
async def update_mentor_time(slot_id: UUID, req: MentorTimeUpdateRequest, user_id: UUID = Depends(extract_user_id)):
    """
    Обновить данные временного слота по id. Можно частично.
    """
    try:
        logger.info(f"User {user_id} updating mentor_time {slot_id} with {req.dict(exclude_unset=True)}")
        await mentor_time_service.update_mentor_time(slot_id, req.dict(exclude_unset=True))
        return {"status": "ok"}
    except ValueError as ve:
        logger.warning(f"MentorTime {slot_id} not found for update")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error updating mentor_time: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@mentor_time_router.delete("/{slot_id}")
async def delete_mentor_time(slot_id: UUID, user_id: UUID = Depends(extract_user_id)):
    """
    Удалить временной слот по id.
    """
    try:
        logger.info(f"User {user_id} deleting mentor_time {slot_id}")
        await mentor_time_service.delete_mentor_time(slot_id)
        return {"status": "ok"}
    except ValueError as ve:
        logger.warning(f"MentorTime {slot_id} not found for delete")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error deleting mentor_time: {e}")
        raise HTTPException(status_code=400, detail=str(e))