import re
from typing import List



class MsgParser:
    @staticmethod
    def tokenize(msg: str) -> List[str]:
        msg = msg.rstrip('\u0000')
        pattern = r'\(|\)|[-+]?\d*\.?\d+|[\\"]?\w+[\\"]?'
        # pattern = r'/(\(|[-\d\.]+|[\\\"\w]+|\))/g'
        return re.findall(pattern, msg)

    @staticmethod
    def parse(tokens: List[str], idx: int = 0):
        result = []
        while idx < len(tokens):
            tok = tokens[idx]
            if tok == '(':
                sublist, idx = MsgParser.parse(tokens, idx + 1)
                result.append(sublist)
            elif tok == ')':
                return result, idx + 1
            else:
                try:
                    if '.' in tok:
                        val = float(tok)
                    else:
                        val = int(tok)
                except ValueError:
                    val = tok
                result.append(val)
                idx += 1
        return result, idx

    @staticmethod
    def parse_msg(msg: str):
        tokens = MsgParser.tokenize(msg)
        parsed, _ = MsgParser.parse(tokens)
        return parsed[0] if parsed else None