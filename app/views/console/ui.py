import sys
import getpass
import textwrap

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}{msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}ERROR: {msg}{Colors.RESET}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}WARNING: {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.CYAN}{msg}{Colors.RESET}")

def sanitize_input(value, cast_type=str, allow_empty=False):
    """Sanitizes input by stripping whitespaces and control characters, and casting to type."""
    if isinstance(value, str):
        # Remove unprintable/control characters except standard whitespace
        value = "".join(ch for ch in value if ch.isprintable() or ch in ('\n', '\r', '\t')).strip()
    
    if not value and not allow_empty:
        raise ValueError("Input cannot be empty.")
        
    if not value and allow_empty:
        return None
        
    try:
        if cast_type == int:
            return int(value)
        elif cast_type == float:
            return float(value)
        else:
            return value
    except ValueError:
        raise ValueError(f"Invalid input type. Expected {cast_type.__name__}.")

def getpass_asterisk(prompt="Password: "):
    """Reads password character-by-character and echoes '*' for visual feedback."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    
    password = []
    try:
        import os
        if os.name == 'nt':
            import msvcrt
            while True:
                ch = msvcrt.getch()
                if ch in (b'\r', b'\n'):
                    sys.stdout.write('\r\n')
                    sys.stdout.flush()
                    break
                elif ch in (b'\x08', b'\x7f'):  # Backspace
                    if password:
                        password.pop()
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                elif ch == b'\x03':  # Ctrl+C
                    sys.stdout.write('\r\n')
                    sys.stdout.flush()
                    raise KeyboardInterrupt
                else:
                    try:
                        ch_str = ch.decode('utf-8')
                        password.append(ch_str)
                        sys.stdout.write('*')
                        sys.stdout.flush()
                    except Exception:
                        pass
        else:
            import termios
            import tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    ch = sys.stdin.read(1)
                    if ch in ('\r', '\n'):
                        sys.stdout.write('\r\n')
                        sys.stdout.flush()
                        break
                    elif ch in ('\x08', '\x7f'):  # Backspace
                        if password:
                            password.pop()
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                    elif ch == '\x03':  # Ctrl+C
                        sys.stdout.write('\r\n')
                        sys.stdout.flush()
                        raise KeyboardInterrupt
                    else:
                        password.append(ch)
                        sys.stdout.write('*')
                        sys.stdout.flush()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception:
        # Fallback if neither termios nor msvcrt is supported or non-interactive
        return getpass.getpass("")
        
    return "".join(password)

def get_input(prompt, cast_type=str, allow_empty=False, is_password=False, view_callback=None):
    """Helper to get and sanitize input from the user."""
    prompt = f"{Colors.YELLOW}{prompt}{Colors.RESET}"
    if view_callback and "[v to view]" not in prompt:
        prompt = prompt.rstrip(": \x1b[0m") + " [v to view]: "
        
    while True:
        try:
            is_mocked = type(input).__name__ != 'builtin_function_or_method' or not sys.stdin.isatty()
            if is_password and not is_mocked:
                try:
                    val = getpass_asterisk(prompt)
                except Exception:
                    val = input(prompt)
            else:
                val = input(prompt)
                
            if view_callback and str(val).strip().lower() == 'v':
                view_callback()
                continue
                
            return sanitize_input(val, cast_type, allow_empty)
        except ValueError as e:
            print_error(str(e))
        except EOFError:
            raise EOFError("Input cancelled (EOF).")
        except StopIteration:
            raise

def display_header(title):
    print(f"\n{Colors.CYAN}" + "="*58)
    print(title.center(58))
    print("="*58 + f"{Colors.RESET}")

def print_card(title, fields, width=58):
    """Prints a styled card with key-value fields. Multiline values are text-wrapped correctly."""
    print("┌" + "─"*(width-2) + "┐")
    print(f"│ {title:<{width-4}} │")
    print("├" + "─"*(width-2) + "┤")
    
    for key, value in fields:
        value_str = str(value)
        key_str = f"│ {key:<17} : "
        
        # Max width available for the value portion
        val_width = width - len(key_str) - 1
        val_width = max(1, val_width)
        
        # Wrap the text so it fits within the value portion
        wrapped_lines = textwrap.wrap(value_str, width=val_width)
        
        if not wrapped_lines:
            print(f"{key_str}{' ':<{val_width}}│")
        else:
            # First line prints with the key
            print(f"{key_str}{wrapped_lines[0]:<{val_width}}│")
            # Subsequent lines print with blank space for the key
            for line in wrapped_lines[1:]:
                blank_key = f"│ {'':<17}   "
                print(f"{blank_key}{line:<{val_width}}│")
                
    print("└" + "─"*(width-2) + "┘")
