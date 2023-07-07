from random import randrange
from config import group_token
from config import user_token
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import datetime
from database_logic import add_user
from database_logic import check_db


vk_group = vk_api.VkApi(token=group_token)
vk_group_got_api = vk_group.get_api()

vk_user = vk_api.VkApi(token=user_token)
vk_user_got_api = vk_user.get_api()

longpoll = VkLongPoll(vk_group)


def get_user_info(user_id):
    user_info = vk_group.method('users.get', {'user_ids': user_id, 'fields': 'sex,bdate,city,country'})
    return user_info


def send_messages(user_id, message):
    vk_group_got_api.messages.send(user_id=user_id, message=message, random_id=randrange(10 ** 7))


def chat_bot(user_id, longpoll):
    user_info = get_user_info(user_id)

    age_from, age_to = get_age(user_id, user_info, longpoll)
    sex = get_sex(user_id, user_info)
    city_id, city_title = get_city(user_id, user_info, longpoll)

    return age_from, age_to, sex, city_title, city_id


def get_age(user_id, user_info, longpoll):
    send_messages(user_id, f'Введите 1 - чтобы использовать возраст, указанный в профиле или введите 2 - чтобы ввести возраст вручную')
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            request = event.text
            if request == '1':
                age_from, age_to = get_your_age(user_id, user_info, longpoll)
                return age_from, age_to
            elif request == '2':
                age_from, age_to = get_new_age(user_id, longpoll)
                return age_from, age_to
            else:
                send_messages(user_id,
                                 f'Введите 1 - чтобы использовать возраст, указанный в профиле или введите 2 - чтобы ввести возраст вручную')


def get_your_age(user_id, user_info, longpoll):
    try:
        birthday = user_info[0]['bdate']
        birthdate = datetime.datetime.strptime(birthday, '%d.%m.%Y')
        today = datetime.datetime.now()
        age = (today - birthdate).days // 365
        send_messages(user_id, f'Ваш возраст: {age}')
        return age, age
    except KeyError:
        send_messages(user_id, f'У вас скрыта информация о вашем возрасте, пожалуйста, введите возраст вручную')
        age_from, age_to = get_new_age(user_id, longpoll)
        return age_from, age_to
    except ValueError:
        send_messages(user_id, f'У вас скрыта информация о вашем возрасте, пожалуйста, введите возраст вручную')
        age_from, age_to = get_new_age(user_id, longpoll)
        return age_from, age_to

def get_new_age(user_id, longpoll):
    send_messages(user_id, f'Введите минимальный возраст для поиска: ')
    min_age = None
    max_age = None
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if min_age is None:
                min_age = event.text
                if not min_age.isdigit() or int(min_age) < 16 or int(min_age) > 65:
                    send_messages(user_id,
                                     'Некорректный минимальный возраст. Пожалуйста, введите число от 16 до 65:')
                    min_age = None
                else:
                    send_messages(user_id, f'Минимальный возраст: {min_age}')
                    send_messages(user_id, f'Введите максимальный возраст для поиска: ')
            elif max_age is None:
                max_age = event.text
                if not max_age.isdigit() or int(max_age) < 16 or int(max_age) > 65 or int(max_age) < int(min_age):
                    send_messages(user_id, 'Некорректный максимальный возраст. '
                                              'Пожалуйста, введите число от 16 до 65 и '
                                              'больше или равное минимальному возрасту:')
                    max_age = None
                else:
                    send_messages(user_id, f'Максимальный возраст: {max_age}')
                    return int(min_age), int(max_age)

def get_sex(user_id, user_info):
    send_messages(user_id, f'Введите ж или м для поиска:')
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            request = event.text.lower()
            if request == 'ж':
                send_messages(user_id, f'Ищем женщину!')
                return 1
            elif request == 'м':
                send_messages(user_id, f'Ищем мужчину!')
                return 2
            else:
                send_messages(user_id,
                            f'Введите ж или м для поиска:')

def get_city(user_id, user_info, longpoll):
    if 'city' in user_info[0]:
        city_id = user_info[0]['city']['id']
        city_name = user_info[0]['city']['id']

        send_messages(user_id, f'Ищем в городе {city_name}')
        return city_id, city_name

    else:
        send_messages(user_id, f'Введите название города:')
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                answer = event.text.lower()
                cities = vk_user_got_api.database.getCities(
                        country_id=1, q=answer.capitalize(), need_all=1, count=1000
                    )["items"]
                for city in cities:
                    if city['title'] == answer.capitalize():
                        city_id = city['id']
                        city_name = city['title']
                        send_messages(user_id, f'Ищем в городе: {city_name}')
                        return city_id, city_name
                else:
                    send_messages(user_id, f'Город не найден, попробуйте еще раз')


def search_for_people(user_id, age_from, age_to, city_id, sex, city_title, offset):
    result = vk_user_got_api.users.search(
        count=30,
        offset=offset,
        city=city_id,
        age_from=age_from,
        age_to=age_to,
        sex=sex,
        status=6,
        has_photo=1,
        fields='is_closed, can_write_private_message, bdate, city'
    )

    try:
        if 'items' in result:
            send_messages(user_id, f'Поиск успешен ')
            for user in result['items']:
                try:
                    if user['is_closed'] == False and user['can_write_private_message'] == True:
                            user_url = f"https://vk.com/id{user['id']}"
                            first_name = user['first_name']
                            last_name = user['last_name']
                            vk_id = user['id']
                            user_bdate = user['bdate']

                            if not check_db(vk_id):
                                #user_photo = get_photo(user_id, user)
                                message = f"Имя: {first_name}\nФамилия: {last_name}\nГород: {city_title}\nСсылка на профиль: {user_url}\nДата рождения: {user_bdate}\n"
                                send_messages(user_id, message)

                                add_user(id_vk=vk_id)
                except vk_api.exceptions.ApiError as e:
                    if e.code == 30:
                        send_messages(user_id, f'Ошибка {e}')
                        continue
        else:
            send_messages(user_id, f'Ключ "items" отсутствует в полученных данных')

        send_messages(user_id, f'Поиск завершен')

    except KeyError:
        send_messages(user_id, f'Ошибка запроса. Возврат в меню')
        return
