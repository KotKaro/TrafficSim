import sys

class StorageMode:
    STORE_TRUE = 0
    STORE_VALUE = 1
    STORE_MULT_VALUES = 2

class OptionType:
    LONG_OPT = 0
    SHORT_OPT = 1
    POSITIONAL_OPT = 2
    EMPTY_OPT = 3

class DictionaryEntry:
    def __init__(self):
        self.pos = 0
        self.name = ""

class Option:
    def __init__(self):
        self.m_long_flag = ""
        self.m_short_flag = ""
        self.m_pos_flag = ""
        self.m_found = False
        self.m_required = False
        self.m_mode = StorageMode.STORE_TRUE
        self.m_help = ""
        self.m_dest = ""
        self.m_default_value = ""

    def help_doc(self):
        h = "    "
        if self.m_long_flag:
            h += self.m_long_flag
            if self.m_short_flag:
                h += ", "
        if self.m_short_flag:
            h += self.m_short_flag
        print(f"{h.ljust(25)}{self.m_help}")

    def found(self):
        return self.m_found

    def required(self, req=None):
        if req is not None:
            self.m_required = req
            return self
        return self.m_required

    def short_flag(self):
        return self.m_short_flag

    def long_flag(self):
        return self.m_long_flag

    def pos_flag(self):
        return self.m_pos_flag

    def mode(self, mode=None):
        if mode is not None:
            self.m_mode = mode
            return self
        return self.m_mode

    def help(self, help_text=None):
        if help_text:
            self.m_help = help_text
            return self
        return self.m_help

    def dest(self, dest=None):
        if dest:
            self.m_dest = dest
            return self
        return self.m_dest

    def default_value(self, default_value=None):
        if default_value is not None:
            self.m_default_value = str(default_value)
            return self
        return self.m_default_value

    def get_type(opt):
        if not opt:
            return OptionType.EMPTY_OPT

        if opt[0] == '-':
            if len(opt) == 2:
                return OptionType.SHORT_OPT
            else:
                return OptionType.LONG_OPT

        return OptionType.POSITIONAL_OPT

    def get_destination(first_option, second_option, first_opt_type, second_opt_type):
        def remove_character(s, c):
            if s.startswith(c):
                s = s[1:]
            return s

        if first_opt_type == OptionType.LONG_OPT:
            dest = remove_character(first_option, '-')
        elif second_opt_type == OptionType.LONG_OPT:
            dest = remove_character(second_option, '-')
        else:
            if first_opt_type == OptionType.SHORT_OPT:
                dest = remove_character(first_option, '-') + "_option"
            elif second_opt_type == OptionType.SHORT_OPT:
                dest = remove_character(second_option, '-') + "_option"
            else:
                if first_opt_type == OptionType.POSITIONAL_OPT:
                    dest = first_option
                elif second_opt_type == OptionType.POSITIONAL_OPT:
                    dest = second_option

        return dest

class OptionParser:
    def __init__(self, description="", create_help=True):
        self.m_options: list[Option] = []
        self.m_values = {}
        self.m_idx = {}
        self.m_description = description

        if create_help:
            self.add_option("--help", "-h").help("Display this help message and exit.")

    def add_option(self, first_option, second_option="") -> Option:
        self.m_options.append(self.add_option_internal(first_option, second_option))
        return self.m_options[-1]

    def add_option_internal(self, first_option, second_option):
        opt = Option()
        first_option_type = Option.get_type(first_option)
        second_option_type = Option.get_type(second_option)

        opt.m_dest = Option.get_destination(first_option, second_option,
                                           first_option_type, second_option_type)

        if first_option_type == OptionType.LONG_OPT:
            opt.m_long_flag = first_option
        elif second_option_type == OptionType.LONG_OPT:
            opt.m_long_flag = second_option

        if first_option_type == OptionType.SHORT_OPT:
            opt.m_short_flag = first_option
        elif second_option_type == OptionType.SHORT_OPT:
            opt.m_short_flag = second_option

        if first_option_type == OptionType.POSITIONAL_OPT:
            opt.m_pos_flag = first_option
        elif second_option_type == OptionType.POSITIONAL_OPT:
            opt.m_pos_flag = second_option

        self.m_idx[opt.m_dest] = len(self.m_options) - 1
        return opt

    def get_value(self, key: str) -> bool:
        try:
            return self.m_options[self.m_idx[key]].m_found
        except KeyError:
            raise KeyError(f"Tried to access value for field '{key}' which is not a valid field.")
        
    def get_value_str(self, key: str) -> str:
        try:
            return self.m_values[key][0]
        except KeyError:
            raise KeyError(f"Tried to access value for field '{key}' which is not a valid field.")

    def get_value_int(self, key: str) -> int:
        try:
            return int(self.m_values[key][0])
        except KeyError:
            raise KeyError(f"Tried to access value for field '{key}' which is not a valid field.")

    def get_value_float(self, key: str) -> float:
        try:
            return float(self.m_values[key][0])
        except KeyError:
            raise KeyError(f"Tried to access value for field '{key}' which is not a valid field.")

    def get_value_list(self, key: str) -> list[str]:
        try:
            return self.m_values[key]
        except KeyError:
            raise KeyError(f"Tried to access value for field '{key}' which is not a valid field.")

    def get_value_list_int(self, key):
        try:
            return list(map(int, self.m_values[key]))
        except KeyError:
            raise KeyError(f"Tried to access value for field '{key}' which is not a valid field.")

    def get_value_bool(self, key):
        try:
            return self.m_options[self.m_idx[key]].m_found
        except KeyError:
            raise KeyError(f"Tried to access value for field '{key}' which is not a valid field.")

    def get_value_dict(self):
        return self.m_values

    def eat_arguments(self, argv):
        arguments = argv[1:]
        arguments.append("-")  # Dummy way to solve problem with last argument of type "arg val1 val2"
        
        for arg in range(len(arguments)):
            match_found = False
            for option in self.m_options:
                if option.m_long_flag and arguments[arg].find(option.m_long_flag) == 0:
                    match_found = self.try_to_get_opt(arguments, arg, option, option.m_long_flag)
                elif option.m_short_flag and arguments[arg].find(option.m_short_flag) == 0:
                    match_found = self.try_to_get_opt(arguments, arg, option, option.m_short_flag)
                elif option.m_pos_flag and arguments[arg].find(option.m_pos_flag) == 0:
                    match_found = self.try_to_get_opt(arguments, arg, option, option.m_pos_flag)

                if match_found:
                    break

            if not match_found:
                if arguments[arg] != "-":
                    self.error(f"Unrecognized flag/option '{arguments[arg]}'")
        
        self.check_for_missing_args()

        if self.get_value("help"):
            self.help()

    def try_to_get_opt(self, arguments, arg, option, flag):
        if not flag:
            return False

        if arguments[arg].find(flag) != 0:
            return False

        if option.m_mode == StorageMode.STORE_TRUE:
            option.m_found = True
            return True

        if (option.m_mode == StorageMode.STORE_VALUE or
            option.m_mode == StorageMode.STORE_MULT_VALUES) and not option.m_found:
            if self.get_value_arg(arguments, arg, option, flag):
                option.m_found = True
                return True

        return False

    def get_value_arg(self, arguments, arg, option, flag):
        val = ""
        self.m_values[option.m_dest] = []
        
        if len(arguments[arg]) > len(flag):
            search_pt = arguments[arg].find('=')

            if search_pt == -1:
                search_pt = arguments[arg].find(' ')

                if search_pt == -1:
                    self.error(f"Error, long options ({flag}) require a '=' or space before a value.")
                    return False

                    vals = arguments[arg][search_pt + 1:].split()
                    self.m_values[option.m_dest].extend(vals)
            else:
                vals = arguments[arg][search_pt + 1:].split()
                self.m_values[option.m_dest].extend(vals)
        else:
            if arg + 1 >= len(arguments):
                if option.m_default_value == "":
                    self.error(f"error, flag '{flag}' requires an argument.")
                    return False

                if not self.m_values[option.m_dest]:
                    val = option.m_default_value
            else:
                if arguments[arg + 1][0] == '-':
                    if option.m_default_value == "":
                        self.error(f"error, flag '{flag}' requires an argument.")
                        return False

                    if not self.m_values[option.m_dest]:
                        val = option.m_default_value
                else:
                    val = arguments[arg + 1]
                    arg += 1

            if val:
                self.m_values[option.m_dest].append(val)
                return True

        while arguments[arg + 1][0] != '-':
            arg += 1
            self.m_values[option.m_dest].append(arguments[arg])
            if arg + 1 >= len(arguments):
                break

        return True

    def check_for_missing_args(self):
        missing = []
        for opt in self.m_options:
            if opt.m_required and not opt.m_found:
                missing.append(opt.m_dest)
            elif opt.m_default_value != "" and not opt.m_found:
                self.m_values[opt.m_dest].append(opt.m_default_value)
                opt.m_found = True

        if missing:
            self.error(f"Missing required flags: {', '.join(missing)}.")

    def error(self, e):
        print(f"In executable '{sys.argv[0]}':")
        print(e)
        sys.exit(1)

    def help(self):
        split = sys.argv[0].rfind('/')
        stripped_name = sys.argv[0][split + 1:]

        print(f"usage: {stripped_name} [-h] ", end="")
        for option in self.m_options:
            if option.m_required:
                if option.m_short_flag:
                    print(option.m_short_flag, end="")
                else:
                    print(option.m_long_flag, end="")

                if option.m_mode == StorageMode.STORE_VALUE:
                    print(" ARG ", end="")
                if option.m_mode == StorageMode.STORE_MULT_VALUES:
                    print(" ARG1 [ARG2 ...] ", end="")
        print("[options]\n")

        if self.m_description:
            print(self.m_description + "\n")
        
        for option in self.m_options:
            option.help_doc()
        
        sys.exit(0)
