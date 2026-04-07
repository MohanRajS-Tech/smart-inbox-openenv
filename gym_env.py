import gymnasium as gym
from gymnasium import spaces
import numpy as np

from server.environment import SmartInboxEnv
from models import EmailAction

class SmartInboxGymEnv(gym.Env):
    """
    A Standard Gymnasium wrapper for the Smart Inbox OpenEnv specification.
    This makes the environment immediately compatible with reinforcement 
    learning libraries like Stable Baselines3, Ray RLlib, and TRL.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, task_id="easy"):
        super().__init__()
        self.task_id = task_id
        self.env = SmartInboxEnv()
        
        # Action space: MultiDiscrete
        # [0] Action type: 0=archive, 1=flag, 2=move_to_folder (Work)
        # [1] Email ID index: 0-14 (Supporting up to 15 emails per episode)
        self.action_space = spaces.MultiDiscrete([3, 15])
        
        # Observation space: Box (continuous floats)
        # We flatten the EmailObservation into a numeric array for standard RL.
        # Max 15 emails. For each email we send 3 features:
        # [is_present (0/1), is_urgent (0/1), is_flagged (0/1)]
        # Plus 2 global features: [goal_progress, steps_remaining_normalized]
        # Total Shape: (15 * 3) + 2 = 47 dimensions
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(47,), dtype=np.float32)

    def _encode_obs(self, obs):
        """Flattens the structured OpenEnv observation into a float32 array."""
        encoded = np.zeros(47, dtype=np.float32)
        encoded[0] = float(obs.goal_progress)
        encoded[1] = float(obs.steps_remaining) / 15.0 # Max Steps is 15 in state defaults
        
        # Cap at 15 to match our Box space
        for i, email in enumerate(obs.emails[:15]):
            # Emails IDs are string numbers "1", "2", etc.
            # We map email_id "1" to index 0, "2" to index 1, etc.
            try:
                # Store the email at a fixed position based on its absolute ID
                # This ensures consistent feature mapping for the neural network
                eid_idx = int(email.id) - 1
                if 0 <= eid_idx < 15:
                    idx = 2 + (eid_idx * 3)
                    encoded[idx] = 1.0     # is_present
                    encoded[idx+1] = 1.0 if getattr(email, "is_urgent", False) else 0.0
                    encoded[idx+2] = 1.0 if getattr(email, "is_flagged", False) else 0.0
            except ValueError:
                pass
                
        return encoded

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        obs = self.env.reset(task_id=self.task_id, seed=seed)
        return self._encode_obs(obs), {}

    def step(self, action):
        action_idx = action[0]
        email_idx = action[1]
        
        # Map back to string commands
        action_map = {0: "archive", 1: "flag", 2: "move_to_folder"}
        action_type = action_map.get(action_idx, "archive")
        
        # Convert absolute index back to email ID string
        email_id = str(email_idx + 1)
        folder_name = "Work" if action_type == "move_to_folder" else None
        
        env_action = EmailAction(action_type=action_type, email_id=email_id, folder_name=folder_name)
        
        obs, reward, done, info = self.env.step(env_action)
        
        return self._encode_obs(obs), reward, done, False, {"last_status": obs.last_action_status}

    def render(self):
        state = self.env.state()
        print(f"Task: {self.task_id} | Score: {state.score:.2f} | Step {state.step_count}/{state.max_steps}")
