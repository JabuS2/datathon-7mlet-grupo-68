from fastapi import APIRouter, Depends

from core.auth_dependencies import AuthDependencies
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from schemas.dashboard import UsersOverview
from services.dashboard.dashboard import DashboardService

router = APIRouter(prefix="/admin", tags=["admin"])
auth = AuthDependencies()


@router.get("/users/overview", response_model=UsersOverview)
async def users_overview(
    _admin=Depends(auth.get_current_admin),
    uow: UnitOfWork = Depends(get_uow),
):
    service = DashboardService(uow=uow)

    return await service.users_overview()
