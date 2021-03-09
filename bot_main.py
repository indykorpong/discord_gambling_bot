import discord
import random
import asyncio

from bot_helper import *

data_filename = 'bot_data/data.txt'
token_filename = 'bot_data/token.txt'
bet_filename = 'bot_data/bet_state.txt'
log_filename = 'bot_data/log.txt'

token_init = 100
token_over_time = 2

my_guild_id = 203177047441408000
text_channel_id = 258601727261933568
judge_role_id = 813266595291463680

bet_dict = {}
duel_dict = {}
min_bet_tokens = 10
win_ratio = 2

BET_SIDE, BET_TOKEN, BET_STATE_USER = range(3)
DUEL_CHALLENGER, DUEL_AMOUNT = range(2)


# The functionality of what bot can do will be implemented below.

# Bot's main asynchronous methods
async def bot_apply(ctx: commands.Context, bot: commands.Bot):
    has_registered = False

    user = ctx.author
    token = token_init
    record_log('{0} has registered in the betting system'.format(user))
    record_log('{0} has earned {1} tokens'.format(user, token))

    if user_in_database(user):
        has_registered = True
        await print_msg(bot, '{0} has already registered!'.format(str(user)))

    with open(data_filename, 'a') as f:
        if not has_registered:
            await print_msg(bot, '{0} has registered in the betting system.'.format(user))

            f.write('{0}:{1}:{2}\n'.format(user, user.id, token))
            await print_msg(bot, '{0} has earned {1} tokens.'.format(user, token))


async def bot_help(ctx: commands.Context, bot: commands.Bot):
    await print_msg(bot,
                    '''Command List:\n\n
    $apply\n
      - Apply for a life of eternal gamba hell, gaining 10 tokens per minute for use in sating your gambling addiction.\n\n 
    $current\n
      - Show an exact amount of your current tokens.\n\n
    $bet_open\n
      - Open a gamba game that can lead you into bankruptcy. Normally a gamba game will open for 6 mins before it’s closed unless bet_close command is issued.\n\n
    $bet_close\n
      - You can use this command to manually close a gamba game and wait for a privileged dude to announce the result.\n\n
    $bet <bet_result> <token_amount/all>\n
      - Choose to become believers or doubters with some tokens that can motivate players’ movement in game. (<bet_result> includes win, loss, lose) Ex. bet loss all \n\n
    $result <bet_result>\n
      - For privileged dude only. Use this command to announce the match result and take all Investors' tokens. Ex. result loss\n\n
    $donate <donatee> <token_amount/all>\n 
      - Donate your tokens to an unfortunate investor in need of spare tokens. Ex. donate @IndyKumaz 322
        ''',
                    destroy=True,
                    delay=60.0)
    await discord.Message.delete(ctx.message, delay=4.0)


async def bot_current(ctx: commands.Context, bot: commands.Bot):
    user = ctx.author
    if user_in_database(user):
        user_token = user_current_tokens(user)
        await print_msg(bot, '{0} now has {1} tokens.'.format(user, user_token))
        await discord.Message.delete(ctx.message, delay=4.0)
    else:
        await print_msg(bot, '{0} has not registered in the system yet.'.format(user))


async def bot_bet_open(bot: commands.Bot):
    if not get_bet_opened() and not get_prediction_started():
        set_bet_opened(True)
        set_prediction_state(True)
        await print_msg(bot, 'Prediction and bet phase have started!')
        await asyncio.sleep(360)
        await bot_bet_close(bot)
    else:
        await print_msg(bot, 'Bet phase has already closed. :(')


async def bot_bet_close(bot: commands.Bot):
    if get_bet_opened() and get_prediction_started():
        set_bet_opened(False)
        await print_msg(bot, 'Bet phase has ended!')
        await print_bet_dict(bot)
    else:
        await print_msg(bot, 'Prediction has not started yet. :(')


async def bot_bet(ctx: commands.Context, bot: commands.Bot, bet_side, token):
    if not get_prediction_started():
        await print_msg(bot, 'Prediction has not started yet. :(')
        return

    if not get_bet_opened() and get_prediction_started():
        await print_msg(bot, 'Bet phase has already closed. :(')
        return

    user = ctx.author
    token_to_deduct = 0.0
    if user_in_database(user):
        try:
            valid_number = await validate_token_amount(bot, str(token), user)
            valid_bet_state = await validate_bet_state(bot, user)

            can_bet = False
            if valid_number and valid_bet_state:
                token_to_deduct = float(token)
                can_bet = True
            elif not valid_number and valid_bet_state:
                if token.lower() == 'all':
                    token_to_deduct = user_current_tokens(user)
                    can_bet = True

            if can_bet:
                if bet_side.lower() == 'win':
                    bet_dict[str(user)] = ('win', token_to_deduct, True)
                    add_user_token(user, -token_to_deduct)
                    await print_msg(bot, '{0} has chosen to be the believers!'.format(user))
                elif bet_side.lower() == 'loss' or bet_side.lower() == 'lose':
                    bet_dict[str(user)] = ('loss', token_to_deduct, True)
                    add_user_token(user, -token_to_deduct)
                    await print_msg(bot, '{0} has chosen to be the doubters!'.format(user))
                else:
                    await print_msg(bot, 'Please enter the valid result.')

        except IndexError:
            await print_msg(bot, 'Please enter the valid result or token value to bet.')
    else:
        await print_msg(bot, '{0} has not registered in the system yet.'.format(user))


async def bot_result(ctx: commands.Context, bot: commands.Bot, bet_result):
    if not get_prediction_started():
        await print_msg(bot, 'Prediction has not started yet. :(')
        return

    user = ctx.author

    if user_is_judge(user):
        try:
            _result = ''
            if bet_result.lower() == 'win':
                _result = 'win'
            elif bet_result.lower() == 'loss' or bet_result.lower() == 'lose':
                _result = 'loss'
            # elif bet_result.lower() == 'na':
            #     _result = 'na'
            # TODO: handle the case where the result is N/A (not applicable)

            for user in bet_dict.keys():
                if bet_dict[user][BET_SIDE] == _result:
                    add_user_token(user, float(bet_dict[user][BET_TOKEN] * win_ratio))
                    await print_msg(bot, '{0} has won {1} tokens.'.format(user, bet_dict[user][BET_TOKEN] * win_ratio))
                else:
                    await print_msg(bot, '{0} has wasted {1} tokens.'.format(user, bet_dict[user][BET_TOKEN]))
            set_bet_opened(False)
            set_prediction_state(False)
            bet_dict.clear()
            await print_msg(bot, 'Prediction has ended.')
        except IndexError:
            await print_msg(bot, 'Please enter the valid result.')
    else:
        await print_msg(bot, '{0} does not have a Prediction Judge role. :['.format(user))


async def bot_donate(ctx: commands.Context, bot: commands.Bot, donatee: discord.Member, donate_amount):
    # $donate <donatee's username> <amount>
    token_to_deduct = 0
    user = ctx.author
    donatee_user = get_user_from_user_id(donatee.id)
    if user_in_database(user) and user_in_database(donatee_user):
        try:
            valid_number = await validate_token_amount(bot, donate_amount, user)
            donated = False
            if valid_number:
                token_to_deduct = float(donate_amount)
                donated = True
            elif donate_amount.lower() == 'all':
                token_to_deduct = user_current_tokens(user)
                donated = True

            if donated:
                add_user_token(user, -token_to_deduct)
                add_user_token_by_id(donatee.id, token_to_deduct)
                await print_msg(bot, '{0} has donated {1} for {2} tokens!'.format(user, donatee_user, token_to_deduct))
        except IndexError:
            await print_msg(bot, "Please enter the valid donatee's username or token value to donate.")
    else:
        await print_msg(bot, 'The donor or donatee has not registered in the system yet.')


async def bot_duel(ctx: commands.Context, bot: commands.Bot, user: discord.Member, tokens):
    challengee = get_user_from_user_id(user.id)
    if not user_in_database(challengee):
        await print_msg(bot, 'Cannot duel with {0} because they are not in the system.'.format(user))
    else:
        try:
            if validate_token_amount(bot, tokens, ctx.author, False):
                if validate_token_amount(bot, tokens, challengee, False):
                    duel_amount = float(tokens)
                    duel_dict[challengee] = [str(ctx.author), duel_amount]
                    await print_msg(bot, '{0} has challenged {1} to duel for {2} tokens.'.format(ctx.author, challengee,
                                                                                                 duel_amount))
                else:
                    await print_msg(bot, 'Your challengee does not have enough tokens to duel.')
            else:
                await print_msg(bot, 'You do not have enough tokens to duel.')
        except ValueError:
            await print_msg(bot, 'Please enter the valid amount of tokens to duel.')


async def bot_duel_accept(ctx: commands.Context, bot: commands.Bot):
    if str(ctx.author) in duel_dict.keys():
        challengee = str(ctx.author)
        challenger = str(duel_dict[challengee][DUEL_CHALLENGER])
        rand = random.randint(1, 100)
        if rand % 2 == 0:
            await print_msg(bot, '{0} has won the duel.'.format(challengee))
            add_user_token(challengee, duel_dict[challengee][DUEL_AMOUNT])
            add_user_token(challenger, -duel_dict[challengee][DUEL_AMOUNT])
            duel_dict.pop(challengee)
        else:
            await print_msg(bot, '{0} has won the duel.'.format(challenger))
            add_user_token(challengee, -duel_dict[challengee][DUEL_AMOUNT])
            add_user_token(challenger, duel_dict[challengee][DUEL_AMOUNT])
            duel_dict.pop(challengee)
    else:
        await print_msg(bot, 'You have not been challenged.')


async def bot_duel_decline(ctx: commands.Context, bot: commands.Bot):
    if str(ctx.author) in duel_dict.keys():
        await print_msg(bot, '{0} has declined the duel'.format(ctx.author))
    else:
        await print_msg(bot, 'You have not been challenged.')


# Helper asynchronous methods
async def wait_for_users(bot: commands.Bot):
    while True:
        voice_channels = get_voice_channels(bot)
        if voice_channels is not None:
            for vc in voice_channels:
                for user in vc.members:
                    if (user_in_database(user) and
                            not user.voice.channel is None and
                            not user.voice.self_mute and
                            not user.voice.self_deaf and
                            not user.voice.mute and
                            not user.voice.deaf):
                        add_user_token(user, token_over_time)
                        await print_msg(bot, '{0} got {1} more tokens!'.format(user, token_over_time))
                    else:
                        record_log('{0} is not in database or not in compatible voice condition'.format(user))

        await asyncio.sleep(60)


async def validate_bet_state(bot: commands.Bot, user):
    if not str(user) in bet_dict.keys():
        return True
    else:
        await print_msg(bot, '{0} has already bet!'.format(user))


async def print_bet_dict(bot: commands.Bot):
    for user in bet_dict.keys():
        await print_msg(bot, '{0} has predicted {1} for {2} tokens'.format(user,
                                                                           bet_dict[user][BET_SIDE],
                                                                           bet_dict[user][BET_TOKEN]), False)
