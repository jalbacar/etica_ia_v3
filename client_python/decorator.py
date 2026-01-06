import asyncio
from functools import wraps

import aiohttp


class EthicalLego:
    def __init__(self, servers):
        self.servers = servers  # ['http://bias-agent:8003', ...]

    async def check_all(self, text):
        async with aiohttp.ClientSession() as session:
            tasks = [
                session.post(
                    f"{s}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": len(self.servers),
                        "method": "bias_detector",
                        "params": {"text": text},
                    },
                )
                for s in self.servers
            ]

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            verdicts = []
            for r in responses:
                if isinstance(r, Exception):
                    continue
                verdict = await r.json()
                verdicts.append(verdict["result"]["ethical"])

            return all(verdicts)


ethical_lego = EthicalLego(
    ["http://bias-agent:8003", "http://ai-act-agent:8004", "http://unesco-agent:8005"]
)


def ethical_guard():
    def decorator(func):
        @wraps(func)
        async def wrapper(prompt):
            if not await ethical_lego.check_all(prompt):
                raise ValueError("🛑 Ethical block")
            result = await func(prompt)
            if not await ethical_lego.check_all(result):
                raise ValueError("🛑 Output block")
            return result

        return wrapper

    return decorator
