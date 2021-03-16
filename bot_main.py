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
bot_id = 249925410819670016

bet_dict = {}
bet_pool_dict = {}
duel_dict = {}
min_bet_tokens = 10

BET_SIDE, BET_TOKEN, BET_STATE_USER = range(3)
DUEL_CHALLENGER, DUEL_AMOUNT = range(2)


# The functionality of what bot can do will be implemented below.

# Bot's main asynchronous methods
async def bot_apply(ctx: commands.Context, bot: commands.Bot):
    user = ctx.author
    user_apply(user, bot)


async def user_apply(user: discord.Member, bot: commands.Bot, is_bot=False):
    token = token_init
    has_registered = False

    if user_in_database(user) and not is_bot:
        has_registered = True
        await print_msg(bot, '{0} has already registered!'.format(str(user)))

    if user_in_database(user) and is_bot:
        has_registered = True

    with open(data_filename, 'a') as f:
        if not has_registered and not is_bot:
            await print_msg(bot, '{0} has registered in the betting system.'.format(user))

            f.write('{0}:{1}:{2}\n'.format(user, user.id, token))
            await print_msg(bot, '{0} has earned {1} tokens.'.format(user, token))
        if not has_registered and is_bot:
            record_log('{0} has registered in the betting system.'.format(user))

            f.write('{0}:{1}:{2}\n'.format(user, user.id, token))
            record_log('{0} has earned {1} tokens.'.format(user, token))


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
    $bet [bet_result] [token_amount/all]\n
      - Choose to become believers or doubters with some tokens that can motivate players’ movement in game. (<bet_result> includes win, loss, lose) Ex. $bet loss all \n\n
    $result [bet_result]\n
      - For privileged dude only. Use this command to announce the match result and take all Investors' tokens. Ex. $result loss\n\n
    $donate [donatee] [token_amount/all]\n 
      - Donate your tokens to an unfortunate investor in need of spare tokens. Ex. $donate @IndyKuma#5444 322n\n\n
    $redeem [peepo] [redeem_type] [hero's name/role]\n
      - redeem_type = coach\n 
        Give a decree to your lovely wimpy coach to entertain peepos as a player. Ex. $redeem @The Look Jork#7812 coach\n
        (cost 20000 tokens)\n
      - redeem_type = hero\n
        Give a decree to your kawaii friend to play a chosen hero such as Meepo, in order to be the real hero!!!. Ex. $redeem @The Look Jork#7812 hero Meepo\n
        (cost 10000 tokens)\n
        #PS: SHAME to those who don't abide by the decree.
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
    if not get_bet_open_state() and not get_prediction_state():
        set_bet_open_state(True)
        set_prediction_state(True)
        bet_pool_dict['win'] = 0
        bet_pool_dict['lose'] = 0
        await print_msg(bot, 'Prediction and bet phase have started!')
        await asyncio.sleep(360)
        await bot_bet_close(bot)
    else:
        await print_msg(bot, 'Bet phase has already closed. :(')


async def bot_bet_close(bot: commands.Bot):
    if get_bet_open_state() and get_prediction_state():
        set_bet_open_state(False)
        # Bot has to bet if there's the prediction pool is unbalanced (either side has return ratio less than 1:1.1)
        bot_user = get_user_from_user_id(bot_id)
        bot_current_tokens = user_current_tokens(bot_user)
        lose_pool_diff = 0.1 * bet_pool_dict['lose'] - bet_pool_dict['win']
        if lose_pool_diff > 0:
            if bot_current_tokens >= lose_pool_diff:
                await user_bet(bot_user, bot, 'win', lose_pool_diff, True)
            else:
                await user_bet(bot_user, bot, 'win', bot_current_tokens, True)
        win_pool_diff = 0.1 * bet_pool_dict['win'] - bet_pool_dict['lose']
        if win_pool_diff > 0:
            if bot_current_tokens >= win_pool_diff:
                await user_bet(bot_user, bot, 'lose', win_pool_diff, True)
            else:
                await user_bet(bot_user, bot, 'lose', bot_current_tokens, True)

        await print_msg(bot, 'Bet phase has ended!')
        await print_bet_dict(bot)
    else:
        await print_msg(bot, 'Prediction has not started yet. :(')


async def bot_bet_reset(ctx: commands.Context, bot: commands.Bot):
    if user_is_judge(ctx.author):
        set_bet_open_state(False)
        set_prediction_state(False)
        await print_msg(bot, 'Bet state has been reset!')
    else:
        await print_msg(bot, 'Sorry, you do not have a permission to do that (have no prediction judge role). ¯\_(ツ)_/¯')


async def bot_bet(ctx: commands.Context, bot: commands.Bot, bet_side, token):
    if not get_prediction_state():
        await print_msg(bot, 'Prediction has not started yet. :(')
        return

    if not get_bet_open_state() and get_prediction_state():
        await print_msg(bot, 'Bet phase has already closed. :(')
        return

    user = ctx.author
    await user_bet(user, bot, bet_side, token)


async def user_bet(user: discord.Member, bot: commands.Bot, bet_side, token, is_bot=False):
    token_to_deduct = 0.0
    if user_in_database(user):
        try:
            valid_number = await validate_token_amount(bot, str(token), user, printed=True, is_bot=is_bot)
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
                    bet_pool_dict['win'] += token_to_deduct
                    add_user_token(user, -token_to_deduct)
                    await print_msg(bot, '{0} has chosen to be the believers!'.format(user))
                elif bet_side.lower() == 'loss' or bet_side.lower() == 'lose':
                    bet_dict[str(user)] = ('loss', token_to_deduct, True)
                    bet_pool_dict['lose'] += token_to_deduct
                    add_user_token(user, -token_to_deduct)
                    await print_msg(bot, '{0} has chosen to be the doubters!'.format(user))
                else:
                    await print_msg(bot, 'Please enter the valid result.')

        except IndexError:
            await print_msg(bot, 'Please enter the valid result or token value to bet.')
    else:
        await print_msg(bot, '{0} has not registered in the system yet.'.format(user))


async def bot_result(ctx: commands.Context, bot: commands.Bot, bet_result):
    if not get_prediction_state():
        await print_msg(bot, 'Prediction has not started yet. :(')
        return

    user = ctx.author
    win_ratio = (bet_pool_dict['win'] + bet_pool_dict['lose']) / bet_pool_dict['win']
    loss_ratio = (bet_pool_dict['win'] + bet_pool_dict['lose']) / bet_pool_dict['lose']
    record_log('Win ratio is 1 : {0}.'.format(win_ratio))
    record_log('Loss ratio is 1 : {0}.'.format(loss_ratio))

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
                    if _result == 'win':
                        add_user_token(user, float(bet_dict[user][BET_TOKEN] * win_ratio))
                        await print_msg(bot,
                                        '{0} has won {1} tokens.'.format(user, bet_dict[user][BET_TOKEN] * win_ratio), destroy=False)
                    elif _result == 'loss':
                        add_user_token(user, float(bet_dict[user][BET_TOKEN] * loss_ratio))
                        await print_msg(bot,
                                        '{0} has won {1} tokens.'.format(user, bet_dict[user][BET_TOKEN] * loss_ratio), destroy=False)
                else:
                    await print_msg(bot, '{0} has wasted {1} tokens.'.format(user, bet_dict[user][BET_TOKEN]), destroy=False)
            set_bet_open_state(False)
            set_prediction_state(False)
            bet_dict.clear()
            bet_pool_dict.clear()
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
            valid_number = await validate_token_amount(bot, str(donate_amount), user)
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
            valid_challenger_amount = await validate_token_amount(bot, str(tokens), ctx.author, False)
            valid_challengee_amount = await validate_token_amount(bot, str(tokens), challengee, False)
            valid_duel = False
            if valid_challenger_amount and valid_challengee_amount:
                duel_amount = float(tokens)
                valid_duel = True
            elif tokens.lower() == 'all':
                duel_amount = user_current_tokens(ctx.author)
                valid_challenger_amount = await validate_token_amount(bot, str(duel_amount), ctx.author, False)
                valid_challengee_amount = await validate_token_amount(bot, str(duel_amount), challengee, False)
                if not valid_challenger_amount:
                    await print_msg(bot, 'You do not have enough tokens to duel.')
                elif not valid_challengee_amount:
                    await print_msg(bot, 'Your challengee does not have enough tokens to duel.')
                else:
                    valid_duel = True
            elif not valid_challenger_amount:
                await print_msg(bot,
                                'You do not have enough tokens to duel or you inserted an invalid amount of tokens.')
            elif not valid_challengee_amount:
                await print_msg(bot,
                                'Your challengee does not have enough tokens to duel or you inserted an invalid amount of tokens.')

            if valid_duel:
                duel_dict[challengee] = [str(ctx.author), duel_amount]
                await print_msg(bot, '{0} has challenged {1} to duel for {2} tokens.'.format(ctx.author, challengee,
                                                                                             duel_amount))

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
        duel_dict.pop(str(ctx.author))
    else:
        await print_msg(bot, 'You have not been challenged.')


async def bot_redeem(ctx: commands.Context, bot: commands.Bot, member: discord.Member, *args):
    redemption_cost = [0, 20000, 10000]  # redemption cost for each redemption type
    # redemption_cost = [0, 20, 10]  # redemption cost for each redemption type "for testing"
    redeem_type = 0
    if args[0] == 'coach':
        redeem_type = 1
    if args[0] == 'hero':
        redeem_type = 2
    required_cost = redemption_cost[redeem_type]
    user = ctx.author
    if user_in_database(user):
        user_token = user_current_tokens(user)
        if user_token < required_cost:
            await print_msg(bot,
                            'You should have at least {0} token for such an invaluable redemption. ;)'.format(
                                required_cost))
        else:
            valid_redeem = False
            if args[0] == 'coach':
                await print_msg(bot, '{0} has redeemed {1} tokens to force {2} to become a player.'.format(user,
                                                                                                           required_cost,
                                                                                                           member),
                                destroy=False)
                valid_redeem = True
            elif args[0] == 'hero':
                try:
                    await print_msg(bot, '{0} has redeemed {1} tokens to force {2} to pick {3}'.format(user,
                                                                                                       required_cost,
                                                                                                       member,
                                                                                                       args[1]),
                                    destroy=False)
                    valid_redeem = True
                except IndexError:
                    await print_msg(bot, 'You have not selected the hero for {0} to pick.'.format(member))
            else:
                await print_msg(bot, 'You have inserted the invalid redeem type.')

            if valid_redeem:
                add_user_token(user, -required_cost)
    else:
        await print_msg(bot, '{0} has not registered in the system yet.'.format(user))


# Helper asynchronous methods
async def wait_for_users(bot: commands.Bot):
    # If the bot has not applied for the system yet, then let the bot apply.
    bot_user = get_user_from_user_id(bot_id)
    if bot_user is None:
        await user_apply(bot.user, bot, True)
    while True:
        await asyncio.sleep(60)

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
                    # else:
                    #     record_log('{0} is not in database or not in compatible voice condition'.format(user))

        add_user_token_by_id(bot_id, get_users_count() * token_over_time)


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
