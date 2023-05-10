import logging
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler
from telegram.ext import ConversationHandler
from telegram.ext import ConversationHandler, Filters
import uuid
import logging
import os


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
TELEGRAM_TOKEN = "6128472055:AAFJTQjSxd2pM4PQL2DWb7rua6WuTSihpuk"
FILTER_NAME_INPUT = 99
FILTER_PHONE_INPUT = 100
FILTER_SERVICE_INPUT = 101
FILTER_RETURN_TIME_INPUT = 102
NAME, PHONE, RETURN_TIME, FILTER_NAME_INPUT, FILTER_PHONE_INPUT, FILTER_SERVICE_INPUT, FILTER_RETURN_TIME_INPUT = range(7)
ADD_SERVICE, ADD_BARBER, BARBER_NAME, BARBER_PHONE, BARBER_BIRTHDAY = range(103, 108)
ADD_SERVICE_NAME = 7
# Constante de estado
SERVICE = 3
BARBER = 6
BIRTHDAY = 7
LAST_CUT_DATE = 8
USER_DATA_V2 = "user_data_v2"



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
            InlineKeyboardButton("Cadastrar", callback_data="add_client"),
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
    update.message.reply_text("Vamos cadastrar um novo cliente. Digite o nome do cliente:")
    client_id = uuid.uuid4().hex
    registration_date = datetime.now().strftime('%Y-%m-%d')
    context.user_data['client_info'] = {'id': client_id, 'registration_date': registration_date}
    return NAME





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

def name_handler(update: Update, context: CallbackContext):
    name = update.message.text
    context.user_data['client_info']['name'] = name
    update.message.reply_text("Digite a data de aniversário do cliente:")
    return BIRTHDAY

def phone_handler(update: Update, context: CallbackContext):
    phone = update.message.text
    context.user_data['client_info']['phone'] = phone

    barbers = load_barbers()
    barbers_keyboard = [[InlineKeyboardButton(barber['name'], callback_data=f"barber:{barber['id']}")] for barber in barbers]
    barbers_keyboard.append([InlineKeyboardButton("Confirmar barbeiro", callback_data="confirm_barber")])  # Adicione esta linha
    reply_markup = InlineKeyboardMarkup(barbers_keyboard)
    update.message.reply_text("Selecione o barbeiro do cliente e confirme:", reply_markup=reply_markup)
    return BARBER


def barber_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    callback_data = query.data

    if callback_data == "confirm_barber":
        # Quando o botão "Confirmar barbeiro" é pressionado, passe para o próximo estado
        services = load_services()
        services_keyboard = [[InlineKeyboardButton(service['name'], callback_data=f"service:{service['id']}")] for service in services]
        services_keyboard.append([InlineKeyboardButton("Confirmar serviço(s)", callback_data="confirm_service")])
        reply_markup = InlineKeyboardMarkup(services_keyboard)
        query.edit_message_text("Selecione o(s) serviço(s) do cliente e confirme:", reply_markup=reply_markup)
        return SERVICE
    else:
        # Se um barbeiro foi selecionado, salve o id do barbeiro e continue a lista de barbeiros
        barber_id = int(callback_data.split(':')[1])
        context.user_data['client_info']['barber_id'] = barber_id
        query.answer()

        barbers = load_barbers()
        barbers_keyboard = [[InlineKeyboardButton(barber['name'], callback_data=f"barber:{barber['id']}")] for barber in barbers]
        barbers_keyboard.append([InlineKeyboardButton("Confirmar barbeiro", callback_data="confirm_barber")])
        reply_markup = InlineKeyboardMarkup(barbers_keyboard)
        query.edit_message_text("Selecione o barbeiro do cliente e confirme:", reply_markup=reply_markup)
        return BARBER




def service_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    if data == "confirm_services":
        # Ações para quando o botão "Confirmar serviços" é pressionado
        query.answer()
        return RETURN_TIME  # ou qualquer próximo estado
    else:
        service_id = int(data.split(':')[1])
        if 'services' not in context.user_data['client_info']:
            context.user_data['client_info']['services'] = []
        context.user_data['client_info']['services'].append(service_id)
        query.answer("Serviço adicionado!")
        return SERVICE

 

def add_service(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Por favor, envie o nome do serviço.")
    return ADD_SERVICE

def save_service(update: Update, context: CallbackContext) -> int:
    service_name = update.message.text
    context.user_data['service_info'] = {'name': service_name}
    save_service_info(context.user_data['service_info'])
    logging.info(f"Adicionando o serviço {service_name}")
    try:
        with open('services.json', 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                logging.warning("JSONDecodeError, criando uma nova lista de serviços")
                data = {"services": []}
    except FileNotFoundError:
        logging.warning("services.json não encontrado, criando um novo arquivo")
        data = {"services": []}

    data["services"].append(service_name)

    with open('services.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info("Serviço adicionado e arquivo services.json atualizado")

    update.message.reply_text(f"Serviço {service_name} adicionado com sucesso.")
    return ConversationHandler.END

def load_barbers():
    try:
        with open('barbers.json', 'r') as f:
            barbers = json.load(f)
    except FileNotFoundError:
        barbers = []

    return barbers

def load_services():
    if os.path.exists('services.json'):
        with open('services.json', 'r') as f:
            services = json.load(f)
            if services:
                return services
            else:
                print("No services found in services.json")
                return []
    else:
        print("services.json not found.")
        return []

def birthday_handler(update: Update, context: CallbackContext):
    birthday = update.message.text
    context.user_data['client_info']['birthday'] = birthday
    update.message.reply_text("Digite o telefone do cliente:")
    return PHONE

def add_barber(update: Update, context: CallbackContext):
    update.message.reply_text("Digite o nome do barbeiro:")
    return BARBER_NAME

def barber_name_handler(update: Update, context: CallbackContext):
    name = update.message.text
    context.user_data['barber_info'] = {'name': name}
    update.message.reply_text("Digite o número de telefone do barbeiro:")
    return BARBER_PHONE

def barber_phone_handler(update: Update, context: CallbackContext):
    phone = update.message.text
    context.user_data['barber_info']['phone'] = phone
    update.message.reply_text("Digite a data de aniversário do barbeiro (formato: DD/MM/AAAA):")
    return BARBER_BIRTHDAY

def barber_birthday_handler(update: Update, context: CallbackContext):
    birthday = update.message.text
    context.user_data['barber_info']['birthday'] = birthday
    save_barber_info(context.user_data['barber_info'])
    update.message.reply_text("Barbeiro cadastrado com sucesso!")
    return ConversationHandler.END

def save_barber_info(info):
    try:
        with open('barbers.json', 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    except FileNotFoundError:
        data = []

    if data:
        barber_id = max([barber.get("id", 0) for barber in data]) + 1
    else:
        barber_id = 1

    info["id"] = barber_id
    data.append(info)

    with open('barbers.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_service_info(info):
    try:
        with open('services.json', 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    except FileNotFoundError:
        data = []

    if data:
        service_id = max([service.get("id", 0) for service in data]) + 1
    else:
        service_id = 1

    info["id"] = service_id
    data.append(info)

    with open('services.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def service_name_handler(update: Update, context: CallbackContext):
    service_name = update.message.text
    context.user_data['service_name'] = service_name

    # Salve o serviço no arquivo JSON
    with open("services.json", "r+") as f:
        data = json.load(f)
        data["services"].append(service_name)
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.truncate()

    update.message.reply_text(f"Serviço {service_name} adicionado com sucesso.")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    logging.warning("Função cancel chamada")
    user = update.effective_user
    update.message.reply_text("Operação cancelada.")
    return ConversationHandler.END

def return_time_handler(update: Update, context: CallbackContext):
    return_time = int(update.message.text)
    context.user_data['client_info']['return_time'] = return_time
    save_client_info(context.user_data['client_info'])
    update.message.reply_text("Cliente cadastrado com sucesso!")
    return ConversationHandler.END

def last_cut_date_handler(update: Update, context: CallbackContext):
    last_cut_date = update.message.text
    context.user_data['client_info']['last_cut_date'] = last_cut_date

    # continue the flow
    update.message.reply_text("Digite a data de retorno:")
    return RETURN_TIME

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
        [InlineKeyboardButton("Cadastrar", url="/add_client")],
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
    return FILTER_NAME_INPUT  # Altere esta linhadef filter_name_input(update: Update, context: CallbackContext):
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

def filter_name_input(update: Update, context: CallbackContext):
    user_data = context.user_data
    query = update.message.text
    logger.info(f"Procurando por: {query}")

    with open('clients.json', 'r') as f:
        data = json.load(f)

    # Busque o cliente pelo nome
    clients = [client for client in data['clients'] if query in client['name']]

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
            CommandHandler('start', start),
            CommandHandler('add_client', add_client),
            CallbackQueryHandler(filter_by_name, pattern="filter_name"),
            CallbackQueryHandler(filter_by_phone, pattern="filter_phone"),
            CallbackQueryHandler(filter_by_service, pattern="filter_service"),
            CallbackQueryHandler(filter_by_return_time, pattern="filter_return_time"),
            CommandHandler("addservice", add_service),
            CommandHandler("addbarber", add_barber),
            CommandHandler("cancel", cancel)
        ],
        states={
            NAME: [MessageHandler(Filters.text, name_handler)],
            BIRTHDAY: [MessageHandler(Filters.text, birthday_handler)],
            PHONE: [MessageHandler(Filters.text, phone_handler)],
            BARBER: [CallbackQueryHandler(barber_handler)],
            SERVICE: [CallbackQueryHandler(service_handler)],
            LAST_CUT_DATE: [MessageHandler(Filters.text, last_cut_date_handler)],
            RETURN_TIME: [MessageHandler(Filters.text, return_time_handler)],
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
            ADD_SERVICE: [
                MessageHandler(Filters.text, save_service),
            ],
            BARBER_NAME: [
                MessageHandler(Filters.text, barber_name_handler),
            ],
            BARBER_PHONE: [
                MessageHandler(Filters.text, barber_phone_handler),
            ],
            BARBER_BIRTHDAY: [
                MessageHandler(Filters.text, barber_birthday_handler),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Adicione o ConversationHandler ao dispatcher
    dp.add_handler(conv_handler)
    
    # Adicione os outros handlers
    dp.add_handler(CommandHandler("checkreturns", check_returns))

    # Inicie o bot
    updater.start_polling()
    updater.idle()



if __name__ == "__main__":
    main()
