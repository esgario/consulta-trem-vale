import json
import asyncio
import requests
from datetime import datetime
from telegram_bot import send_message

def convert_date(date_string):
    """Convert a date string to a timestamp"""
    return int(datetime.strptime(date_string, "%d/%m/%Y").timestamp() * 1000)


def convert_timestamp(timestamp):
    """Convert a timestamp to a date string"""
    return datetime.fromtimestamp(timestamp / 1000).strftime("%d/%m/%Y")


def get_codes():
    """Load json file with codes"""
    with open('src/codigos.json', 'r') as f:
        return json.load(f)
    

def send_message_with_retry(text, retry=3):
    """Send a message to the user with retry"""
    for i in range(retry):
        try:
            asyncio.run(send_message(text=text))
            break
        except Exception as e:
            print(f"Error sending message: {e}")
            if i == retry - 1:
                print("Failed to send message")
                break
    

def filter_passagens_ida(results, data_ida):
    """Filter passagens ida by date"""
    date_founded = False
    passagens_ida = []
    min_timestamp = convert_date(data_ida) - 86400000
    max_timestamp = convert_date(data_ida) + 2 * 86400000
    for passagem in results["passagensIda"]:
        if (passagem["partidaProgramada"] >= min_timestamp and
            passagem["partidaProgramada"] <= max_timestamp):
            passagens_ida.append(passagem)
        if data_ida == passagem["horaPartidaPrevista"]:
            date_founded = True
    return passagens_ida, date_founded
    

def prepare_response(response, data_ida, data_volta=None):
    """Prepare the response to be sent to the user"""
    message = ""
    if response.status_code == 200:
        results = response.json()
        message += f"Origem: {results['descricaoOrigem']}\n"
        message += f"Destino: {results['descricaoDestino']}\n"
        message += f"Data de consulta: {data_ida}\n"
        passagens_ida, date_founded = filter_passagens_ida(results, data_ida)

        if date_founded:
            message += "\nA data informada foi encontrada \U0001F600\n"
        else:
            message += "\nA data informada não foi encontrada\U0001F621\n"
            message += "\nDatas próximas disponíveis:\n"
            message += "----\n"
            for passagem in passagens_ida:
                message += " - " + passagem["horaPartidaPrevista"] + "\n"
            message += "----\n"
        
    else:
        message = "Erro ao consultar a API"
    
    return message


def main(data_ida="19/05/2024", data_volta=None):
    """Main function to send a request to the API and save the results to a file"""

    url = "https://tremdepassageiros.vale.com/sgpweb/rest/externo/VendaInternet/publico/pesquisaDisponibilidadePortal"
    codes = get_codes()
    num_passengers = 1
    body_data = {
        "codigoFerrovia": codes["ferrovia"]["Estrada de Ferro Vitoria a Minas"],
        "codigoLocalOrigem": codes["locais"]["Governador Valadares"],
        "codigoLocalDestino": codes["locais"]["Pedro Nolasco"],
        "dataIda": convert_date(data_ida),
        "detalheVenda": [
            {
                "detalhe": 33,
                "qtd": num_passengers,
                "funcionario": False
            }
        ],
        "codigoClasse": codes["classes"]["Executiva"]
    }
    if data_volta:
        body_data["dataVolta"] = convert_date(data_volta)

    headers = {'Content-type': 'application/json'}

    response = requests.post(url, data=json.dumps(body_data), headers=headers, verify=False)

    response_message = prepare_response(response, data_ida, data_volta)
    
    send_message_with_retry(response_message)


if __name__ == '__main__':

    main()
    