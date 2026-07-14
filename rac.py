#!/usr/bin/env python3
import sys
import os
from libcompiler import main

if __name__ == "__main__":
    try:
        main.main()
    except EOFError:
        from libcompiler.i18n import t
        print(t("err_stdin_closed"))
    except Exception as e:
        from libcompiler import utils
        utils.report_error(e)
