import json
import asyncio
from typing import List
from datetime import date
from pathlib import Path
from app.domain.ports import MercadoPublicoClientPort
from app.domain.models import Licitacion, LicitacionResponse

class MockMercadoPublicoClient(MercadoPublicoClientPort):
    def __init__(self, list_file: str, detail_file: str):
        self.list_file = Path(list_file)
        self.detail_file = Path(detail_file)

    async def get_daily_list(self, target_date: date) -> List[Licitacion]:
        await asyncio.sleep(0.5)  # Simulate latency
        if not self.list_file.exists():
            return []
        
        with open(self.list_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            response = LicitacionResponse(**data)
            return response.listado

    async def get_detail(self, code: str) -> Licitacion:
        await asyncio.sleep(0.5)  # Simulate latency
        if not self.detail_file.exists():
            raise ValueError(f"Detail file {self.detail_file} not found")
            
        with open(self.detail_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            response = LicitacionResponse(**data)
            # Retornamos la primera (y única) licitación del listado de detalle
            return response.listado[0]
