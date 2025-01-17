from typing import List

from langchain.tools import Tool
from pydantic import BaseModel, Field

from crewai.agent import Agent
from crewai.utilities import I18N


class AgentTools(BaseModel):
    """Default tools around agent delegation"""

    agents: List[Agent] = Field(description="List of agents in this crew.")
    i18n: I18N = Field(default=I18N(), description="Internationalization settings.")

    def tools(self):
        """        Return a list of tools available for the user.

        This method returns a list of Tool objects, each representing a specific tool available for the user to utilize.

        Returns:
            list: A list of Tool objects.

        Raises:
             None
        """

        return [
            Tool.from_function(
                func=self.delegate_work,
                name="Delegate work to co-worker",
                description=self.i18n.tools("delegate_work").format(
                    coworkers=", ".join([agent.role for agent in self.agents])
                ),
            ),
            Tool.from_function(
                func=self.ask_question,
                name="Ask question to co-worker",
                description=self.i18n.tools("ask_question").format(
                    coworkers=", ".join([agent.role for agent in self.agents])
                ),
            ),
        ]

    def delegate_work(self, command):
        """        Useful to delegate a specific task to a coworker.

        Args:
            self: The object instance
            command: The specific task to be delegated

        Returns:
            The result of executing the command
        """
        return self._execute(command)

    def ask_question(self, command):
        """        Useful to ask a question, opinion or take from a coworker.

        Args:
            command (str): The command to be executed.

        Returns:
            The result of executing the command.
        """
        return self._execute(command)

    def _execute(self, command):
        """        Execute the command.

        Args:
            command (str): The command to be executed in the format "agent|task|context".

        Returns:
            str: The result of executing the command.

        Raises:
            ValueError: If the command does not contain all three parts separated by "|".
            ValueError: If any of the parts (agent, task, context) is missing in the command.
            ValueError: If the specified agent does not exist in the list of available agents.
        """
        try:
            agent, task, context = command.split("|")
        except ValueError:
            return self.i18n.errors("agent_tool_missing_param")

        if not agent or not task or not context:
            return self.i18n.errors("agent_tool_missing_param")

        agent = [
            available_agent
            for available_agent in self.agents
            if available_agent.role == agent
        ]

        if not agent:
            return self.i18n.errors("agent_tool_unexsiting_coworker").format(
                coworkers=", ".join([agent.role for agent in self.agents])
            )

        agent = agent[0]
        return agent.execute_task(task, context)
