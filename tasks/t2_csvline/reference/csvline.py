"""Reference solution (never shown to agents)."""


def parse_line(line, delimiter=","):
    if not isinstance(delimiter, str) or len(delimiter) != 1 or delimiter == '"':
        raise ValueError("delimiter must be one character other than a quote")
    if line.endswith("\r\n"):
        line = line[:-2]
    elif line.endswith("\n"):
        line = line[:-1]
    fields = []
    i, n = 0, len(line)
    while True:
        if i < n and line[i] == '"':
            i += 1
            buf = []
            while True:
                if i >= n:
                    raise ValueError("unterminated quoted field")
                ch = line[i]
                if ch == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        buf.append('"')
                        i += 2
                        continue
                    i += 1
                    break
                buf.append(ch)
                i += 1
            fields.append("".join(buf))
            if i == n:
                return fields
            if line[i] != delimiter:
                raise ValueError("text after closing quote")
            i += 1
        else:
            j = line.find(delimiter, i)
            if j == -1:
                fields.append(line[i:])
                return fields
            fields.append(line[i:j])
            i = j + 1
