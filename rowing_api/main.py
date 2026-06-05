from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import Config
from .routers import telemetry, analysis, statistics, state, session, strategy, review, intervention

app = FastAPI(
    title="赛艇训练桨频数据实时聚合与划姿分析 API",
    description="各桨位传感器数据实时聚合、时序对齐、划姿分析与教练端统计接口",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry.router)
app.include_router(analysis.router)
app.include_router(statistics.router)
app.include_router(state.router)
app.include_router(session.router)
app.include_router(strategy.router)
app.include_router(review.router)
app.include_router(intervention.router)


@app.get("/")
async def root():
    return {
        "code": 200,
        "message": "success",
        "data": {
            "name": "赛艇训练数据实时分析 API",
            "version": "2.0.0",
            "port": Config.PORT,
            "endpoints": {
                "遥测上报": "/api/telemetry/report",
                "批量上报": "/api/telemetry/batch-report",
                "同步率计算": "/api/analysis/sync-rate",
                "异常检测": "/api/analysis/detect",
                "稳定性排行": "/api/analysis/stability/ranking",
                "训练负荷": "/api/statistics/training-load",
                "改进趋势": "/api/statistics/improvement",
                "当前状态": "/api/state/current",
                "结束训练": "/api/state/end-training",
                "训练会话": "/api/session/create",
                "策略配置": "/api/strategy/create",
                "训练复盘": "/api/review/{session_id}",
                "实时干预": "/api/intervention/{session_id}",
                "API文档": "/docs"
            }
        }
    }


@app.get("/health")
async def health_check():
    return {
        "code": 200,
        "message": "success",
        "data": {
            "status": "healthy",
            "service": "rowing-analysis-api",
            "port": Config.PORT
        }
    }


def start():
    uvicorn.run(
        "rowing_api.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False
    )


if __name__ == "__main__":
    start()
