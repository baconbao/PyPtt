import re

from SingleLog.log import Logger

from . import _api_util
from . import check_value
from . import command
from . import connect_core
from . import data_type, lib_util
from . import exceptions
from . import i18n
from . import screens
from .data_type import SearchType, NewIndex


def _get_newest_index(api) -> int:
    logger = Logger('get_newest_index', Logger.INFO)
    last_screen = api.connect_core.get_screen_queue()[-1]
    # print(last_screen)
    last_screen_list = last_screen.split('\n')
    last_screen_list = last_screen_list[3:]
    last_screen_list = '\n'.join([x[:9] for x in last_screen_list])
    # print(last_screen_list)
    all_index = re.findall(r'\d+', last_screen_list)

    if len(all_index) == 0:
        # print(last_screen)
        # raise exceptions.UnknownError(i18n.UnknownError)
        return 0

    all_index = list(map(int, all_index))
    all_index.sort(reverse=True)
    # print(all_index)

    max_check_range = 6
    newest_index = 0
    for index_temp in all_index:
        need_continue = True
        if index_temp > max_check_range:
            check_range = max_check_range
        else:
            check_range = index_temp
        for i in range(1, check_range):
            if str(index_temp - i) not in last_screen:
                need_continue = False
                break
        if need_continue:
            logger.debug(i18n.find_newest_index, index_temp)
            newest_index = index_temp
            break

    if newest_index == 0:
        last_screen = api.connect_core.get_screen_queue()[-1]
        print(last_screen)
        raise exceptions.UnknownError(i18n.UnknownError)

    return newest_index


def get_newest_index(
        api,
        index_type: int,
        search_type: int = 0,
        search_condition: str = None,
        search_list: list = None,
        # BBS
        board: str = None) -> int:
    _api_util._one_thread(api)

    if not api._login_status:
        raise exceptions.Requirelogin(i18n.require_login)

    if not isinstance(index_type, NewIndex):
        TypeError('index_type must be NewIndex')

    if not isinstance(search_type, SearchType):
        raise TypeError(f'search_type must be SearchType, but {search_type}')

    if index_type == NewIndex.MAIL:
        if api.unregistered_user:
            raise exceptions.UnregisteredUser(lib_util.get_current_func_name())

        if board is not None:
            raise ValueError('board should not input in mail mode')

        mail_search_options = [
            SearchType.KEYWORD,
            SearchType.AUTHOR,
            SearchType.MARK,
            SearchType.NOPE,
        ]
        if search_type not in mail_search_options:
            ValueError(f'search type must in {mail_search_options} in mail mode')

    if search_condition is not None:
        check_value.check_type(str, 'search_condition', search_condition)

    if search_list is not None:
        check_value.check_type(api.config, list, 'search_list', search_list)
    check_value.check_type(int, 'SearchType', search_type)

    if index_type == data_type.NewIndex.BBS:

        check_value.check_type(str, 'board', board)

        api._check_board(board)
        api._goto_board(board)

        cmd_list, normal_newest_index = _api_util.get_search_condition_cmd(
            api,
            index_type,
            search_type,
            search_condition,
            search_list,
            board)

        cmd_list.append('1')
        cmd_list.append(command.enter)
        cmd_list.append('$')

        cmd = ''.join(cmd_list)

        target_list = [
            connect_core.TargetUnit(
                i18n.no_post,
                '沒有文章...',
                break_detect=True,
                log_level=Logger.DEBUG),
            connect_core.TargetUnit(
                i18n.complete,
                screens.Target.InBoard,
                break_detect=True,
                log_level=Logger.DEBUG),
            connect_core.TargetUnit(
                i18n.complete,
                screens.Target.InBoardWithCursor,
                break_detect=True,
                log_level=Logger.DEBUG),
            connect_core.TargetUnit(
                i18n.no_such_board,
                screens.Target.MainMenu_Exiting,
                exceptions_=exceptions.NoSuchBoard(api.config, board)),
        ]
        index = api.connect_core.send(cmd, target_list)
        if index < 0:
            # OriScreen = api.connect_core.getScreenQueue()[-1]
            # print(OriScreen)
            raise exceptions.NoSuchBoard(api.config, board)

        if index == 0:
            return 0

        newest_index = _get_newest_index(api)

        if normal_newest_index == newest_index:
            raise exceptions.NoSearchResult()

    elif index_type == data_type.NewIndex.MAIL:

        cmd_list = list()
        cmd_list.append(command.go_main_menu)
        cmd_list.append(command.ctrl_z)
        cmd_list.append('m')

        _cmd_list, normal_newest_index = _api_util.get_search_condition_cmd(
            api,
            index_type,
            search_type,
            search_condition,
            search_list,
            board)
        # print('normal_newest_index', normal_newest_index)

        cmd_list.extend(_cmd_list)
        cmd_list.append(command.ctrl_f * 50)

        cmd = ''.join(cmd_list)

        target_list = [
            connect_core.TargetUnit(
                i18n.mail_box,
                screens.Target.InMailBox,
                break_detect=True),
            connect_core.TargetUnit(
                i18n.no_mail,
                screens.Target.CursorToGoodbye,
                break_detect=True,
                log_level=Logger.DEBUG),
        ]

        def get_index(api):
            current_capacity, _ = _api_util.get_mailbox_capacity(api)
            last_screen = api.connect_core.get_screen_queue()[-1]
            cursor_line = [x for x in last_screen.split('\n') if x.strip().startswith(api.cursor)][0]
            # print('---->', cursor_line)
            list_index = int(re.compile('(\d+)').search(cursor_line).group(0))

            # print('----> list_index', list_index)
            # print('----> current_capacity', current_capacity)
            if search_type == 0 and search_list is None:
                if list_index > current_capacity:
                    newest_index = list_index
                else:
                    newest_index = current_capacity
            else:
                newest_index = list_index

            return newest_index

        for i in range(3):
            index = api.connect_core.send(
                cmd,
                target_list)
            # print('index', index)
            # last_screen = api.connect_core.get_screen_queue()[-1]
            # print(last_screen)

            if index == 0:
                newest_index = get_index(api)
                if normal_newest_index == newest_index:
                    if i == 2:
                        raise exceptions.NoSearchResult()
                    else:
                        continue
                break
            newest_index = 0

    return newest_index
