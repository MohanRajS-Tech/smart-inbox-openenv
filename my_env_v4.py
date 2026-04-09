import asyncio
import os
from typing import Optional, Dict, Any

from models import EmailAction, EmailObservation
from server.environment import SmartInboxEnv

class MyEnvV4Action:
    """Wraps the environment actions for V4 compliance."""
    def __init__(self, action_type: str, email_id: str, folder_name: Optional[str] = None):
        self.action_type = action_type
        self.email_id = email_id
        self.folder_name = folder_name

    def to_email_action(self) -> EmailAction:
        """Converts to the internal EmailAction model."""
        return EmailAction(
            action_type=self.action_type,
            email_id=self.email_id,
            folder_name=self.folder_name
        )

    def __repr__(self):
        if self.folder_name:
            return f"{self.action_type}({self.email_id}, {self.folder_name})"
        return f"{self.action_type}({self.email_id})"

class MyEnvV4Env:
    """Async wrapper for SmartInboxEnv to meet OpenEnv V4 specifications."""
    
    def __init__(self):
        self._env = SmartInboxEnv()
        self.observation: Optional[EmailObservation] = None
        self.done = False

    @classmethod
    async def from_docker_image(cls, image_name: str = None, env_vars: Dict[str, str] = None):
        """
        Factory method required by the V4 spec.
        Locally, we ignore the image_name and just return the wrapped local environment.
        """
        # In a real Docker scenario, this would spin up a container.
        # For the hackathon's local validation, we return the local instance.
        return cls()

    async def reset(self, task_id: str = None) -> Any:
        """Async reset that matches the expected V4 return type."""
        # Use the TASK_NAME environment variable if task_id isn't provided
        if task_id is None:
            task_id = os.getenv("TASK_NAME", "easy")
            
        self.observation = self._env.reset(task_id)
        self.done = self.observation.done
        
        # Wrapped return for result.observation access
        class ResetResult:
            def __init__(self, obs):
                self.observation = obs
                self.done = obs.done
        
        return ResetResult(self.observation)

    async def step(self, action: MyEnvV4Action) -> Any:
        """Async step that matches the expected V4 return type."""
        # Convert V4 action to internal action
        internal_action = action.to_email_action()
        
        # Execute step
        obs, reward, done, info = self._env.step(internal_action)
        self.observation = obs
        self.done = done
        
        # Wrapped return for result.observation access
        class StepResult:
            def __init__(self, obs, reward, done, info):
                self.observation = obs
                self.reward = reward
                self.done = done
                self.info = info
        
        return StepResult(obs, reward, done, info)

    async def close(self):
        """Cleanup any resources."""
        # Clean up logic here if needed (e.g., closing browser, stopping container)
        pass
