import json
import os
from dotenv import load_dotenv
from colorama import Fore, Style
from time import sleep

load_dotenv()

REQUIRED_ENV_VARS = ["VASTAI_KEY", "NUM_GPUS", "DISK_SIZE", "MODEL_NAME_OLLAMA", "INSTANCE_TAG"]

my_key = os.getenv('VASTAI_KEY')
num_gpu = os.getenv('NUM_GPUS')
disk_size = os.getenv('DISK_SIZE')
model_name = os.getenv('MODEL_NAME_OLLAMA')
instance_tag = os.getenv('INSTANCE_TAG')
ollama_image = 'ollama/ollama:latest'
ollama_envs = '-p 11434:11434 -e OLLAMA_HOST=0.0.0.0 docker run -d -v ollama:/root/.ollama --name ollama'

def _validate_env_vars() -> None:
    """Validate that all required environment variables are set."""
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def search_result():
    try:
        print(f'{Fore.GREEN}Searching for instances ...{Style.RESET_ALL}')
        sleep(3)
        os.system(f'vastai search offers "reliability > 0.99 compute_cap > 800 gpu_ram >= 24 num_gpus = {num_gpu} static_ip=true direct_port_count > 1 cuda_vers >= 12.4 disk_space >= 50" --api-key {my_key} --raw > search_results.json')
    except Exception as e:
        print(f'{Fore.RED}{e}{Style.RESET_ALL}')

def parse_results():
    instances = [{}]
    with open(f'./search_results.json', 'r')as input_file:
        data = json.load(input_file)
        for index, line in enumerate(data):
            instance_id = line['id']
            price_total = line['dph_total']
            location = line['geolocation']
            gpu_name = line['gpu_name']
            gpu_ram = line['gpu_total_ram']
            inet_down = line['inet_down']
            inet_up = line['inet_up']
            instances.append({'Number': f'{index}', 'id': f'{instance_id}', 'location': f'{location}', 'gpu': f'{gpu_name}', 'gpu_ram': f'{gpu_ram}', 'inet_down': f'{inet_down} Mbps', 'inet_up': f'{inet_up} Mbps', 'price/h': f'{price_total: .2f}/hr'})
        
        print("Select the Instance you want (Number: )... ")
        print("---------------------------------")
        for _ in instances:
            if len(_) == 0:
                pass
            else:
                print(_)
        deploy_ollama(instances)

def deploy_ollama(instances):
    input_number = input("Input the Instance Number you want (ex: Number: 21): ")
    if input_number:
        for _ in instances:
            inst_number = _.get('Number')
            if input_number == inst_number:
                instance_id = _.get('id')
                try:
                    os.system(f'vastai create instance {instance_id} --image {ollama_image} --disk {disk_size} --env "{ollama_envs}" --ssh --direct --onstart-cmd "ollama serve &" --label {instance_tag} --api-key {my_key} --raw > creation_output.json')
                    with open(f'creation_output.json', 'r') as output_file:
                        data = json.load(output_file)
                        if data['success']:
                            print(f'{Fore.GREEN}Instance Created !{Style.RESET_ALL}')
                            sleep(10)
                            print(f'{Fore.GREEN} Will connect to the instance and pull the model for you :) ...{Style.RESET_ALL}')
                        else:
                            print(f'{Fore.RED}Something went wrong !{Style.RESET_ALL}')
                except Exception as e:
                    print(f'{Fore.RED}{e}{Style.RESET_ALL}')
    else:
        print(f"{Fore.RED}You must enter a numeric value here ...{Style.RESET_ALL}")

def status_check():
    running = False
    while running == False:
        sleep(3)
        os.system(f'vastai show instances --api-key {my_key} --raw > instances_list.json')
        with open('./instances_list.json', 'r')as input_file:
            data = json.load(input_file)
            for _ in data:
                if _['label'] == instance_tag:
                    status = _['actual_status']
                    if status == 'running':
                        print(f'{Fore.GREEN}Instance running !{Style.RESET_ALL}')
                        running = True
                    else:
                        print(f'{Fore.MAGENTA}Instance is still booting up ...{Style.RESET_ALL}')

def pull_model():
    try:
        with open('./instances_list.json', 'r')as input_file:
            data = json.load(input_file)
            for _ in data:
                public_ipaddr = _["public_ipaddr"]
                ssh_port = _['ports']['22/tcp'][1]['HostPort']
                ollama_port = _['ports']['11434/tcp'][0]['HostPort']
                print(f'{Fore.CYAN}Connecting to {instance_tag} via SSH to pull {model_name}')
                os.system(f'ssh -p {ssh_port} root@{public_ipaddr} -L 8080:localhost:8080 "ollama pull {model_name}"')
                print(f'You can now set your {Fore.YELLOW}.env{Style.RESET_ALL} file as such: ')
                print(f'OLLAMA_BASE_URL={Fore.GREEN}"http://{public_ipaddr}:{ollama_port}"{Style.RESET_ALL}')
                print(f'OLLAMA_MODEL_NAME={Fore.GREEN}"{model_name}"{Style.RESET_ALL}')
                os.system('rm -f instances_list.json creation_output.json search_results.json')
    except Exception:
        print(f'{Fore.RED}instances_list.json might not exists{Style.RESET_ALL}')

_validate_env_vars()
search_result()
parse_results()
status_check()
pull_model()