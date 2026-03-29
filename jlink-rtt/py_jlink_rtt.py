import pylink
import time
import sys
import argparse

def find_rtt_control_block(jlink, start_addr=0x20000000, max_size=0x20000, step=0x1000):
    """
    扫描内存自动查找 RTT 控制块地址
    RTT 控制块以 "SEGGER RTT" 开头（16字节对齐）
    :param jlink: JLink 实例
    :param start_addr: 扫描起始地址 (默认 RAM 起始)
    :param max_size: 最大扫描范围
    :param step: 每次读取内存块大小
    :return: 控制块地址或 None
    """
    print(f"Scanning for RTT control block (range: 0x{start_addr:08X} - 0x{start_addr + max_size:08X})...")

    rtt_id = b"SEGGER RTT"

    for offset in range(0, max_size, step):
        addr = start_addr + offset
        try:
            # 读取内存块
            data = jlink.memory_read(addr, step)
            data_bytes = bytes(data)

            # 搜索 SEGGER RTT 标识符
            pos = data_bytes.find(rtt_id)
            if pos != -1:
                cb_addr = addr + pos
                # 验证对齐 (16字节对齐)
                if cb_addr % 16 == 0:
                    print(f"  Found RTT identifier at 0x{cb_addr:08X}")
                    return cb_addr
        except Exception:
            # 跳过不可读区域
            continue

    return None

def read_rtt_logs(device_name="GD32F103C8", channel=0, timeout_sec=10, debug_ret_type=False, rtt_cb_addr=None):
    """
    连接 J-Link 并实时读取 RTT 日志
    :param device_name: 目标芯片型号
    :param channel: RTT 通道号 (0 通常是终端输出)
    :param timeout_sec: 运行时长
    :param debug_ret_type: 是否打印 rtt_read 返回值类型(调试用)
    """
    jlink = pylink.JLink()
    
    print(f"Connecting to {device_name} ...")
    try:
        jlink.open()
        jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
        jlink.connect(device_name)
        print("Connection successful!")
    except pylink.errors.JLinkException as e:
        print(f"Connection failed: {e}")
        return

    # 1. 启动 RTT 会话（自动扫描或使用指定地址）
    print("Starting RTT session...")
    try:
        # 先尝试停止之前的 RTT 会话（如果有）
        try:
            jlink.rtt_stop()
        except:
            pass

        # 如果没有指定地址，自动扫描
        if rtt_cb_addr is None:
            scanned_addr = find_rtt_control_block(jlink)
            if scanned_addr is None:
                print("Error: Unable to auto-scan RTT control block, please specify address manually")
                jlink.close()
                return
            rtt_cb_addr = scanned_addr

        jlink.rtt_start(rtt_cb_addr)

        # 短暂等待 RTT 控制块就绪
        time.sleep(0.1)

        # 验证 RTT 是否成功启动
        num_up = jlink.rtt_get_num_up_buffers()
        num_down = jlink.rtt_get_num_down_buffers()
        print(f"RTT session started (control block: 0x{rtt_cb_addr:08X}, up: {num_up}, down: {num_down})")

    except Exception as e:
        print(f"RTT startup exception: {e}")
        print("Hint: If the control block address changed after firmware recompilation, please check the new address in J-Link RTT Viewer")
        jlink.close()
        return

    # 2. 开始读取循环
    print(f"Listening on RTT channel {channel} (press Ctrl+C to stop)...")
    print("-" * 30)

    start_time = time.time()
    buffer_accumulator = []  # 批量输出缓冲区
    last_flush_time = time.time()
    FLUSH_INTERVAL = 0.01  # 最多10ms刷新一次输出
    EMPTY_SLEEP = 0.001    # 无数据时休眠1ms
    BATCH_SIZE = 4096      # 单次最大读取量

    try:
        while True:
            # 检查超时
            if time.time() - start_time > timeout_sec:
                print("\n[Timeout] Stopped reading.")
                break

            # 读取数据（增大单次读取量，减少USB通信次数）
            try:
                ret = jlink.rtt_read(channel, BATCH_SIZE)
            except Exception as e:
                print(f"\n[Read error] {e}")
                break

            if debug_ret_type:
                print(f"[Debug] rtt_read return type: {type(ret).__name__}")

            # 解析返回值
            if isinstance(ret, tuple) and len(ret) == 2:
                read_count, data = ret
            elif ret is None:
                read_count, data = 0, []
            else:
                data = ret
                read_count = len(data)

            if read_count > 0:
                # 解码并加入缓冲区
                text = bytes(data).decode('utf-8', errors='ignore')
                buffer_accumulator.append(text)

                # 检查是否需要刷新：缓冲区较大 或 距上次刷新超过间隔
                current_time = time.time()
                total_buffered = sum(len(s) for s in buffer_accumulator)

                if total_buffered >= 512 or (current_time - last_flush_time) >= FLUSH_INTERVAL:
                    sys.stdout.write("".join(buffer_accumulator))
                    sys.stdout.flush()
                    buffer_accumulator = []
                    last_flush_time = current_time

                # 有数据时立即继续读取，不休眠（最大化吞吐）
                continue
            else:
                # 无数据时：先刷新残留缓冲区，然后短暂休眠
                if buffer_accumulator:
                    sys.stdout.write("".join(buffer_accumulator))
                    sys.stdout.flush()
                    buffer_accumulator = []
                    last_flush_time = time.time()

                time.sleep(EMPTY_SLEEP)

    except KeyboardInterrupt:
        # 退出前刷新残留数据
        if buffer_accumulator:
            sys.stdout.write("".join(buffer_accumulator))
            sys.stdout.flush()
        print("\n[User interrupt] Stopped reading.")

    finally:
        jlink.close()
        print("J-Link disconnected.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="J-Link RTT Log Reader Tool")
    parser.add_argument("-d", "--device", default="GD32F303RC", help="Target device model (default: GD32F303RC)")
    parser.add_argument("-c", "--channel", type=int, default=0, help="RTT channel number (default: 0)")
    parser.add_argument("-t", "--timeout", type=int, default=60, help="Runtime in seconds (default: 60)")
    parser.add_argument("-a", "--rtt-addr", type=lambda x: int(x, 0), default=None,
                        help="RTT control block address, e.g. 0x20000b90 (auto-scan if not specified)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output, print rtt_read return type")

    args = parser.parse_args()

    read_rtt_logs(args.device, channel=args.channel, timeout_sec=args.timeout,
                  debug_ret_type=args.debug, rtt_cb_addr=args.rtt_addr)