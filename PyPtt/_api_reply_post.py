try:
    from . import data_type
    from . import i18n
    from . import connect_core
    from . import log
    from . import exceptions
    from . import command
except ModuleNotFoundError:
    import data_type
    import i18n
    import connect_core
    import log
    import exceptions
    import command


def reply_post(
        api,
        reply_type: int,
        board: str,
        content: str,
        sign_file,
        post_aid: str,
        post_index: int) -> None:
    # log.showValue(
    #     api.config,
    #     Logger.INFO,
    #     [
    #         i18n.PTT,
    #         i18n.Msg
    #     ],
    #     i18n.MarkPost
    # )

    api._goto_board(board)

    cmd_list = list()

    if post_aid is not None:
        cmd_list.append('#' + post_aid)
    elif post_index != 0:
        cmd_list.append(str(post_index))
    cmd_list.append(command.enter * 2)
    cmd_list.append('r')

    if reply_type == data_type.reply_type.BOARD:
        reply_target_unit = connect_core.TargetUnit(
            i18n.ReplyBoard,
            '▲ 回應至',
            log_level=Logger.INFO,
            response='F' + command.enter
        )
    elif reply_type == data_type.reply_type.MAIL:
        reply_target_unit = connect_core.TargetUnit(
            i18n.ReplyMail,
            '▲ 回應至',
            log_level=Logger.INFO,
            response='M' + command.enter
        )
    elif reply_type == data_type.reply_type.BOARD_MAIL:
        reply_target_unit = connect_core.TargetUnit(
            i18n.ReplyBoard_Mail,
            '▲ 回應至',
            log_level=Logger.INFO,
            response='B' + command.enter
        )

    cmd = ''.join(cmd_list)
    target_list = [
        connect_core.TargetUnit(
            i18n.any_key_continue,
            '任意鍵繼續',
            break_detect=True,
        ),
        connect_core.TargetUnit(
            i18n.no_response,
            '◆ 很抱歉, 此文章已結案並標記, 不得回應',
            log_level=Logger.INFO,
            exceptions_=exceptions.NoResponse()
        ),
        connect_core.TargetUnit(
            i18n.ForcedWrite,
            '(E)繼續編輯 (W)強制寫入',
            log_level=Logger.INFO,
            response='W' + command.enter
        ),
        connect_core.TargetUnit(
            i18n.SelectSignature,
            '請選擇簽名檔',
            response=str(sign_file) + command.enter,
        ),
        connect_core.TargetUnit(
            i18n.SaveFile,
            '確定要儲存檔案嗎',
            response='s' + command.enter,
        ),
        connect_core.TargetUnit(
            i18n.EditPost,
            '編輯文章',
            log_level=Logger.INFO,
            response=str(content) + command.enter + command.ctrl_x
        ),
        connect_core.TargetUnit(
            i18n.QuoteOriginal,
            '請問要引用原文嗎',
            log_level=Logger.DEBUG,
            response='Y' + command.enter
        ),
        connect_core.TargetUnit(
            i18n.UseTheOriginalTitle,
            '採用原標題[Y/n]?',
            log_level=Logger.DEBUG,
            response='Y' + command.enter
        ),
        reply_target_unit,
        connect_core.TargetUnit(
            i18n.SelfSaveDraft,
            '已順利寄出，是否自存底稿',
            log_level=Logger.DEBUG,
            response='Y' + command.enter
        ),
    ]

    api.connect_core.send(
        cmd,
        target_list,
        screen_timeout=api.config.screen_long_timeout)

    log.log(
        api.config,
        Logger.INFO,
        i18n.RespondSuccess)
