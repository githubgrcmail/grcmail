import logging
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler
from telegram.ext import ConversationHandler
from telegram.ext import ConversationHandler, Filters
import uuid
import logging

logger = logging.getLogger(__name__)
TELEGRAM_TOKEN = "6128472055:AAFJTQjSxd2pM4PQL2DWb7rua6WuTSihpuk"
FILTER_NAME_INPUT = 99
FILTER_PHONE_INPUT = 100
FILTER_SERVICE_INPUT = 101
FILTER_RETURN_TIME_INPUT = 102
NAME, PHONE, SERVICE, RETURN_TIME, FILTER_NAME_INPUT, FILTER_PHONE_INPUT, FILTER_SERVICE_INPUT, FILTER_RETURN_TIME_INPUT = range(8)

# Inicializa o arquivo de dados dos clientes
data_file = "clients_data.json"

def save_data(clients_data):
    with open(data_file, "w") as f:
        json.dump(clients_data, f, ensure_ascii=False, indent=4)

def load_data():
    try:
        with open(data_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

clients_data = load_data()

#---------------------Funções do Inicio---------------------#

def start(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Cadastrar", callback_data='cadastrar'),
            InlineKeyboardButton("Filtrar por nome", callback_data='filter_name'),
            InlineKeyboardButton("Filtrar por telefone", callback_data='filter_phone'),
        ],
        [
            InlineKeyboardButton("Filtrar por serviço", callback_data='filter_service'),
            InlineKeyboardButton("Filtrar por tempo de retorno", callback_data='filter_return_time'),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("Por favor, escolha uma opção:", reply_markup=reply_markup)


def add_client(update: Update, context: CallbackContext):
    message = update.message.text
    message_parts = message.split(",")

    if len(message_parts) != 4:
        update.message.reply_text(
            "Formato incorreto. Por favor, envie as informações no seguinte formato:\n"
            "/addclient Nome, Telefone, Serviço, Dias para retorno"
        )
        return

    name, phone, service, days = [part.strip() for part in message_parts]
    client_id = str(update.message.from_user.id) + "_" + phone

    if client_id not in clients_data:
        clients_data[client_id] = {
            "name": name,
            "phone": phone,
            "service": service,
            "return_days": int(days),
            "last_visit": str(datetime.now())
        }
        save_data(clients_data)
        update.message.reply_text("Cliente cadastrado com sucesso!")
    else:
        update.message.reply_text("Cliente já cadastrado.")


def check_returns(update: Update, context: CallbackContext):
    clients_to_contact = []

    for client_id, client_data in clients_data.items():
        last_visit = datetime.strptime(client_data["last_visit"], "%Y-%m-%dT%H:%M:%S.%f")
        return_date = last_visit + timedelta(days=client_data["return_days"])

        if datetime.now() >= return_date:
            clients_to_contact.append(client_data)

    if clients_to_contact:
        message = "Clientes para entrar em contato para agendamento:\n"
        for client in clients_to_contact:
            message += f"{client['name']} ({client['phone']})\n"
        update.message.reply_text(message)
    else:
        update.message.reply_text("Nenhum cliente para entrar em contato no momento.")

#---------------------Funções de Cadastro---------------------#

def cadastrar(update: Update, context: CallbackContext):
    query = update.callback_query

    # Adicione essa linha para inicializar o dicionário 'client_info'
    context.user_data['client_info'] = {}

    if query:
        query.answer()
        chat_id = query.message.chat_id
        context.bot.send_message(chat_id, "Vamos cadastrar um novo cliente.\nPor favor, digite o nome do cliente:")
    else:
        update.message.reply_text("Vamos cadastrar um novo cliente.\nPor favor, digite o nome do cliente:")

    return NAME


def name_handler(update: Update, context: CallbackContext):
    name = update.message.text
    context.user_data['client_info']['name'] = name
    update.message.reply_text("Digite o número de telefone do cliente:")
    return PHONE


def phone_handler(update: Update, context: CallbackContext):
    phone = update.message.text
    context.user_data['client_info']['phone'] = phone

    # Crie o teclado inline com as opções de serviços
    service_keyboard = [
        [
            InlineKeyboardButton("Barba", callback_data="Barba"),
            InlineKeyboardButton("Corte", callback_data="Corte"),
            InlineKeyboardButton("Barba e Corte", callback_data="Barba e Corte")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(service_keyboard)

    # Envie a mensagem com o teclado inline
    update.message.reply_text("Selecione o serviço utilizado:", reply_markup=reply_markup)
    return SERVICE


def service_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    service = query.data
    context.user_data['client_info']['service'] = service

    # Atualize a mensagem com a seleção do usuário
    query.edit_message_text(f"Serviço selecionado: {service}\nDigite o tempo para retorno (em dias):")
    return RETURN_TIME


def return_time_handler(update: Update, context: CallbackContext):
    return_time = int(update.message.text)
    context.user_data['client_info']['return_time'] = return_time
    save_client_info(context.user_data['client_info'])
    update.message.reply_text("Cliente cadastrado com sucesso!")
    return ConversationHandler.END


#---------------------Fim de Cadastro---------------------#


def save_client_info(client_info):
    client_info["id"] = str(uuid.uuid4())
    client_info["registration_datetime"] = str(datetime.now())

    with open("clients.json", "r+") as f:
        data = json.load(f)
        data["clients"].append(client_info)
        f.seek(0)
        json.dump(data, f, indent=4)


def show_main_menu(update: Update, context: CallbackContext):
    menu_keyboard = [
        [InlineKeyboardButton("Cadastrar", callback_data="cadastrar")],
        [InlineKeyboardButton("Filtrar por Nome", callback_data="filter_name")],
        [InlineKeyboardButton("Filtrar por Telefone", callback_data="filter_phone")],
        [InlineKeyboardButton("Filtrar por Serviço", callback_data="filter_service")],
        [InlineKeyboardButton("Filtrar por Tempo de Retorno", callback_data="filter_return_time")]
    ]
    reply_markup = InlineKeyboardMarkup(menu_keyboard)
    update.message.reply_text("Selecione uma opção:", reply_markup=reply_markup)


#---------------------Filtros---------------------#


def filter_by_name(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text("Digite o nome que deseja buscar:")
    return FILTER_NAME_INPUT  # Altere esta linha


def filter_name_input(update: Update, context: CallbackContext):
    user_data = context.user_data
    query = update.message.text
    logger.info(f"Procurando por: {query}")

    with open('clients.json', 'r') as f:
        data = json.load(f)

    # Busque o cliente pelo nome
    clients = [client for client in data['clients'] if query.lower() in client['name'].lower()]

    # Log para verificar os clientes encontrados
    logger.info(f"Clientes encontrados: {clients}")

    if not clients:
        update.message.reply_text("Nenhum cliente encontrado.")
    else:
        response = "Clientes encontrados:\n\n"
        for client in clients:
            response += f"{client['name']}\nTelefone: {client['phone']}\nServiço: {client['service']}\nTempo de retorno: {client['return_time']} dias\n\n"

        update.message.reply_text(response)

    return ConversationHandler.END


def filter_by_phone(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("Digite o número de telefone que deseja buscar:")
    return FILTER_PHONE_INPUT


def filter_by_service(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("Digite o serviço que deseja buscar:")
    return FILTER_SERVICE_INPUT


def filter_by_return_time(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("Digite o tempo de retorno que deseja buscar:")
    return FILTER_RETURN_TIME_INPUT


def filter_phone_input(update: Update, context: CallbackContext):
    user_data = context.user_data
    query = update.message.text
    logger.info(f"Procurando por: {query}")

    with open('clients.json', 'r') as f:
        data = json.load(f)

    # Busque o cliente pelo telefone
    clients = [client for client in data['clients'] if query in client['phone']]

    if not clients:
        update.message.reply_text("Nenhum cliente encontrado.")
    else:
        response = "Clientes encontrados:\n\n"
        for client in clients:
            response += f"{client['name']}\nTelefone: {client['phone']}\nServiço: {client['service']}\nTempo de retorno: {client['return_time']} dias\n\n"

        update.message.reply_text(response)

    return ConversationHandler.END


def filter_service_input(update: Update, context: CallbackContext):
    user_data = context.user_data
    query = update.message.text
    logger.info(f"Procurando por: {query}")

    with open('clients.json', 'r') as f:
        data = json.load(f)

    # Busque o cliente pelo serviço
    clients = [client for client in data['clients'] if query.lower() in client['service'].lower()]

    if not clients:
        update.message.reply_text("Nenhum cliente encontrado.")
    else:
        response = "Clientes encontrados:\n\n"
        for client in clients:
            response += f"{client['name']}\nTelefone: {client['phone']}\nServiço: {client['service']}\nTempo de retorno: {client['return_time']} dias\n\n"

        update.message.reply_text(response)

    return ConversationHandler.END


def filter_return_time_input(update: Update, context: CallbackContext):
    user_data = context.user_data
    query = int(update.message.text)
    logger.info(f"Procurando por: {query}")

    with open('clients.json', 'r') as f:
        data = json.load(f)

    # Busque o cliente pelo tempo de retorno
    clients = [client for client in data['clients'] if query == client['return_time']]

    if not clients:
        update.message.reply_text("Nenhum cliente encontrado.")
    else:
        response = "Clientes encontrados:\n\n"
        for client in clients:
            response += f"{client['name']}\nTelefone: {client['phone']}\nServiço: {client['service']}\nTempo de retorno: {client['return_time']} dias\n\n"

        update.message.reply_text(response)

    return ConversationHandler.END


def main():
    logging.basicConfig(level=logging.INFO)
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Crie o ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            
            CallbackQueryHandler(cadastrar, pattern="cadastrar"),
            CallbackQueryHandler(filter_by_name, pattern="filter_name"),
            CallbackQueryHandler(filter_by_phone, pattern="filter_phone"),
            CallbackQueryHandler(filter_by_service, pattern="filter_service"),
            CallbackQueryHandler(filter_by_return_time, pattern="filter_return_time"),
            
        ],
        states={
            NAME: [
                MessageHandler(Filters.text, name_handler),
            ],
            PHONE: [
                MessageHandler(Filters.text, phone_handler),
            ],
            SERVICE: [
                CallbackQueryHandler(service_handler),
            ],
            RETURN_TIME: [
                MessageHandler(Filters.text, return_time_handler),
            ],
            FILTER_NAME_INPUT: [
                MessageHandler(Filters.text, filter_name_input)
            ],
            FILTER_PHONE_INPUT: [
                MessageHandler(Filters.text, filter_phone_input)
            ],
            FILTER_SERVICE_INPUT: [
                MessageHandler(Filters.text, filter_service_input)
            ],
            FILTER_RETURN_TIME_INPUT: [
                MessageHandler(Filters.text, filter_return_time_input)
            ],
        },
        fallbacks=[],
    )


    # Adicione o ConversationHandler ao dispatcher
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("start", start))
    # Adicione os outros handlers
    dp.add_handler(CommandHandler("addclient", add_client))
    dp.add_handler(CommandHandler("checkreturns", check_returns))

    # Inicie o bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
