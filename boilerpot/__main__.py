from .boilerpot import extract_text

if __name__ == '__main__':
    import sys

    for fname in sys.argv[1:]:
        f = (sys.stdin if (fname == '-') else open(fname))
        with f:
            title, body = extract_text(f.read())
        print title
        print body
