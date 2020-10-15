from pydantic import BaseModel


class CommandStats(BaseModel):
    return_code: int
    real_time: int
    cpu_time: int
    max_memory: int


class RunResult(BaseModel):
    stats: CommandStats
    stdout: str
    stderr: str
    run_log: str
