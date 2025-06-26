from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger

from services.student_service import StudentService
from utils.jwt_utils import extract_user_id

student_service = StudentService()

student_router = APIRouter(
    prefix="/student",
    tags=["Student"],
    responses={404: {"description": "Not Found"}},
)


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


class RequestGetAllResponse(BaseModel):
    requests: List[RequestDto]


class SendMessageRequestPostRequest(BaseModel):
    mentor_id: UUID
    description: str


class SendMessageRequestGetResponse(BaseModel):
    id: UUID


class SendCallRequestPostRequest(BaseModel):
    mentor_id: UUID
    description: str
    call_time: datetime


class SendCallRequestGetResponse(BaseModel):
    id: UUID


class GetRequestByIdGetResponse(BaseModel):
    call_type: bool
    time_sended: datetime
    mentor_id: UUID
    guest_id: UUID
    description: str
    call_time: Optional[datetime]
    response: int


class RequestUpdateRequest(BaseModel):
    call_type: Optional[bool] = None
    mentor_id: Optional[UUID] = None
    guest_id: Optional[UUID] = None
    description: Optional[str] = None
    call_time: Optional[datetime] = None
    response: Optional[int] = None


@student_router.get("/", response_model=RequestGetAllResponse)
async def get_all(user_id: UUID = Depends(extract_user_id)):
    """
    Get all requests.

    Authorization header required with Bearer token containing user_id.

    Returns all requests' information.
    """
    try:
        logger.info(f"User {user_id} retrieving all requests")
        requests = await student_service.get_all_requests()

        return RequestGetAllResponse(
            requests=[RequestDto(id=request.id,
                                 call_type=request.call_type,
                                 time_sended=request.time_sended,
                                 mentor_id=request.mentor_id,
                                 guest_id=request.guest_id,
                                 description=request.description,
                                 call_time=request.call_time,
                                 response=request.response,)
                     for request in requests]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving all requests: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@student_router.post("/message/", response_model=SendMessageRequestGetResponse, status_code=201)
async def create_message(request_request: SendMessageRequestPostRequest, user_id: UUID = Depends(extract_user_id)):
    """
    Create a new message request.

    - **mentor_id**: Unique identifier of the mentor.
    - **description**: Description of the request.

    Authorization header required with Bearer token containing user_id.

    Returns the created request.
    """
    try:
        logger.info(f"Creating message request for user {user_id} to mentor {request_request.mentor_id}")
        request_id = await student_service.send_message_request(
            request_request.mentor_id, user_id, request_request.description)
        return SendMessageRequestGetResponse(
            id=request_id,
        )
    except Exception as e:
        logger.error(f"Error creating message request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@student_router.post("/call/", response_model=SendCallRequestGetResponse, status_code=201)
async def create_call(request_request: SendCallRequestPostRequest, user_id: UUID = Depends(extract_user_id)):
    """
    Create a new call request.

    - **mentor_id**: Unique identifier of the mentor.
    - **description**: Description of the request.
    - **call_time**: time of the call.

    Authorization header required with Bearer token containing user_id.

    Returns the created request.
    """
    try:
        logger.info(f"Creating call request for user {user_id} to mentor {request_request.mentor_id}")
        request_id = await student_service.send_call_request(
            request_request.mentor_id, user_id,
            request_request.description, call_time=request_request.call_time)
        return SendCallRequestGetResponse(
            id=request_id,
        )
    except Exception as e:
        logger.error(f"Error creating call request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@student_router.get("/{request_id}", response_model=GetRequestByIdGetResponse)
async def get_by_id(request_id: UUID, user_id: UUID = Depends(extract_user_id)):
    """
    Get details of a request by ID.

    - **request_id**: Unique identifier of the request.

    Authorization header required with Bearer token containing user_id.

    Returns all request information.
    """
    try:
        logger.info(f"Getting request {request_id} for user {user_id}")
        request = await student_service.get_request_by_id(request_id)
        if not request:
            logger.warning(f"Request {request_id} not found")
            raise HTTPException(status_code=404, detail="Запрос не найден")

        return GetRequestByIdGetResponse(
            call_type=request.call_type,
            time_sended=request.time_sended,
            mentor_id=request.mentor_id,
            guest_id=request.guest_id,
            description=request.description,
            call_time=request.call_time,
            response=request.response,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting request by ID: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@student_router.patch("/{request_id}")
async def update_request(request_id: UUID, req: RequestUpdateRequest, user_id: UUID = Depends(extract_user_id)):
    """
    Обновить данные запроса (request) по id. Можно частично.
    """
    try:
        logger.info(f"User {user_id} updating request {request_id} with {req.dict(exclude_unset=True)}")
        await student_service.update_request(request_id, req.dict(exclude_unset=True))
        return {"status": "ok"}
    except ValueError as ve:
        logger.warning(f"Request {request_id} not found for update")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error updating request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@student_router.delete("/{request_id}")
async def delete_request(request_id: UUID, user_id: UUID = Depends(extract_user_id)):
    """
    Удалить запрос по id.
    """
    try:
        logger.info(f"User {user_id} deleting request {request_id}")
        await student_service.delete_request(request_id)
        return {"status": "ok"}
    except ValueError as ve:
        logger.warning(f"Request {request_id} not found for delete")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error deleting request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
