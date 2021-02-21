import discord
import asyncio

client = discord.Client()

data_filename = 'data.txt'
token_filename = 'token.txt'

token_init = 100
token_incr_in_vc = 10

my_guild_id = 203177047441408000
textchannel_id = 258601727261933568


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await wait_for_users()


@client.event
async def on_message(msg):
    if '$' in msg.content[0].lower():
        content = msg.content[1:].strip().split(' ')
        if content[0].lower() == 'apply':
            print('{0} has applied for the betting system'.format(msg.author))
            print('{0} has earned {1} tokens'.format(msg.author, token_init))

            await first_apply(msg.author, token_init)

        if content[0].lower() == 'current':
            if user_in_database(msg.author):
                user_token = user_current_tokens(msg.author)
                await print_msg(textchannel_id, '{0} now has {1} tokens'.format(msg.author, user_token))
            else:
                await print_msg(textchannel_id, '{0} has not applied for the system yet'.format(msg.author))


async def print_msg(channel_id, msg):
    message = await client.get_channel(channel_id).send(msg)
    await message.delete(delay=3.0)


async def first_apply(user, token):
    has_applied = False

    if user_in_database(user):
        has_applied = True
        print('{0} have already applied!'.format(str(user)))
        await print_msg(textchannel_id, 'You have already applied!')

    with open(data_filename, 'a') as f:
        if not has_applied:
            await print_msg(textchannel_id, '{0} has applied for the betting system'.format(user))

            f.write('{0}:{1}:{2}\n'.format(user, user.id, token))
            print('appended "{0}:{1}:{2}" to the data file'.format(user, user.id, token))
            await print_msg(textchannel_id, '{0} has earned {1} tokens'.format(user, token))


async def wait_for_users():
    while True:
        voice_channels = get_voice_channels()
        if voice_channels is not None:
            for vc in voice_channels:
                for user in vc.members:
                    print(user)
                    if (user_in_database(user) and
                            not user.voice.channel is None and
                            not user.voice.self_mute and
                            not user.voice.self_deaf):
                        increase_token(user, token_incr_in_vc)
                        print('{0} got {1} more tokens!'.format(user, token_incr_in_vc))
                        await print_msg(textchannel_id, '{0} got {1} more tokens!'.format(user, token_incr_in_vc))

        await asyncio.sleep(60)


def get_voice_channels():
    for guild in client.guilds:
        if guild.id == my_guild_id:
            voice_channels = guild.voice_channels
            return voice_channels

    return None


def read_app_token():
    with open(token_filename, 'r') as f:
        lines = f.readlines()
        return lines[0].strip()


def increase_token(user, token):
    with open(data_filename, 'r') as f:
        lines = f.readlines()

    with open(data_filename, 'w') as f:
        for line in lines:
            line = line.strip(' \n')
            if ':' in line:
                line_user, line_user_id, line_token = line.split(':')
                if int(line_user_id) == user.id:
                    line_token = str(int(line_token) + token)

                f.write('{0}:{1}:{2}\n'.format(line_user, line_user_id, line_token))
                print('edit {0}:{1}:{2}'.format(line_user, line_user_id, line_token))


def user_in_database(user):
    with open(data_filename, 'r') as f:
        for line in f:
            line = line.strip(' \n')
            if ':' in line:
                line_user, line_user_id, line_token = line.split(':')
                if int(line_user_id) == int(user.id):
                    return True

    return False


def user_current_tokens(user):
    tokens = 0
    with open(data_filename, 'r') as f:
        for line in f:
            line = line.strip(' \n')
            if ':' in line:
                line_user, line_user_id, line_token = line.split(':')
                if int(line_user_id) == int(user.id):
                    tokens = int(line_token)

    return tokens


if __name__ == '__main__':
    TOKEN = read_app_token()
    client.run(TOKEN)
