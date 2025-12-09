Build Docker image:

docker build -t aura-assistant-ollama .


Run Docker command:

docker run -d --gpus '"device=0"' --name oscar-ai aura-assistant-ollama 

#you could specify what gpu device to use, index starts from 0


Inside Docker to run python program:

docker exec -it oscar-ai bash

>cd ems_isomorphic/
>python ems_client_ollama.py







