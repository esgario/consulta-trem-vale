import json
import asyncio
import requests
import argparse

from datetime import datetime
from telegram_bot import send_message


def _convert_date(date_string):
    """Convert a date string to a timestamp"""
    return int(datetime.strptime(date_string, "%d/%m/%Y").timestamp() * 1000)


def _get_codes():
    """Load json file with codes"""
    with open("src/codigos.json", "r") as f:
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
    min_timestamp = _convert_date(data_ida) - 86400000
    max_timestamp = _convert_date(data_ida) + 2 * 86400000
    for passagem in results["passagensIda"]:
        if (
            passagem["partidaProgramada"] >= min_timestamp
            and passagem["partidaProgramada"] <= max_timestamp
        ):
            passagens_ida.append(passagem)
        if data_ida == passagem["horaPartidaPrevista"]:
            date_founded = True
    return passagens_ida, date_founded


def prepare_response(response, data_ida, classe):
    """Prepare the response to be sent to the user"""
    message = ""
    if response.status_code == 200:
        results = response.json()
        message += f"Origem: {results['descricaoOrigem']}\n"
        message += f"Destino: {results['descricaoDestino']}\n"
        message += f"Classe: {classe}\n"
        message += f"Data de consulta: {data_ida}\n"
        passagens_ida, date_founded = filter_passagens_ida(results, data_ida)

        if date_founded:
            message += "\nA data informada foi encontrada \U00002705\n"
        else:
            message += "\nA data informada não foi encontrada \U0000274C\n"
            message += "\nDatas próximas disponíveis:\n"
            for passagem in passagens_ida:
                message += " - " + passagem["horaPartidaPrevista"] + "\n"

    else:
        message = "Erro ao consultar a API"

    return message


def call_api(
    data_ida: str, origem: str, destino: str, classe: str, total_passageiros: int
):
    """Call the API to get the available trips

    Args:
        data_ida (str): The date of the trip
        origem (str): The origin of the trip
        destino (str): The destination of the trip
        total_passageiros (int): The number of passengers

    Returns:
        requests.Response: The response from the API
    """
    url = "https://tremdepassageiros.vale.com/sgpweb/rest/externo/VendaInternet/publico/pesquisaDisponibilidadePortal"
    codes = _get_codes()
    body_data = {
        "codigoFerrovia": codes["ferrovia"]["Estrada de Ferro Vitoria a Minas"],
        "codigoLocalOrigem": codes["locais"][origem],
        "codigoLocalDestino": codes["locais"][destino],
        "dataIda": _convert_date(data_ida),
        "detalheVenda": [
            {"detalhe": 33, "qtd": total_passageiros, "funcionario": False}
        ],
        "codigoClasse": codes["classes"][classe],
    }

    headers = {"Content-type": "application/json"}

    response = requests.post(
        url, data=json.dumps(body_data), headers=headers, verify=False
    )

    return response


def parse_args():
    """Parse the arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_ida", type=str, help="Data Ida")
    parser.add_argument(
        "--origem", type=str, help="Origem", default="Governador Valadares"
    )
    parser.add_argument("--destino", type=str, help="Destino", default="Pedro Nolasco")
    parser.add_argument("--classe", type=str, help="Classe", default="Executiva")
    parser.add_argument(
        "--total_passageiros", type=int, help="Total de Passageiros", default=1
    )
    return parser.parse_args()


def main():
    """Main function to send a request to the API and send the results to the user"""
    args = parse_args()
    response = call_api(
        args.data_ida, args.origem, args.destino, args.classe, args.total_passageiros
    )
    response_message = prepare_response(response, args.data_ida, args.classe)
    send_message_with_retry(response_message)


if __name__ == "__main__":
    main()
