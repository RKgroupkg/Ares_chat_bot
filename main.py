import logging
from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext,CommandHandler,ConversationHandler,CallbackQueryHandler
#pip install python-telegram-bot==12.8

import google.generativeai as genai
import threading
from colorama import Fore, Style
import textwrap

import PIL.Image
import os
from IPython.display import display
from IPython.display import Markdown

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Set up Gemini client with your API key
api_key = os.environ['Google_api']
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])
messages =[]  #Multi-turn conversations

# Define global variable to store user's choice
user_setting = "Generative_conversation"

# Telegram bot token
telegram_bot_token =os.environ['Telgarm_api']


defult_promt = "You name is Ares. devloped by Rkgroup, be a human and talk in simple english . Respond like you're Ares who chat likes human : "
new_promt =None

def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

# Function to generate response using OpenAI
def generate_response(input_text: str) -> str:
    colored_print("genrating response....",Fore.CYAN)
    try:
        response = chat.send_message(input_text,safety_settings={'HARASSMENT':'block_none','DANGEROUS_CONTENT':'block_none','HATE_SPEECH':'block_none','SEXUALLY_EXPLICIT':'block_none'} )
        colored_print(f"promt : {input_text}\n\n\nResponse: \n{response.text}",Fore.YELLOW)
        return response.text if input_text else "error"
    except Exception:
        try:
            response = model.generate_content(input_text,
                                            )
            colored_print(f"promt : {input_text}\n\n\nResponse: \n{response.text}",Fore.YELLOW)
            return response.text if input_text else "error"
        except Exception as e:
            return f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\n error:{e}:::\n\n\n\n  Safety rating:  {response.prompt_feedback}"

def Multi_turn_conversations(input_text: str,username: str) -> str:
    colored_print("genrating response with(Multi_turn_conversations)....",Fore.CYAN)
    try:
        messages.append({'role':'user',
                 'parts':[input_text]})
        print (messages)
        response = model.generate_content(messages)
        messages.append({'role':'model',
                 'parts':[response.text]})
        return response.text
    except Exception as e:
            return f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\n error:{e} \n error type {e.__traceback__}"



def colored_print(text, color):
  """
  Prints text in a specified color using the colorama library.

  Args:
      text: The text to be printed.
      color: The desired color for the text. Can be any of the color constants
          provided by the colorama library (e.g., Fore.RED, Fore.GREEN, etc.).
  """
  colored_text = color + text + Style.RESET_ALL
  print(colored_text)

def is_group_message(update: Update) -> bool:
    """Check if the message is from a group chat."""
    chat_type = update.message.chat.type
    return chat_type in ["group", "supergroup"]

def process_message(update: Update, context: CallbackContext) -> None:
    if  is_group_message  : 
        user_message = update.message.text.lower() # Convert message to lowercase

        if user_message.startswith(("hey ares", "hi ares", "ares","yo ares")):
            user_message =strip_greetings(user_message)
            username = update.message.from_user.username

            # Check if the message is a reply
            if update.message.reply_to_message:

                # Extract the text from the replied message
                user_message = f"Original message: {update.message.reply_to_message.text} : Reply to that message:{user_message}"
                threading.Thread(target=process_message_thread, args=(update, user_message,username)).start()
            else:
                threading.Thread(target=process_message_thread, args=(update, user_message,username)).start()

            #give the command promt
            if username:    
                colored_print(f"{username}: {user_message}",Fore.BLUE)
            else:
                colored_print(f"Someone: {user_message}",Fore.BLUE)

# Function to handle incoming messages and generate response
def strip_greetings(message):
    greetings = ["hey ares", "hi ares", "ares", "yo ares"]

    for greeting in greetings:
        if message.lower().startswith(greeting):  # Case-insensitive check
            if len(message) > len(greeting) and message.lower().replace(greeting, "").strip() != "":
                return message[len(greeting):].strip()  # Remove greeting and any leading space
            else:
                return message

    return message  # Return the original message if no greeting was found


def process_message_thread(update: Update, user_message: str,username :str) -> None:
    if user_setting == "Generative_conversation":
        try:
            # Send the initial "responding..." message
            indicator_message = update.message.reply_text("<b>Thinking🤔..</b>",parse_mode='html')
            if new_promt:
                prompt = f"{new_promt}: {user_message}" 
                print("chosed new promt ")
            else:
                prompt = f"{defult_promt}: {user_message}" 
                print(f"chosed defult promt :{new_promt}")

            # Generate the response
            response =generate_response(prompt)

            # Split into chunks if necessary
            chunks = textwrap.wrap(response, width=100 * 4, replace_whitespace=False)  # ~400 characters 

            indicator_message.delete()  # Delete "responding..." 

            for chunk in chunks:
                update.message.reply_text(chunk, parse_mode='html')

        except Exception as e:
            logging.error(f"Error processing message: {e}")
            try:
                indicator_message.edit_text("Sorry, I encountered an error while processing your message.")
            except Exception:  # If the original message couldn't be edited
                update.message.reply_text("Sorry, I encountered an error while processing your message.") 

    elif user_setting == "Multi_turn_conversations":
        # Send the initial "responding..." message
            indicator_message = update.message.reply_text("<b>Thinking🤔....</b>",parse_mode='html')
            response = Multi_turn_conversations(user_message,username)

            indicator_message.delete()  # Delete "responding..." 

            update.message.reply_text(response, parse_mode='html')



def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('<b>This bot is powered by <i>gemeni</i> and can assist you with various queries.\n\n Just start your message with "Hey Ares" or "Hi Ares", followed by your question or message, and Ares will respond accordingly.\n\n Please keep the conversation in English and refrain from using complex language.\n\n To customize the behavior of the bot, you can use the following commands:\n\n - /ChangePrompt [new prompt]: Change the prompt for generating responses. For example: /ChangePrompt You are a cat.\n\n\n Enjoy chatting with Ares! </b>',parse_mode='html')

def change_prompt(update: Update, context: CallbackContext) -> None:
    """Change the prompt for generating responses."""
    global new_promt
    new_promt = " ".join(context.args)
    if new_promt:
        update.message.reply_text(f"The prompt has been successfully changed to: <b>'{new_promt}'</b>", parse_mode='html')
    else:
        update.message.reply_text("To use this command correctly, type '/ChangePrompt' followed by your prompt. For example: '/ChangePrompt You are a cat'")

def process_image(update: Update, context: CallbackContext) -> None:
    modelImg = genai.GenerativeModel('gemini-pro-vision')
    # Define a function to handle image processing and response generation
    def handle_image():
        # Check if the message contains a photo
        if update.message.photo:
            # Get the user message
            user_message = update.message.caption if update.message.caption else ""

            # Process the image
            file_id = update.message.photo[-1].file_id  # Get the file_id of the largest version of the photo

            # Download the image
            file = context.bot.get_file(file_id)
            file_path = file.download()
            img = PIL.Image.open(file_path)

            # Send "thinking" message
            thinking_message = update.message.reply_text("Thinking..")

            # Generate response based on text and image
            response = modelImg.generate_content([user_message, img])

            # Send the response to the user
            update.message.reply_text(response.text)

            # Delete the "thinking" message
            thinking_message.delete()

            # Delete the image after use
            os.remove(file_path)
        else:
            # No image uploaded
            pass

    # Start a new thread to handle image processing and response generation
    threading.Thread(target=handle_image).start()

def Token(update: Update, context: CallbackContext) -> None:
  global chat  
  update.message.reply_text(f'Total token used: {model.count_tokens(chat.history)}',parse_mode='html')


def main() -> None:
    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Register the message handler
    message_handler = MessageHandler(Filters.text & ~Filters.command, process_message)
    dispatcher.add_handler(message_handler)

    # Register the message handler
    dispatcher.add_handler(MessageHandler(Filters.photo, process_image))


    # Register the help command handler
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Register the help command handler
    dispatcher.add_handler(CommandHandler("Token", Token))

    # Register the ChangePrompt command handler
    dispatcher.add_handler(CommandHandler("ChangePrompt", change_prompt, pass_args=True))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('setting', setting_command_handler)],
        states={1: [CallbackQueryHandler(setting_selection)]},
        fallbacks=[],
    )

    # Add the conversation handler to the dispatcher
    updater.dispatcher.add_handler(conv_handler)


    # Start the Bot
    print("Bot started!")
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()
  
def setting_command_handler(update: Update, context: CallbackContext) -> None:
    # Define the options
    options = ["Multi_turn_conversations", "Generative_conversation"]

    # Create buttons for each option
    keyboard = [[InlineKeyboardButton(option, callback_data=option)] for option in options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the options as buttons to the user
    update.message.reply_text("Please select an option:", reply_markup=reply_markup)

    # Return conversation state
    return 1

def setting_selection(update: Update, context: CallbackContext) -> int:
    # Access the global variable
    global user_setting

    # Get the user's choice from the callback data
    user_setting = update.callback_query.data

    # Send a message confirming the user's choice
    update.callback_query.message.reply_text(f"You have selected: {user_setting}")

    # End the conversation
    return ConversationHandler.END

if __name__ == '__main__':
    main()
