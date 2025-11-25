from logging import getLogger
from pydantic import BaseModel
from openai import OpenAI
from typing import Optional

logger = getLogger("chat.wish_agent")
client = OpenAI()
model = "gpt-5-nano"  # gpt-5-nano quick, -mini for more realistic,
system_prompt = """
You are an expert integration architect. 
Your goal is to collect 3 pieces of info: Integration Type, KPIs, and Main Goal.
Ask 1 or 2 questions at a time. 
Do not stop until you have all 3.
When ready, please tell user that you have all the info you need as show it as next question.
"""


class IntegrationSpecs(BaseModel):
    integration_type: Optional[str] = None
    kpi_involved: Optional[str] = None
    main_goal: Optional[str] = None


class AgentResponse(BaseModel):
    next_question_to_user: Optional[str] 
    extracted_data: IntegrationSpecs
    is_complete: bool


def chat_about_wishes(chat_history):

    if not chat_history or len(chat_history) == 0:
        raise ValueError("chat_history cannot be empty")
    
    if chat_history[0]['role'] != 'system':
        chat_history = [{"role": "system", "content": system_prompt}, *chat_history]

    logger.info(f"Chat history sent to agent: {chat_history}")

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=chat_history,
        response_format=AgentResponse,
    )

    logger.info(f"Agent response: {completion.choices[0].message}")
    return completion.choices[0].message

