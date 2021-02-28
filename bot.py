import discord
import asyncio

client = discord.Client()

data_filename = 'bot_data/data.txt'
token_filename = 'bot_data/token.txt'
bet_filename = 'bot_data/bet_state.txt'

token_init = 100
token_incr_in_vc = 10

my_guild_id = 203177047441408000
text_channel_id = 258601727261933568
judge_role_id = 813266595291463680

bet_dict = {}
min_bet_tokens = 10
win_ratio = 2

BET_SIDE, BET_TOKEN, BET_STATE_USER = range(3)


# Discord's asynchronous methods

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await print_msg('IndyBot has come online!', False)
    await wait_for_users()


@client.event
async def on_message(msg):
    if '$' in msg.content[0].lower():
        content = msg.content[1:].strip().split(' ')
        if content[0].lower() == 'apply':
            await user_register(msg.author, token_init)

        if content[0].lower() == 'current':
            await user_current(msg.author)

        if content[0].lower() == 'bet.open':
            await open_bet()

        if content[0].lower() == 'bet.close':
            await close_bet()

        if content[0].lower() == 'bet':
            await user_bet(msg.author, content)

        if content[0].lower() == 'result':
            await bet_result(msg.author, content)

        if content[0].lower() == 'donate':
            await user_donate(msg.author, content)


# Main asynchronous methods

async def wait_for_users():
    count = 0
    n_minute = 5
    while True:
        voice_channels = get_voice_channels()
        if voice_channels is not None:
            for vc in voice_channels:
                for user in vc.members:
                    print(user)
                    if (user_in_database(user) and
                            not user.voice.channel is None and
                            not user.voice.self_mute and
                            not user.voice.self_deaf and
                            not user.voice.mute and
                            not user.voice.deaf):
                        add_user_token(user, token_incr_in_vc)

                        count += 1
                        if count % n_minute == 0:
                            await print_msg('{0} got {1} more tokens!'.format(user, n_minute * token_incr_in_vc))

        print('------')
        await asyncio.sleep(60)


async def user_register(user, token):
    has_registered = False

    print('{0} has registered in the betting system'.format(user))
    print('{0} has earned {1} tokens'.format(user, token))

    if user_in_database(user):
        has_registered = True
        await print_msg('{0} has already registered!'.format(str(user)))

    with open(data_filename, 'a') as f:
        if not has_registered:
            await print_msg('{0} has registered in the betting system.'.format(user))

            f.write('{0}:{1}:{2}\n'.format(user, user.id, token))
            await print_msg('{0} has earned {1} tokens.'.format(user, token))


async def user_current(user):
    if user_in_database(user):
        user_token = user_current_tokens(user)
        await print_msg('{0} now has {1} tokens.'.format(user, user_token))
    else:
        await print_msg('{0} has not registered in the system yet.'.format(user))


async def open_bet():
    if not get_bet_opened() and not get_prediction_started():
        set_bet_opened(True)
        set_prediction_state(True)
        await print_msg('Prediction and bet phase have started!')
        await asyncio.sleep(360)
        await close_bet()
    else:
        await print_msg('Bet phase has already closed. :(')


async def close_bet():
    if get_bet_opened() and get_prediction_started():
        set_bet_opened(False)
        await print_msg('Bet phase has ended!')
        await print_bet_dict()
    else:
        await print_msg('Prediction has not started yet. :(')


async def user_bet(user, content):
    if not get_prediction_started():
        await print_msg('Prediction has not started yet. :(')
        return

    if not get_bet_opened() and get_prediction_started():
        await print_msg('Bet phase has already closed. :(')
        return

    if user_in_database(user):
        try:
            valid_number = await validate_number(content[2], user)
            valid_bet_state = await validate_bet_state(user)
            print(valid_number, valid_bet_state)

            can_bet = False
            if valid_number and valid_bet_state:
                token_to_deduct = float(content[2])
                can_bet = True

            elif not valid_number and valid_bet_state:
                if content[2].lower() == 'all':
                    token_to_deduct = user_current_tokens(user)
                    can_bet = True

            if can_bet:
                if content[1].lower() == 'win':
                    bet_dict[str(user)] = ('win', token_to_deduct, True)
                    add_user_token(user, -token_to_deduct)
                    await print_msg('{0} has chosen to be the believers!'.format(user))
                elif content[1].lower() == 'loss' or content[1].lower() == 'lose':
                    bet_dict[str(user)] = ('loss', token_to_deduct, True)
                    add_user_token(user, -token_to_deduct)
                    await print_msg('{0} has chosen to be the doubters!'.format(user))
                else:
                    await print_msg('Please enter the valid result.')

        except IndexError:
            await print_msg('Please enter the valid result or token value to bet.')
    else:
        await print_msg('{0} has not registered in the system yet.'.format(user))


async def bet_result(user, content):
    if not get_prediction_started():
        await print_msg('Prediction has not started yet. :(')
        return

    if user_is_judge(user):
        try:
            result = ''
            if content[1].lower() == 'win':
                result = 'win'
            elif content[1].lower() == 'loss' or content[1].lower() == 'lose':
                result = 'loss'
            for user in bet_dict.keys():
                if bet_dict[user][BET_SIDE] == result:
                    add_user_token(user, float(bet_dict[user][BET_TOKEN] * win_ratio))
                    await print_msg('{0} has won {1} tokens.'.format(user, bet_dict[user][BET_TOKEN] * win_ratio))
                else:
                    await print_msg('{0} has wasted {1} tokens.'.format(user, bet_dict[user][BET_TOKEN]))
            set_bet_opened(False)
            set_prediction_state(False)
            bet_dict.clear()
            await print_msg('Prediction has ended.')
        except IndexError:
            await print_msg('Please enter the valid result.')
    else:
        await print_msg('{0} does not have a Prediction Judge role. :['.format(user))


async def user_donate(user, content):
    # $donate <donatee's username> <amount>
    if user_in_database(user) and user_in_database(content[1]):
        try:
            valid_number = await validate_number(content[2], user)
            if valid_number:
                token_to_deduct = float(content[2])
                add_user_token(user, -token_to_deduct)
                add_user_token(content[1], token_to_deduct)
                await print_msg('{0} has donated {1} for {2} tokens!'.format(user, content[1], float(content[2])))
        except IndexError:
            await print_msg("Please enter the valid donatee's username or token value to donate.")
    else:
        await print_msg('The donor or donatee has not registered in the system yet.'.format(user))


# Helper asynchronous methods

async def print_msg(msg, destroy=True):
    print(msg)
    msg = '```\n' + msg + '\n```'
    message = await client.get_channel(text_channel_id).send(msg)
    if destroy:
        await message.delete(delay=5.0)


async def validate_number(string, user):
    try:
        number = float(string)
        if min_bet_tokens <= number <= user_current_tokens(user):
            return True
        else:
            await print_msg(
                'Please insert the valid number of tokens according to your current tokens or minimum requirement (10 tokens).')
            return False
    except ValueError:
        if string != 'all':
            await print_msg('Please insert the valid number of tokens to bet.')
        return False


async def validate_bet_state(user):
    if not str(user) in bet_dict.keys():
        return True
    else:
        await print_msg('{0} has already bet!'.format(user))


async def print_bet_dict():
    for user in bet_dict.keys():
        await print_msg('{0} has predicted {1} for {2} tokens'.format(user,
                                                                      bet_dict[user][BET_SIDE],
                                                                      bet_dict[user][BET_TOKEN]), False)


# Synchronous methods

def get_voice_channels():
    for guild in client.guilds:
        if guild.id == my_guild_id:
            voice_channels = guild.voice_channels
            return voice_channels
    return None


def get_guild():
    for guild in client.guilds:
        if guild.id == my_guild_id:
            return guild
    return None


def read_app_token():
    with open(token_filename, 'r') as f:
        lines = f.readlines()
        return lines[0].strip()


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
                    print('edit {0}:{1}:{2}'.format(line_user, line_user_id, line_token))
                f.write('{0}:{1}:{2}\n'.format(line_user, line_user_id, line_token))


def user_in_database(user):
    with open(data_filename, 'r') as f:
        for line in f:
            line = line.strip(' \n')
            if ':' in line:
                line_user, line_user_id, line_token = line.split(':')
                if str(line_user) == str(user):
                    return True
    return False


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
            print('No bet_opened value!')
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
            print('Invalid bet_opened value!')


def get_prediction_started():
    with open(bet_filename, 'r') as f:
        lines = f.readlines()
        prediction_state = lines[1].strip('\n')
        if prediction_state == '1':
            return True
        elif prediction_state == '0':
            return False
        else:
            print('No prediction_state value!')
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
            print('Invalid bet_opened value!')


# Call main

if __name__ == '__main__':
    TOKEN = read_app_token()
    client.run(TOKEN)
