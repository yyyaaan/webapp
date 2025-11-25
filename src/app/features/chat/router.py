from asyncio import sleep
from fastapi import APIRouter, Request
from json import dumps, loads
from logging import getLogger
from starlette.responses import StreamingResponse

from .agent_wish import chat_about_wishes

logger = getLogger("chat")
router = APIRouter()
# web router /chat location under /web


@router.post("/chat/stream")
async def chat_stream(request: Request):
    """
    Streaming endpoint that returns structured JSON responses.
    chat_history to formatted as [{"role": "user"/"assistant", "content": "..."}]
    """
    form = await request.form()
    prompt = (form.get("message") or "")
    chat_history_str = form.get("chat_history", "[]")
    
    try:
        chat_history = loads(chat_history_str)
        logger.info(f"frontend send chat history n={len(chat_history)}, len={len(chat_history_str)}, roles={[msg['role'] for msg in chat_history]}")

    except Exception as e:
        chat_history = []
        logger.warning(f"chat history parsing failed, defaulting to empty list. Error {e}")


    completion = chat_about_wishes(chat_history).parsed.model_dump()

    async def generator():
        # Simulate an assistant generating a response with output and state
        output_text = completion.pop("next_question_to_user")

        # Simulate streaming the output token-by-token
        accumulated_output = ""
        for token in output_text.split():
            await sleep(0.06)
            accumulated_output += token + " "
            # Send structured response as newline-delimited JSON
            response_obj = {
                "output": accumulated_output.strip(),
                **completion
            }
            yield (dumps(response_obj) + "\n").encode("utf-8")

    return StreamingResponse(generator(), media_type="application/x-ndjson; charset=utf-8")


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
