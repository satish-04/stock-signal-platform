from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.trading_workflows import (
    DuplicateTradingWorkflowError,
    InvalidWorkflowTransitionError,
    TradingWorkflowNotFoundError,
    WorkflowApprovalError,
    WorkflowReference,
    get_trading_workflow_service,
)

router = APIRouter(prefix="/api/v1/trading-workflows", tags=["trading-workflows"])


class CreateRequest(BaseModel):
    idempotency_key: str = Field(min_length=1)
    workflow_type: Literal["ENTRY", "EXIT"]
    account_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    parent_workflow_id: str | None = None


class TransitionRequest(BaseModel):
    status: str
    message: str | None = None


class ApprovalRequest(BaseModel):
    approved_by: str = Field(min_length=1)


class FailureRequest(BaseModel):
    failure_type: str
    message: str = Field(min_length=1)
    retryable: bool = False


def _dump(workflow):
    from dataclasses import asdict

    return asdict(workflow)


@router.post("")
async def create_workflow(payload: CreateRequest):
    try:
        workflow = await get_trading_workflow_service().create(
            payload.idempotency_key,
            payload.workflow_type,
            payload.account_id,
            payload.symbol,
            WorkflowReference(parent_workflow_id=payload.parent_workflow_id),
        )
        return _dump(workflow)
    except DuplicateTradingWorkflowError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("")
async def list_workflows(account_id: str = Query(min_length=1)):
    return [_dump(w) for w in await get_trading_workflow_service().list_for_account(account_id)]


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    try:
        return _dump(await get_trading_workflow_service().get(workflow_id))
    except TradingWorkflowNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/{workflow_id}/transition")
async def transition_workflow(workflow_id: str, payload: TransitionRequest):
    try:
        return _dump(
            await get_trading_workflow_service().transition(
                workflow_id, payload.status, message=payload.message
            )
        )
    except InvalidWorkflowTransitionError as exc:
        raise HTTPException(409, str(exc)) from exc
    except WorkflowApprovalError as exc:
        raise HTTPException(403, str(exc)) from exc


@router.post("/{workflow_id}/approve")
async def approve_workflow(workflow_id: str, payload: ApprovalRequest):
    try:
        return _dump(await get_trading_workflow_service().approve(workflow_id, payload.approved_by))
    except WorkflowApprovalError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/{workflow_id}/fail")
async def fail_workflow(workflow_id: str, payload: FailureRequest):
    return _dump(
        await get_trading_workflow_service().fail(
            workflow_id, payload.failure_type, payload.message, payload.retryable
        )
    )


@router.post("/{workflow_id}/retry")
async def retry_workflow(workflow_id: str):
    try:
        return _dump(await get_trading_workflow_service().retry(workflow_id))
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
