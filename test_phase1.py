import asyncio
from my_env_v4 import MyEnvV4Env, MyEnvV4Action

async def test_v4_interface():
    print("Testing Phase 1: V4 Interface Wrapper...")
    
    # 1. Test Factory
    env = await MyEnvV4Env.from_docker_image("test-image")
    print("[OK] from_docker_image() works")
    
    # 2. Test Reset
    result = await env.reset(task_id="easy")
    print(f"[OK] reset() works. Observations: {len(result.observation.emails)} emails")
    
    # 3. Test Step
    action = MyEnvV4Action(action_type="archive", email_id="1")
    result = await env.step(action)
    print(f"[OK] step() works. Reward: {result.reward}, Done: {result.done}")
    
    await env.close()
    print("Phase 1 Verification SUCCESSFUL")

if __name__ == "__main__":
    asyncio.run(test_v4_interface())
