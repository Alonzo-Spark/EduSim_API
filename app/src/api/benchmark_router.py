// app/src/api/benchmark_router.py
import subprocess
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/benchmark/claude-3-5-sonnet")
async def run_claude_benchmark():
    """Run the sequential benchmark for Claude 3.5 Sonnet.
    The endpoint invokes the Node benchmark script and returns the
    generated markdown report path and basic execution details.
    """
    # Resolve project root (assumes this file lives under app/src/api)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    script_path = os.path.join(project_root, "scratch", "benchmark_sequential_model.js")
    if not os.path.isfile(script_path):
        raise HTTPException(status_code=500, detail="Benchmark script not found.")
    try:
        # Run the node script synchronously; capture stdout & stderr
        result = subprocess.run(
            ["node", script_path, "Claude 3.5 Sonnet"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Benchmark execution failed: {result.stderr.strip()}",
            )
        # Extract the report path from the script output (look for .md filename)
        report_path = None
        for line in result.stdout.splitlines():
            if "Markdown summary saved to:" in line:
                report_path = line.split(":", 1)[1].strip()
                break
        if not report_path:
            report_path = "Report path could not be determined."
        return JSONResponse(
            content={
                "status": "completed",
                "output": result.stdout,
                "report_path": report_path,
            }
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Benchmark timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
