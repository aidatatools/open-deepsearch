import os, sys

def main():
    print("Hello World!")
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

if __name__ == '__main__':
    main()