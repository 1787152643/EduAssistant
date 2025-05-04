#from vertexai.generative_models import GenerativeModel 
#from src.tools.serp import search as google_search
#from src.tools.google import google_search, fetch_page_content
#from src.tools.google import web_search as google_search
#from .tools.wiki import search as wiki_search
#from .tools.bocha import bocha_search
#from .tools.sql import *
import app.react.tools.analyze_agent
import app.react.tools.wiki
#from vertexai.generative_models import Part 
from app.utils.io import write_to_file
from app.utils.logging import logger
#from src.config.setup import config
#from app.utils.llm.gemini import generate
from app.utils.llm.deepseek import chat_deepseek
#from app.utils.llm.silicon import chat_silicon
#from app.utils.llm.lm_studio import chat_lm_studio
from app.react.tools_register import student_tools, teacher_tools, admin_tools
from app.utils.io import read_file
from pydantic import BaseModel
from typing import Callable
from pydantic import Field 
from typing import Union
from typing import List 
from typing import Dict 
import json
from app.services.user_service import UserService

from playhouse.shortcuts import model_to_dict
from flask import session
from app.models.user import User
Observation = Union[str, Exception]

PROMPT_TEMPLATE_PATH = "./data/input/react-Chinese.txt"
OUTPUT_TRACE_PATH = "./data/output/trace.txt"

class Choice(BaseModel):
    """
    Represents a choice of tool with a reason for selection.
    """
    name: str = Field(..., description="The name of the tool chosen.")
    reason: str = Field(..., description="The reason for choosing this tool.")


class Message(BaseModel):
    """
    Represents a message with sender role and content.
    """
    role: str = Field(..., description="The role of the message sender.")
    content: str = Field(..., description="The content of the message.")


class Tool:
    """
    A wrapper class for tools used by the agent, executing a function based on tool type.
    """

    def __init__(self, name: str, func: Callable[[str], str], description: str):
        """
        Initializes a Tool with a name and an associated function.
        
        Args:
            name (str): The name of the tool.
            func (Callable[[str], str]): The function associated with the tool.
            description (str): The description of the tool.
        """
        self.name = name
        self.func = func
        self.description = description
    
    def use(self, query: str) -> Observation:
        """
        Executes the tool's function with the provided query.

        Args:
            query (str): The input query for the tool.

        Returns:
            Observation: Result of the tool's function or an error message if an exception occurs.
        """
        try:
            return self.func(query)
        except Exception as e:
            logger.error(f"Error executing tool {self.name}: {e}")
            return str(e)


class Agent:
    """
    Defines the agent responsible for executing queries and handling tool interactions.
    """

    def __init__(self, model) -> None:
        """
        Initializes the Agent with a generative model, tools dictionary, and a messages log.

        Args:
            model (GenerativeModel): The generative model used by the agent.
        """
        self.model = model
        self.tools: Dict[str, Tool] = {}
        self.history: List[Message] = []  # 历史消息记录
        self.messages: List[Message] = [] # 本次任务的观测记录
        self.query = ""
        self.max_iterations = 20
        self.current_iteration = 0
        self.template = self.load_template()

    def load_template(self) -> str:
        """
        Loads the prompt template from a file.

        Returns:
            str: The content of the prompt template file.
        """
        return read_file(PROMPT_TEMPLATE_PATH)

    def register(self, name: str, func: Callable[[str], str], description: str) -> None:
        """
        Registers a tool to the agent.

        Args:
            name (str): The name of the tool.
            func (Callable[[str], str]): The function associated with the tool.
        """
        self.tools[name] = Tool(name, func, description)

    def trace(self, role: str, content: str) -> None:
        """
        Logs the message with the specified role and content and writes to file.

        Args:
            role (str): The role of the message sender.
            content (str): The content of the message.
        """
        if role != "system":
            self.messages.append(Message(role=role, content=content))
        write_to_file(path=OUTPUT_TRACE_PATH, content=f"{role}: {content}\n")

    def add_history(self, role: str, content: str) -> None:
        """
        Adds a message to the conversation history.

        Args:
            role (str): The role of the message sender.
            content (str): The content of the message.
        """
        self.history.append(Message(role=role, content=content))
    
    def get_history(self) -> str:
        return "\n".join([f"{message.role}: {message.content}" for message in self.history])

    def get_messages(self) -> str:
        """
        Retrieves the conversation history.

        Returns:
            str: Formatted history of messages.
        """
        return "\n".join([f"{message.role}: {message.content}" for message in self.messages])

    def think(self) -> None:
        """
        Processes the current query, decides actions, and iterates until a solution or max iteration limit is reached.
        """
        self.current_iteration += 1
        logger.info(f"Starting iteration {self.current_iteration}")
        write_to_file(path=OUTPUT_TRACE_PATH, content=f"\n{'='*50}\nIteration {self.current_iteration}\n{'='*50}\n")

        if self.current_iteration > self.max_iterations:
            logger.warning("Reached maximum iterations. Stopping.")
            self.trace("assistant", "I'm sorry, but I couldn't find a satisfactory answer within the allowed number of iterations. Here's what I know so far: " + self.get_messages())
            return

        prompt = self.template.format(
            query=self.query, 
            history=self.get_history(),
            messages=self.get_messages(),
            tools='\n\n'.join([
                f"{str(tool.name)}: \n \'\'\'{tool.description}\n\'\'\'" 
                for tool in self.tools.values()
                ]),
            user_info=json.dumps(UserService.get_user_info(session.get('user_id')), indent=4)
            #database_schema=database_schema
        )
        if self.current_iteration == 1:
            print(prompt)

        response = self.ask_llm(prompt)
        logger.info(f"Thinking => {response}")
        self.trace("assistant", f"Thought: {response}")
        self.decide(response)

    def decide(self, response: str) -> None:
        """
        Processes the agent's response, deciding actions or final answers.

        Args:
            response (str): The response generated by the model.
        """
        try:
            cleaned_response = response.strip().strip('`').strip()
            if cleaned_response.startswith('json'):
                cleaned_response = cleaned_response[4:].strip()
            
            parsed_response = json.loads(cleaned_response)
            
            if "action" in parsed_response:
                actions = parsed_response["action"]
                for action in actions:
                    tool_name = action["name"]
                    if not tool_name or tool_name == "none":
                        logger.info("No action needed. Proceeding to final answer.")
                    else:
                        self.trace("assistant", f"Action: Using {tool_name} tool")
                        self.act(tool_name, action.get("input", self.query))
                # 处理完所有action后，再进行思考
                self.think()
            elif "answer" in parsed_response:
                self.trace("assistant", f"{parsed_response['answer']}")
            else:
                raise ValueError("Invalid response format")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {response}. Error: {str(e)}")
            self.trace("assistant", "I encountered an error in processing. Let me try again.")
            self.think()
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            self.trace("assistant", "I encountered an unexpected error. Let me try a different approach.")
            self.think()

    def act(self, tool_name: str, query: str) -> None:
        """
        Executes the specified tool's function on the query and logs the result.

        Args:
            tool_name (str): The tool to be used.
            query (str): The query for the tool.
        """
        tool = self.tools.get(tool_name)
        if tool:
            result = tool.use(query)
            observation = f"Observation from {tool_name}: {result}"
            self.trace("system", observation)
            self.messages.append(Message(role="system", content=observation))  # Add observation to message history
            #self.think()
        else:
            logger.error(f"No tool registered for choice: {tool_name}")
            self.trace("system", f"Error: Tool {tool_name} not found")
            #self.think()

    def execute(self, query: str) -> str:
        """
        Executes the agent's query-processing workflow.

        Args:
            query (str): The query to be processed.

        Returns:
            str: The final answer or last recorded message content.
        """
        self.query = query
        self.trace(role="user", content=query)
        self.think()
        return self.messages[-1].content

    def ask_llm(self, prompt: str) -> str:
        """
        Queries the generative model with a prompt.

        Args:
            prompt (str): The prompt text for the model.

        Returns:
            str: The model's response as a string.
        """
        #contents = [Part.from_text(prompt)]
        #response = generate(self.model, contents)
        response = chat_deepseek([
            {
                "role": "user",
                "content": prompt
            }
        ])
        return str(response) if response is not None else "No response from LLM"

def run(query: str, role: str, history: List) -> str:
    """
    Sets up the agent, registers tools, and executes a query.

    Args:
        query (str): The query to execute.
        role (str): The role of the user.
        history (List): The history of the messages.

    Returns:
        str: The agent's final answer.
    """
    agent = Agent(model=None)
    tools =  student_tools if role == "student" \
        else teacher_tools if role == "teacher" \
        else admin_tools
    #tools = {'learning_analyze': teacher_tools['learning_analyze']}
    for name, tool in tools.items(): 
        agent.register(name, tool['function'], tool['description'])
    for message in history:
        agent.add_history(message.role, message.content)
    answer = agent.execute(query)
    return answer


if __name__ == "__main__":
    query = "Can you help me analysis the leanring situation of the students?"
    final_answer = run(query)
    logger.info(final_answer)
