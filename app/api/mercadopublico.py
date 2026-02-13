from typing import Callable, Any
import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.dependencies import get_mercado_publico_client, require_admin_token
from app.infrastructure.mercadopublico.client import MercadoPublicoClient
from app.domain.schemas import LicitacionListResponse, LicitacionDetailResponse, ErrorResponse, LicitacionEstado
from enum import Enum

router = APIRouter(
    prefix="/test", 
    tags=["Mercado Público Integración Real"],
    dependencies=[Depends(require_admin_token)]
)

async def _handle_mp_request(func: Callable, *args, **kwargs) -> Any:
    """Helper to handle common Mercado Público API logic and errors."""
    client: MercadoPublicoClient = kwargs.pop("client")
    try:
        return await func(*args, **kwargs)
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        try:
            error_data = e.response.json()
            return JSONResponse(
                status_code=status_code, 
                content={"error": "API Error", "detail": error_data}
            )
        except Exception:
            return JSONResponse(
                status_code=status_code, 
                content={"error": "HTTP Error", "detail": e.response.text}
            )
    finally:
        await client.close()

@router.get(
    "/", 
    response_model=LicitacionListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "API Error from Mercado Público"},
        503: {"description": "Service Unavailable - Mercado Público API is overloaded (e.g., unconditional drop overload)"}
    }
)
async def test_real(fecha: str, client: MercadoPublicoClient = Depends(get_mercado_publico_client)):
    # Consumir directamente la API real (Lista de licitaciones)
    return await _handle_mp_request(client.get_by_date, fecha, client=client)

@router.get(
    "/detail", 
    response_model=dict,
    responses={
        500: {"model": ErrorResponse, "description": "API Error from Mercado Público"},
        503: {"description": "Service Unavailable - Mercado Público API is overloaded"}
    }
)
async def test_real_detail(codigo: str, client: MercadoPublicoClient = Depends(get_mercado_publico_client)):
    # Consumir directamente la API real (Detalle de licitación) sin filtro Pydantic
    return await _handle_mp_request(client.get_raw_by_code, codigo, client=client)

@router.get(
    "/detail/dto",
    response_model=dict,
    responses={
        500: {"model": ErrorResponse, "description": "API Error from Mercado Público"},
        503: {"description": "Service Unavailable - Mercado Público API is overloaded"}
    }
)
async def test_real_detail_dto(codigo: str, client: MercadoPublicoClient = Depends(get_mercado_publico_client)):
    """
    Obtiene el detalle de una licitación y lo transforma a DTO simplificado para API.
    
    Args:
        codigo: Código de la licitación (ej: 2732-49-LE25)
    
    Returns:
        TenderSummaryDTO: Objeto transformado listo para list view
    """
    from app.application.transformer_service import TenderTransformer
    
    async def transform_to_dto(codigo: str):
        response = await client.get_by_code(codigo)
        if response.listado:
            licitacion = response.listado[0]
            dto = TenderTransformer.to_summary_dto(licitacion)
            return dto.model_dump(by_alias=True)
        return {"error": "No se encontró la licitación"}
    
    return await _handle_mp_request(transform_to_dto, codigo, client=client)

@router.get(
    "/status/{estado}", 
    response_model=LicitacionListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "API Error from Mercado Público"},
        503: {"description": "Service Unavailable - Mercado Público API is overloaded"}
    }
)
async def test_real_status(estado: LicitacionEstado, client: MercadoPublicoClient = Depends(get_mercado_publico_client)):
    """
    Consulta licitaciones por estado directamente a la API real.
    
    Posibles estados: activas, publicada, cerrada, desierta, adjudicada, revocada, suspendida, todos.
    """
    return await _handle_mp_request(client.get_by_status, estado.value, client=client)
