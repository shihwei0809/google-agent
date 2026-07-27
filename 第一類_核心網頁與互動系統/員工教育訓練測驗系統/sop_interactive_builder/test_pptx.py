import asyncio
from pathlib import Path

async def test():
    from app import export_pptx
    jobs = sorted(Path('jobs').iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    job_id = jobs[0].name
    print('Testing:', job_id[:50])
    try:
        result = await export_pptx(job_id=job_id)
        print('Result:', result)
        # Check file exists
        from pathlib import Path as P
        pptx = P('jobs') / job_id / f"{job_id}.pptx"
        print('File exists:', pptx.exists(), 'Size:', pptx.stat().st_size if pptx.exists() else 0)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
