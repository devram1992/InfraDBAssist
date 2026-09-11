from fastapi import FastAPI

app = FastAPI(
    title="InfraDB Assist",
    description="AI-powered assistant for OS and Database Team",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
