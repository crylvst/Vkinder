from config import group_token
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import bot_logic
import database_logic

vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)

offset = 0
search_completed = False

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        request = event.text
        user_id = event.user_id

        if request == 'vkinder':
            database_logic.create_database()
            age_from, age_to, sex, city_title, city_id = bot_logic.chat_bot(user_id, longpoll)
            search_completed = True
            offset = 0
            bot_logic.send_messages(user_id, f'Вы зарегистрированы в системе, для показа анкет введите смотреть')

        elif request == 'смотреть':
            if search_completed:
                # if age_from is not None and age_to is not None and sex is not None and city_title and city_id: (Можно использовать и такую конструкцию, смысл будет один)
                if all([age_from, age_to, sex, city_title, city_id]):
                    bot_logic.send_messages(user_id, f"offset = {offset}")
                    bot_logic.send_messages(user_id, "Смотрим")
                    bot_logic.search_for_people(user_id=user_id, age_from=age_from, age_to=age_to, sex=sex, city_title=city_title, city_id=city_id, offset=offset)
                    offset += 30
                else:
                    bot_logic.send_messages(user_id,
                                              f'Не все данные определены. Сначала нужно выполнить команду "vkinder"')
            else:
                bot_logic.send_messages(user_id, f'Для начала поиска введите vkinder')

        elif request == 'очистка':
            database_logic.create_database()
            bot_logic.send_messages(user_id, f'База очищена')

        else:
            bot_logic.send_messages(user_id, f"Введите 'vkinder' для начала работы\n"
                                               f"Введите 'смотреть', чтобы показать результаты\n"
                                               f"Введите 'очистка',чтобы очистить базу данных")
