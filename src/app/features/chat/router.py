import json
from fastapi import APIRouter, Request
from logging import getLogger
from openai import OpenAI
from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse, StreamingResponse
from typing import Optional, List


logger = getLogger("chat.wish")
router = APIRouter()
# web ui router /chat location under /web

client = OpenAI()
model = "gpt-5-nano"  # gpt-5-nano quick, -mini for more realistic,
system_prompt = """
You are an expert in designing AI agent with integrations that delight user's wishes
Your goal is to collect business requirements in terms of 6 key aspects:
1. Main Goal: What is the primary objective the user wants to achieve with this AI agent?
2. Data Connection: What data sources or APIs should the agent connect to in order to function effectively?
3. Metrics: What key performance indicators (KPIs) or metrics will be used to measure the success of?
4. Strategic Fit: How does this AI agent align with the user's overall business strategy and goals?
5. Risks: What potential risks or challenges should be considered in the development and deployment of this AI agent?
6. Experimental Ideas: Are there any innovative or experimental features the user would like to explore with?
If user tells story that does not naturally fit to the above, put them under "Other Wishes".
Ask 1 or 2 questions at a time. Make sure to use engaging and friendly tone, without excessive technical jargons.
Do not stop until you have all 6 aspects, unless user explicitly want to leave a few empty.
When ready, please tell user that you have all the info you need as show it as next question.
"""


class IntegrationSpecs(BaseModel):
    # Data is placed first for model prioritization
    main_goal: Optional[str] = Field(None, description="The primary objective or business problem this integration addresses.")
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
        
    # --- ADJUSTMENT 1: System Prompt Check ---
    if not chat_history or chat_history[0].get("role") != "system":
        chat_history.insert(0, {"role": "system", "content": system_prompt})

    # Add the user message to the context
    chat_history.append({"role": "user", "content": user_message})

    try:
        # --- ADJUSTMENT 2: Single, Blocking Parse (Data Integrity Guaranteed) ---
        # This is fast enough for short outputs and guarantees the JSON schema.
        completion = client.beta.chat.completions.parse(
            model="gpt-5",
            messages=chat_history,
            response_format=AgentResponse,
        )

        # The message content is the guaranteed, complete JSON string
        structured_message = completion.choices[0].message
        
        # Extract the user-facing text from the parsed object
        response_text = completion.choices[0].message.parsed.next_question_to_user
        
        if not response_text:
             response_text = "I've successfully gathered all the required information. Thank you!"

        # Update history with the guaranteed JSON output
        chat_history.append({"role": "assistant", "content": structured_message.content})

    except Exception as e:
        # Fallback for API/Parsing errors
        response_text = f"🚨 An error occurred while processing your request: {e}. Please try again."
        # If error, do not update history state
        chat_history.pop() 

    # Serialize the updated history for the OOB swap
    new_history_json = json.dumps(chat_history)
    
    # --- Frontend Swap: We return the response text and the OOB update tag ---
    html_response = f"""
    <div class='bubble assistant' style='margin-right: auto; max-width: 90%;'>{response_text}</div>
    
    <input type="hidden" 
           id="chat-state-store" 
           name="chat_history_json" 
           value='{new_history_json}' 
           hx-swap-oob="true" />
    """
    
    # We use HTMLResponse because we are returning a complete HTML fragment (the bubble + input)
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
