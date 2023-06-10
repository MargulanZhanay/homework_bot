import os

from dotenv import load_dotenv

load_dotenv()

TIMESTAMP = 1654773946
RETRY_PERIOD = 600

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HEADERS = {'Authorization': f'OAuth {os.getenv("PRACTICUM_TOKEN")}'}
