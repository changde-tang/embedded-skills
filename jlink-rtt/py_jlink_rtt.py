import pylink
import time
import sys
import argparse
import threading
import queue


def parse_send_arg(s):
    """
    解析 --send 参数，格式：秒数:内容
    支持 \\n \\r \\t 转义
    例如：5:hello\\n  ->  (5.0, b'hello\n')
    """
    try:
        colon = s.index(":")
    except ValueError:
        raise argparse.ArgumentTypeError(f"--send 格式错误，应为 '秒数:内容'，收到: {s!r}")

    time_str = s[:colon]
    content_str = s[colon + 1:]

    try:
        t = float(time_str)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--send 时间解析失败，应为数字，收到: {time_str!r}")

    if t < 0:
        raise argparse.ArgumentTypeError(f"--send 时间不能为负数，收到: {t}")

    # 处理转义字符
    content_str = content_str.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t")
    data = content_str.encode("utf-8")

    return (t, data)


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
            data = jlink.memory_read(addr, step)
            data_bytes = bytes(data)

            pos = data_bytes.find(rtt_id)
            if pos != -1:
                cb_addr = addr + pos
                if cb_addr % 16 == 0:
                    print(f"  Found RTT identifier at 0x{cb_addr:08X}")
                    return cb_addr
        except Exception:
            continue

    return None


def read_rtt_logs(device_name="GD32F103C8", channel=0, timeout_sec=10,
                  debug_ret_type=False, rtt_cb_addr=None, send_schedule=None):
    """
    连接 J-Link 并实时读取 RTT 日志，支持定时发送上行数据
    :param device_name: 目标芯片型号
    :param channel: RTT 通道号 (0 通常是终端输出)
    :param timeout_sec: 运行时长（秒）
    :param debug_ret_type: 是否打印 rtt_read 返回值类型（调试用）
    :param rtt_cb_addr: RTT 控制块地址（None 则自动扫描）
    :param send_schedule: 发送计划列表，元素为 (delay_sec, bytes_data)
    """
    if send_schedule is None:
        send_schedule = []

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

    # 1. 启动 RTT 会话
    print("Starting RTT session...")
    try:
        try:
            jlink.rtt_stop()
        except Exception:
            pass

        if rtt_cb_addr is None:
            scanned_addr = find_rtt_control_block(jlink)
            if scanned_addr is None:
                print("Error: Unable to auto-scan RTT control block, please specify address manually")
                jlink.close()
                return
            rtt_cb_addr = scanned_addr

        jlink.rtt_start(rtt_cb_addr)
        time.sleep(0.1)

        num_up = jlink.rtt_get_num_up_buffers()
        num_down = jlink.rtt_get_num_down_buffers()
        print(f"RTT session started (control block: 0x{rtt_cb_addr:08X}, up: {num_up}, down: {num_down})")

    except Exception as e:
        print(f"RTT startup exception: {e}")
        print("Hint: If the control block address changed after firmware recompilation, please check the new address in J-Link RTT Viewer")
        jlink.close()
        return

    # 2. 注册定时发送任务
    #    使用队列将待发送数据传回主线程，避免跨线程直接调用 jlink
    send_queue = queue.Queue()
    timers = []

    def make_send_callback(delay, data):
        def callback():
            send_queue.put((delay, data))
        return callback

    for delay, data in send_schedule:
        if delay > timeout_sec:
            print(f"[WARN] --send {delay}s 超过总运行时间 {timeout_sec}s，已忽略")
            continue
        t = threading.Timer(delay, make_send_callback(delay, data))
        t.daemon = True
        t.start()
        timers.append(t)

    # 3. 打印发送计划
    if send_schedule:
        print("Send schedule:")
        for delay, data in sorted(send_schedule, key=lambda x: x[0]):
            preview = data.decode("utf-8", errors="replace").replace("\n", "\\n").replace("\r", "\\r")
            print(f"  @{delay:.2f}s  >>> {preview!r}")

    print(f"Listening on RTT channel {channel} (press Ctrl+C to stop)...")
    print("-" * 30)

    start_time = time.time()
    buffer_accumulator = []
    last_flush_time = time.time()
    FLUSH_INTERVAL = 0.01   # 最多 10ms 刷新一次输出
    EMPTY_SLEEP = 0.001     # 无数据时休眠 1ms
    BATCH_SIZE = 4096       # 单次最大读取量

    def flush_buffer():
        """刷新输出缓冲区"""
        nonlocal buffer_accumulator, last_flush_time
        if buffer_accumulator:
            sys.stdout.write("".join(buffer_accumulator))
            sys.stdout.flush()
            buffer_accumulator = []
            last_flush_time = time.time()

    def do_send(delay, data):
        """执行发送并打印发送日志"""
        preview = data.decode("utf-8", errors="replace").replace("\n", "\\n").replace("\r", "\\r")
        elapsed = time.time() - start_time
        # 发送前先刷新已有日志，保证输出顺序清晰
        flush_buffer()
        sys.stdout.write(f"\n[SEND @{elapsed:.2f}s] >>> {preview!r}\n")
        sys.stdout.flush()
        try:
            written = jlink.rtt_write(channel, list(data))
            if written != len(data):
                sys.stdout.write(f"[WARN] rtt_write: requested {len(data)} bytes, written {written} bytes\n")
                sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(f"[SEND ERROR] {e}\n")
            sys.stdout.flush()

    try:
        while True:
            # 检查超时
            if time.time() - start_time > timeout_sec:
                flush_buffer()
                print("\n[Timeout] Stopped reading.")
                break

            # 检查并执行待发送队列（由 Timer 线程投递）
            while not send_queue.empty():
                try:
                    delay, data = send_queue.get_nowait()
                    do_send(delay, data)
                except queue.Empty:
                    break

            # 读取 RTT 数据
            try:
                ret = jlink.rtt_read(channel, BATCH_SIZE)
            except Exception as e:
                print(f"\n[Read error] {e}")
                break

            if debug_ret_type:
                print(f"[Debug] rtt_read return type: {type(ret).__name__}")

            # 解析返回值（兼容不同 pylink 版本）
            if isinstance(ret, tuple) and len(ret) == 2:
                read_count, data = ret
            elif ret is None:
                read_count, data = 0, []
            else:
                data = ret
                read_count = len(data)

            if read_count > 0:
                text = bytes(data).decode("utf-8", errors="ignore")
                buffer_accumulator.append(text)

                current_time = time.time()
                total_buffered = sum(len(s) for s in buffer_accumulator)

                if total_buffered >= 512 or (current_time - last_flush_time) >= FLUSH_INTERVAL:
                    flush_buffer()

                continue
            else:
                flush_buffer()
                time.sleep(EMPTY_SLEEP)

    except KeyboardInterrupt:
        flush_buffer()
        print("\n[User interrupt] Stopped reading.")

    finally:
        # 取消所有未触发的定时器
        for t in timers:
            t.cancel()
        jlink.close()
        print("J-Link disconnected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="J-Link RTT Log Reader Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 只监听日志，60秒
  python py_jlink_rtt.py -d GD32F303RC -t 60

  # 监听10秒，第5秒发送 hello，第7秒发送 start_test
  python py_jlink_rtt.py -d GD32F303RC -t 10 --send 5:hello --send 7:start_test

  # 指定 RTT 控制块地址
  python py_jlink_rtt.py -d GD32F303RC -a 0x20000b90 -t 30 --send 10:reboot
        """
    )
    parser.add_argument("-d", "--device", default="GD32F303RC",
                        help="Target device model (default: GD32F303RC)")
    parser.add_argument("-c", "--channel", type=int, default=0,
                        help="RTT channel number (default: 0)")
    parser.add_argument("-t", "--timeout", type=int, default=60,
                        help="Runtime in seconds (default: 60)")
    parser.add_argument("-a", "--rtt-addr", type=lambda x: int(x, 0), default=None,
                        help="RTT control block address, e.g. 0x20000b90 (auto-scan if not specified)")
    parser.add_argument("--send", type=parse_send_arg, action="append", default=[],
                        metavar="SEC:DATA",
                        help="Send data at specified second, e.g. --send 5:hello (can be repeated)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug output, print rtt_read return type")

    args = parser.parse_args()

    read_rtt_logs(
        args.device,
        channel=args.channel,
        timeout_sec=args.timeout,
        debug_ret_type=args.debug,
        rtt_cb_addr=args.rtt_addr,
        send_schedule=args.send,
    )