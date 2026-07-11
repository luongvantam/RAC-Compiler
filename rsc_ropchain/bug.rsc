@set.test at 0xd630

var my_number = 1

@python {
    if my_number == 1:
        ket_qua = '"Một"'
    elif my_number == 2:
        ket_qua = '"Hai"'
    else:
        ket_qua = '"Không biết"'
        
    for i in range(3):
        print(f"Đang đếm: {i}")
}

ket_qua