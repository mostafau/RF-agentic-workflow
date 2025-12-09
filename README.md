Build Docker image:

docker build -t aura-assistant-ollama .


Run Docker command:

docker run -d --gpus '"device=0"' --name oscar-ai aura-assistant-ollama 

#you could specify what gpu device to use, index starts from 0


Inside Docker to run python program:

docker exec -it oscar-ai bash


This program use multi-stage Agentic workflow:

see WORKFLOW.md file for understanding the details workflow of this program.

>cd ems_langgraph/

>python intent_langgraph.py








