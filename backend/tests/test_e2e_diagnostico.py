import asyncio
import io
from PIL import Image
from httpx import ASGITransport, AsyncClient
from plagas.main import create_app
from plagas.config import Settings


async def main():
    print("Iniciando prueba E2E de Diagnóstico...")
    settings = Settings(
        app_database_url="sqlite+aiosqlite:///./test_plagas.db",
        env="dev",
        auth_mode="desarrollo",
    )
    app = create_app(settings)

    # Crear una imagen sintética simulando una hoja
    img = Image.new("RGB", (640, 640), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://localhost") as client:
            # 1. Health check
            res = await client.get("/health/live")
            assert res.status_code == 200, f"Health live falló: {res.text}"
            print("✓ Health check live: OK")

            # 2. Catálogo de plagas y enfermedades
            res = await client.get("/api/v1/catalogo")
            assert res.status_code == 200, f"Catálogo falló: {res.text}"
            catalogo = res.json()
            print(f"✓ Catálogo obtenido con éxito: {len(catalogo)} elementos registrados")

            # 3. Diagnóstico individual
            files = {"imagen": ("hoja_test.jpg", img_bytes, "image/jpeg")}
            data = {"organo": "hoja"}
            res = await client.post("/api/v1/diagnosticos", files=files, data=data)
            assert res.status_code == 201, f"Diagnóstico falló: {res.text}"
            diag = res.json()
            print("✓ Diagnóstico individual procesado:")
            print(f"   ID: {diag['id']}")
            print(f"   Sano: {diag['es_sano']}")
            print(f"   Detecciones: {len(diag['detecciones'])}")
            print(f"   Enfermedades: {diag['enfermedades']}")
            print(f"   URL Imagen: {diag['imagen_url']}")

            # 4. Diagnóstico por lote (batch)
            files_batch = [
                ("imagenes", ("hoja_1.jpg", img_bytes, "image/jpeg")),
                ("imagenes", ("hoja_2.jpg", img_bytes, "image/jpeg")),
            ]
            res_batch = await client.post("/api/v1/diagnosticos/batch", files=files_batch, data=data)
            assert res_batch.status_code == 201, f"Diagnóstico batch falló: {res_batch.text}"
            batch = res_batch.json()
            print(f"✓ Diagnóstico por lote procesado: {batch['total']} imágenes analizadas")

            # 5. Listar historial persistido
            res_historial = await client.get("/api/v1/diagnosticos")
            assert res_historial.status_code == 200, f"Historial falló: {res_historial.text}"
            historial = res_historial.json()
            print(f"✓ Historial persistido en base de datos: {len(historial)} registros encontrados")
            assert len(historial) >= 3, "Deberían haber al menos 3 diagnósticos guardados"

            # 6. Obtener diagnóstico por ID
            id_diag = diag['id']
            res_get = await client.get(f"/api/v1/diagnosticos/{id_diag}")
            assert res_get.status_code == 200, f"Obtener por ID falló: {res_get.text}"
            assert res_get.json()['id'] == id_diag
            print(f"✓ Consulta de diagnóstico por ID {id_diag}: OK")

    print("\n¡TODAS LAS PRUEBAS E2E PASARON EXITOSAMENTE!")


if __name__ == "__main__":
    asyncio.run(main())
