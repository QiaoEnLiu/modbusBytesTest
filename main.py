import serial

# 配置串口
ser = serial.Serial(
    port='COM12',        # 替換為實際的串口名稱
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1
)


def compute_crc(data: bytes) -> int:
    """
    計算 Modbus RTU 報文的 CRC 校驗值。

    :param data: 報文的字節數據
    :return: CRC 校驗值（整數）
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

def build_modbus_message(address, function_code, starting_register, length):
    """
    根據 Modbus 參數構建報文，不包含 CRC。

    :param address: 從站地址
    :param function_code: 功能碼
    :param starting_register: 起始寄存器
    :param length: 讀取寄存器數量
    :return: 構建的報文
    """
    message = (
        address.to_bytes(1, 'big') +
        function_code.to_bytes(1, 'big') +
        starting_register.to_bytes(2, 'big') +
        length.to_bytes(2, 'big')
    )
    return message

def send_modbus_message(ser, message_with_crc):
    """
    發送 Modbus 報文並接收回應。

    :param ser: 已配置好的串口對象
    :param message_with_crc: 已附加 CRC 的報文
    :return: 設備回應
    """
    ser.write(message_with_crc)
    response = ser.read(100)  # 根據回應長度調整大小
    return response

def verify_crc(response):
    """
    驗證回應的 CRC。

    :param response: 設備回應
    :return: CRC 驗證結果 (True/False)
    """
    if len(response) > 2:  # 回應必須至少包含 Address, Function Code 和 CRC
        response_crc = int.from_bytes(response[-2:], byteorder='little')  # 提取回應中的 CRC
        calculated_crc = compute_crc(response[:-2])  # 計算數據部分的 CRC
        return response_crc == calculated_crc
    return False

def format_hex_output(byte_data):
    return ' '.join([f'{byte:02X}' for byte in byte_data])


try:
    # 從 console input 讀取參數，單行輸入，並分割參數
    input_data = input("請輸入參數 (十六進位樣式，例如: 0x01 0x03 0x00 0x00 0x00 0x02): ")

    # 解析輸入的數據，將每個數字轉換為整數
    input_values = input_data.split()
    print(input_values)

    # 將每個十六進位字串轉換為十進位整數
    address = int(input_values[0], 16)
    function_code = int(input_values[1], 16)
    starting_register = int(input_values[2], 16) << 8 | int(input_values[3], 16)  # 兩個字節合併
    length = int(input_values[4], 16) << 8 | int(input_values[5], 16)  # 兩個字節合併

    # 驗證輸入參數
    if not (0 <= address <= 255):
        raise ValueError("從站地址必須在 0-255 之間")
    if not (0 <= function_code <= 255):
        raise ValueError("功能碼必須在 0-255 之間")
    if not (0 <= starting_register <= 65535):
        raise ValueError("起始寄存器地址必須在 0-65535 之間")
    if not (1 <= length <= 125):
        print(length)
        raise ValueError("寄存器數量必須在 1-125 之間")

    # 構建報文
    message = build_modbus_message(address, function_code, starting_register, length)

    # 計算並附加 CRC
    crc = compute_crc(message)
    message_with_crc = message + crc.to_bytes(2, 'little')

    print("發送的報文 (Hex):", format_hex_output(message_with_crc))

    # 發送報文並接收回應
    response = send_modbus_message(ser, message_with_crc)
    print("設備回應 (Hex):", format_hex_output(response))

    # 驗證 CRC
    if verify_crc(response):
        print("CRC 驗證成功！")
        # 提取數據部分（假設正常回應格式）
        data = response[3:-2]  # 去掉 Address, Function Code 和 CRC
        print("寄存器數據 (Hex):", format_hex_output(data))
    else:
        print("CRC 驗證失敗！")

except Exception as e:
    print(f"發生錯誤: {e}")

finally:
    # 確保關閉串口
    ser.close()
