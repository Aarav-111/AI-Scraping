"""
dependencies: ProlabsRobotics

Install Command:
pip install git+https://github.com/Aarav-111/ProlabsRobotics.git
"""

from ProlabsRobotics import AI

Prompt = input("Enter your prompt: ")
system_prompt = """
(Example system Prompt: Act like a human)
"""

print(AI(system_prompt=system_prompt).ask(Prompt))
