import pylink
import os
import time
import argparse

def flash_gd32_with_jlink(bin_file, device_name="GD32F103C8", start_addr=0x08000000,
                          erase=True, verify=True, reset=True):
    """
    使用 J-Link 将程序烧录到目标芯片
    :param bin_file: 固件文件路径 (.bin 或 .hex)
    :param device_name: 目标芯片型号 (需与 J-Link 数据库一致)
    :param start_addr: 烧录起始地址
    :param erase: 烧录前是否擦除芯片
    :param verify: 烧录后是否验证
    :param reset: 烧录后是否复位运行
    """

    # 1. 初始化 J-Link
    jlink = pylink.JLink()

    print(f"Opening J-Link...")
    jlink.open()

    # 2. 选择目标芯片
    print(f"Selecting device: {device_name}")
    try:
        jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
        jlink.connect(device_name)
    except pylink.errors.JLinkException as e:
        print(f"Connection failed: {e}")
        print("Hint: Please check if the device name is correct. Run 'JLinkDevices' command to view the supported device list.")
        return

    print(f"Connected to chip. Core: {jlink.core_name()}")

    # 3. 擦除芯片 (可选)
    if erase:
        print("Erasing chip...")
        jlink.erase()

    # 4. 烧录文件
    print(f"Flashing file: {bin_file}")
    jlink.flash_file(bin_file, start_addr)

    # 5. 验证 (可选)
    if verify:
        print("Verifying...")
        try:
            # pylink 库没有直接验证方法，手动读取并比较
            with open(bin_file, 'rb') as f:
                file_data = f.read()
            mem_data = bytes(jlink.memory_read(start_addr, len(file_data)))
            if mem_data == file_data:
                print("Verification successful!")
            else:
                print("Verification failed! Data mismatch (ignore this for Hex file flashing)")
        except Exception as e:
            print(f"Verification skipped: {e}")

    # 6. 复位并运行 (可选)
    if reset:
        print("Reset and run program...")
        jlink.reset()

    # 断开连接
    jlink.close()
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="J-Link Firmware Flashing Tool")
    parser.add_argument("firmware", help="Firmware file path (.bin or .hex)")
    parser.add_argument("-d", "--device", default="GD32F103C8",
                        help="Target device model (default: GD32F103C8)")
    parser.add_argument("-a", "--addr", type=lambda x: int(x, 0), default=0x08000000,
                        help="Flash start address (default: 0x08000000)")
    parser.add_argument("--no-erase", action="store_true",
                        help="Do not erase chip before flashing")
    parser.add_argument("--no-verify", action="store_true",
                        help="Do not verify after flashing")
    parser.add_argument("--no-run", action="store_true",
                        help="Do not reset and run after flashing")

    args = parser.parse_args()

    if not os.path.exists(args.firmware):
        print(f"Error: Firmware file not found: {args.firmware}")
        exit(1)

    flash_gd32_with_jlink(args.firmware, device_name=args.device, start_addr=args.addr,
                          erase=not args.no_erase, verify=not args.no_verify,
                          reset=not args.no_run)