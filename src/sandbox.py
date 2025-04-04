import ctypes
import struct

import psutil
import win32api
import win32con
import win32process

# Constants
PROCESS_ALL_ACCESS = 0x1F0FFF


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    """Defines MEMORY_BASIC_INFORMATION for VirtualQueryEx()"""
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
    ]


def get_process_pid(_process_name):
    """Find the PID of a process by name."""
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        # print(proc)
        if proc.name().lower() == _process_name.lower():
            return proc.pid
    return None


PROCESS_NAME = "exefile.exe"
# Find process PID
pid = get_process_pid(PROCESS_NAME)
print(f"Found {PROCESS_NAME} with PID {pid}")
PROCESS_HANDLE = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)


def read_memory(_address, size=4, offset=0, format_result=True):
    """Read memory from a given address in a process."""
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t()
    _address += offset * 8

    if ctypes.windll.kernel32.ReadProcessMemory(
            PROCESS_HANDLE,
            ctypes.c_void_p(_address),
            buffer,
            size,
            ctypes.byref(bytes_read)
    ):
        return "".join(f"{b:02X}" for b in buffer.raw) if format_result else buffer.raw
    else:
        error_code = ctypes.windll.kernel32.GetLastError()
        if error_code == 299:  # Partial read case
            # print(f"Warning: Partial read at {hex(address)} ({bytes_read.value} bytes read)")
            return "".join(f"{b:02X}" for b in buffer.raw[:bytes_read.value])
        else:
            print(f"Failed to read at {hex(address)} - Error: {error_code}")
            return None


def scan_memory(_value):
    """Scan a process's memory for a specific value."""
    _address = 0
    results = []

    if len(_value) % 2 == 1:
        _value = "0" + _value
    _value_bytes = bytes.fromhex(_value)

    # Memory scanning loop
    mem_info = MEMORY_BASIC_INFORMATION()
    while ctypes.windll.kernel32.VirtualQueryEx(
            PROCESS_HANDLE,
            ctypes.c_void_p(_address),
            ctypes.byref(mem_info),
            ctypes.sizeof(mem_info)
    ):
        if mem_info.State == win32con.MEM_COMMIT and mem_info.Protect & win32con.PAGE_READONLY | win32con.PAGE_READWRITE:
            buffer = read_memory(_address, mem_info.RegionSize, format_result=False)
            if buffer and _value_bytes in buffer:
                offset = buffer.find(_value_bytes)
                results.append(hex(_address + offset)[2:].upper())

        _address += mem_info.RegionSize
        if _address >= 0x7FFFFFFF0000:  # Stop at user-mode memory limit
            break

    return results


def format_bytes(byte_data):
    hex_str = " ".join(f"{b:02X}" for b in byte_data)  # Convert bytes to hex
    formatted = ""

    # Insert '|' every 16 characters (excluding spaces)
    count = 0
    for hex_pair in hex_str.split():
        formatted += hex_pair + " "
        count += 1
        if count % 8 == 0:
            formatted += "| "

    return formatted.strip()  # Remove trailing space


def format_search_data(hex_str, should_flip):
    hex_str = hex_str.replace(" ", "").upper()
    if not should_flip:
        return hex_str

    if len(hex_str) % 2 != 0:
        hex_str = "0" + hex_str

    # Split into byte pairs, reverse order, and join back
    reversed_hex = "".join(reversed([hex_str[i:i + 2] for i in range(0, len(hex_str), 2)]))

    # Pad with "0"s to make the length a multiple of 16
    while len(reversed_hex) % 16 != 0:
        reversed_hex += "00"

    return reversed_hex


def pointer(hex_str):
    return int(format_search_data(hex_str, True), 16)


def get_type_of(_address):
    type_pointer = read_memory(_address, 8, 1)
    if not type_pointer:
        return "None?"
    type_name_pointer = read_memory(pointer(type_pointer), 8, 3)
    if not type_name_pointer:
        return "None?"
    type_name_hex_value = read_memory(pointer(type_name_pointer), size=32, offset=0)
    type_name_string_value = bytes.fromhex(type_name_hex_value).decode("utf-8", errors="ignore").split("\x00", 1)[0]
    return type_name_string_value


def get_value_of_str(_address):
    size_bytes = read_memory(_address, size=8, offset=2)
    _size = int(format_search_data(size_bytes, True), 16)

    _value_bytes = read_memory(_address, size=_size, offset=4)
    str_value = bytes.fromhex(_value_bytes).decode("utf-8", errors="replace")
    return str_value


def get_value_of_unicode(_address):
    size_bytes = read_memory(_address, size=8, offset=2)
    _size = int(format_search_data(size_bytes, True), 16)
    start_address = pointer(read_memory(_address, size=8, offset=3))

    data_bytes = read_memory(start_address, size=2 * _size)
    return bytes.fromhex(data_bytes).decode("utf-16", errors="replace")


def get_value_of(_address):
    type_name = get_type_of(_address)
    if type_name == "str":
        return get_value_of_str(_address)
    if type_name == "unicode":
        return get_value_of_unicode(_address)
    else:
        return f"{type_name} at: {hex(_address)[2:].upper()}"


def is_dict_data_pointer(dict_data_pointer_address):
    int_data_pointer = int(dict_data_pointer_address, 16)
    int_data_pointer -= 5 * 8
    type_name = get_type_of(int_data_pointer)
    print(type_name)
    return type_name == "dict"


def find_dict_root(_dict_entry_address):
    _dict_address = None
    entry_count = 0
    while not _dict_address:
        print(f"analyzing dict entry at: {_dict_entry_address}")
        dict_entry = read_memory(int(_dict_entry_address, 16), 8 * 3)

        hash_bytes = dict_entry[0:16]
        key_bytes = dict_entry[16:32]
        value_bytes = dict_entry[32:48]

        if hash_bytes != "0000000000000000":
            entry_count += 1
            print(hash_bytes, key_bytes, value_bytes)
            print(get_value_of(pointer(key_bytes)))
            print(get_value_of(pointer(value_bytes)))

            refs_to_dict_entry = scan_memory(format_search_data(_dict_entry_address, True))
            for ref_to_entry in refs_to_dict_entry:
                if is_dict_data_pointer(ref_to_entry):
                    _dict_address = hex(int(ref_to_entry, 16) - (5 * 8))[2:].upper()

        _dict_entry_address = hex(int(_dict_entry_address, 16) - (3 * 8))[2:].upper()
    print(f"entry count: {entry_count}")
    return _dict_address


def read_dict(_dict_address):
    dict_data_pointer = pointer(read_memory(int(_dict_address, 16), size=8, offset=5))
    dict_length_hex = format_search_data(read_memory(int(_dict_address, 16), size=8, offset=3), True)
    dict_length = int(dict_length_hex, 16) + 1
    while dict_length > 0:
        dict_entry = read_memory(dict_data_pointer, size=8*3)

        hash_bytes = dict_entry[0:16]
        key_bytes = dict_entry[16:32]
        value_bytes = dict_entry[32:48]

        if hash_bytes != "0000000000000000":
            dict_length -= 1
            print(f"{get_value_of(pointer(key_bytes)):30} : {get_value_of(pointer(value_bytes))}")

        dict_data_pointer = dict_data_pointer + (3 * 8)


def read_list(_address):
    list_bytes = read_memory(int(_address, 16), size=4 * 8)

    length_bytes = list_bytes[32:48]
    length = int(format_search_data(length_bytes, True), 16)

    first_entry_address = pointer(list_bytes[48:64])
    for _ in range(length):
        entry_address = read_memory(first_entry_address, size=8)
        entry_pointer = pointer(entry_address)
        entry_type = get_type_of(entry_pointer)
        entry_value = get_value_of(entry_pointer)

        first_entry_address += 8
        print(f"{entry_type:20} : {entry_value}")

        # read_tuple(hex(pointer(entry_address))[2:].upper())


def read_tuple(_address):
    tuple_size_bytes = read_memory(int(_address, 16), size=8, offset=2)
    tuple_size = int(format_search_data(tuple_size_bytes, True), 16)

    tuple_entry_bytes = read_memory(int(_address, 16), size=8 * tuple_size, offset=3)
    for i in range(0, len(tuple_entry_bytes), 16):
        entry_pointer = pointer(tuple_entry_bytes[i:i+16])
        entry_type = get_type_of(entry_pointer)
        entry_value = get_value_of(entry_pointer)

        print(f"{entry_type:20} : {entry_value}")


def read_bunch(_address):
    read_dict(_address)




# process_name = input("Enter process name (e.g., notepad.exe): ").strip()

# address = int(input("Enter memory address (hex): "), 16)  # Convert hex input
address = int("1170B762CD8", 16)

search_value = format_search_data("24452080A50", True)

# ----------------------------------------

# formatted_value = format_bytes(read_memory(process_handle, address, 8 * 3, -1))
# print(formatted_value)

# search_address = scan_memory(process_handle, search_value)
# print(search_address)
# print(get_type_of(process_handle, int("1170B769630", 16)))


# dict_address = find_dict_root("28EBB1479C0")
# read_dict("28EBCB98990")
# read_list("28F26BE6F08")

# edit -> textbuffers -> tuple -> list -> bunch(same as dict) -> letters(unicode)
# edit dict
read_dict("28F29448618")
print("-------------")
# textbuffers
read_list("28F26BE6F08")
print("-------------")
# tuple[2]
read_tuple("28EBCB25888")
print("-------------")
# list
read_list("28EBCB2BA48")
print("-------------")
# Bunch
read_dict("28EBCD73428")
print("-------------")
# letters(Unicode)
print(get_value_of(int("28EBB0E74B0", 16)))

# read_list("28F26BE6F08")

# read_list("28EBCB2B808")

# key_value = read_memory(format_search_data(key_bytes, True))
# p = format_search_data("2309D0F61E0", True)
# a = scan_memory(process_handle, p)
# if a:
#     print(a)
# a1 = read_memory(process_handle, int("116DF848F60", 16), 8)
# p1 = format_search_data(a1, True)

# ----------------------------------------

ctypes.windll.kernel32.CloseHandle(PROCESS_HANDLE)
