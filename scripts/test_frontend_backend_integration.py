"""
SatQuery AI - Frontend + Backend Integration Test
"""
import asyncio
import httpx

async def main():
    print("Testing live FastAPI + Frontend Integration at http://127.0.0.1:8000...")
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # 1. Frontend index.html
        r = await client.get("/")
        assert r.status_code == 200
        assert "SatQuery AI" in r.text
        print("  [1/6] GET / (Frontend HTML) -> 200 OK")

        # 2. Frontend CSS & JS assets
        r_css = await client.get("/style.css")
        assert r_css.status_code == 200
        r_js = await client.get("/script.js")
        assert r_js.status_code == 200
        print("  [2/6] GET /style.css & /script.js (Frontend Assets) -> 200 OK")

        # 3. Health check
        r_health = await client.get("/api/v1/health")
        assert r_health.status_code == 200
        h_data = r_health.json()["data"]
        print(f"  [3/6] GET /api/v1/health -> {h_data['service']} v{h_data['version']} (status: {h_data['components']['database']})")

        # 4. Preset sample loading
        r_sample = await client.post("/api/v1/uploads/sample/optical_sample.png", data={"modality": "optical", "tag": "primary"})
        assert r_sample.status_code == 201
        sample_data = r_sample.json()["data"]
        img_id = sample_data["id"]
        meta = sample_data["metadata"]
        print(f"  [4/6] POST /api/v1/uploads/sample/optical_sample.png -> ID: {img_id[:8]}..., CRS: {meta.get('crs')}, Size: {meta.get('width')}x{meta.get('height')}")

        # 5. Full analysis pipeline execution
        r_analysis = await client.post("/api/v1/analysis", json={
            "query": "What type of environment and infrastructure is visible in this satellite imagery?",
            "image_ids": [img_id],
            "async_mode": False
        })
        assert r_analysis.status_code == 200
        a_data = r_analysis.json()["data"]
        score_pct = a_data["confidence"]["score"] * 100
        print(f"  [5/6] POST /api/v1/analysis -> Task: {a_data['task']}, Conf: {score_pct:.1f}%, Duration: {a_data['execution_duration_ms']:.1f}ms")
        print(f"        Answer: {a_data['answer'][:80]}...")

        # 6. History audit log
        r_history = await client.get("/api/v1/history")
        assert r_history.status_code == 200
        history_items = r_history.json()["data"]
        print(f"  [6/6] GET /api/v1/history -> Total logged sessions: {len(history_items)}")

    print("\n>> ALL FRONTEND + BACKEND INTEGRATION CHECKS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    asyncio.run(main())
