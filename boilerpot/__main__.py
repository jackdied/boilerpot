from .boilerpot import extract_text

if __name__ == '__main__':
    import sys
    for fname in sys.argv[1:]:
        with open(fname) as f:
            title, body = extract_text(f.read())
        print title
        print body
