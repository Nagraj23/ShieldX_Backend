# TODO - Code Analysis & Review

- [x] Gather repo context (file listing)
- [x] Read key files: main.py, safety_controller.py, safety_service.py, redis_listener.py, redis_config.py, database.py, requirements.txt
- [ ] Produce end-to-end flow explanation (request -> Redis session -> TTL -> keyspace expired -> emergency publish)
- [ ] Explain technology choices and how they interact (FastAPI lifespan, asyncio tasks, redis asyncio client, passlib bcrypt)
- [ ] Explain DB layer (MongoDB/Motor) usage and note any dead/unused parts for this service
- [ ] Call out issues/risks (debug prints, return payload logic, keyspace notifications requirements, async task cancellation)
- [ ] Summarize what is “OK” vs what needs fixes

