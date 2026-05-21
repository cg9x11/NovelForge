
import json
from typing import AsyncGenerator


async def wrap_sse_stream(generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    async for item in generator:
        yield f"data: {json.dumps({'content': item}, ensure_ascii=False)}\n\n"
