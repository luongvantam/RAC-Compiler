@section.main at 0xd730 backup 0xe9e0
def check_bit_coord : 094c8
def black_pixel_draw : 091ea
def white_pixel_draw : 091e6
def r0 & r5, pop r4,rt : 1620e

lbl setup
    xr0 = var_m, 0x0000
    num_frombyte

lbl program

    lbl check_pixel_status
        er2 = adr(coordinate, dist.main)
        setlr_pc
        er0 = [er2],r2 = 9,rt
        er2 = adr(output, 4)
        check_bit_coord
        r1 = 0,rt
        ea = adr(bit_table)
        ea_switchcase
        r0=[ea],rt
        er8 = er0

            lbl output
                er0 = hex 00 00

        r0 = [er0]
        er2 = adr(store_r5, 5)
        [er2] = r0,r2 = 0

            lbl store_r5
                er4 = hex 00 00

        er0 = er8
        r0 & r5, pop r4,rt
        hex 00 00

    lbl process_ant_decision
        r1 = 0,rt
        er4 = hex 00 01
        er0+=er4,rt
        ea = adr(decision_table)
        ea_switchcase
        er6 = [ea+]
        sp = er6,pop er8

            lbl turn_clockwise
                xr0 = adr(addr_increase_degree), var_m
                calc_func
                er2 = adr(coordinate, dist.main)
                setlr_pc
                er0 = [er2],r2 = 9,rt
                black_pixel_draw
                goto calculate

            lbl turn_counter_clockwise
                xr0 = adr(addr_decrease_degree), var_m
                calc_func
                er2 = adr(coordinate, dist.main)
                setlr_pc
                er0 = [er2],r2 = 9,rt
                white_pixel_draw

    lbl calculate

        lbl save_coordinate
            er0 = adr(coordinate, dist.main)
            r0 = [er0]
            setlr_pc
            er2 = er0,er0+=er4,rt
            er0 = var_x
            num_frombyte

            er0 = adr(coordinate, dist.main)
            r0 = [er0]
            setlr_pc
            er2 = er0,er0+=er4,rt
            er0 = var_y
            num_frombyte

        lbl clockwise
            xr0 = adr(addr_turn), var_a
            calc_func
            pop er0 (var_a)
            num_to_hex
            er2 = adr(coordinate, dist.main)
            setlr_pc
            [er2]=er0,r2 = 0,pop er4,rt
            hex 00 00
    
    lbl restore
        render.ddd4
        pop xr4, pop xr12
        adr(program)
        pr_length
        adr(program, dist.main)
        adr(program, -12)
        memcpy_auto_jump

lbl bit_table
    hex 01 00 40 00
    hex 02 00 20 00
    hex 03 00 10 00
    hex 04 00 08 00
    hex 05 00 04 00
    hex 06 00 02 00
    hex 07 00 01 00
    hex 00 00 80 00

lbl decision_table
    hex 00 01
    adr(turn_clockwise, -2)
    hex 00 00
    adr(turn_counter_clockwise, -2)

lbl coordinate
    hex 60 20

lbl addr_turn
    adr(turn)

lbl addr_increase_degree
    adr(increase_degree)

lbl addr_decrease_degree
    adr(decrease_degree)

lbl turn
    '2 5 6 Int( y - cos( M ) ) + Int( x + sin( M ) ) _'

lbl increase_degree
    'M + 9 0 _'

lbl decrease_degree
    'M - 9 0 _'

@section.launcher at 0xd180

lbl save_register
    hex fd 20
    adr(setup)
    hex fe 01
    hex 30 30 30 30
    adr(setup, dist.main)
    adr(setup, -12)

lbl launch
    setlr_pc
    setsfr
    di,rt
    memcpy_auto_jump