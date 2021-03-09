import os
import discord

from discord.ext import commands
from datetime import datetime

data_filename = 'bot_data/data.txt'
token_filename = 'bot_data/token.txt'
bet_filename = 'bot_data/bet_state.txt'
log_filename = 'bot_data/log.txt'

my_guild_id = 203177047441408000
text_channel_id = 258601727261933568
judge_role_id = 813266595291463680

min_bet_tokens = 10


# Miscellaneous methods that is widely used in this project will be implemented below.

# Asynchronous methods
async def print_msg(bot: commands.Bot, msg, destroy=True, delay=5.0):
    record_log(msg)
    msg = '```\n' + msg + '\n```'
    message = await bot.get_channel(text_channel_id).send(msg)
    if destroy:
        await message.delete(delay=delay)


async def validate_token_amount(bot: commands.Bot, string: str, user, printed=True):
    try:
        number = float(string)
        if min_bet_tokens <= number <= user_current_tokens(user):
            return True
        else:
            if printed:
                await print_msg(bot,
                                'Please insert the valid number of tokens according to your current tokens or minimum requirement (10 tokens).')
            return False
    except ValueError:
        if string != 'all':
            if printed:
                await print_msg(bot, 'Please insert the valid number of tokens to bet.')
        return False


# Synchronous methods
def get_voice_channels(bot: commands.Bot):
    for guild in bot.guilds:
        if guild.id == my_guild_id:
            voice_channels = guild.voice_channels
            return voice_channels
    return None


def record_log(msg):
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S.%f")
    msg = timestampStr + " : " + msg
    print(msg)
    if not os.path.exists(log_filename):
        with open(log_filename, 'w') as f:
            f.write('{0}\n'.format(msg))
    else:
        with open(log_filename, 'a') as f:
            f.write('{0}\n'.format(msg))


def user_in_database(user):
    with open(data_filename, 'r') as f:
        for line in f:
            line = line.strip(' \n')
            if ':' in line:
                line_user, line_user_id, line_token = line.split(':')
                if str(line_user) == str(user):
                    return True
    return False


def add_user_token(user, token):
    with open(data_filename, 'r') as f:
        lines = f.readlines()

    with open(data_filename, 'w') as f:
        for line in lines:
            line = line.strip(' \n')
            if ':' in line:
                line_user, line_user_id, line_token = line.split(':')
                if str(line_user) == str(user):
                    line_token = str(float(line_token) + float(token))
                    # record_log('edit {0}:{1}:{2}'.format(line_user, line_user_id, line_token))
                f.write('{0}:{1}:{2}\n'.format(line_user, line_user_id, line_token))


def add_user_token_by_id(user_id, token):
    with open(data_filename, 'r') as f:
        lines = f.readlines()

    with open(data_filename, 'w') as f:
        for line in lines:
            line = line.strip(' \n')
            if ':' in line:
                line_user, line_user_id, line_token = line.split(':')
                if str(line_user_id) == str(user_id):
                    line_token = str(float(line_token) + float(token))
                    record_log('edit {0}:{1}:{2}'.format(line_user, line_user_id, line_token))
                f.write('{0}:{1}:{2}\n'.format(line_user, line_user_id, line_token))


def get_user_from_user_id(user_id):
    with open(data_filename, 'r') as f:
        for line in f:
            line = line.strip(' \n')
            if ':' in line:
                line_user, line_user_id, line_token = line.split(':')
                if str(line_user_id) == str(user_id):
                    return line_user
    return None


def user_current_tokens(user):
    tokens = 0
    with open(data_filename, 'r') as f:
        for line in f:
            line = line.strip(' \n')
            if ':' in line:
                line_user, line_user_id, line_token = line.split(':')
                if str(line_user) == str(user):
                    tokens = float(line_token)
    return tokens


def user_is_judge(user):
    for role in user.roles:
        if role.id == judge_role_id:
            return True
    return False


def get_bet_opened():
    with open(bet_filename, 'r') as f:
        lines = f.readlines()
        bet_opened = lines[0].strip('\n')
        if bet_opened == '1':
            return True
        elif bet_opened == '0':
            return False
        else:
            record_log('No bet_opened value!')
            return None


def set_bet_opened(value):
    with open(bet_filename, 'r') as f:
        lines = f.readlines()
        tmp = lines[1].strip('\n')

    with open(bet_filename, 'w') as f:
        try:
            if value:
                f.write('1\n')
            else:
                f.write('0\n')
            f.write(tmp)
        except ValueError:
            record_log('Invalid bet_opened value!')


def get_prediction_started():
    with open(bet_filename, 'r') as f:
        lines = f.readlines()
        prediction_state = lines[1].strip('\n')
        if prediction_state == '1':
            return True
        elif prediction_state == '0':
            return False
        else:
            record_log('No prediction_state value!')
            return None


def set_prediction_state(value):
    with open(bet_filename, 'r') as f:
        lines = f.readlines()
        tmp = lines[0]

    with open(bet_filename, 'w') as f:
        try:
            f.write(tmp)
            if value:
                f.write('1\n')
            else:
                f.write('0\n')
        except ValueError:
            record_log('Invalid bet_opened value!')
