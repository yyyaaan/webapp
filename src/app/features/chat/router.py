from asyncio import sleep
from fastapi import APIRouter, Request
from logging import getLogger
from starlette.responses import StreamingResponse

logger = getLogger("chat")
router = APIRouter()
# web router /chat location under /web


@router.post("/chat/stream")
async def chat_stream(request: Request):
    """
    Streaming endpoint token-by-token response.
    """
    form = await request.form()
    prompt = (form.get("message") or "")

    async def generator():
        # Echo back the user message first (client already renders it, so optional)
        # Simulate an assistant generating a long sentence token-by-token
        long_sentence = (
            "This is a streamed assistant response demonstrating token by token "
            "output. The server sends small chunks with short pauses to emulate "
            "an agent gradually producing text, allowing the frontend to append "
            "each piece as it arrives so users see incremental updates in real time."
        )

        # If a prompt was provided, prepend a short acknowledgement
        if prompt:
            ack = f"Acknowledged prompt: {prompt}. "
            for ch in ack.split():
                await sleep(0.02)
                yield (ch + " ").encode("utf-8")

        for token in long_sentence.split():
            await sleep(0.06)
            yield (token + " ").encode("utf-8")

        # final newline to mark end
        yield b"\n"

    return StreamingResponse(generator(), media_type="text/plain; charset=utf-8")


@router.post("/chat/feedback")
async def chat_feedback(request: Request):
    """
    Receive simple feedback for a specific assistant message.
    Expects JSON body: {"message_id": "msg-...", "feedback": "up"|"down"}
    """
    try:
        data = await request.json()
    except Exception:
        data = {}

    message_id = data.get("message_id")
    feedback = data.get("feedback")

    logger.info(f"Received feedback: message_id={message_id} feedback={feedback}")

    return {"status": "ok", "message_id": message_id, "feedback": feedback}
