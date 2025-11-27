import json
from fastapi import APIRouter, Request
from html import escape
from logging import getLogger
from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse, StreamingResponse
from time import time
from typing import Optional, List

from .service import chat_service, client

logger = getLogger("chat.wish")
router = APIRouter()
# web ui router /chat location under /web

LLM_MODEL = "gpt-5-nano"  # gpt-5-nano quick, -mini for more realistic,
SYSTEM_PROMPT = """
You are an expert in designing AI agent with integrations that delight user's wishes
Your goal is to collect business requirements in terms of 6 key aspects:
1. Goal and functionality: What is the primary objective the user wants to achieve with this AI agent?
2. Data Connection: What data sources or APIs should the agent connect to in order to function effectively?
3. Metrics: What key performance indicators (KPIs) or metrics will be used to measure the success of?
4. Strategic Fit: How does this AI agent align with the user's overall business strategy and goals?
5. Risks: What potential risks or challenges should be considered in the development and deployment of this AI agent?
6. Experimental Ideas: Are there any innovative or experimental features the user would like to explore with?
If user tells story that does not naturally fit to the above, put them under "Other Wishes".
Ask 1 or 2 questions at a time. Make sure to use engaging and friendly tone, without excessive technical jargons.
Do not stop until you have all 6 aspects, unless user explicitly want to leave a few empty, and when appropriate tell user that they can leave blank for now.
Remember that user is not expected to tell long story, so if any small pieces of in info is available, you can rely on it.
When ready, please tell user that you have all the info you need as show it as next question.

"""


class IntegrationSpecs(BaseModel):
    # Data is placed first for model prioritization
    goal_and_func: Optional[str] = Field(None, description="The primary objective or business problem this integration addresses.")
    data_connection: Optional[str] = Field(None, description="The specific source/target systems involved (e.g., Salesforce, HubSpot).")
    metrics: Optional[str] = Field(None, description="The key performance indicators (KPIs) or metrics to be tracked (e.g., MRR, leads).")
    strategic_fit: Optional[str] = Field(None, description="How this integration aligns with the long-term business strategy.")
    risks: Optional[str] = Field(None, description="Potential risks or challenges (technical, security, budget) associated with the project.")
    experimental_ideas: Optional[str] = Field(None, description="Any innovative or non-standard ideas to explore with the integration.")
    other_wishes: Optional[str] = Field(None, description="Any remaining comments, constraints, or unique requirements.")


class AgentResponse(BaseModel):
    extracted_data: IntegrationSpecs
    is_complete: bool = Field(False, description="Set to true only when all fields are successfully extracted.")
    next_question_to_user: Optional[str] # The user-facing output is placed last


@router.post("/chat/stream")
async def chat_stream(request: Request):
    form = await request.form()
    user_message = form.get("message", "")
    chat_history_str = form.get("chat_history_json", "[]")

    try:
        chat_history: List[dict] = json.loads(chat_history_str)
    except json.JSONDecodeError:
        chat_history = []
        
    if not chat_history or chat_history[0].get("role") != "system":
        chat_history.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    chat_history.append({"role": "user", "content": user_message})
    
    # Generate ID for feedback
    msg_id = f"msg_{int(time()*1000)}"

    try:
        completion = client.beta.chat.completions.parse(
            model=LLM_MODEL,
            messages=chat_history,
            response_format=AgentResponse,
        )
        structured_message = completion.choices[0].message
        response_text = completion.choices[0].message.parsed.next_question_to_user or "Thank you!"
        chat_history.append({"role": "assistant", "content": structured_message.content})

    except Exception as e:
        response_text = f"🚨 Error: {e}"
        chat_history.pop() 

    new_history_json = escape(json.dumps(chat_history))

    # Saving if done
    if structured_message.parsed.is_complete:
        chat_service.save_chat_state(msg_id, structured_message.parsed.extracted_data.dict())
    
    html_response = f"""
    <div class="message-container assistant-container mb-3">
        <div class='bubble assistant'>{response_text}</div>
        
        <div class="feedback-row d-flex align-items-center gap-3 ms-2 mt-1">
            <i class="fas fa-thumbs-up feedback-icon" 
               data-msg-id="{msg_id}" 
               data-type="up" 
               title="Good response"></i>
               
            <i class="fas fa-thumbs-down feedback-icon" 
               data-msg-id="{msg_id}" 
               data-type="down" 
               title="Bad response"></i>
               
            <span class="feedback-status small text-muted" id="status-{msg_id}"></span>
        </div>
    </div>
    
    <input type="hidden" 
           id="chat-state-store" 
           name="chat_history_json" 
           value='{new_history_json}' 
           hx-swap-oob="true" />
    """
    
    return HTMLResponse(content=html_response)


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
