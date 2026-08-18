#!python3
import pyvisa as visa
import string
import struct
import sys
import numpy as np
import matplotlib.pyplot as plt
import os
import env

InfiniiVision = None
debug = 0
NUM_WAVEFORMS = 5000

# =========================================================
# ヘルパー関数群 (変更なし)
# =========================================================
def do_command(command, hide_params=False):
    if hide_params:
        (header, data) = command.split(" ", 1)
        if debug: print("\nCmd = '%s'" % header)
    else:
        if debug: print("\nCmd = '%s'" % command)
    InfiniiVision.write("%s" % command)
    if hide_params:
        check_instrument_errors(header)
    else:
        check_instrument_errors(command)

def do_query_string(query):
    if debug: print("Qys = '%s'" % query)
    result = InfiniiVision.query("%s" % query)
    check_instrument_errors(query)
    return result

def do_query_ieee_block(query):
    if debug: print("Qyb = '%s'" % query)
    result = InfiniiVision.query_binary_values(query, datatype='b', is_big_endian=False)
    check_instrument_errors(query)
    return result

def check_instrument_errors(command):
    while True:
        error_string = InfiniiVision.query(":SYSTem:ERRor?")
        if error_string:
            if error_string.find("+0,", 0, 3) == -1:
                print("ERROR: %s, command: '%s'" % (error_string, command))
                print("エラーにより終了しました。")
                sys.exit(1)
            else: # "+0, No error"
                break
        else:
            print("ERROR: :SYSTem:ERRor? が何も返しませんでした。 command: '%s'" % command)
            print("エラーにより終了しました。")
            sys.exit(1)

# =========================================================
# このプログラムの主要な関数
# =========================================================
def initialize_for_adc(trigger_level):
    print("ADC測定のための初期設定中...")
    do_command("*RST")
    do_command("*CLS")
    
    do_command(":TIMebase:MODE MAIN")
    do_command(":ACQuire:TYPE NORMal")
    do_command(":ACQuire:COMPlete 100")
    do_command(":TRIGger:SWEep NORMal")
    do_command(":CHANnel1:PROBe 1")
    do_command(":TRIGger:EDGE:SLOPe NEGative")
    do_command(f":TRIGger:EDGE:LEVel {trigger_level}")
    
    do_command(":CHANnel1:DISPlay ON")
    do_command(":WAVeform:SOURce CHANnel1")
    do_command(":CHANnel1:SCALe 50E-3")
    do_command(":TIMebase:SCALe 50E-9")
    do_command(":CHANnel1:OFFSet 0")
    do_command(":WAVeform:FORMat BYTE")
    do_command(":WAVeform:UNSigned OFF")
    print("設定完了。")

def create_adc_spectrum(output_dir, filename_base):
    output_filename = os.path.join(output_dir, filename_base)

    preamble_string = do_query_string(":WAVeform:PREamble?")
    (
        wav_form, acq_type, wfmpts, avgcnt, x_increment, x_origin,
        x_reference, y_increment, y_origin, y_reference
    ) = preamble_string.split(",")
    
    y_increment = float(y_increment)
    y_origin = float(y_origin)
    y_reference = float(y_reference)

    peak_voltages = []
    print(f"{NUM_WAVEFORMS}個の波形からピーク値を収集します...")

    for i in range(NUM_WAVEFORMS):
        do_command(":DIGitize CHANnel1")
        do_query_string("*OPC?")
        sData = do_query_ieee_block(":WAVeform:DATA?")
        values = np.array(sData, dtype=np.int8)
        voltages = ((values - y_reference) * y_increment) + y_origin
        peak = np.min(voltages)
        peak_voltages.append(peak)

        if (i + 1) % 50 == 0:
            print(f"  ... {i+1} / {NUM_WAVEFORMS} 波形完了")
    
    print("データ収集完了。")

    os.makedirs(output_dir, exist_ok=True)
    
    print(f"ピーク値を'{output_filename}'に保存中")
    np.savetxt(output_filename, peak_voltages, fmt='%.6f')
    print("保存完了。")

# =========================================================
# main
# =========================================================
def main():
    
    global InfiniiVision
    
   
    if len(sys.argv) != 4:
        print("実行方法が正しくありません。")
        print(f"Usage: python3 {sys.argv[0]} <保存ファイル名> <保存ディレクトリパス> <トリガー電圧>")
        print(f"例: python {sys.argv[0]} adc.csv output -0.025")
        sys.exit(1)


    filename_base = sys.argv[1]
    output_dir = sys.argv[2]
    try:
        current_volt = float(sys.argv[3])
    except ValueError:
        print("エラー: トリガー電圧は数値で指定してください。例: -0.025")
        sys.exit(1)

    try:
        rm = visa.ResourceManager()
        InfiniiVision = rm.open_resource(env.visa_addr) 
        
        InfiniiVision.timeout = 20000
        InfiniiVision.read_termination = '\n'
        InfiniiVision.write_termination = '\n'

        print("オシロスコープに接続しました。")
        print(do_query_string("*IDN?"))

        # ★変更点: 関数に引数を渡して実行
        initialize_for_adc(current_volt)
        create_adc_spectrum(output_dir, filename_base)

    except Exception as e:
        print(f"エラーが発生しました: {e}")

    finally:
        if InfiniiVision is not None:
            InfiniiVision.close()
            print("オシロスコープとの接続を閉じました。")

    print("プログラムを終了します。")


if __name__ == "__main__":
    main()
