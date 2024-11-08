# Import relevant functionality
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain.llms.base import LLM
from pydantic import Field
import erniebot

# Define the ErnieBotLLM class
class ErnieBotLLM(LLM):
    api_type: str = Field(..., description="ErnieBot的API类型，例如 'aistudio'")
    access_token: str = Field(..., description="ErnieBot API的访问令牌")
    model: str = Field(default="ernie-3.5", description="ErnieBot的模型名称")

    def __init__(self, api_type: str, access_token: str, model: str = "ernie-3.5", **kwargs):
        super().__init__(api_type=api_type, access_token=access_token, model=model, **kwargs)

    def _call(self, prompt: str, stop=None):
        print('ErnieBotLLM 正在处理请求...')
        response = erniebot.ChatCompletion.create(
            _config_=dict(
                api_type=self.api_type,
                access_token=self.access_token,
            ),
            model=self.model,
            messages=[{"role": "user", "content": f"请用中文回答：{prompt}"}],
        )
        return response.get('result', '未找到结果')

    @property
    def _llm_type(self):
        return "erniebot_llm"

# Create the agent
model = ErnieBotLLM(api_type="aistudio", access_token="03a794f63c8002be85524c48337924d4d04634fe")
search = TavilySearchResults(max_results=2)
tools = [search]
memory = MemorySaver()
agent_executor = create_react_agent(model, tools, checkpointer=memory)

# Use the agent
config = {"configurable": {"thread_id": "abc123"}}
for chunk in agent_executor.stream(
    {"messages": [HumanMessage(content="你好，我是小明，住在北京")]}, config
):
    print(chunk)
    print("----")

for chunk in agent_executor.stream(
    {"messages": [HumanMessage(content="我住的地方天气怎么样？")]}, config
):
    print(chunk)
    print("----")
