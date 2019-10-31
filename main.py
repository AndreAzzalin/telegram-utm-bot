from uuid import uuid4

from telegram import Bot, Update, Chat, Location
from telegram.ext import Dispatcher, MessageHandler, Filters, CallbackContext, CommandHandler
import responder
import utm
import logging

from location_model import ChatLocations

# parametri di configurazione per server e token per API Telegram
base_url = 'https://ff9d238a.ngrok.io' + '/'
bot_token = '895587413:AAFNlfhLq2x0xMgBWByQQAZeIueUn5EfiWw'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger()
bot_instance = Bot(bot_token)
secret_token = uuid4().hex
bot_instance.set_webhook(base_url + secret_token)
logger.info('Webhook URL set to %s', base_url + secret_token)

dispatcher = Dispatcher(bot_instance, None, workers=0, use_context=True)
chat_repository = {}


def is_user_admin(chat, user):
    return chat.type == Chat.PRIVATE or user.id in [admin.user.id for admin in chat.get_administrators()]


# converte coordinate e invia messaggio formattato
def send_utm_coords(bot, update):
    utm_coords = utm.from_latlon(update.message.location.latitude, update.message.location.longitude)
    msg_text = '{zone}{letter} {e:.0f}E {n:.0f}N'.format(zone=utm_coords[2], letter=utm_coords[3], e=utm_coords[0],
                                                         n=utm_coords[1])
    bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text=msg_text)


# setta tracking_active a true e inzia il tracking
def start_tracking_handler(update: Update, context: CallbackContext):
    if not is_user_admin(update.effective_chat, update.effective_user):
        context.bot.send_message(chat_id=update.effective_message.chat_id,
                                 text='You must be a group admin to start location tracking')
        return
    if update.effective_message.chat_id not in chat_repository:
        chat_repository[update.effective_message.chat_id] = ChatLocations(update.effective_message.chat_id)
    if not chat_repository[update.effective_message.chat_id].tracking_active:
        chat_repository[update.effective_message.chat_id].tracking_active = True
        context.bot.send_message(chat_id=update.effective_message.chat_id, text='Location tracking started')
    else:
        context.bot.send_message(chat_id=update.effective_message.chat_id, text='Location tracking already in progress')


# blocca il tracking
def stop_tracking_handler(update: Update, context: CallbackContext):
    if not is_user_admin(update.effective_chat, update.effective_user):
        context.bot.send_message(chat_id=update.effective_message.chat_id,
                                 text='You must be a group admin to stop location tracking')
        return
    if update.effective_message.chat_id in chat_repository and chat_repository[
        update.effective_message.chat_id].tracking_active:
        chat_repository[update.message.chat_id].tracking_active = False
        context.bot.send_message(chat_id=update.effective_message.chat_id, text='Location tracking stopped')
    else:
        context.bot.send_message(chat_id=update.effective_message.chat_id, text='Location tracking not in progress')


# pulisce la chat_repository dove sono locate le informazioni della chat corrente
def reset_locations_handler(update: Update, context: CallbackContext):
    if not is_user_admin(update.effective_chat, update.effective_user):
        context.bot.send_message(chat_id=update.effective_message.chat_id,
                                 text='You must be a group admin to reset location data')
        return
    if update.effective_message.chat_id in chat_repository:
        chat_repository[update.message.chat_id].location_list = {}
        context.bot.send_message(chat_id=update.effective_message.chat_id, text='Location data reset')


# esegue la get di tutte le location con chat_id come parametro
def get_info_handler(update: Update, context: CallbackContext):
    logger.info("list " + chat_repository.__str__())
    if update.effective_message.chat_id not in chat_repository:
        chat_repository[update.effective_message.chat_id] = ChatLocations(update.effective_message.chat_id)

    msg_text = str(chat_repository[update.effective_message.chat_id])
    context.bot.send_message(chat_id=update.effective_message.chat_id, text=msg_text)


# esegue il tracking dell'user che ha inviato la posizione
def location_start_handler(update: Update, context: CallbackContext):
    logger.info("ricevuto location da %s", update.effective_user.name)
    if update.effective_message.chat_id in chat_repository and chat_repository[
        update.effective_message.chat_id].tracking_active:
        logger.info("Started location sharing for user %s", update.effective_user.name)

        chat_locations = chat_repository.setdefault(update.effective_message.chat_id,
                                                    ChatLocations(update.effective_message.chat_id))
        chat_locations.update_location(update.effective_user.id,
                                       update.effective_user.name,
                                       (update.effective_message.location.latitude,
                                        update.effective_message.location.longitude),
                                       update.effective_message.date)

        logger.info("chat: %s", str(chat_locations))


# aggiorna la location dell user in chat_locations
def location_update_handler(update: Update, context: CallbackContext):
    if update.effective_message.chat_id in chat_repository and chat_repository[
        update.effective_message.chat_id].tracking_active:
        logger.info("Updated location for user %s", update.effective_user.name)
        chat_locations = chat_repository.setdefault(update.effective_message.chat_id,
                                                    ChatLocations(update.effective_message.chat_id))
        chat_locations.update_location(update.effective_user.id,
                                       update.effective_user.name,
                                       (update.effective_message.location.latitude,
                                        update.effective_message.location.longitude),
                                       update.effective_message.edit_date)

        logger.info("chat: %s", str(chat_locations))


# assoziazione handler -> metodo da eseguire
dispatcher.add_handler(CommandHandler("start", start_tracking_handler))
dispatcher.add_handler(CommandHandler("stop", stop_tracking_handler))
dispatcher.add_handler(CommandHandler("reset", reset_locations_handler))
dispatcher.add_handler(CommandHandler("get", get_info_handler))
dispatcher.add_handler(MessageHandler(Filters.location & (~ Filters.update.edited_message), location_start_handler))
dispatcher.add_handler(MessageHandler(Filters.location & Filters.update.edited_message, location_update_handler))

app = responder.API(cors=True)


# telegram_send_message_url = 'https://api.telegram.org/%(token)s/sendMessage' % {'token': bot_token}

# configurazione porta e indirizzo locale per ambiente virtuale
def main():
    app.run(port=5000, address='localhost')


@app.route('/{token}')
async def handle_update(req, resp, *, token):
    @app.background.task
    def process_data(json_update):
        rec_update = Update.de_json(json_update, bot_instance)
        dispatcher.process_update(rec_update)

    if token == secret_token:
        data = await req.media()
        process_data(data)
        resp.media = {'success': True}
    else:
        resp.media = {'success': False}


if __name__ == "__main__":
    main()
