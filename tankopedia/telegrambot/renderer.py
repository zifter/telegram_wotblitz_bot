def render_vehicle(vehicle):
    msg_pattern = u"""
<a href=\'%(tankopedia)s\'>%(name)s (%(nation)s)</a>
%(prem)s%(type)s %(level)s уровня
Цена: %(cost)s
<i>%(descr)s</i>
<a href=\'%(image_url)s\'>&#160;</a>
    """
    context = {
        'tankopedia': vehicle.tankopedia_url,
        'name': vehicle.get_loc_name(),
        'nation': vehicle.get_loc_nation(),
        'image_url': vehicle.image_normal,
        'descr': vehicle.description,
        'cost': vehicle.get_loc_cost(),
        'prem': u'Премиум ' if vehicle.is_premium else u'',
        'level': vehicle.tier,
        'type': vehicle.get_loc_type(),
    }

    msg = msg_pattern % context
    return msg


def render_player(player):
    msg_pattern = u"""
<b>{nickname}</b>
Account id {account_id}
Win rate {winrate}
    """
    return msg_pattern.format(nickname=player.raw.nickname,
                              account_id=player.raw.account_id,
                              winrate=player.win_rate_str())

