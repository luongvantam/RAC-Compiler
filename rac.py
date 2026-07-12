#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
from lib import main

if __name__ == "__main__":
    try:
        main.main()
    except EOFError:
        print("Error: stdin closed.")
    except Exception as e:
        import utils
        utils.report_error(e)
