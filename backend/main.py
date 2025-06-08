import httpx
from fastapi import FastAPI, Response, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from authx import AuthX
from authx.exceptions import JWTDecodeError
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from backend.core.config import config
from backend.core.database import SessionDep

from backend.models.models import UserModel, MonitoringRequestModel
from backend.schemas import UserLogin, MonitoringRequestCreate

from passlib.context import CryptContext

from backend.service.hh_runner import parse_dicts_to_models

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = AuthX(config=config)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.exception_handler(JWTDecodeError)
async def jwt_expired_handler(request: Request, exc: JWTDecodeError):
    return JSONResponse(
        status_code=401,
        content={"detail": "Срок действия токена истёк. Пожалуйста, выполните вход заново."},
    )

@app.post("/api/login")
async def login(credentials: UserLogin, response: Response, session: SessionDep):
    stmt = select(UserModel).where(UserModel.email == credentials.email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = security.create_access_token(uid=str(user.id))
    response.set_cookie(
        key=config.JWT_ACCESS_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="Lax",
        secure=False,  # Set to True in production with HTTPS
        max_age=3600  # 1 hour
    )
    return {"access_token": token, "message": "Login successful"}

@app.post("/api/register")
async def register(credentials: UserLogin, session: SessionDep):
    # Проверяем, существует ли пользователь с таким email
    stmt = select(UserModel).where(UserModel.email == credentials.email)
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")

    # Хешируем пароль
    hashed_password = pwd_context.hash(credentials.password)

    # Создаем нового пользователя
    new_user = UserModel(
        email=credentials.email,
        hashed_password=hashed_password,
        role="hr"  # По умолчанию роль hr
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return {"message": "Регистрация прошла успешно", "user_id": str(new_user.id)}

@app.post("/api/logout")
async def logout(response: Response):
    # Clear the access token cookie
    response.delete_cookie(
        key=config.JWT_ACCESS_COOKIE_NAME,
        httponly=True,
        samesite="Lax",
        secure=False  # Set to True in production with HTTPS
    )
    return {"message": "Successfully logged out"}

async def run_hh_parser(text: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post("http://hh_parser:8000/parse/", json={"text": text})
        response.raise_for_status()
        return response.json()["vacancies"]

@app.post("/api/monitoring")
async def monitor(payload: MonitoringRequestCreate, session: SessionDep, user=Depends(security.access_token_required)):
    try:
        # 1. Save the request
        request = MonitoringRequestModel(
            salary=payload.salary,
            position=payload.position,
            region=payload.region,
            experience=payload.experience,
        )
        session.add(request)
        await session.flush()  # to get ID
        await session.commit()

        # 2. Run parser with proper error handling
        try:
            vacancies_data = await run_hh_parser(text=f"{payload.position} {payload.region} {payload.salary}")
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch vacancies: {str(e)}"
            )

        # 3. Read CSV and save vacancies
        try:
            vacancies = await parse_dicts_to_models(vacancies_data, request.id)
            
            # Filter vacancies by experience if needed
            filtered_vacancies = [v for v in vacancies if v.experience == payload.experience]
            
            session.add_all(filtered_vacancies)
            await session.commit()

            # 4. Return response in the format expected by frontend
            return {
                "vacancies_found": len(filtered_vacancies),
                "vacancies": [
                    {
                        "id": str(v.id),
                        "request_id": str(v.request_id),
                        "name": v.name,
                        "url": f"https://hh.ru/vacancy/{v.id}",  # Construct URL from ID
                        "salary_from": v.salary_min,
                        "salary_to": v.salary_max,
                        "experience": v.experience,
                        "company_name": v.employer,
                        "region": payload.region,  # Use the requested region
                        "published_at": datetime.now().isoformat(),  # Since we don't have this info
                    }
                    for v in filtered_vacancies
                ]
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process vacancies: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


