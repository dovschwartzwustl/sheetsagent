from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import add_expense_tool
from parse import parse_purchase_tool
import sys



load_dotenv()

class SheetsResponse(BaseModel):
    merchant: str
    purchase_item: str
    price: float
    purchase_category: str
    tools_used: list[str]

llm = ChatOpenAI(model='gpt-4.1-nano')
parser = PydanticOutputParser(pydantic_object=SheetsResponse)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a bookkeeping assistant that helps input spending into a google sheet
            based on what the user requests. You will need to decide how to input the expense
            into the spreadsheet based on user instructions. Use necessary tools to accomplish this.
            Make sure to indicate while you work what category you are deciding and how you are going
            to input the expense into the google sheet.
            # Wrap the output in this format and provide no other text\n{format_instructions}
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

tools = [add_expense_tool, parse_purchase_tool]
agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=tools
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
if len(sys.argv) > 1:
    query = []
    for arg in sys.argv[1:]:
        query.append(arg)
    query = " ".join(query)
    raw_response = agent_executor.invoke({"query": query})
else:
    query = input("What expense would you like to input? ")
    raw_response = agent_executor.invoke({"query": query})

try:
    print(raw_response)
    # structured_response = parser.parse(raw_response.get("output")[0]["text"])
except Exception as e:
    print("Error parsing response", e, "Raw Response - ", raw_response)