def calculate_fspl(rssi, p_tx, g_tx = 0, g_rx = 0):

    fspl = p_tx + g_tx + g_rx - rssi
    return fspl

