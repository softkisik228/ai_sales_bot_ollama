def find_client(crm_data_list, client_name):
    for row in crm_data_list:
        if row["client_name"].lower() == client_name.lower():
            return row
    return None


def build_prompt(client_data, client_message):
    """
    client_data: один словарь с полями client_name, budget, last_purchase, deal_status
    client_message: текст, который ввёл клиент
    """
    return f"""
        Клиент: {client_data['client_name']}.
        Бюджет: {client_data['budget']}$.
        Предыдущая покупка: {client_data['last_purchase']}.
        Статус сделки: {client_data['deal_status']}.

        Запрос клиента: "{client_message}"

        Ты — опытный менеджер премиального автосалона. Учитывай бюджет, упомяни прошлую покупку, предложи релевантную модель и сделай апсейл, если уместно.
        """
