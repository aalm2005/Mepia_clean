"""Servidor aislado para probar el tutorial; solo fixtures y proveedores simulados."""
from fastapi.middleware.cors import CORSMiddleware
from tests.mepia_demo_server import app
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:3027"],
                   allow_methods=["*"], allow_headers=["*"])
