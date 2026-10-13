#!python3

import pyvisa as visa
import sys
import os
import env

InfiniiVision = None
debug = 0

NUM_MEASUREMENTS = 1000000000
TRIGGER_LEVEL = -150E-3
TRIGGER_WAIT_TIMEOUT_MS = 5 * 60 * 1000
MAX_STOP_EDGE_OCCURRENCES = 1000
INVALID_MEASUREMENT_LIMIT = 1.0E+37


# =========================================================
# ヘルパー関数群
# =========================================================
def do_command(command):
    """コマンドを送信する"""
    InfiniiVision.write(command)

    if debug:
        print(f"Cmd = '{command}'")


def do_query_string(query):
    """クエリを送信し、文字列で結果を受け取る"""
    if debug:
        print(f"Query = '{query}'")

    return InfiniiVision.query(query).strip()


def measure_all_stops_after_start():
    """CH2 START以降にある、時間窓内の全CH3 STOPとの時間差を返す。"""
    delays = []

    for stop_occurrence in range(1, MAX_STOP_EDGE_OCCURRENCES + 1):
        # -1: CH2の1番目の立下り、-N: CH3のN番目の立下り。
        do_command(f":MEASure:DEFine DELay,-1,-{stop_occurrence}")
        result = do_query_string(":MEASure:DELay? CHANnel2,CHANnel3")

        try:
            delay = float(result)
        except ValueError:
            print(f"警告: 数値に変換できない応答を受信しました: {result}")
            break

        # N番目のSTOPがなければ、それ以降のSTOPもない。
        if abs(delay) >= INVALID_MEASUREMENT_LIMIT:
            break

        # STARTより前のSTOPは捨て、START以降のSTOPはすべて残す。
        if delay >= 0.0:
            delays.append(delay)

    return delays


# =========================================================
# オシロスコープの初期設定
# =========================================================
def initialize_for_tdc():
    print("TDC測定のための初期設定中...")

    do_command("*RST")
    do_command("*CLS")

    do_command(":TIMebase:MODE MAIN")

    do_command(":ACQuire:TYPE NORMal")
    do_command(":ACQuire:COMPlete 100")

    do_command(":TRIGger:SWEep NORMal")

    do_command(":CHANnel1:DISPlay OFF")
    do_command(":CHANnel2:DISPlay ON")
    do_command(":CHANnel3:DISPlay ON")

    do_command(":CHANnel2:PROBe 1")
    do_command(":CHANnel3:PROBe 1")

    do_command(":TRIGger:SOURce CHANnel2")
    do_command(":TRIGger:EDGE:SLOPe NEGative")
    do_command(f":TRIGger:EDGE:LEVel {TRIGGER_LEVEL}")

    do_command(":CHANnel2:SCALe 100E-3")
    do_command(":CHANnel3:SCALe 100E-3")

    do_command(":TIMebase:SCALe 5E-6")

    do_command(":WAVeform:FORMat BYTE")
    do_command(":WAVeform:UNSigned OFF")

    print("設定完了。")


# =========================================================
# TDC測定
# =========================================================
def create_tdc_spectrum(output_dir, filename):
    print(f"{NUM_MEASUREMENTS}回の測定を開始します...")

    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, filename)

    saved_stop_count = 0
    acquisitions_without_stop = 0

    with open(output_filename, "w", buffering=1) as output_file:
        output_file.write("Acquisition,StopOrder,Time\n")
        output_file.flush()

        for i in range(NUM_MEASUREMENTS):
            if i == 0:
                print(
                    "1回目の波形取得を開始しました。"
                    "START=CH2の立下りトリガーを待っています..."
                )

            try:
                do_query_string(":DIGitize CHANnel2,CHANnel3;*OPC?")
            except visa.errors.VisaIOError:
                print(
                    f"波形取得が{TRIGGER_WAIT_TIMEOUT_MS / 1000:g}秒以内に完了しませんでした。"
                )
                print(
                    f"START=CH2が{TRIGGER_LEVEL:g} Vを立下り方向に横切るか確認してください。"
                )
                raise

            delays = measure_all_stops_after_start()

            if not delays:
                acquisitions_without_stop += 1

            for stop_order, delay in enumerate(delays, start=1):
                output_file.write(
                    f"{i + 1},{stop_order},{delay:.12e}\n"
                )
                saved_stop_count += 1

            output_file.flush()

            if (i + 1) % 50 == 0:
                print(
                    f"  ... {i + 1} / {NUM_MEASUREMENTS} 回完了"
                    f"（保存STOP: {saved_stop_count}, "
                    f"STOPなし取得: {acquisitions_without_stop}）"
                )

    print("測定終了。")
    print(f"保存したSTOP数: {saved_stop_count}")
    print(f"START後のSTOPがなかった取得数: {acquisitions_without_stop}")
    print(f"保存先: {output_filename}")


# =========================================================
# main
# =========================================================
def main():
    global InfiniiVision

    if len(sys.argv) != 3:
        print(
            f"Usage: python {sys.argv[0]} "
            "<保存ディレクトリ> <保存ファイル名>"
        )
        print(
            f"例: python {sys.argv[0]} "
            "output tdc_multi_stop.csv"
        )
        sys.exit(1)

    output_dir = sys.argv[1]
    filename = sys.argv[2]

    try:
        rm = visa.ResourceManager()

        print("Establishing connection...")

        InfiniiVision = rm.open_resource(
            env.visa_addr
        )

        print("Connection Established")

        InfiniiVision.timeout = TRIGGER_WAIT_TIMEOUT_MS

        initialize_for_tdc()
        create_tdc_spectrum(output_dir, filename)

    except KeyboardInterrupt:
        print("\n測定が手動で停止されました。")
        print("停止までに取得したデータはファイルに保存されています。")

    except Exception as error:
        print(f"\nエラーが発生しました: {error}")
        print("エラー発生前までの有効データはファイルに保存されています。")

    finally:
        if InfiniiVision is not None:
            InfiniiVision.close()
            print("オシロスコープとの接続を閉じました。")


if __name__ == "__main__":
    main()
