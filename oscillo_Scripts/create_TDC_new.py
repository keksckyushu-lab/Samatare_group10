#!python3

import pyvisa as visa
import sys
import os
import env

InfiniiVision = None
debug = 0

NUM_MEASUREMENTS = 10000000
TRIGGER_LEVEL = -150E-3
TRIGGER_WAIT_TIMEOUT_MS = 5 * 60 * 1000


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

    do_command(":CHANnel1:DISPlay ON")
    do_command(":CHANnel2:DISPlay ON")

    do_command(":CHANnel1:PROBe 1")
    do_command(":CHANnel2:PROBe 1")

    # 動作実績のある旧版と同じ順序でトリガーを設定する
    do_command(":TRIGger:SOURce CHANnel1")
    do_command(":TRIGger:EDGE:SLOPe NEGative")
    do_command(f":TRIGger:EDGE:LEVel {TRIGGER_LEVEL}")

    do_command(":CHANnel1:SCALe 100E-3")
    do_command(":CHANnel2:SCALe 100E-3")

    do_command(":TIMebase:SCALe 10E-6")

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

    # CH1の立下りとCH2の立下りの時間差を測定
    do_command(":MEASure:DEFine DELay,-1,-1")

    valid_count = 0

    # 測定開始時にファイルを新しく作る
    with open(output_filename, "w", buffering=1) as output_file:
        output_file.write("Time\n")
        output_file.flush()

        for i in range(NUM_MEASUREMENTS):
            if i == 0:
                print(
                    "1回目の波形取得を開始しました。"
                    "CH1の立下りトリガーを待っています..."
                )

            # DIGitizeとOPC?を同じメッセージにして、波形取得完了まで待つ
            try:
                do_query_string(":DIGitize CHANnel1,CHANnel2;*OPC?")
            except visa.errors.VisaIOError:
                print(
                    f"波形取得が{TRIGGER_WAIT_TIMEOUT_MS / 1000:g}秒以内に完了しませんでした。"
                )
                print(
                    f"CH1が{TRIGGER_LEVEL:g} Vを立下り方向に横切るか確認してください。"
                )
                raise

            # CH1とCH2のdelayを取得
            result = do_query_string(
                ":MEASure:DELay? CHANnel1,CHANnel2"
            )

            try:
                val = float(result)
            except ValueError:
                print(
                    f"警告: 数値に変換できない応答を受信しました: {result}"
                )
                continue

            # オシロが測定不能時に返す異常値を除外
            if abs(val) < 1.0E+37:
                # 有効なイベントごとにファイルへ書き込む
                output_file.write(f"{val:.12e}\n")

                # PythonのバッファからOSへ書き出す
                output_file.flush()

                valid_count += 1

            if (i + 1) % 50 == 0:
                print(
                    f"  ... {i + 1} / {NUM_MEASUREMENTS} 回完了"
                    f"（有効イベント: {valid_count}）"
                )

    print("測定終了。")
    print(f"有効イベント数: {valid_count}")
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
            "output new_test_tdc_ch1_ch2.txt"
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

        # トリガーが来ない場合に、長時間停止したように見えるのを防ぐ
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
