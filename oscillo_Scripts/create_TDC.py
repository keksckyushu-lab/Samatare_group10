#!python3

import pyvisa as visa
import sys
import numpy as np
import os
import env

InfiniiVision = None
debug = 0

NUM_MEASUREMENTS = 100000
TRIGGER_LEVEL = -150E-3

# =========================================================
# ヘルパー関数群
# =========================================================
def do_command(command):
    """コマンドを送信する"""
    InfiniiVision.write(command)
    print(f"Cmd = '{command}'")


def do_query_string(query):
    """クエリを送信し、文字列で結果を受け取る"""
    return InfiniiVision.query(query).strip()


def initialize_for_tdc():
    print("TDC測定のための初期設定中...")

    do_command("*RST")
    do_command("*CLS")
    do_command(":TIMebase:MODE MAIN")
    do_command(":ACQuire:TYPE NORMal")
    do_command(":ACQuire:COMPlete 100")
    do_command(":TRIGger:SWEep NORMal")
    do_command(":CHANnel1:DISPlay ON")
    do_command(":CHANnel2:DISPlay ON")
    do_command(":CHANnel1:PROBe 1")
    do_command(":CHANnel2:PROBe 1")
    do_command(":TRIGger:SOURce CHANnel1")
    do_command(":TRIGger:EDGE:SLOPe NEGative")
    do_command(f":TRIGger:EDGE:LEVel {TRIGGER_LEVEL}")
    do_command(":CHANnel1:SCALe 100E-3")
    # do_command(":CHANnel1:OFFSet -400E-3")
    do_command(":CHANnel2:SCALe 100E-3")
    # do_command(":CHANnel2:OFFSet -400E-3")
    do_command(":TIMebase:SCALe 10E-6")
    do_command(":WAVeform:FORMat BYTE")
    do_command(":WAVeform:UNSigned OFF")

    print("設定完了。")


def create_tdc_spectrum(OUTPUT_DIR, FILENAME):
    time_diffs = []

    print(f"{NUM_MEASUREMENTS}個のデータを収集します...")

    do_command(":MEASure:DEFine DELay,-1,-1")

    for i in range(NUM_MEASUREMENTS):
        do_command(":DIGitize CHANnel1,CHANnel2")
        do_query_string("*OPC?")

        result = do_query_string(
            ":MEASure:DELay? CHANnel1,CHANnel2"
        )

        val = float(result)

        if val < 1.0e+37:
            time_diffs.append(val)

        if (i + 1) % 50 == 0:
            print(
                f"  ... {i + 1} / {NUM_MEASUREMENTS} 完了"
            )

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    OUTPUT_FILENAME = os.path.join(
        OUTPUT_DIR,
        FILENAME
    )

    header_line = "Time"

    np.savetxt(
        OUTPUT_FILENAME,
        time_diffs,
        delimiter=",",
        header=header_line,
        comments=""
    )


def main():
    global InfiniiVision

    if len(sys.argv) != 3:
        print(
            f"Usage: python {sys.argv[0]} "
            "<保存ディレクトリ> <保存ファイル名>"
        )
        print(
            f"例: python {sys.argv[0]} "
            "output tdc_ch1_ch2.csv"
        )
        sys.exit(1)

    OUTPUT_DIR = sys.argv[1]
    FILENAME = sys.argv[2]

    try:
        rm = visa.ResourceManager()

        print("Establishing connection...")

        InfiniiVision = rm.open_resource(
            env.visa_addr
        )

        print("Connection Established")

        InfiniiVision.timeout = 1000000

        initialize_for_tdc()
        create_tdc_spectrum(
            OUTPUT_DIR,
            FILENAME
        )

    finally:
        if InfiniiVision is not None:
            InfiniiVision.close()


if __name__ == "__main__":
    main()
